"""
Data models for storing match and analysis data
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

@dataclass
class MatchConfig:
    """Match configuration settings"""
    # New fields for React integration
    player_position: str = 'near'  # 'near' or 'far'
    num_sets: int = 3  # 1, 3, or 5
    player_name: str = 'Player 1'
    opponent_name: str = 'Player 2'
    court_corners: List = field(default_factory=list)  # List of 4 corners [{x, y}, ...]
    
    # Original fields
    set_format: str = 'best_of_3'  # best_of_3, best_of_5, single_set
    games_per_set: int = 6
    tiebreak_at: int = 6  # Games to trigger tiebreak
    tiebreak_points: int = 7  # Points needed to win tiebreak
    deciding_set_format: str = 'match_tiebreak'  # match_tiebreak, regular, super_tiebreak
    match_tiebreak_points: int = 10
    use_ads: bool = True  # Traditional deuce/ad scoring
    use_no_ad: bool = False  # No-ad scoring (one point at deuce)
    
    def to_dict(self):
        return {
            'set_format': self.set_format,
            'games_per_set': self.games_per_set,
            'tiebreak_at': self.tiebreak_at,
            'tiebreak_points': self.tiebreak_points,
            'deciding_set_format': self.deciding_set_format,
            'match_tiebreak_points': self.match_tiebreak_points,
            'use_ads': self.use_ads,
            'use_no_ad': self.use_no_ad
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class CourtCalibration:
    """Court corner positions for calibration"""
    top_left: Tuple[int, int]
    top_right: Tuple[int, int]
    bottom_left: Tuple[int, int]
    bottom_right: Tuple[int, int]
    transform_matrix: Optional[List] = None

@dataclass
class Shot:
    """Individual shot data"""
    frame_number: int
    timestamp: float
    ball_position: Tuple[float, float]  # Court coordinates
    ball_position_pixels: Tuple[int, int]  # Pixel coordinates
    shot_type: str  # forehand, backhand, serve, volley, etc.
    direction: str  # crosscourt, down_line, center
    depth: str  # shallow, mid, deep
    player: int  # 1 or 2
    outcome: str  # winner, error, in_play
    speed: Optional[float] = None
    spin: Optional[str] = None

@dataclass
class Rally:
    """A single rally (point)"""
    rally_number: int
    shots: List[Shot] = field(default_factory=list)
    winner: int = 0  # 1 or 2, 0 if ongoing
    point_type: str = ''  # winner, forced_error, unforced_error
    duration: float = 0.0
    shot_count: int = 0

@dataclass
class Game:
    """A single game"""
    game_number: int
    set_number: int
    server: int  # 1 or 2
    rallies: List[Rally] = field(default_factory=list)
    score: Dict = field(default_factory=dict)  # {1: points, 2: points}
    winner: int = 0
    is_tiebreak: bool = False

@dataclass
class Set:
    """A single set"""
    set_number: int
    games: List[Game] = field(default_factory=list)
    score: Dict = field(default_factory=dict)  # {1: games, 2: games}
    winner: int = 0
    tiebreak_score: Optional[Dict] = None

@dataclass
class Match:
    """Complete match data"""
    match_id: str
    upload_date: datetime
    player_names: Dict = field(default_factory=lambda: {1: "Player 1", 2: "Player 2"})
    user_player: int = 1  # Which player number is the user (1 or 2)
    opponent_player: int = 2  # Which player number is the opponent
    config: MatchConfig = field(default_factory=MatchConfig)
    calibration: Optional[CourtCalibration] = None
    sets: List[Set] = field(default_factory=list)
    video_path: str = ''
    processing_status: str = 'pending'  # pending, processing, complete, failed
    winner: int = 0
    final_score: str = ''
    
    def get_all_rallies(self) -> List[Rally]:
        """Get all rallies from all sets and games"""
        rallies = []
        for set_data in self.sets:
            for game in set_data.games:
                rallies.extend(game.rallies)
        return rallies
    
    def get_all_shots(self) -> List[Shot]:
        """Get all shots from all rallies"""
        shots = []
        for rally in self.get_all_rallies():
            shots.extend(rally.shots)
        return shots
    
    def get_user_name(self) -> str:
        """Get the user's name"""
        return self.player_names.get(self.user_player, "You")
    
    def get_opponent_name(self) -> str:
        """Get the opponent's name"""
        return self.player_names.get(self.opponent_player, "Opponent")
    
    def is_user(self, player_number: int) -> bool:
        """Check if a player number is the user"""
        return player_number == self.user_player

@dataclass
class AnalysisResults:
    """Complete analysis results"""
    match_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Basic statistics
    total_shots: int = 0
    total_rallies: int = 0
    match_duration: float = 0.0
    
    # Shot DNA results
    shot_dna: Dict = field(default_factory=dict)
    
    # Counterfactual results
    counterfactual: Dict = field(default_factory=dict)
    
    # Momentum analysis
    momentum: Dict = field(default_factory=dict)
    
    # Shadow Self results (note: using shadow_self to match frontend)
    shadow_self: Dict = field(default_factory=dict)
    
    # Fatigue analysis
    fatigue: Dict = field(default_factory=dict)
    
    # Decision heatmap
    decision_heatmap: Dict = field(default_factory=dict)
    
    # Chaos theory
    chaos_theory: Dict = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'shotDNA': self.shot_dna,
            'counterfactual': self.counterfactual,
            'momentum': self.momentum,
            'shadowSelf': self.shadow_self,
            'fatigue': self.fatigue,
            'decisionHeatmap': self.decision_heatmap,
            'chaosTheory': self.chaos_theory,
        }
    
    def to_json(self):
        """Convert to JSON-serializable dict"""
        return {
            'match_id': self.match_id,
            'generated_at': self.generated_at.isoformat() if hasattr(self.generated_at, 'isoformat') else str(self.generated_at),
            'total_shots': self.total_shots,
            'total_rallies': self.total_rallies,
            'match_duration': self.match_duration,
            'shot_dna': self.shot_dna,
            'counterfactual': self.counterfactual,
            'momentum': self.momentum,
            'shadow_self': self.shadow_self,
            'fatigue': self.fatigue,
            'decision_heatmap': self.decision_heatmap,
            'chaos_theory': self.chaos_theory
        }
    
    def format_for_user(self, match: Match) -> Dict:
        """Format results with 'You' and 'Opponent' labels"""
        formatted = self.to_json()
        
        # Helper function to replace player references
        def replace_player_refs(obj):
            if isinstance(obj, dict):
                new_obj = {}
                for key, value in obj.items():
                    # Replace player_1 or player_2 with you/opponent
                    new_key = key
                    if f'player_{match.user_player}' in key:
                        new_key = key.replace(f'player_{match.user_player}', 'you')
                    elif f'player_{match.opponent_player}' in key:
                        new_key = key.replace(f'player_{match.opponent_player}', 'opponent')
                    
                    new_obj[new_key] = replace_player_refs(value)
                return new_obj
            elif isinstance(obj, list):
                return [replace_player_refs(item) for item in obj]
            else:
                return obj
        
        return replace_player_refs(formatted)
