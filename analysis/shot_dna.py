"""
Shot DNA - Pattern Fingerprinting Analysis
Identifies unconscious patterns in player decision-making
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from models import Match, Shot, Rally
import logging

logger = logging.getLogger(__name__)

class ShotDNA:
    """Analyzes player shot selection patterns"""
    
    def __init__(self, match: Match):
        self.match = match
        self.player1_patterns = defaultdict(list)
        self.player2_patterns = defaultdict(list)
        
    def analyze(self) -> Dict:
        """
        Run complete shot DNA analysis
        Returns: Dictionary of pattern insights
        """
        logger.info("Starting Shot DNA analysis")
        
        results = {
            'pressure_response': self._analyze_pressure_response(),
            'situational_bias': self._analyze_situational_bias(),
            'score_dependency': self._analyze_score_dependency(),
            'predictability_score': {},
            'exploitable_patterns': [],
            'recommendations': []
        }
        
        # Calculate overall predictability
        results['predictability_score'] = self._calculate_predictability()
        
        # Find exploitable patterns
        results['exploitable_patterns'] = self._find_exploitable_patterns(results)
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        logger.info("Shot DNA analysis complete")
        return results
    
    def _is_pressure_point(self, game_score: Dict, set_score: Dict) -> bool:
        """Determine if this is a pressure point"""
        p1_points = game_score.get(1, 0)
        p2_points = game_score.get(2, 0)
        
        # Break point
        if (p1_points == 40 and p2_points >= 30) or (p2_points == 40 and p1_points >= 30):
            return True
        
        # Set point
        p1_games = set_score.get(1, 0)
        p2_games = set_score.get(2, 0)
        if (p1_games >= 5 and p1_games > p2_games) or (p2_games >= 5 and p2_games > p1_games):
            return True
        
        return False
    
    def _analyze_pressure_response(self) -> Dict:
        """Analyze what players do under pressure"""
        pressure_shots = {1: [], 2: []}
        normal_shots = {1: [], 2: []}
        
        for set_data in self.match.sets:
            for game in set_data.games:
                for rally in game.rallies:
                    is_pressure = self._is_pressure_point(game.score, set_data.score)
                    
                    for shot in rally.shots:
                        shot_choice = f"{shot.shot_type}_{shot.direction}_{shot.depth}"
                        
                        if is_pressure:
                            pressure_shots[shot.player].append(shot_choice)
                        else:
                            normal_shots[shot.player].append(shot_choice)
        
        results = {}
        for player in [1, 2]:
            if pressure_shots[player]:
                pressure_counter = Counter(pressure_shots[player])
                normal_counter = Counter(normal_shots[player])
                
                # Find most common pressure shot
                most_common_pressure = pressure_counter.most_common(1)[0]
                pressure_choice = most_common_pressure[0]
                pressure_freq = most_common_pressure[1] / len(pressure_shots[player])
                
                # Compare to normal frequency
                normal_freq = normal_counter.get(pressure_choice, 0) / max(len(normal_shots[player]), 1)
                
                results[f'player_{player}'] = {
                    'most_common_pressure_shot': pressure_choice,
                    'pressure_frequency': pressure_freq,
                    'normal_frequency': normal_freq,
                    'pressure_bias': pressure_freq - normal_freq,
                    'total_pressure_points': len(pressure_shots[player]),
                    'is_predictable': pressure_freq > 0.65
                }
        
        return results
    
    def _analyze_situational_bias(self) -> Dict:
        """Analyze decision patterns in different court positions"""
        position_patterns = {1: defaultdict(list), 2: defaultdict(list)}
        
        for shot in self.match.get_all_shots():
            # Categorize position
            x, y = shot.ball_position
            
            # Court zones
            if x < 3.66:  # Left third
                zone_x = 'left'
            elif x < 7.31:  # Middle third
                zone_x = 'center'
            else:  # Right third
                zone_x = 'right'
            
            if y < 7.92:  # Defensive zone
                zone_y = 'defensive'
            elif y < 15.85:  # Neutral zone
                zone_y = 'neutral'
            else:  # Attacking zone
                zone_y = 'attacking'
            
            zone = f"{zone_x}_{zone_y}"
            shot_choice = f"{shot.direction}_{shot.depth}"
            
            position_patterns[shot.player][zone].append(shot_choice)
        
        results = {}
        for player in [1, 2]:
            zone_biases = {}
            for zone, shots in position_patterns[player].items():
                if len(shots) >= 5:  # Minimum sample size
                    counter = Counter(shots)
                    most_common = counter.most_common(1)[0]
                    frequency = most_common[1] / len(shots)
                    
                    if frequency > 0.6:  # Strong bias
                        zone_biases[zone] = {
                            'preferred_shot': most_common[0],
                            'frequency': frequency,
                            'sample_size': len(shots)
                        }
            
            results[f'player_{player}'] = zone_biases
        
        return results
    
    def _analyze_score_dependency(self) -> Dict:
        """Analyze how strategy changes with score"""
        results = {}
        
        for player in [1, 2]:
            ahead_shots = []
            behind_shots = []
            even_shots = []
            
            for set_data in self.match.sets:
                for game in set_data.games:
                    p1_games = set_data.score.get(1, 0)
                    p2_games = set_data.score.get(2, 0)
                    
                    # Determine if player is ahead/behind
                    if player == 1:
                        game_diff = p1_games - p2_games
                    else:
                        game_diff = p2_games - p1_games
                    
                    for rally in game.rallies:
                        for shot in rally.shots:
                            if shot.player == player:
                                shot_type = shot.shot_type
                                
                                if game_diff > 1:
                                    ahead_shots.append(shot_type)
                                elif game_diff < -1:
                                    behind_shots.append(shot_type)
                                else:
                                    even_shots.append(shot_type)
            
            # Calculate aggression levels
            def get_aggression_rate(shots):
                if not shots:
                    return 0.0
                aggressive = sum(1 for s in shots if s in ['winner', 'volley', 'approach'])
                return aggressive / len(shots)
            
            results[f'player_{player}'] = {
                'aggression_when_ahead': get_aggression_rate(ahead_shots),
                'aggression_when_behind': get_aggression_rate(behind_shots),
                'aggression_when_even': get_aggression_rate(even_shots),
                'score_sensitivity': abs(get_aggression_rate(ahead_shots) - get_aggression_rate(behind_shots))
            }
        
        return results
    
    def _calculate_predictability(self) -> Dict:
        """Calculate overall predictability score for each player"""
        results = {}
        
        for player in [1, 2]:
            shots = [s for s in self.match.get_all_shots() if s.player == player]
            
            if not shots:
                results[f'player_{player}'] = 0.0
                continue
            
            # Calculate entropy of shot selection
            shot_choices = [f"{s.shot_type}_{s.direction}" for s in shots]
            counter = Counter(shot_choices)
            total = len(shot_choices)
            
            # Shannon entropy
            entropy = 0
            for count in counter.values():
                p = count / total
                if p > 0:
                    entropy -= p * np.log2(p)
            
            # Max possible entropy (all choices equally likely)
            max_entropy = np.log2(len(counter))
            
            # Predictability score (0 = random, 1 = perfectly predictable)
            predictability = 1 - (entropy / max_entropy if max_entropy > 0 else 0)
            
            results[f'player_{player}'] = {
                'predictability_score': predictability,
                'unique_shot_patterns': len(counter),
                'most_common_pattern': counter.most_common(1)[0] if counter else ('unknown', 0),
                'interpretation': self._interpret_predictability(predictability)
            }
        
        return results
    
    def _interpret_predictability(self, score: float) -> str:
        """Interpret predictability score"""
        if score > 0.8:
            return "HIGHLY PREDICTABLE - Opponent can easily anticipate your shots"
        elif score > 0.6:
            return "MODERATELY PREDICTABLE - Consider mixing up your patterns"
        elif score > 0.4:
            return "BALANCED - Good variety in shot selection"
        else:
            return "UNPREDICTABLE - Excellent shot variety"
    
    def _find_exploitable_patterns(self, analysis: Dict) -> List[Dict]:
        """Find patterns that opponents can exploit"""
        exploitable = []
        
        # Check pressure response
        for player in [1, 2]:
            pressure = analysis['pressure_response'].get(f'player_{player}', {})
            if pressure.get('is_predictable', False):
                exploitable.append({
                    'player': player,
                    'type': 'pressure_response',
                    'severity': 'HIGH',
                    'pattern': pressure['most_common_pressure_shot'],
                    'frequency': pressure['pressure_frequency'],
                    'description': f"Player {player} goes to {pressure['most_common_pressure_shot']} {pressure['pressure_frequency']:.0%} of the time on pressure points"
                })
        
        # Check positional biases
        for player in [1, 2]:
            biases = analysis['situational_bias'].get(f'player_{player}', {})
            for zone, data in biases.items():
                if data['frequency'] > 0.7:
                    exploitable.append({
                        'player': player,
                        'type': 'positional_bias',
                        'severity': 'MEDIUM',
                        'pattern': f"{zone} → {data['preferred_shot']}",
                        'frequency': data['frequency'],
                        'description': f"Player {player} heavily favors {data['preferred_shot']} from {zone} position"
                    })
        
        return exploitable
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for pattern in analysis['exploitable_patterns']:
            player = pattern['player']
            
            if pattern['type'] == 'pressure_response':
                recommendations.append(
                    f"Player {player}: Vary your shot selection on pressure points. "
                    f"You're currently choosing {pattern['pattern']} {pattern['frequency']:.0%} of the time, "
                    f"making you predictable when it matters most."
                )
            elif pattern['type'] == 'positional_bias':
                recommendations.append(
                    f"Player {player}: When in {pattern['pattern'].split(' → ')[0]} position, "
                    f"consider more shot variety. Opponents will anticipate your tendency to hit "
                    f"{pattern['pattern'].split(' → ')[1]}."
                )
        
        # Add general recommendations
        for player in [1, 2]:
            pred = analysis['predictability_score'].get(f'player_{player}', {})
            if pred.get('predictability_score', 0) > 0.6:
                recommendations.append(
                    f"Player {player}: Work on increasing shot variety to become less predictable."
                )
        
        return recommendations
