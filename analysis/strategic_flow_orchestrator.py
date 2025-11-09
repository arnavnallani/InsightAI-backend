"""
Strategic Flow Orchestrator

Integrates all components to create a unified strategic narrative:
- Minimax decision tree analysis
- Opponent tendency learning
- Impact propagation (momentum, fatigue, decision quality)
- Narrative composition
"""

from typing import List, Dict, Any, Tuple
import random
from .strategic_flow_models import (
    MatchState, CriticalJuncture, StrategicPath, RippleCascade,
    ShotType, ShotDirection, ShotDepth, ShotIntent, ShotState, CourtPosition,
    OpponentTendencyProfile, StrategicFlowNarrative
)
from .minimax_core import MinimaxSimulationCore
from .tendency_learner import OpponentTendencyLearner
from .impact_models import ImpactModels


class StrategicFlowOrchestrator:
    """
    Orchestrates the complete strategic flow analysis.
    
    Takes match data and produces a cohesive narrative showing:
    - What actually happened
    - What should have happened (via minimax)
    - How different decisions would ripple through the match
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.tendency_learner = OpponentTendencyLearner()
        self.impact_models = ImpactModels()
    
    def analyze_match(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        player_name: str,
        opponent_name: str
    ) -> Dict[str, Any]:
        """
        Perform complete strategic flow analysis on a match.
        
        Args:
            shots: All shots from the match
            rallies: All rallies from the match
            player_name: Name of the player being analyzed
            opponent_name: Name of the opponent
            
        Returns:
            Complete strategic flow analysis dict
        """
        # Step 1: Learn opponent tendencies
        import sys
        print(f"Learning {opponent_name}'s tendencies...", file=sys.stderr)
        opponent_profile = self.tendency_learner.learn_from_match(
            shots, rallies, player_name
        )
        
        # Step 2: Identify critical junctures (important moments in the match)
        print("Identifying critical junctures...", file=sys.stderr)
        critical_junctures = self._identify_critical_junctures(
            shots, rallies, player_name, opponent_profile
        )
        
        # Step 3: For each juncture, run minimax to find optimal path
        print("Running minimax simulations...", file=sys.stderr)
        strategic_paths = []
        ripple_cascades = []
        
        for juncture in critical_junctures:
            # Run minimax from this point with Monte Carlo evaluation
            minimax_core = MinimaxSimulationCore(
                opponent_profile=opponent_profile,
                max_depth=4,  # Look 4 shots ahead
                branching_factor=4,  # Consider 4 shot options per decision
                num_rollouts=30  # Run 30 simulations per leaf node (Monte Carlo - optimized for speed)
            )
            
            optimal_tree = minimax_core.find_optimal_path(juncture.match_state)
            optimal_path_nodes = minimax_core.get_best_path(optimal_tree)
            
            # Calculate impact of optimal decision
            if optimal_path_nodes and len(optimal_path_nodes) > 1:
                optimal_decision = optimal_path_nodes[1]  # First decision after root
                
                # Update juncture with optimal info
                juncture.optimal_decision = optimal_decision.decision if optimal_decision.decision else juncture.actual_decision
                juncture.optimal_path = optimal_path_nodes
                
                # Calculate momentum impact
                outcome_won = optimal_decision.value > 0.6  # High value = likely win
                momentum_shift = self.impact_models.calculate_momentum_impact(
                    juncture.match_state,
                    optimal_decision,
                    outcome_won
                )
                juncture.momentum_shift = momentum_shift
                
                # Calculate fatigue impact
                fatigue_impact = self.impact_models.calculate_fatigue_impact(
                    juncture.match_state,
                    optimal_path_nodes,
                    momentum_shift
                )
                juncture.fatigue_impact = fatigue_impact
                
                # Calculate butterfly effect ripple
                butterfly_ripple = self.impact_models.calculate_butterfly_ripple(
                    juncture.rally_num,
                    len(rallies),
                    momentum_shift,
                    fatigue_impact
                )
                juncture.butterfly_effect = butterfly_ripple['narrative']
                
                # Create strategic path
                strategic_path = self._create_strategic_path(
                    juncture, optimal_tree, optimal_path_nodes
                )
                strategic_paths.append(strategic_path)
                
                # Create ripple cascade
                ripple_cascade = self._create_ripple_cascade(
                    juncture, butterfly_ripple
                )
                ripple_cascades.append(ripple_cascade)
        
        # Step 4: Calculate decision quality by zone
        print("Analyzing decision quality by court position...", file=sys.stderr)
        decision_quality_zones = self.impact_models.calculate_decision_quality_by_zone(
            shots, player_name
        )
        
        # Step 5: Generate match summary and key insights
        match_summary, key_insight = self._generate_match_summary(
            critical_junctures, strategic_paths, opponent_profile
        )
        
        # Step 6: Generate recommendations
        recommendations, drills = self._generate_recommendations(
            critical_junctures, strategic_paths, opponent_profile, decision_quality_zones
        )
        
        # Compile complete analysis
        return {
            'match_summary': match_summary,
            'key_insight': key_insight,
            'opponent_profile': {
                'breakdown_thresholds': [
                    {
                        'sequence': [st.value for st in t.shot_sequence],
                        'avg_shots_to_break': t.avg_shots_to_break,
                        'confidence': t.confidence
                    }
                    for t in opponent_profile.breakdown_thresholds
                ],
                'strong_zones': opponent_profile.strong_zones,
                'weak_zones': opponent_profile.weak_zones,
                'pressure_error_rate': opponent_profile.pressure_error_rate
            },
            'critical_junctures': [self._serialize_juncture(j) for j in critical_junctures],
            'strategic_paths': [self._serialize_path(p) for p in strategic_paths],
            'ripple_cascades': [self._serialize_cascade(c) for c in ripple_cascades],
            'decision_quality_zones': [
                {
                    'zone': z.court_zone,
                    'player_quality': z.player_decision_quality,
                    'opponent_quality': z.opponent_decision_quality,
                    'advantage': z.zone_advantage
                }
                for z in decision_quality_zones
            ],
            'recommendations': recommendations,
            'practice_drills': drills
        }
    
    def _identify_critical_junctures(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        player_name: str,
        opponent_profile: OpponentTendencyProfile
    ) -> List[CriticalJuncture]:
        """
        Identify critical moments in the match.
        
        Critical moments are:
        - Break points
        - Set points
        - Deuce/advantage points
        - Long rallies in close games
        - Momentum shift opportunities
        """
        junctures = []
        
        # Group shots by rally
        rally_shots = {}
        for shot in shots:
            rally_id = shot.get('rally_id', 0)
            if rally_id not in rally_shots:
                rally_shots[rally_id] = []
            rally_shots[rally_id].append(shot)
        
        # Analyze each rally for critical moments
        for rally_idx, rally in enumerate(rallies):
            importance = self._calculate_rally_importance(rally, rally_idx, len(rallies))
            
            # Only keep meaningful moments (importance > 0.15 - adjusted for better coverage)
            if importance < 0.15:
                continue
            
            # Get shots for this rally
            shots_in_rally = rally_shots.get(rally.get('id', rally_idx), [])
            player_shots_in_rally = [s for s in shots_in_rally if s.get('player') == player_name]
            
            if not player_shots_in_rally:
                continue
            
            # Create match state
            match_state = self._create_match_state_from_rally(
                rally, shots_in_rally, player_name, opponent_profile
            )
            
            # Determine actual outcome
            actual_outcome = "won_point" if rally.get('winner') == player_name else "lost_point"
            
            # Get actual decision (last shot by player in rally)
            actual_decision = self._create_shot_state_from_dict(player_shots_in_rally[-1])
            
            # Create juncture
            juncture = CriticalJuncture(
                match_state=match_state,
                score_string=rally.get('score', 'Unknown'),
                rally_num=rally_idx,
                actual_decision=actual_decision,
                actual_outcome=actual_outcome,
                optimal_decision=actual_decision,  # Will be updated later
                optimal_path=[],  # Will be filled by minimax
                momentum_shift=None,  # Will be calculated
                fatigue_impact=None,  # Will be calculated
                butterfly_effect="",  # Will be generated
                importance_score=importance,
                explanation=self._explain_juncture_importance(rally, importance)
            )
            
            junctures.append(juncture)
        
        # Sort by importance and take top 8-12
        junctures.sort(key=lambda j: j.importance_score, reverse=True)
        return junctures[:min(12, len(junctures))]
    
    def _calculate_rally_importance(self, rally: Dict, rally_idx: int, total_rallies: int) -> float:
        """Calculate how important/critical a rally is (0-1 scale)"""
        importance = 0.0
        
        point_score = rally.get('point_score', '0-0')
        game_score = rally.get('game_score', (0, 0))
        set_num = rally.get('set_num', 1)
        
        # Break points, set points are critical
        if 'break' in point_score.lower() or '40-30' in point_score or '30-40' in point_score:
            importance += 0.4
        
        # Deuce points
        if 'deuce' in point_score.lower() or '40-40' in point_score:
            importance += 0.3
        
        # Close games (2-2, 3-3, etc.)
        if abs(game_score[0] - game_score[1]) <= 1:
            importance += 0.2
        
        # Later in the match
        progress = rally_idx / total_rallies
        if progress > 0.7:
            importance += 0.2
        elif progress > 0.4:
            importance += 0.1
        
        # Long rallies
        rally_length = rally.get('length', 0)
        if rally_length > 10:
            importance += 0.15
        elif rally_length > 7:
            importance += 0.1
        
        return min(1.0, importance)
    
    def _create_match_state_from_rally(
        self,
        rally: Dict,
        shots_in_rally: List[Dict],
        player_name: str,
        opponent_profile: OpponentTendencyProfile
    ) -> MatchState:
        """Create a MatchState from rally data"""
        game_score_str = rally.get('game_score', (0, 0))
        if isinstance(game_score_str, tuple):
            game_score = game_score_str
        else:
            game_score = (0, 0)
        
        # Get player/opponent strengths and weaknesses
        player_strengths = [ShotType.FOREHAND]  # Default, would be learned
        player_weaknesses = [ShotType.BACKHAND]
        opponent_strengths = [ShotType.FOREHAND]
        opponent_weaknesses = [ShotType.BACKHAND]
        
        # Build recent shots
        recent_shots = []
        for shot_dict in shots_in_rally[-5:]:
            shot_state = self._create_shot_state_from_dict(shot_dict)
            recent_shots.append(shot_state)
        
        return MatchState(
            set_num=rally.get('set_num', 1),
            game_score=game_score,
            point_score=rally.get('point_score', '0-0'),
            player_energy=0.7,  # Would be calculated from match progress
            opponent_energy=0.7,
            player_momentum=0.0,  # Would be tracked from previous rallies
            recent_shots=recent_shots,
            rally_length=len(shots_in_rally),
            player_position=CourtPosition(x=2.0, y=0.5),  # Default baseline center
            opponent_position=CourtPosition(x=2.0, y=0.5),
            player_strengths=player_strengths,
            player_weaknesses=player_weaknesses,
            opponent_strengths=opponent_strengths,
            opponent_weaknesses=opponent_weaknesses
        )
    
    def _create_shot_state_from_dict(self, shot_dict: Dict) -> ShotState:
        """Convert shot dictionary to ShotState"""
        return ShotState(
            shot_type=ShotType(shot_dict.get('shot_type', 'forehand')),
            direction=ShotDirection(shot_dict.get('direction', 'crosscourt')),
            depth=ShotDepth(shot_dict.get('depth', 'deep')),
            speed_mph=shot_dict.get('speed_mph', 70.0),
            spin_rpm=shot_dict.get('spin_rpm', 2000),
            position=CourtPosition(
                x=shot_dict.get('hit_x', 2.0),
                y=shot_dict.get('hit_y', 0.5)
            ),
            intent=ShotIntent.ATTACK,  # Would be inferred
            quality=shot_dict.get('quality', 0.7)
        )
    
    def _explain_juncture_importance(self, rally: Dict, importance: float) -> str:
        """Generate explanation for why a juncture is important"""
        reasons = []
        
        if importance >= 0.8:
            reasons.append("Critical match moment")
        elif importance >= 0.6:
            reasons.append("High-pressure point")
        
        point_score = rally.get('point_score', '')
        if 'break' in point_score.lower():
            reasons.append("break point opportunity")
        elif 'deuce' in point_score.lower():
            reasons.append("deuce situation")
        
        if rally.get('length', 0) > 10:
            reasons.append("long rally battle")
        
        return " - ".join(reasons) if reasons else "Key tactical moment"
    
    def _create_strategic_path(
        self,
        juncture: CriticalJuncture,
        optimal_tree,
        optimal_path_nodes
    ) -> StrategicPath:
        """Create strategic path from minimax results"""
        # Extract path description
        path_description = self._describe_decision_path(optimal_path_nodes)
        
        # Calculate expected success metrics
        final_value = optimal_path_nodes[-1].value if optimal_path_nodes else 0.5
        success_probability = max(0.0, min(1.0, (final_value + 1) / 2))
        
        # Estimate points gained
        points_gained = int(success_probability * 3) if juncture.actual_outcome == "lost_point" else 0
        
        return StrategicPath(
            name=f"Optimal Strategy at {juncture.score_string}",
            description=path_description,
            root_decision=optimal_tree,
            expected_shots_to_success=len(optimal_path_nodes),
            success_probability=success_probability,
            points_gained=points_gained,
            momentum_advantage=juncture.momentum_shift.delta if juncture.momentum_shift else 0.0,
            fatigue_advantage=0.1 if juncture.fatigue_impact else 0.0
        )
    
    def _describe_decision_path(self, path_nodes) -> str:
        """Generate narrative description of decision path"""
        if len(path_nodes) < 2:
            return "Maintain current strategy"
        
        # Analyze the path
        shot_types = []
        for node in path_nodes[1:4]:  # First 3 decisions
            if node.decision:
                shot_types.append(node.decision.shot_type.value)
        
        if shot_types:
            return f"Execute {' → '.join(shot_types)} sequence to dominate the rally"
        return "Optimal tactical sequence"
    
    def _create_ripple_cascade(
        self,
        juncture: CriticalJuncture,
        butterfly_ripple: Dict
    ) -> RippleCascade:
        """Create ripple cascade from butterfly effect calculation"""
        affected_points = list(range(
            juncture.rally_num + 1,
            juncture.rally_num + 1 + butterfly_ripple['affected_points']
        ))
        
        return RippleCascade(
            trigger_juncture=juncture,
            affected_points=affected_points,
            total_momentum_shift=butterfly_ripple['total_momentum_shift'],
            total_points_swing=butterfly_ripple['points_swing'],
            fatigue_differential_change=butterfly_ripple['fatigue_differential_change'],
            set_win_prob_change=butterfly_ripple['set_win_prob_change'],
            match_win_prob_change=butterfly_ripple['match_win_prob_change'],
            narrative=butterfly_ripple['narrative']
        )
    
    def _generate_match_summary(
        self,
        junctures,
        paths,
        opponent_profile
    ) -> Tuple[str, str]:
        """Generate match summary and key insight"""
        summary = f"Analyzed {len(junctures)} critical moments in the match. "
        summary += f"Found {len(opponent_profile.breakdown_thresholds)} opponent breakdown patterns. "
        
        if paths:
            avg_success_prob = sum(p.success_probability for p in paths) / len(paths)
            summary += f"Optimal strategies show {avg_success_prob*100:.0f}% average success probability."
        
        # Key insight
        if opponent_profile.breakdown_thresholds:
            threshold = opponent_profile.breakdown_thresholds[0]
            key_insight = f"Opponent breaks after {threshold.avg_shots_to_break:.0f} consecutive {threshold.shot_sequence[0].value if threshold.shot_sequence else 'pressure'} shots"
        else:
            key_insight = "Exploit opponent weaknesses with targeted shot sequences"
        
        return summary, key_insight
    
    def _generate_recommendations(
        self,
        junctures,
        paths,
        opponent_profile,
        decision_quality_zones
    ) -> Tuple[List[Dict], List[Dict]]:
        """Generate actionable recommendations and practice drills"""
        recommendations = []
        drills = []
        
        # Recommendation 1: Target opponent breakdown patterns
        if opponent_profile.breakdown_thresholds:
            threshold = opponent_profile.breakdown_thresholds[0]
            recommendations.append({
                'priority': 1,
                'title': 'Exploit Breakdown Pattern',
                'issue': f'Opponent breaks under pressure',
                'solution': f'Hit {threshold.avg_shots_to_break:.0f} consecutive shots to their weakness',
                'expected_impact': 'High - Forces errors and weak shots'
            })
            
            drills.append({
                'name': 'Consistency Drill',
                'description': f'Practice hitting {threshold.avg_shots_to_break:.0f}+ consecutive {threshold.shot_sequence[0].value if threshold.shot_sequence else "pressure"} shots',
                'duration': '20 minutes',
                'goal': 'Build ability to maintain pressure'
            })
        
        # Recommendation 2: Improve weak zones
        weak_zones = [z for z in decision_quality_zones if z.player_decision_quality < 0.5]
        if weak_zones:
            worst_zone = min(weak_zones, key=lambda z: z.player_decision_quality)
            recommendations.append({
                'priority': 2,
                'title': f'Improve {worst_zone.court_zone} Decision Making',
                'issue': f'Low quality decisions in {worst_zone.court_zone}',
                'solution': 'Practice shot selection and execution in this zone',
                'expected_impact': 'Medium - Reduces unforced errors'
            })
        
        # Recommendation 3: Use optimal strategies
        if paths:
            recommendations.append({
                'priority': 3,
                'title': 'Execute Optimal Shot Sequences',
                'issue': 'Not following optimal decision paths',
                'solution': 'Study and practice the strategic sequences identified',
                'expected_impact': 'High - Maximizes point-winning probability'
            })
        
        return recommendations[:5], drills[:5]
    
    def _serialize_juncture(self, j: CriticalJuncture) -> Dict:
        """Convert juncture to serializable dict"""
        return {
            'score': j.score_string,
            'rally_num': j.rally_num,
            'actual_outcome': j.actual_outcome,
            'importance': j.importance_score,
            'explanation': j.explanation,
            'momentum_shift': {
                'before': j.momentum_shift.before,
                'after': j.momentum_shift.after,
                'delta': j.momentum_shift.delta,
                'ripple_points': j.momentum_shift.ripple_points
            } if j.momentum_shift else None,
            'butterfly_effect': j.butterfly_effect
        }
    
    def _serialize_path(self, p: StrategicPath) -> Dict:
        """Convert strategic path to serializable dict"""
        return {
            'name': p.name,
            'description': p.description,
            'success_probability': p.success_probability,
            'points_gained': p.points_gained,
            'momentum_advantage': p.momentum_advantage
        }
    
    def _serialize_cascade(self, c: RippleCascade) -> Dict:
        """Convert ripple cascade to serializable dict"""
        return {
            'trigger_score': c.trigger_juncture.score_string,
            'affected_points': len(c.affected_points),
            'points_swing': c.total_points_swing,
            'set_win_prob_change': c.set_win_prob_change,
            'narrative': c.narrative
        }
