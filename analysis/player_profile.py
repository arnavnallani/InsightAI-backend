"""
Player Behavioral Profile - Realistic tennis player tendencies
This simulates how a real player behaves (like SwingVision would capture)
"""
import random
from typing import Dict, Any, Literal

class PlayerBehavioralProfile:
    """
    Defines a tennis player's realistic behavioral tendencies.
    These are NOT patterns to be discovered - they're how a real player naturally plays.
    The Pattern Discovery Engine will analyze the resulting shot data to find weaknesses.
    """
    
    def __init__(self, skill_level: Literal['beginner', 'intermediate', 'advanced'] = 'intermediate'):
        self.skill_level = skill_level
        
        # BACKHAND CHARACTERISTICS
        # Most intermediate players have weaker backhands (this is realistic)
        self.backhand_speed_avg = 58  # mph (vs forehand 68mph)
        self.backhand_depth_distribution = {
            'deep': 0.30,   # Only 30% deep (should be 50%+)
            'mid': 0.45,
            'short': 0.25   # Too many short balls
        }
        self.backhand_crosscourt_bias = 0.75  # Hits 75% crosscourt (predictable)
        
        # SERVE CHARACTERISTICS  
        # Real players often develop serve patterns they're comfortable with
        self.serve_placement_distribution = {
            'T': 0.70,      # Goes to T 70% of time (predictable)
            'body': 0.15,
            'wide': 0.15
        }
        self.first_serve_percentage = 0.62
        
        # ATTACK DECISION-MAKING
        # When receiving short ball (depth='short', speed<65mph)
        self.attack_short_ball_probability = 0.35  # Only attacks 35% (should be 70%+)
        self.attack_speed_threshold = 65  # Considers balls under 65mph as "attackable"
        
        # PRESSURE RESPONSE
        # On important points (deuce, ad, break point, game point)
        self.pressure_speed_reduction = 8  # Loses 8mph under pressure
        self.pressure_conservative_probability = 0.70  # Plays safe 70% of time
        
        # COURT POSITIONING
        # Baseline vs aggressive positioning
        self.baseline_position_bias = 0.75  # Stays back 75% of time (should approach more)
        self.net_approach_on_short_ball = 0.20  # Only comes to net 20% when receiving short ball
        
        # RALLY CONSTRUCTION
        self.rally_length_preference = 'medium'  # Prefers 6-10 shot rallies
        self.risk_tolerance = 0.45  # 0=very safe, 1=very aggressive
        
    def get_shot_characteristics(
        self, 
        shot_type: str,
        is_pressure_point: bool,
        opponent_last_shot: Dict[str, Any] = None,
        fatigue_factor: float = 0.0
    ) -> Dict[str, Any]:
        """
        Returns realistic shot characteristics based on player's tendencies.
        This is what SwingVision would capture - the AI discovers patterns from this.
        """
        
        # BASE CHARACTERISTICS BY SHOT TYPE
        if shot_type == 'backhand':
            base_speed = self.backhand_speed_avg
            depth = random.choices(
                ['deep', 'mid', 'short'],
                weights=[
                    self.backhand_depth_distribution['deep'],
                    self.backhand_depth_distribution['mid'],
                    self.backhand_depth_distribution['short']
                ]
            )[0]
            
            # Crosscourt bias for backhand
            if random.random() < self.backhand_crosscourt_bias:
                angle = 'cross_court'
            else:
                angle = random.choice(['down_line', 'inside_out'])
                
        elif shot_type == 'forehand':
            base_speed = 68  # Stronger forehand
            depth = random.choices(['deep', 'mid', 'short'], weights=[0.55, 0.30, 0.15])[0]
            angle = random.choices(
                ['cross_court', 'down_line', 'inside_out', 'inside_in'],
                weights=[0.45, 0.35, 0.12, 0.08]
            )[0]
            
        elif shot_type == 'serve':
            base_speed = random.uniform(95, 110)  # First serve speed
            depth = 'deep'
            
            # Predictable serve placement
            placement = random.choices(
                ['T', 'body', 'wide'],
                weights=[
                    self.serve_placement_distribution['T'],
                    self.serve_placement_distribution['body'],
                    self.serve_placement_distribution['wide']
                ]
            )[0]
            angle = placement
            
        else:  # volleys, overheads, etc.
            base_speed = random.uniform(60, 85)
            depth = random.choice(['mid', 'deep'])
            angle = random.choice(['cross_court', 'down_line'])
        
        # ADJUST FOR PRESSURE
        if is_pressure_point and random.random() < self.pressure_conservative_probability:
            base_speed -= self.pressure_speed_reduction
            # Play safer - more mid-court shots
            if depth == 'deep':
                depth = 'mid' if random.random() < 0.4 else 'deep'
        
        # ADJUST FOR FATIGUE
        base_speed *= (1 - fatigue_factor * 0.15)
        
        # MISSED ATTACK OPPORTUNITY TENDENCY
        should_attack = False
        if opponent_last_shot:
            is_attackable = (
                opponent_last_shot.get('depth') in ['short', 'mid'] and
                opponent_last_shot.get('speed_mph', 999) < self.attack_speed_threshold
            )
            
            if is_attackable and random.random() < self.attack_short_ball_probability:
                should_attack = True
                base_speed += 12  # Attack with more pace
                depth = random.choice(['deep', 'mid'])  # Hit deeper
            elif is_attackable:
                # MISSED ATTACK - plays defensively instead
                base_speed -= 5  # Conservative shot
                depth = 'mid'  # Safe placement
        
        return {
            'speed_mph': base_speed,
            'depth': depth,
            'angle': angle,
            'should_attack': should_attack,
            'is_conservative': is_pressure_point and random.random() < self.pressure_conservative_probability
        }
    
    def is_pressure_point(self, player_score: int, opponent_score: int) -> bool:
        """Determine if this is a pressure point (deuce, ad, break point, etc.)"""
        # Deuce or advantage
        if player_score >= 3 and opponent_score >= 3:
            return True
        # Break point (opponent one point from winning)
        if opponent_score >= 3 and player_score < opponent_score:
            return True
        # Game point (player one point from winning)
        if player_score >= 3 and opponent_score < player_score:
            return True
        
        return False


class OpponentProfile:
    """Opponent has different (stronger) tendencies - creates contrast for pattern discovery"""
    
    def __init__(self):
        # Opponent is more aggressive and consistent
        self.forehand_speed_avg = 72
        self.backhand_speed_avg = 65  # Strong backhand
        self.attack_short_ball_probability = 0.75  # Capitalizes on short balls
        
    def get_shot_characteristics(
        self,
        shot_type: str,
        opponent_last_shot: Dict[str, Any] = None,
        fatigue_factor: float = 0.0
    ) -> Dict[str, Any]:
        """Opponent plays more aggressively and consistently"""
        
        if shot_type == 'backhand':
            base_speed = self.backhand_speed_avg
            depth = random.choices(['deep', 'mid', 'short'], weights=[0.50, 0.35, 0.15])[0]
        elif shot_type == 'forehand':
            base_speed = self.forehand_speed_avg
            depth = random.choices(['deep', 'mid', 'short'], weights=[0.60, 0.30, 0.10])[0]
        else:
            base_speed = random.uniform(65, 90)
            depth = random.choice(['mid', 'deep'])
        
        angle = random.choice(['cross_court', 'down_line', 'inside_out'])
        
        # Opponent attacks short balls aggressively
        should_attack = False
        if opponent_last_shot:
            is_attackable = (
                opponent_last_shot.get('depth') in ['short', 'mid'] and
                opponent_last_shot.get('speed_mph', 999) < 68
            )
            if is_attackable and random.random() < self.attack_short_ball_probability:
                should_attack = True
                base_speed += 15
                depth = 'deep'
        
        base_speed *= (1 - fatigue_factor * 0.12)
        
        return {
            'speed_mph': base_speed,
            'depth': depth,
            'angle': angle,
            'should_attack': should_attack
        }
