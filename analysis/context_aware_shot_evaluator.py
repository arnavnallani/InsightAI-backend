"""
Context-Aware Shot Evaluator
Evaluates every shot quality considering full match context

Integrates position, score, energy, opponent style, and sequences to provide
professional-level tactical evaluation of each shot.
"""

from typing import Dict, Any, List, Optional, Tuple
import sys
from pattern_utils import Shot, Rally
from tennis_strategy_knowledge import (
    POSITION_BASED_TACTICS,
    OPPONENT_STYLE_TACTICS,
    SCORE_BASED_TACTICS,
    ENERGY_MANAGEMENT
)


class ContextAwareShotEvaluator:
    """
    Evaluates shot quality considering ALL context:
    - Player court position
    - Opponent court position  
    - Score situation (break point, tiebreak, etc.)
    - Energy level (set 1 vs set 3)
    - Previous shots in sequence
    - Opponent style
    """
    
    def __init__(self):
        self.opponent_style = "baseliner"  # Default, can be learned
        
    def evaluate_shot(
        self,
        shot: Shot,
        rally: Rally,
        match_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive shot evaluation considering all context
        
        Args:
            shot: The shot to evaluate
            rally: Current rally context
            match_context: Match-level context (set, score, energy, etc.)
            
        Returns:
            {
                'quality': 'excellent/good/neutral/poor/terrible',
                'tactical_reasoning': 'Why this shot was good/bad',
                'better_alternative': 'What you should have done',
                'context_factors': ['Position', 'Score', 'Energy'],
                'context_details': {...},
                'position_category': 'inside_baseline/baseline_neutral/etc',
                'score_pressure': 0.0-1.0,
                'energy_level': 'high/medium/low'
            }
        """
        # Extract context features
        position_context = self._analyze_position_context(shot, rally)
        score_context = self._analyze_score_context(rally, match_context)
        energy_context = self._analyze_energy_context(match_context)
        sequence_context = self._analyze_sequence_context(shot, rally)
        
        # Evaluate shot quality based on context
        quality_assessment = self._evaluate_with_context(
            shot,
            position_context,
            score_context,
            energy_context,
            sequence_context
        )
        
        return {
            'quality': quality_assessment['quality'],
            'tactical_reasoning': quality_assessment['reasoning'],
            'better_alternative': quality_assessment.get('alternative', None),
            'context_factors': quality_assessment['factors'],
            'context_details': {
                'position': position_context,
                'score': score_context,
                'energy': energy_context,
                'sequence': sequence_context
            },
            'position_category': position_context['category'],
            'score_pressure': score_context['pressure_level'],
            'energy_level': energy_context['level']
        }
    
    def _analyze_position_context(self, shot: Shot, rally: Rally) -> Dict[str, Any]:
        """
        Determine player's court position and tactical situation
        
        Returns category: deep_behind_baseline, baseline_neutral, inside_baseline,
                         short_ball_zone, at_net, moving_forward, moving_backward
        """
        # Estimate player position from shot data
        player_y = getattr(shot, 'player_y', 50)  # 0-100 scale
        ball_landed_y = getattr(shot, 'y', 50)  # Where ball landed
        
        # Determine position category
        if player_y > 95:
            category = "deep_behind_baseline"
        elif player_y > 85 and player_y <= 95:
            category = "baseline_neutral"
        elif player_y > 65 and player_y <= 85:
            category = "inside_baseline"
        elif player_y > 40 and player_y <= 65:
            category = "short_ball_zone"
        elif player_y <= 40:
            category = "at_net"
        else:
            category = "baseline_neutral"
        
        # Get tactical guidance for this position
        position_tactics = POSITION_BASED_TACTICS.get(category, {})
        
        return {
            'category': category,
            'player_y': player_y,
            'tactical_guidance': position_tactics,
            'best_shots': position_tactics.get('best_shots', []),
            'avoid': position_tactics.get('avoid', []),
            'reasoning': position_tactics.get('reasoning', '')
        }
    
    def _analyze_score_context(self, rally: Rally, match_context: Dict) -> Dict[str, Any]:
        """
        Analyze score situation and pressure level
        
        Returns: break_point, tiebreak, crucial_game, etc.
        """
        is_break_point = getattr(rally, 'is_break_point', False)
        is_set_point = getattr(rally, 'is_set_point', False)
        is_match_point = getattr(rally, 'is_match_point', False)
        point_score = getattr(rally, 'point_score', '0-0')
        game_score = getattr(rally, 'game_score', '0-0')
        
        # Determine pressure level (0.0-1.0)
        pressure_level = 0.0
        situation = "neutral"
        
        if is_match_point:
            pressure_level = 1.0
            situation = "match_point"
        elif is_set_point:
            pressure_level = 0.9
            situation = "set_point"
        elif is_break_point:
            pressure_level = 0.8
            situation = "break_point"
        elif '40' in point_score:
            pressure_level = 0.6
            situation = "game_point"
        elif point_score in ['30-30', 'deuce']:
            pressure_level = 0.5
            situation = "deuce_crucial"
        else:
            pressure_level = 0.2
            situation = "neutral"
        
        # Get score-based tactics
        score_tactics = None
        if is_break_point:
            serving = getattr(rally, 'serving', False)
            score_tactics = SCORE_BASED_TACTICS.get(
                'serving_break_point' if serving else 'returning_break_point',
                {}
            )
        elif situation == "deuce_crucial":
            score_tactics = SCORE_BASED_TACTICS.get('deuce_crucial', {})
        
        return {
            'situation': situation,
            'pressure_level': pressure_level,
            'is_break_point': is_break_point,
            'point_score': point_score,
            'game_score': game_score,
            'tactical_guidance': score_tactics
        }
    
    def _analyze_energy_context(self, match_context: Dict) -> Dict[str, Any]:
        """
        Determine energy level and physical state
        
        Returns: high, medium, or low energy
        """
        set_number = match_context.get('set_number', 1)
        game_number = match_context.get('game_number', 1)
        
        # Estimate energy based on match progress
        if set_number == 1 and game_number <= 4:
            energy_level = "high_energy"
        elif set_number == 1 or (set_number == 2 and game_number <= 4):
            energy_level = "medium_energy"
        else:
            energy_level = "low_energy"
        
        # Get energy management tactics
        energy_tactics = ENERGY_MANAGEMENT.get(energy_level, {})
        
        return {
            'level': energy_level,
            'set_number': set_number,
            'game_number': game_number,
            'tactical_guidance': energy_tactics,
            'rally_length_target': energy_tactics.get('tactical_approach', {}).get('rally_length', '6-8 shots')
        }
    
    def _analyze_sequence_context(self, shot: Shot, rally: Rally) -> Dict[str, Any]:
        """
        Analyze previous shots in sequence to identify patterns
        
        Returns: What pattern is being executed (if any)
        """
        if not hasattr(rally, 'shots') or not rally.shots:
            return {
                'pattern': None,
                'shot_number_in_rally': 0,
                'previous_shots': []
            }
        
        shot_number = getattr(shot, 'shot_number', 0)
        
        # Get previous 2-3 shots
        previous_shots = []
        for s in rally.shots:
            if s.shot_number < shot_number:
                previous_shots.append({
                    'shot_type': s.shot_type,
                    'direction': getattr(s, 'direction', None),
                    'player': s.player
                })
        
        # Detect if following a known sequence pattern
        pattern = self._detect_sequence_pattern(previous_shots, shot)
        
        return {
            'pattern': pattern,
            'shot_number_in_rally': shot_number,
            'previous_shots': previous_shots[-3:] if previous_shots else []
        }
    
    def _detect_sequence_pattern(self, previous_shots: List[Dict], current_shot: Shot) -> Optional[str]:
        """Detect if following a known tactical sequence"""
        if len(previous_shots) < 2:
            return None
        
        # Check for crosscourt → crosscourt → DTL pattern
        if len(previous_shots) >= 2:
            last_two = previous_shots[-2:]
            if all(s.get('direction') == 'crosscourt' for s in last_two if s.get('direction')):
                return "crosscourt_crosscourt_dtl"
        
        # Check for serve + 1 pattern
        if len(previous_shots) >= 1:
            if previous_shots[0].get('shot_type', '').lower() == 'serve':
                return "serve_plus_one"
        
        return None
    
    def _evaluate_with_context(
        self,
        shot: Shot,
        position_ctx: Dict,
        score_ctx: Dict,
        energy_ctx: Dict,
        sequence_ctx: Dict
    ) -> Dict[str, Any]:
        """
        Final quality assessment combining all context
        """
        quality = "neutral"
        reasoning = []
        alternative = None
        factors = []
        
        shot_type = getattr(shot, 'shot_type', 'Unknown').lower()
        speed = getattr(shot, 'speed', 0)
        direction = getattr(shot, 'direction', '')
        
        # POSITION CONTEXT EVALUATION
        position_category = position_ctx['category']
        best_shots = position_ctx.get('best_shots', [])
        avoid_shots = position_ctx.get('avoid', [])
        
        # Check if shot matches position-appropriate tactics
        if position_category == "inside_baseline":
            # Should be attacking
            if speed < 70:
                quality = "poor"
                reasoning.append(f"Inside baseline but hitting soft shot ({speed}mph) - wasting offensive position")
                alternative = "Attack with 75+ mph down-the-line or sharp crosscourt angle"
                factors.append("Position")
            elif speed >= 75:
                quality = "good"
                reasoning.append(f"Inside baseline with aggressive shot ({speed}mph) - proper attacking")
                factors.append("Position")
        
        elif position_category == "deep_behind_baseline":
            # Should be defensive/recovery
            if 'down' in direction.lower() and speed > 70:
                quality = "poor"
                reasoning.append("Behind baseline trying risky down-the-line - should hit safe crosscourt")
                alternative = "Deep heavy crosscourt with topspin to recover position"
                factors.append("Position")
            elif 'cross' in direction.lower():
                quality = "good"
                reasoning.append("Behind baseline hitting crosscourt - correct defensive shot")
                factors.append("Position")
        
        elif position_category == "short_ball_zone":
            # MUST attack
            if speed < 75:
                quality = "terrible"
                reasoning.append(f"Short ball zone but hitting soft shot ({speed}mph) - FREE POINT wasted!")
                alternative = "Attack with 80+ mph down-the-line or approach net"
                factors.append("Position")
            elif speed >= 80:
                quality = "excellent"
                reasoning.append(f"Short ball zone with strong attack ({speed}mph) - proper execution")
                factors.append("Position")
        
        # SCORE CONTEXT EVALUATION
        pressure_level = score_ctx['pressure_level']
        situation = score_ctx['situation']
        
        if situation == "break_point" and pressure_level > 0.7:
            # High-pressure point
            if speed < 60:
                quality = "poor" if quality == "neutral" else quality
                reasoning.append("Break point but playing too conservatively - should use your weapons")
                alternative = "Be aggressive - this is when your strengths matter most"
                factors.append("Score")
        
        # ENERGY CONTEXT EVALUATION
        energy_level = energy_ctx['level']
        rally_length = len(sequence_ctx.get('previous_shots', [])) + 1
        
        if energy_level == "low_energy" and rally_length > 8:
            quality = "poor" if quality == "neutral" else quality
            reasoning.append(f"Low energy but rally at {rally_length} shots - should shorten points")
            alternative = "Attack earlier to shorten points (target 4-5 shot rallies)"
            factors.append("Energy")
        
        # SEQUENCE CONTEXT EVALUATION
        pattern = sequence_ctx.get('pattern')
        if pattern == "crosscourt_crosscourt_dtl" and 'cross' in direction.lower():
            quality = "poor" if quality == "neutral" else quality
            reasoning.append("After 2 crosscourts, should go down-the-line to change rhythm")
            alternative = "Go down-the-line to break opponent's pattern"
            factors.append("Sequence")
        
        # Default reasoning if nothing specific found
        if not reasoning:
            reasoning.append("Standard shot - tactical context considered")
        
        return {
            'quality': quality,
            'reasoning': '; '.join(reasoning),
            'alternative': alternative,
            'factors': factors if factors else ['General']
        }
    
    def tag_pattern_with_context(
        self,
        rally: Rally,
        match_context: Dict
    ) -> Dict[str, Any]:
        """
        Tag a rally with context metadata for pattern discovery
        
        Returns: {
            'position_tags': [...],
            'score_tags': [...],
            'energy_tags': [...],
            'sequence_tags': [...]
        }
        """
        tags = {
            'position_tags': [],
            'score_tags': [],
            'energy_tags': [],
            'sequence_tags': []
        }
        
        # Analyze each player shot in rally
        for shot in rally.shots:
            if shot.player.lower() in ['you', 'player']:
                eval_result = self.evaluate_shot(shot, rally, match_context)
                
                # Add position tags
                if eval_result['position_category']:
                    tags['position_tags'].append(eval_result['position_category'])
                
                # Add score tags
                if eval_result['context_details']['score']['situation'] != 'neutral':
                    tags['score_tags'].append(eval_result['context_details']['score']['situation'])
                
                # Add energy tags
                tags['energy_tags'].append(eval_result['energy_level'])
        
        return tags
