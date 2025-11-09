"""
Shadow Self - AI Clone that learns your playing style
Creates an AI that plays like you, then finds counter-strategies
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from models import Match, Shot
import logging

logger = logging.getLogger(__name__)

class ShadowAI:
    """Creates AI clone of player's decision patterns"""
    
    def __init__(self, match: Match):
        self.match = match
        self.player1_model = defaultdict(lambda: defaultdict(int))
        self.player2_model = defaultdict(lambda: defaultdict(int))
        
    def analyze(self) -> Dict:
        """
        Run complete shadow AI analysis
        Returns: Dictionary of shadow AI insights
        """
        logger.info("Starting Shadow AI analysis")
        
        # Train models on player behavior
        self._train_models()
        
        results = {
            'player_1_model': self._analyze_player_model(1),
            'player_2_model': self._analyze_player_model(2),
            'counter_strategies': self._find_counter_strategies(),
            'predicted_vs_actual': self._compare_predictions(),
            'exploits': self._find_exploitable_weaknesses()
        }
        
        logger.info("Shadow AI analysis complete")
        return results
    
    def _encode_game_state(self, shot: Shot, rally_context: Dict = None) -> str:
        """Encode game state into a string key"""
        x, y = shot.ball_position
        
        # Discretize position
        zone_x = 'L' if x < 3.66 else ('C' if x < 7.31 else 'R')
        zone_y = 'D' if y > 18 else ('N' if y > 10 else 'A')  # Defensive/Neutral/Attack
        
        # Encode state
        state = f"{zone_x}{zone_y}"
        
        # Add previous shot context if available
        if rally_context and 'prev_shot' in rally_context:
            prev = rally_context['prev_shot']
            state += f"_after_{prev.shot_type}_{prev.direction}"
        
        return state
    
    def _train_models(self):
        """Train decision models for both players"""
        for rally in self.match.get_all_rallies():
            for i, shot in enumerate(rally.shots):
                # Get previous shot context
                prev_shot = rally.shots[i-1] if i > 0 else None
                context = {'prev_shot': prev_shot} if prev_shot else None
                
                # Encode state
                state = self._encode_game_state(shot, context)
                
                # Encode action
                action = f"{shot.shot_type}_{shot.direction}_{shot.depth}"
                
                # Update model
                if shot.player == 1:
                    self.player1_model[state][action] += 1
                else:
                    self.player2_model[state][action] += 1
    
    def _predict_shot(self, player: int, game_state: str) -> Tuple[str, float]:
        """
        Predict what shot player will make in given state
        Returns: (predicted_action, confidence)
        """
        model = self.player1_model if player == 1 else self.player2_model
        
        if game_state not in model:
            return ("unknown", 0.0)
        
        actions = model[game_state]
        total = sum(actions.values())
        
        if total == 0:
            return ("unknown", 0.0)
        
        # Most common action
        predicted_action = max(actions.items(), key=lambda x: x[1])
        confidence = predicted_action[1] / total
        
        return (predicted_action[0], confidence)
    
    def _analyze_player_model(self, player: int) -> Dict:
        """Analyze trained model for a player"""
        model = self.player1_model if player == 1 else self.player2_model
        
        analysis = {
            'total_states_learned': len(model),
            'total_observations': sum(sum(actions.values()) for actions in model.values()),
            'most_common_patterns': [],
            'state_coverage': {},
            'predictability_by_state': {}
        }
        
        # Find most common patterns
        for state, actions in model.items():
            total = sum(actions.values())
            most_common = max(actions.items(), key=lambda x: x[1])
            frequency = most_common[1] / total
            
            if total >= 3:  # Minimum observations
                analysis['most_common_patterns'].append({
                    'state': state,
                    'action': most_common[0],
                    'frequency': frequency,
                    'sample_size': total
                })
                
                analysis['predictability_by_state'][state] = frequency
        
        # Sort patterns by frequency
        analysis['most_common_patterns'].sort(key=lambda x: x['frequency'], reverse=True)
        analysis['most_common_patterns'] = analysis['most_common_patterns'][:10]
        
        # Calculate average predictability
        if analysis['predictability_by_state']:
            analysis['average_predictability'] = np.mean(list(analysis['predictability_by_state'].values()))
        else:
            analysis['average_predictability'] = 0.0
        
        return analysis
    
    def _simulate_rally(self, p1_strategy: str, p2_strategy: str) -> int:
        """
        Simulate a rally between two strategies
        Returns: Winner (1 or 2)
        """
        # Simplified simulation using learned patterns
        # In reality, this would be much more sophisticated
        
        # Random winner based on strategy strengths
        # This is a placeholder - real implementation would be more complex
        if np.random.random() < 0.5:
            return 1
        else:
            return 2
    
    def _find_counter_strategies(self) -> Dict:
        """Find optimal counter-strategies against each player"""
        counter_strategies = {}
        
        for player in [1, 2]:
            opponent = 2 if player == 1 else 1
            model = self.player1_model if player == 1 else self.player2_model
            
            counters = []
            
            # For each predictable state
            for state, actions in model.items():
                total = sum(actions.values())
                if total < 3:
                    continue
                
                most_common = max(actions.items(), key=lambda x: x[1])
                frequency = most_common[1] / total
                
                if frequency > 0.6:  # Predictable
                    predicted_action = most_common[0]
                    
                    # Determine counter
                    counter = self._determine_counter(predicted_action)
                    
                    counters.append({
                        'state': state,
                        'predicted_action': predicted_action,
                        'frequency': frequency,
                        'counter_strategy': counter,
                        'expected_advantage': self._estimate_counter_advantage(counter, predicted_action)
                    })
            
            counters.sort(key=lambda x: x['expected_advantage'], reverse=True)
            counter_strategies[f'player_{player}'] = counters[:10]
        
        return counter_strategies
    
    def _determine_counter(self, predicted_action: str) -> str:
        """Determine optimal counter to predicted action"""
        # Parse action
        parts = predicted_action.split('_')
        if len(parts) != 3:
            return "anticipate_early"
        
        shot_type, direction, depth = parts
        
        # Counter strategies
        if direction == 'crosscourt':
            return "Position for crosscourt, attack down the line"
        elif direction == 'down_line':
            return "Shade to line side, prepare running crosscourt"
        elif depth == 'deep':
            return "Stay back, wait for short ball"
        elif depth == 'shallow':
            return "Move forward aggressively, attack"
        
        return "Stay centered, react quickly"
    
    def _estimate_counter_advantage(self, counter: str, predicted_action: str) -> float:
        """Estimate advantage gained from counter strategy"""
        # Simplified estimation
        # Real implementation would simulate many scenarios
        base_advantage = 0.6  # 60% win rate when anticipating correctly
        
        # Certain counters are more effective
        if "attack" in counter.lower():
            base_advantage += 0.1
        if "anticipate" in counter.lower():
            base_advantage += 0.05
        
        return min(base_advantage, 0.9)
    
    def _compare_predictions(self) -> Dict:
        """Compare shadow AI predictions vs actual shot choices"""
        comparisons = {1: {'correct': 0, 'total': 0}, 
                       2: {'correct': 0, 'total': 0}}
        
        for rally in self.match.get_all_rallies():
            for i, shot in enumerate(rally.shots):
                prev_shot = rally.shots[i-1] if i > 0 else None
                context = {'prev_shot': prev_shot} if prev_shot else None
                
                state = self._encode_game_state(shot, context)
                predicted, confidence = self._predict_shot(shot.player, state)
                
                actual = f"{shot.shot_type}_{shot.direction}_{shot.depth}"
                
                comparisons[shot.player]['total'] += 1
                if predicted == actual:
                    comparisons[shot.player]['correct'] += 1
        
        # Calculate accuracy
        for player in [1, 2]:
            total = comparisons[player]['total']
            if total > 0:
                comparisons[player]['accuracy'] = comparisons[player]['correct'] / total
            else:
                comparisons[player]['accuracy'] = 0.0
        
        return comparisons
    
    def _find_exploitable_weaknesses(self) -> Dict:
        """Find specific exploitable weaknesses in each player's game"""
        weaknesses = {}
        
        for player in [1, 2]:
            model = self.player1_model if player == 1 else self.player2_model
            player_weaknesses = []
            
            # Look for states where player is highly predictable
            for state, actions in model.items():
                total = sum(actions.values())
                if total < 5:
                    continue
                
                # Calculate entropy (unpredictability)
                entropy = 0
                for count in actions.values():
                    p = count / total
                    if p > 0:
                        entropy -= p * np.log2(p)
                
                # Low entropy = predictable = exploitable
                if entropy < 1.0:  # Highly predictable
                    most_common = max(actions.items(), key=lambda x: x[1])
                    
                    player_weaknesses.append({
                        'state': state,
                        'predictability': 1.0 - (entropy / 2.0),  # Normalize
                        'predicted_response': most_common[0],
                        'frequency': most_common[1] / total,
                        'exploit': self._describe_exploit(state, most_common[0])
                    })
            
            player_weaknesses.sort(key=lambda x: x['predictability'], reverse=True)
            weaknesses[f'player_{player}'] = player_weaknesses[:5]
        
        return weaknesses
    
    def _describe_exploit(self, state: str, action: str) -> str:
        """Describe how to exploit this weakness"""
        return f"When in {state} position, opponent almost always hits {action}. Position accordingly and counter-attack."
