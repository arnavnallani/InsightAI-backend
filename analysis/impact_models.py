"""
Impact Models

Calculates how strategic decisions ripple through the match affecting:
- Momentum shifts
- Fatigue dynamics
- Decision quality by court position
"""

from typing import List, Dict, Tuple
import math
from .strategic_flow_models import (
    MatchState, DecisionNode, MomentumShift, FatigueImpact,
    DecisionQualityImpact, ShotType
)


class ImpactModels:
    """
    Models that calculate ripple effects of strategic decisions.
    
    Given a counterfactual decision at a critical point, calculates:
    - How momentum shifts
    - How fatigue changes
    - How decision quality varies by court position
    """
    
    def __init__(self):
        """Initialize impact models with default parameters"""
        # Momentum decay rate (how fast momentum returns to neutral)
        self.momentum_decay = 0.15
        
        # Fatigue recovery rate from adrenaline/momentum
        self.adrenaline_recovery_factor = 0.2
        
        # Rally length impact on fatigue
        self.rally_fatigue_factor = 0.02
    
    def calculate_momentum_impact(
        self,
        original_state: MatchState,
        counterfactual_decision: DecisionNode,
        outcome_won: bool
    ) -> MomentumShift:
        """
        Calculate how a different decision would shift momentum.
        
        Args:
            original_state: The actual match state
            counterfactual_decision: The alternative decision tree
            outcome_won: Whether the counterfactual wins the point
            
        Returns:
            MomentumShift with before/after and ripple effects
        """
        before_momentum = original_state.player_momentum
        
        # Calculate new momentum based on decision quality and outcome
        decision_quality = self._evaluate_decision_quality(counterfactual_decision)
        
        # Momentum boost from winning with strong decision
        if outcome_won:
            momentum_boost = 0.3 + (decision_quality * 0.2)
        else:
            momentum_boost = -0.2
        
        after_momentum = max(-1, min(1, before_momentum + momentum_boost))
        
        # Calculate ripple effect on subsequent points
        ripple_points = self._calculate_ripple_duration(before_momentum, after_momentum)
        
        # Calculate win probability change for next point
        win_prob_change = self._momentum_to_win_prob_change(before_momentum, after_momentum)
        
        return MomentumShift(
            before=before_momentum,
            after=after_momentum,
            delta=after_momentum - before_momentum,
            ripple_points=ripple_points,
            win_prob_change=win_prob_change
        )
    
    def calculate_fatigue_impact(
        self,
        original_state: MatchState,
        counterfactual_path: List[DecisionNode],
        momentum_shift: MomentumShift
    ) -> FatigueImpact:
        """
        Calculate how a different decision affects fatigue.
        
        Factors:
        - Rally length change (longer rallies = more fatigue)
        - Adrenaline boost from momentum (reduces perceived fatigue)
        - Quality of shots (higher quality = less energy wasted)
        """
        # Original fatigue
        player_fatigue_before = 1.0 - original_state.player_energy
        opponent_fatigue_before = 1.0 - original_state.opponent_energy
        
        # Calculate rally length in counterfactual
        counterfactual_rally_length = len(counterfactual_path)
        original_rally_length = original_state.rally_length
        rally_length_change = counterfactual_rally_length - original_rally_length
        
        # Fatigue from rally length
        fatigue_change = rally_length_change * self.rally_fatigue_factor
        
        # Adrenaline boost from positive momentum (reduces fatigue)
        adrenaline_boost = 0.0
        if momentum_shift.delta > 0:
            adrenaline_boost = momentum_shift.delta * self.adrenaline_recovery_factor
        
        # Calculate new fatigue levels
        player_fatigue_after = max(0, min(1, player_fatigue_before + fatigue_change - adrenaline_boost))
        
        # Opponent fatigue increases if they're defending more
        opponent_fatigue_increase = fatigue_change * 1.2  # Defending is more tiring
        opponent_fatigue_after = max(0, min(1, opponent_fatigue_before + opponent_fatigue_increase))
        
        return FatigueImpact(
            player_fatigue_before=player_fatigue_before,
            player_fatigue_after=player_fatigue_after,
            opponent_fatigue_before=opponent_fatigue_before,
            opponent_fatigue_after=opponent_fatigue_after,
            rally_length_change=rally_length_change,
            adrenaline_boost=adrenaline_boost
        )
    
    def calculate_decision_quality_by_zone(
        self,
        shots: List[Dict],
        player_name: str
    ) -> List[DecisionQualityImpact]:
        """
        Calculate decision quality for both players by court zone.
        
        Args:
            shots: All shots from the match
            player_name: Name of the player
            
        Returns:
            List of decision quality impacts per zone
        """
        # Group shots by zone
        player_zone_shots = {}
        opponent_zone_shots = {}
        
        for shot in shots:
            zone = self._get_zone_name(shot.get('land_x', 2.0), shot.get('land_y', 2.0))
            
            if shot.get('player') == player_name:
                if zone not in player_zone_shots:
                    player_zone_shots[zone] = []
                player_zone_shots[zone].append(shot)
            else:
                if zone not in opponent_zone_shots:
                    opponent_zone_shots[zone] = []
                opponent_zone_shots[zone].append(shot)
        
        # Calculate quality per zone
        zone_impacts = []
        
        all_zones = set(list(player_zone_shots.keys()) + list(opponent_zone_shots.keys()))
        
        for zone in all_zones:
            player_quality = self._calculate_zone_quality(player_zone_shots.get(zone, []))
            opponent_quality = self._calculate_zone_quality(opponent_zone_shots.get(zone, []))
            
            # Determine advantage
            if player_quality > opponent_quality + 0.1:
                advantage = "player"
            elif opponent_quality > player_quality + 0.1:
                advantage = "opponent"
            else:
                advantage = "neutral"
            
            zone_impacts.append(DecisionQualityImpact(
                court_zone=zone,
                player_decision_quality=player_quality,
                opponent_decision_quality=opponent_quality,
                zone_advantage=advantage
            ))
        
        return zone_impacts
    
    def calculate_butterfly_ripple(
        self,
        critical_point_rally: int,
        total_rallies: int,
        momentum_shift: MomentumShift,
        fatigue_impact: FatigueImpact
    ) -> Dict[str, any]:
        """
        Calculate the butterfly effect ripple from a critical decision.
        
        Shows how one decision at a critical point cascades through
        subsequent points.
        
        Returns:
            Dict with ripple metrics and narrative
        """
        # How many points are affected
        affected_points = min(momentum_shift.ripple_points, total_rallies - critical_point_rally)
        
        # Calculate cumulative momentum advantage
        cumulative_momentum = 0.0
        for i in range(affected_points):
            decay_factor = math.exp(-i * self.momentum_decay)
            cumulative_momentum += momentum_shift.delta * decay_factor
        
        # Estimate points swing
        # Each point has base 50% win rate, momentum adds win probability
        points_swing = 0
        for i in range(affected_points):
            decay_factor = math.exp(-i * self.momentum_decay)
            win_prob_boost = momentum_shift.win_prob_change * decay_factor
            
            # If boosted probability > 50%, likely to win that point
            if 0.5 + win_prob_boost > 0.5:
                points_swing += 1
        
        # Estimate set/match win probability change
        # Simplified: each point swing changes set win prob by ~2-3%
        set_win_prob_change = points_swing * 0.025
        match_win_prob_change = points_swing * 0.015
        
        # Calculate fatigue differential change
        fatigue_diff_change = (
            (fatigue_impact.opponent_fatigue_after - fatigue_impact.player_fatigue_after) -
            (fatigue_impact.opponent_fatigue_before - fatigue_impact.player_fatigue_before)
        )
        
        # Generate narrative
        narrative = self._generate_butterfly_narrative(
            momentum_shift, fatigue_impact, points_swing, affected_points
        )
        
        return {
            'affected_points': affected_points,
            'total_momentum_shift': cumulative_momentum,
            'points_swing': points_swing,
            'fatigue_differential_change': fatigue_diff_change,
            'set_win_prob_change': set_win_prob_change,
            'match_win_prob_change': match_win_prob_change,
            'narrative': narrative
        }
    
    def _evaluate_decision_quality(self, decision_node: DecisionNode) -> float:
        """Evaluate quality of a decision (0-1 scale)"""
        if not decision_node.decision:
            return 0.5
        
        # Quality based on shot execution and strategic value
        shot_quality = decision_node.decision.quality
        strategic_value = decision_node.strength_exploitation
        
        # Combined quality
        return (shot_quality * 0.6) + ((strategic_value + 1) / 2 * 0.4)
    
    def _calculate_ripple_duration(self, before_momentum: float, after_momentum: float) -> int:
        """Calculate how many points the momentum shift affects"""
        delta = abs(after_momentum - before_momentum)
        
        # Larger momentum swings last longer
        base_duration = 5
        momentum_factor = delta * 8  # Up to 8 more points for max swing
        
        return int(base_duration + momentum_factor)
    
    def _momentum_to_win_prob_change(self, before: float, after: float) -> float:
        """Convert momentum change to win probability change"""
        # Momentum from -1 to 1 maps to win probability
        # -1 momentum = ~20% win prob, +1 momentum = ~80% win prob
        
        before_prob = 0.5 + (before * 0.3)
        after_prob = 0.5 + (after * 0.3)
        
        return after_prob - before_prob
    
    def _calculate_zone_quality(self, zone_shots: List[Dict]) -> float:
        """Calculate decision quality in a zone based on shots"""
        if not zone_shots:
            return 0.5
        
        # Metrics: winner rate - error rate, weighted by shot quality
        total_quality = 0.0
        winners = 0
        errors = 0
        
        for shot in zone_shots:
            total_quality += shot.get('quality', 0.7)
            if shot.get('is_winner'):
                winners += 1
            if shot.get('is_error'):
                errors += 1
        
        avg_quality = total_quality / len(zone_shots)
        success_rate = (winners - errors) / len(zone_shots)
        
        # Combined: 60% quality, 40% success rate
        return (avg_quality * 0.6) + ((success_rate + 1) / 2 * 0.4)
    
    def _get_zone_name(self, x: float, y: float) -> str:
        """Get zone name from coordinates"""
        y_zone = "Net" if y >= 3 else "Volley" if y >= 2 else "Mid" if y >= 1 else "Baseline"
        x_zone = "Ad Side" if x < 1.5 else "Center" if x < 2.5 else "Deuce Side"
        return f"{x_zone} {y_zone}"
    
    def _generate_butterfly_narrative(
        self,
        momentum: MomentumShift,
        fatigue: FatigueImpact,
        points_swing: int,
        affected_points: int
    ) -> str:
        """Generate narrative description of butterfly effect"""
        parts = []
        
        # Momentum impact
        if momentum.delta > 0.3:
            parts.append(f"Massive momentum swing (+{momentum.delta:.1f}) creates psychological advantage")
        elif momentum.delta > 0.1:
            parts.append(f"Positive momentum shift (+{momentum.delta:.1f}) boosts confidence")
        
        # Fatigue impact
        if fatigue.adrenaline_boost > 0.1:
            parts.append(f"adrenaline reduces fatigue by {fatigue.adrenaline_boost*100:.0f}%")
        
        # Points impact
        if points_swing > 0:
            parts.append(f"likely wins {points_swing} of next {affected_points} points")
        
        # Overall narrative
        if parts:
            return "This decision shift " + ", ".join(parts) + "."
        else:
            return "Minimal ripple effect on subsequent points."
