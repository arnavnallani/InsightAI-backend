"""
Strategic Flow Engine - Core Data Structures

This module defines the foundational data structures for the integrated
strategic narrative system that combines minimax decision trees,
opponent tendency learning, and impact propagation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


# ============================================================================
# Shot and Decision Types
# ============================================================================

class ShotType(Enum):
    """Types of tennis shots"""
    FOREHAND = "forehand"
    BACKHAND = "backhand"
    FOREHAND_VOLLEY = "forehand_volley"
    BACKHAND_VOLLEY = "backhand_volley"
    SERVE = "serve"
    RETURN = "return"
    OVERHEAD = "overhead"
    DROP_SHOT = "drop_shot"
    LOB = "lob"


class ShotDirection(Enum):
    """Shot direction on court"""
    CROSSCOURT = "crosscourt"
    DOWN_THE_LINE = "down_the_line"
    INSIDE_OUT = "inside_out"
    INSIDE_IN = "inside_in"
    CENTER = "center"


class ShotDepth(Enum):
    """Shot depth categories"""
    DEEP = "deep"  # Near baseline
    MID = "mid"    # Mid-court
    SHORT = "short"  # Near service line or net


class ShotIntent(Enum):
    """Strategic intent of shot"""
    ATTACK = "attack"
    NEUTRALIZE = "neutralize"
    DEFEND = "defend"
    SETUP = "setup"


# ============================================================================
# Match State Representation
# ============================================================================

@dataclass
class CourtPosition:
    """Position on tennis court (normalized 0-4 scale)"""
    x: float  # 0=Ad side, 4=Deuce side
    y: float  # 0=Baseline, 4=Net
    
    def zone_name(self) -> str:
        """Get friendly zone name"""
        y_zone = "Net" if self.y >= 3 else "Volley" if self.y >= 2 else "Mid" if self.y >= 1 else "Baseline"
        x_zone = "Ad Side" if self.x < 1.5 else "Center" if self.x < 2.5 else "Deuce Side"
        return f"{x_zone} {y_zone}"


@dataclass
class ShotState:
    """State of a single shot"""
    shot_type: ShotType
    direction: ShotDirection
    depth: ShotDepth
    speed_mph: float
    spin_rpm: int
    position: CourtPosition
    intent: ShotIntent
    quality: float  # 0-1 scale of execution quality
    

@dataclass
class MatchState:
    """Complete state at a point in the match"""
    # Score context
    set_num: int
    game_score: Tuple[int, int]  # (player_games, opponent_games)
    point_score: str  # "0-0", "15-0", "30-15", etc.
    
    # Player states
    player_energy: float  # 0-1 scale
    opponent_energy: float
    player_momentum: float  # -1 to 1 scale (-1=very negative, 1=very positive)
    
    # Shot sequence context (last N shots)
    recent_shots: List[ShotState]
    rally_length: int
    
    # Player position
    player_position: CourtPosition
    opponent_position: CourtPosition
    
    # Strength/weakness context
    player_strengths: List[ShotType]
    player_weaknesses: List[ShotType]
    opponent_strengths: List[ShotType]
    opponent_weaknesses: List[ShotType]


# ============================================================================
# Decision Tree Nodes
# ============================================================================

@dataclass
class DecisionNode:
    """Node in the minimax decision tree"""
    # State information
    state: MatchState
    depth: int
    
    # Decision made at this node
    decision: Optional[ShotState] = None
    
    # Tree structure
    children: List['DecisionNode'] = field(default_factory=list)
    parent: Optional['DecisionNode'] = None
    
    # Minimax values
    value: float = 0.0  # Composite evaluation score
    alpha: float = float('-inf')
    beta: float = float('inf')
    
    # Value components (for explainability)
    point_equity: float = 0.0  # Probability of winning the point
    momentum_impact: float = 0.0  # Change in momentum
    fatigue_delta: float = 0.0  # Change in fatigue differential
    strength_exploitation: float = 0.0  # How well it uses strengths/exploits weaknesses
    
    # Narrative metadata
    description: str = ""
    rationale: str = ""
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    def is_max_node(self) -> bool:
        """True if this is a player decision node (maximizing)"""
        return self.depth % 2 == 0
    
    def is_min_node(self) -> bool:
        """True if this is an opponent decision node (minimizing)"""
        return not self.is_max_node()


# ============================================================================
# Opponent Tendency Learning
# ============================================================================

@dataclass
class ShotContext:
    """Context for shot tendency learning"""
    shot_type: ShotType
    direction: ShotDirection
    depth: ShotDepth
    pressure_level: str  # "low", "medium", "high"
    court_zone: str
    rally_length_bin: str  # "short", "medium", "long"
    
    def __hash__(self):
        return hash((self.shot_type, self.direction, self.depth, 
                    self.pressure_level, self.court_zone, self.rally_length_bin))


@dataclass
class ShotResponse:
    """Opponent's response to a shot"""
    shot_type: ShotType
    direction: ShotDirection
    depth: ShotDepth
    quality: float  # 0-1 scale
    is_error: bool
    is_winner: bool
    
    def __hash__(self):
        # Round quality to 1 decimal for hashing to avoid float precision issues
        return hash((self.shot_type, self.direction, self.depth, 
                    round(self.quality, 1), self.is_error, self.is_winner))


@dataclass
class BreakdownThreshold:
    """When opponent breaks under repeated stress"""
    shot_sequence: List[ShotType]  # Sequence that causes breakdown
    avg_shots_to_break: float  # Average shots before weak response
    breakdown_shot_types: Dict[ShotType, float]  # Distribution of weak shots given
    confidence: float  # 0-1 confidence in this pattern


@dataclass
class OpponentTendencyProfile:
    """Learned tendencies of opponent"""
    # Conditional probabilities: given context, what does opponent do?
    # P(response | context)
    response_probabilities: Dict[ShotContext, Dict[ShotResponse, float]] = field(default_factory=dict)
    
    # Breakdown patterns: what sequences make them break?
    breakdown_thresholds: List[BreakdownThreshold] = field(default_factory=list)
    
    # Strength/weakness zones
    strong_zones: List[str] = field(default_factory=list)  # Court zones where they're strong
    weak_zones: List[str] = field(default_factory=list)    # Court zones where they're weak
    
    # Fatigue patterns
    fatigue_response_degradation: Dict[str, float] = field(default_factory=dict)  # How response quality degrades
    
    # Pressure handling
    pressure_error_rate: Dict[str, float] = field(default_factory=dict)  # Error rate at different pressures


# ============================================================================
# Impact Models
# ============================================================================

@dataclass
class MomentumShift:
    """Change in momentum from a decision"""
    before: float  # Momentum before (-1 to 1)
    after: float   # Momentum after
    delta: float   # Change
    ripple_points: int  # How many subsequent points are affected
    win_prob_change: float  # Change in probability of winning next point


@dataclass
class FatigueImpact:
    """Change in fatigue from a decision"""
    player_fatigue_before: float
    player_fatigue_after: float
    opponent_fatigue_before: float
    opponent_fatigue_after: float
    rally_length_change: int  # Change in rally length
    adrenaline_boost: float  # Adrenaline boost from momentum


@dataclass
class DecisionQualityImpact:
    """How decision quality changes based on court position"""
    court_zone: str
    player_decision_quality: float  # 0-1 scale
    opponent_decision_quality: float
    zone_advantage: str  # "player", "opponent", "neutral"


# ============================================================================
# Flow Narrative Structure
# ============================================================================

@dataclass
class CriticalJuncture:
    """A critical moment in the match narrative"""
    # When and where
    match_state: MatchState
    score_string: str  # "Set 1, 3-3, 30-30"
    rally_num: int
    
    # What happened
    actual_decision: ShotState
    actual_outcome: str  # "lost_point", "won_point"
    
    # What should have happened
    optimal_decision: ShotState
    optimal_path: List[DecisionNode]  # Full decision tree path
    
    # Impact if optimal path taken
    momentum_shift: MomentumShift
    fatigue_impact: FatigueImpact
    butterfly_effect: str  # Narrative description of ripple effects
    
    # Why this matters
    importance_score: float  # 0-1 scale
    explanation: str


@dataclass
class StrategicPath:
    """Alternative strategic path (counterfactual)"""
    name: str  # "Backhand Exploitation Strategy"
    description: str
    
    # The decision tree
    root_decision: DecisionNode
    expected_shots_to_success: float
    success_probability: float
    
    # Compared to what actually happened
    points_gained: int
    momentum_advantage: float
    fatigue_advantage: float


@dataclass
class RippleCascade:
    """How one decision cascades through the match"""
    trigger_juncture: CriticalJuncture
    affected_points: List[int]  # Rally numbers affected
    
    # Cumulative effects
    total_momentum_shift: float
    total_points_swing: int
    fatigue_differential_change: float
    
    # Probability shifts
    set_win_prob_change: float
    match_win_prob_change: float
    
    narrative: str  # Story of how it cascades


@dataclass
class FlowNarrativeNode:
    """A node in the strategic flow narrative"""
    section_type: str  # "hero_context", "critical_juncture", "ripple_cascade", "action_plan"
    title: str
    content: str  # Main narrative text
    
    # Supporting data
    visual_type: str  # "decision_tree", "momentum_graph", "court_heatmap", etc.
    visual_data: Dict[str, Any]
    
    # Metrics
    metrics: Dict[str, float]
    
    # References
    related_junctures: List[int] = field(default_factory=list)
    related_paths: List[str] = field(default_factory=list)


@dataclass
class StrategicFlowNarrative:
    """Complete strategic narrative for the match"""
    # Overview
    match_summary: str
    key_insight: str  # One-sentence main takeaway
    
    # The flow
    narrative_nodes: List[FlowNarrativeNode]
    
    # Critical moments
    critical_junctures: List[CriticalJuncture]
    
    # Strategic alternatives
    strategic_paths: List[StrategicPath]
    
    # Ripple effects
    ripple_cascades: List[RippleCascade]
    
    # Action plan
    top_recommendations: List[Dict[str, str]]
    practice_drills: List[Dict[str, str]]
    expected_improvement: str
