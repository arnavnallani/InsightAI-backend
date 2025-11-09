"""
SIMPLIFIED MINIMAX ADAPTER
===========================
Converts SwingVision rally data → Minimax MatchState for counterfactual analysis.

This adapter bridges the gap between:
- INPUT: SwingVision shot data (type, speed, placement, trajectory, spin)
- OUTPUT: MatchState for minimax engine (court positions, tactical state, fatigue)

Enables two-tier minimax analysis:
- Supporting rallies: depth=2, branching=3, rollouts=10
- Critical moments: depth=3, branching=3, rollouts=15
"""

from typing import Dict, Any, List, Optional, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pattern_utils import Rally, Shot
from strategic_flow_models import (
    MatchState, 
    ShotType, 
    ShotDirection, 
    ShotDepth,
    CourtPosition,
    ShotState,
    OpponentTendencyProfile
)

try:
    from minimax_core import MinimaxSimulationCore
    MINIMAX_AVAILABLE = True
    print("✅ minimax_core imported successfully!", file=sys.stderr)
except ImportError as e:
    MINIMAX_AVAILABLE = False
    print(f"❌ Warning: minimax_core import failed: {e}", file=sys.stderr)
    print(f"   sys.path: {sys.path[:3]}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)


class SimplifiedMinimaxAdapter:
    """
    Converts SwingVision rallies to minimax analysis.
    
    Two-tier configuration:
    - Supporting: Quick counterfactual (depth=2)
    - Critical: Deep tactical analysis (depth=3)
    """
    
    def __init__(
        self,
        depth_supporting: int = 2,
        depth_critical: int = 3,
        branching: int = 3,
        rollouts_supporting: int = 10,
        rollouts_critical: int = 15
    ):
        """Initialize adapter with two-tier minimax configuration"""
        self.depth_supporting = depth_supporting
        self.depth_critical = depth_critical
        self.branching = branching
        self.rollouts_supporting = rollouts_supporting
        self.rollouts_critical = rollouts_critical
        
        # Initialize minimax engines if available
        if MINIMAX_AVAILABLE:
            # Create default opponent profile (can be learned from data later)
            default_profile = OpponentTendencyProfile()
            
            self.minimax_supporting = MinimaxSimulationCore(
                opponent_profile=default_profile,
                max_depth=depth_supporting,
                num_rollouts=rollouts_supporting
            )
            self.minimax_critical = MinimaxSimulationCore(
                opponent_profile=default_profile,
                max_depth=depth_critical,
                num_rollouts=rollouts_critical
            )
        else:
            self.minimax_supporting = None
            self.minimax_critical = None
    
    def analyze_rally_counterfactual(
        self, 
        rally: Rally,
        your_shot_index: int,
        is_critical: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a specific shot in a rally for counterfactual recommendation.
        
        Args:
            rally: Rally object from pattern detection
            your_shot_index: Index of your shot to analyze
            is_critical: If True, use deeper analysis (depth=3, rollouts=15)
            
        Returns:
            Dictionary with:
            - your_shot: What you actually did
            - your_expected_value: Probability of winning the point
            - optimal_shot: What you should have done
            - optimal_expected_value: Probability if you had done optimal
            - improvement: Difference in expected values
            - tactical_reasoning: Why optimal is better (geometric, tactical)
        """
        # Convert rally to MatchState
        match_state = self._rally_to_match_state(rally, your_shot_index)
        
        # Get your actual shot
        your_shot = rally.shots[your_shot_index]
        
        # If minimax not available, return stub analysis
        if not MINIMAX_AVAILABLE or self.minimax_supporting is None:
            return self._stub_counterfactual(your_shot, rally.outcome)
        
        # Choose minimax engine based on criticality
        minimax = self.minimax_critical if is_critical else self.minimax_supporting
        
        # Run minimax to find optimal shot
        try:
            optimal_result = minimax.find_optimal_shot(match_state)
            
            # Calculate expected values
            your_expected_value = self._estimate_shot_value(your_shot, match_state)
            optimal_expected_value = optimal_result.get('expected_value', 0.6)
            
            # Get optimal shot and ensure it has placement coordinates
            optimal_shot_data = optimal_result.get('optimal_shot', {})
            
            # DEBUG: Check if placement is present
            if 'placement' in optimal_shot_data:
                print(f"✅ Using minimax placement: {optimal_shot_data['placement']}", file=sys.stderr)
            else:
                print(f"⚠️  WARNING: No placement in minimax result, using fallback", file=sys.stderr)
            
            # Add placement coordinates if missing
            if optimal_shot_data and 'placement' not in optimal_shot_data:
                optimal_shot_data = self._add_placement_to_optimal_shot(
                    optimal_shot_data,
                    your_shot
                )
            
            # Generate tactical reasoning
            tactical_reasoning = self._generate_tactical_reasoning(
                your_shot, 
                optimal_shot_data,
                match_state
            )
            
            return {
                'your_shot': self._shot_to_dict(your_shot),
                'your_expected_value': your_expected_value,
                'optimal_shot': optimal_shot_data,
                'optimal_expected_value': optimal_expected_value,
                'improvement': optimal_expected_value - your_expected_value,
                'tactical_reasoning': tactical_reasoning,
                'depth_analyzed': self.depth_critical if is_critical else self.depth_supporting,
                'rollouts': self.rollouts_critical if is_critical else self.rollouts_supporting
            }
        except Exception as e:
            print(f"Minimax analysis error: {e}", file=sys.stderr)
            return self._stub_counterfactual(your_shot, rally.outcome)
    
    def _rally_to_match_state(self, rally: Rally, shot_index: int) -> MatchState:
        """
        Convert SwingVision rally to minimax MatchState.
        
        Extracts:
        - Player positions from shot placements
        - Score and pressure context
        - Fatigue level from set/game
        - Shot history for tendency learning
        """
        shot = rally.shots[shot_index]
        
        # Determine player positions from previous shots
        if shot_index > 0:
            prev_shot = rally.shots[shot_index - 1]
            you_x, you_y = self._estimate_player_position(shot, prev_shot)
            opp_x, opp_y = self._estimate_opponent_position(prev_shot, shot)
        else:
            # Initial serve position
            you_x, you_y = 50, 95  # Baseline center
            opp_x, opp_y = 50, 5   # Opponent baseline
        
        # Score context
        your_games, opp_games = self._parse_game_score(rally.game_score)
        
        # Fatigue estimation (increases with set/game progression)
        total_games = your_games + opp_games
        fatigue_you = min(total_games / 20, 0.3)  # Max 30% fatigue
        fatigue_opp = min(total_games / 20, 0.3)
        
        # Create court positions (convert from 0-100 to 0-4 scale)
        player_pos = CourtPosition(x=you_x / 25, y=you_y / 25)
        opponent_pos = CourtPosition(x=opp_x / 25, y=opp_y / 25)
        
        # Create MatchState with correct parameters
        match_state = MatchState(
            set_num=rally.set_number,
            game_score=(your_games, opp_games),
            point_score=rally.point_score,
            player_energy=1.0 - fatigue_you,
            opponent_energy=1.0 - fatigue_opp,
            player_momentum=0.0,  # Neutral momentum
            recent_shots=[],  # Empty for now
            rally_length=len(rally.shots),
            player_position=player_pos,
            opponent_position=opponent_pos,
            player_strengths=[],  # Could be learned from data
            player_weaknesses=[],
            opponent_strengths=[],
            opponent_weaknesses=[]
        )
        
        return match_state
    
    def _parse_game_score(self, game_score: str) -> Tuple[int, int]:
        """Parse game score like '3-2' into (your_games, opp_games)"""
        try:
            parts = game_score.split('-')
            return (int(parts[0]), int(parts[1]))
        except:
            return (0, 0)
    
    def _stub_rally_to_match_state_old(
        self, 
        rally: Rally, 
        shot_index: int
    ) -> MatchState:
        """OLD VERSION - DEPRECATED - keeping for reference"""
        shot = rally.shots[shot_index]
        
        # Determine player positions from previous shots
        if shot_index > 0:
            prev_shot = rally.shots[shot_index - 1]
            you_x, you_y = self._estimate_player_position(shot, prev_shot)
            opp_x, opp_y = self._estimate_opponent_position(prev_shot, shot)
        else:
            # Initial serve position
            you_x, you_y = 50, 95  # Baseline center
            opp_x, opp_y = 50, 5   # Opponent baseline
        
        # Score context
        your_games, opp_games = self._parse_game_score(rally.game_score)
        
        # Fatigue estimation (increases with set/game progression)
        total_games = your_games + opp_games
        fatigue_you = min(total_games / 20, 0.3)  # Max 30% fatigue
        fatigue_opp = min(total_games / 20, 0.3)
        
        # Create OLD MatchState format
        match_state_old = MatchState(
            you_position_x=you_x,
            you_position_y=you_y,
            opponent_position_x=opp_x,
            opponent_position_y=opp_y,
            score_you=your_games,
            score_opponent=opp_games,
            is_break_point=rally.is_break_point,
            is_game_point=rally.is_game_point,
            fatigue_you=fatigue_you,
            fatigue_opponent=fatigue_opp,
            serving=rally.serving
        )
        
        return match_state
    
    def _estimate_player_position(
        self, 
        current_shot: Shot, 
        prev_shot: Shot
    ) -> Tuple[float, float]:
        """
        Estimate player position based on where they're hitting from.
        
        Uses previous shot placement + shot type to infer position.
        """
        # If previous shot was deep, player is likely at baseline
        if prev_shot.y > 70:
            y = 90  # Near baseline
        elif prev_shot.y < 40:
            y = 60  # Moved forward
        else:
            y = 75  # Mid court
        
        # X position based on previous shot direction
        x = prev_shot.x
        
        return x, y
    
    def _estimate_opponent_position(
        self, 
        their_shot: Shot, 
        your_response: Shot
    ) -> Tuple[float, float]:
        """Estimate opponent position (mirror of player estimation)"""
        if their_shot.y > 70:
            y = 10  # Near opponent baseline
        elif their_shot.y < 40:
            y = 40  # They moved forward
        else:
            y = 25  # Mid court
        
        x = their_shot.x
        
        return x, y
    
    
    def _estimate_shot_value(self, shot: Shot, state: MatchState) -> float:
        """
        Estimate expected value of a shot (probability of winning point).
        
        Uses simplified heuristics:
        - Errors = 0.0
        - Winners = 1.0
        - Otherwise, estimate based on shot quality
        """
        if shot.is_error:
            return 0.0
        if shot.is_winner:
            return 1.0
        
        # Heuristic: aggressive shots = higher value
        base_value = 0.5
        
        # Speed bonus
        if shot.speed > 75:
            base_value += 0.1
        elif shot.speed < 55:
            base_value -= 0.1
        
        # Trajectory bonus (low = aggressive)
        if shot.trajectory == 'low':
            base_value += 0.05
        elif shot.trajectory == 'high':
            base_value -= 0.05
        
        # Depth bonus
        if shot.y > 75:  # Deep shot
            base_value += 0.05
        
        return max(0.0, min(1.0, base_value))
    
    def _generate_tactical_reasoning(
        self, 
        your_shot: Shot,
        optimal_shot: Optional[Dict],
        state: MatchState
    ) -> str:
        """
        Generate geometric and tactical reasoning for why optimal is better.
        
        Example:
        "Crosscourt = 82ft diagonal (longest court distance), 3ft net (lowest).
        Your DTL = 60ft distance, 3.5ft net height. Crosscourt gives 37% more margin."
        """
        if not optimal_shot:
            return "Optimal shot not determined"
        
        # Crosscourt vs DTL reasoning
        your_direction = self._classify_direction(your_shot.x)
        optimal_direction = optimal_shot.get('direction', 'crosscourt')
        
        if optimal_direction == 'crosscourt' and your_direction == 'dtl':
            return (
                "Crosscourt = 82ft diagonal (longest court distance), 3ft net height (lowest point). "
                "Your down-the-line = 60ft distance, 3.5ft net. "
                "Crosscourt provides 37% more margin for error with same power."
            )
        elif optimal_direction == 'dtl' and your_direction == 'crosscourt':
            return (
                "Down-the-line changes rally direction, catching opponent moving wrong way. "
                "From this position, DTL creates 15-20 degree angle opponent must cover. "
                "Forces opponent to reverse direction = late to ball = weak reply."
            )
        elif 'speed' in optimal_shot and optimal_shot.get('speed', 0) > your_shot.speed:
            speed_diff = optimal_shot.get('speed', 0) - your_shot.speed
            return (
                f"Optimal shot {speed_diff:.0f}mph faster puts opponent under time pressure. "
                f"At {optimal_shot.get('speed', 75):.0f}mph, opponent has 0.15s less reaction time. "
                "Prevents them from setting up and attacking."
            )
        else:
            return "Optimal shot provides better tactical positioning and point control"
    
    def _classify_direction(self, x: float) -> str:
        """Classify shot direction from x coordinate"""
        if x < 25 or x > 75:
            return 'dtl'
        else:
            return 'crosscourt'
    
    def _add_placement_to_optimal_shot(
        self, 
        optimal_shot: Dict[str, Any],
        your_shot: Shot
    ) -> Dict[str, Any]:
        """
        Add placement coordinates to optimal shot based on direction and depth.
        
        Args:
            optimal_shot: Optimal shot dict from minimax (might be missing placement)
            your_shot: Your actual shot for context
            
        Returns:
            Enhanced optimal shot with placement coordinates
        """
        # Make a copy to avoid modifying the original
        enhanced = optimal_shot.copy()
        
        # Get direction from optimal shot
        direction = enhanced.get('direction', 'crosscourt')
        shot_type = enhanced.get('shot_type', your_shot.shot_type)
        
        # Calculate optimal placement coordinates based on direction and depth
        if direction == 'crosscourt':
            # Crosscourt placement depends on which side
            if shot_type == 'Forehand' or your_shot.x > 50:
                # Forehand crosscourt to ad side
                optimal_x = 25
            else:
                # Backhand crosscourt to deuce side
                optimal_x = 75
        else:
            # Down-the-line
            if shot_type == 'Forehand' or your_shot.x > 50:
                # Forehand DTL to deuce side
                optimal_x = 85
            else:
                # Backhand DTL to ad side
                optimal_x = 15
        
        # Vary depth based on tactical situation
        import random
        
        # 70% deep, 30% mid-depth for variety
        if random.random() < 0.7:
            optimal_y = 10 + random.randint(0, 10)  # Deep: 10-20
        else:
            optimal_y = 25 + random.randint(0, 10)  # Mid: 25-35
        
        enhanced['placement'] = {'x': optimal_x, 'y': optimal_y}
        
        return enhanced
    
    def _shot_to_dict(self, shot: Shot) -> Dict[str, Any]:
        """Convert Shot object to dictionary for JSON output"""
        return {
            'shot_type': shot.shot_type,
            'speed': shot.speed,
            'placement': {'x': shot.x, 'y': shot.y},
            'trajectory': shot.trajectory,
            'spin': shot.spin,
            'depth': shot.depth
        }
    
    def _stub_counterfactual(self, shot: Shot, outcome: str) -> Dict[str, Any]:
        """
        Stub implementation when minimax is not available.
        
        Returns plausible counterfactual based on simple heuristics.
        """
        # Simple heuristic: if you lost, suggest opposite direction
        your_ev = 0.35 if outcome == 'lost' else 0.65
        optimal_ev = 0.65 if outcome == 'lost' else 0.70
        
        optimal_direction = 'crosscourt' if shot.x < 25 or shot.x > 75 else 'down-the-line'
        
        # CRITICAL FIX: Don't recommend Serve for groundstrokes!
        # Only keep shot_type if it's a valid groundstroke
        optimal_shot_type = shot.shot_type
        if shot.shot_type == 'Serve':
            # If original was a serve, keep it as serve (serve rally)
            optimal_shot_type = 'Serve'
        elif shot.shot_type not in ['Forehand', 'Backhand', 'Volley', 'Overhead']:
            # If invalid shot type, default to Forehand
            optimal_shot_type = 'Forehand'
        # Otherwise keep the original groundstroke type (Forehand stays Forehand, etc.)
        
        # Calculate optimal placement coordinates based on direction and depth
        if optimal_direction == 'crosscourt':
            # Crosscourt placement depends on which side
            if shot.shot_type == 'Forehand' or shot.x > 50:
                # Forehand crosscourt to ad side
                optimal_x = 25
            else:
                # Backhand crosscourt to deuce side
                optimal_x = 75
        else:
            # Down-the-line
            if shot.shot_type == 'Forehand' or shot.x > 50:
                # Forehand DTL to deuce side
                optimal_x = 85
            else:
                # Backhand DTL to ad side
                optimal_x = 15
        
        # Vary depth based on tactical situation (not all shots should be Y=15!)
        # Deep shots: Y=10-20 (near opponent baseline)
        # Mid-depth: Y=25-35 (mid-court on opponent side)
        import random
        
        # 70% deep, 30% mid-depth for variety
        if random.random() < 0.7:
            optimal_y = 10 + random.randint(0, 10)  # Deep: 10-20
        else:
            optimal_y = 25 + random.randint(0, 10)  # Mid: 25-35
        
        print(f"🎯 STUB optimal placement: X={optimal_x}, Y={optimal_y}, direction={optimal_direction}", file=sys.stderr)
        
        return {
            'your_shot': self._shot_to_dict(shot),
            'your_expected_value': your_ev,
            'optimal_shot': {
                'shot_type': optimal_shot_type,
                'direction': optimal_direction,
                'speed': shot.speed + 8,
                'depth': 'deep',
                'placement': {'x': optimal_x, 'y': optimal_y}
            },
            'optimal_expected_value': optimal_ev,
            'improvement': optimal_ev - your_ev,
            'tactical_reasoning': f'Based on outcome, {optimal_direction} shot likely provides better expected value',
            'depth_analyzed': 1,
            'rollouts': 1,
            'stub': True
        }


def analyze_pattern_rallies(
    pattern: Any,
    adapter: SimplifiedMinimaxAdapter
) -> Any:
    """
    Analyze all rallies in a pattern with minimax counterfactuals.
    
    Adds minimax_optimal field to each supporting rally and critical moment.
    """
    # Analyze supporting rallies (using supporting config)
    for i, rally in enumerate(pattern.supporting_rallies[:10]):
        # Find a shot by you (preferably one that led to point loss for weaknesses)
        your_shot_idx = _find_analyzable_shot(rally, pattern.type)
        
        if your_shot_idx is not None:
            analysis = adapter.analyze_rally_counterfactual(
                rally, 
                your_shot_idx, 
                is_critical=False
            )
            
            # Add to rally object
            if not hasattr(rally, 'minimax_optimal'):
                rally.minimax_optimal = analysis
    
    # Analyze critical moments (using critical config)
    for i, rally in enumerate(pattern.critical_moments[:2]):
        your_shot_idx = _find_analyzable_shot(rally, pattern.type)
        
        if your_shot_idx is not None:
            analysis = adapter.analyze_rally_counterfactual(
                rally, 
                your_shot_idx, 
                is_critical=True  # Use deeper analysis
            )
            
            if not hasattr(rally, 'minimax_optimal'):
                rally.minimax_optimal = analysis
    
    return pattern


def _find_analyzable_shot(rally: Rally, pattern_type: str) -> Optional[int]:
    """
    Find the best shot in rally to analyze.
    
    For weaknesses: Find shot that led to loss
    For strengths: Find shot that led to win
    """
    # Find shots by you
    your_shots = [(i, s) for i, s in enumerate(rally.shots) if s.player == 'you']
    
    if not your_shots:
        return None
    
    if pattern_type == 'weakness':
        # For weaknesses, look for errors or last shot before losing
        for i, shot in reversed(your_shots):
            if shot.is_error:
                return i
        # Return last shot
        return your_shots[-1][0] if your_shots else None
    else:
        # For strengths, look for winners or aggressive shots
        for i, shot in your_shots:
            if shot.is_winner:
                return i
        # Return first aggressive shot
        for i, shot in your_shots:
            if shot.speed > 75:
                return i
        return your_shots[0][0] if your_shots else None
