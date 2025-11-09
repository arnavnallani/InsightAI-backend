"""
Counterfactual Shot Simulator - What If Analysis
Simulates alternative shot choices to find missed opportunities
"""

import numpy as np
from typing import Dict, List, Tuple
from models import Match, Shot, Rally
import logging

logger = logging.getLogger(__name__)

class CounterfactualAnalyzer:
    """Analyzes what would have happened with different shot choices"""
    
    def __init__(self, match: Match):
        self.match = match
        self.shot_success_rates = self._calculate_shot_success_rates()
        
    def analyze(self) -> Dict:
        """
        Run complete counterfactual analysis
        Returns: Dictionary of missed opportunities
        """
        logger.info("Starting Counterfactual analysis")
        
        results = {
            'missed_opportunities': self._find_missed_opportunities(),
            'optimal_shot_analysis': self._analyze_optimal_shots(),
            'win_probability_deltas': self._calculate_win_prob_deltas(),
            'biggest_mistakes': [],
            'summary': {}
        }
        
        # Identify biggest mistakes
        results['biggest_mistakes'] = self._rank_biggest_mistakes(results['missed_opportunities'])
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        logger.info("Counterfactual analysis complete")
        return results
    
    def _calculate_shot_success_rates(self) -> Dict:
        """Calculate historical success rates for different shot types"""
        success_counts = {}
        total_counts = {}
        
        for shot in self.match.get_all_shots():
            key = f"{shot.shot_type}_{shot.direction}_{shot.depth}"
            
            if key not in total_counts:
                total_counts[key] = 0
                success_counts[key] = 0
            
            total_counts[key] += 1
            if shot.outcome in ['winner', 'in_play']:
                success_counts[key] += 1
        
        success_rates = {}
        for key in total_counts:
            if total_counts[key] > 0:
                success_rates[key] = success_counts[key] / total_counts[key]
            else:
                success_rates[key] = 0.5  # Default
        
        return success_rates
    
    def _get_alternative_shots(self, current_shot: Shot) -> List[Dict]:
        """Generate alternative shot options for a given situation"""
        alternatives = []
        
        shot_types = ['forehand', 'backhand', 'slice', 'lob', 'drop_shot']
        directions = ['crosscourt', 'down_line', 'center']
        depths = ['shallow', 'mid', 'deep']
        
        for shot_type in shot_types:
            for direction in directions:
                for depth in depths:
                    # Skip if same as current shot
                    if (shot_type == current_shot.shot_type and 
                        direction == current_shot.direction and 
                        depth == current_shot.depth):
                        continue
                    
                    # Create alternative
                    alt = {
                        'type': shot_type,
                        'direction': direction,
                        'depth': depth,
                        'key': f"{shot_type}_{direction}_{depth}"
                    }
                    
                    # Estimate success probability
                    alt['success_prob'] = self._estimate_shot_success(alt, current_shot)
                    
                    # Estimate win probability if successful
                    alt['win_prob_if_success'] = self._estimate_win_probability(alt, current_shot)
                    
                    # Overall expected value
                    alt['expected_value'] = alt['success_prob'] * alt['win_prob_if_success']
                    
                    alternatives.append(alt)
        
        return alternatives
    
    def _estimate_shot_success(self, alternative: Dict, current_shot: Shot) -> float:
        """Estimate probability of alternative shot succeeding"""
        # Get base success rate from history
        base_rate = self.shot_success_rates.get(alternative['key'], 0.5)
        
        # Adjust based on court position
        x, y = current_shot.ball_position
        
        # Harder shots from defensive position
        if y > 20:  # Deep in court
            base_rate *= 0.8
        elif y < 5:  # Net position
            if alternative['type'] == 'volley':
                base_rate *= 1.2
            else:
                base_rate *= 0.9
        
        # Certain shots are inherently riskier
        if alternative['type'] == 'drop_shot':
            base_rate *= 0.7
        elif alternative['type'] == 'lob':
            base_rate *= 0.75
        
        # Down the line is riskier than crosscourt
        if alternative['direction'] == 'down_line':
            base_rate *= 0.85
        
        return min(base_rate, 1.0)
    
    def _estimate_win_probability(self, alternative: Dict, current_shot: Shot) -> float:
        """Estimate probability of winning point if shot succeeds"""
        base_prob = 0.5
        
        # Aggressive shots that land have higher win probability
        if alternative['depth'] == 'deep' and alternative['direction'] == 'down_line':
            base_prob += 0.2
        
        if alternative['type'] == 'winner':
            base_prob = 0.9
        elif alternative['type'] == 'drop_shot':
            base_prob += 0.25
        elif alternative['type'] == 'lob':
            base_prob += 0.15
        
        # Court position matters
        x, y = current_shot.ball_position
        if y < 8:  # Attacking position
            base_prob += 0.1
        
        return min(base_prob, 0.95)
    
    def _find_missed_opportunities(self) -> List[Dict]:
        """Find shots where a better alternative existed"""
        missed = []
        
        for rally_idx, rally in enumerate(self.match.get_all_rallies()):
            for shot_idx, shot in enumerate(rally.shots):
                # Skip if shot was a winner
                if shot.outcome == 'winner':
                    continue
                
                # Get alternatives
                alternatives = self._get_alternative_shots(shot)
                
                # Find best alternative
                if alternatives:
                    best_alt = max(alternatives, key=lambda x: x['expected_value'])
                    
                    # Current shot expected value
                    current_key = f"{shot.shot_type}_{shot.direction}_{shot.depth}"
                    current_success = self.shot_success_rates.get(current_key, 0.5)
                    current_ev = current_success * 0.5  # Baseline win prob
                    
                    # If alternative is significantly better
                    improvement = best_alt['expected_value'] - current_ev
                    if improvement > 0.15:  # 15% better
                        missed.append({
                            'rally': rally_idx,
                            'shot': shot_idx,
                            'player': shot.player,
                            'timestamp': shot.timestamp,
                            'actual_shot': {
                                'type': shot.shot_type,
                                'direction': shot.direction,
                                'depth': shot.depth,
                                'expected_value': current_ev
                            },
                            'better_option': best_alt,
                            'improvement': improvement,
                            'position': shot.ball_position
                        })
        
        return missed
    
    def _analyze_optimal_shots(self) -> Dict:
        """Analyze what percentage of shots were optimal"""
        results = {1: {'optimal': 0, 'suboptimal': 0}, 
                   2: {'optimal': 0, 'suboptimal': 0}}
        
        missed = self._find_missed_opportunities()
        all_shots = self.match.get_all_shots()
        
        missed_by_player = {1: 0, 2: 0}
        for opportunity in missed:
            missed_by_player[opportunity['player']] += 1
        
        for player in [1, 2]:
            player_shots = sum(1 for s in all_shots if s.player == player)
            results[player]['suboptimal'] = missed_by_player[player]
            results[player]['optimal'] = player_shots - missed_by_player[player]
            results[player]['optimal_percentage'] = (results[player]['optimal'] / player_shots * 100) if player_shots > 0 else 0
        
        return results
    
    def _calculate_win_prob_deltas(self) -> Dict:
        """Calculate how much win probability changed with each decision"""
        deltas = []
        
        for opportunity in self._find_missed_opportunities():
            delta = {
                'rally': opportunity['rally'],
                'shot': opportunity['shot'],
                'player': opportunity['player'],
                'actual_win_prob': opportunity['actual_shot']['expected_value'],
                'optimal_win_prob': opportunity['better_option']['expected_value'],
                'delta': opportunity['improvement']
            }
            deltas.append(delta)
        
        return {'deltas': deltas, 'total_opportunities': len(deltas)}
    
    def _rank_biggest_mistakes(self, missed_opportunities: List[Dict]) -> List[Dict]:
        """Rank the biggest mistakes by improvement potential"""
        # Sort by improvement (descending)
        ranked = sorted(missed_opportunities, key=lambda x: x['improvement'], reverse=True)
        
        # Return top 10
        return ranked[:10]
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary statistics"""
        missed = results['missed_opportunities']
        
        summary = {
            'total_missed_opportunities': len(missed),
            'by_player': {
                1: sum(1 for m in missed if m['player'] == 1),
                2: sum(1 for m in missed if m['player'] == 2)
            },
            'average_improvement': np.mean([m['improvement'] for m in missed]) if missed else 0,
            'biggest_miss': results['biggest_mistakes'][0] if results['biggest_mistakes'] else None
        }
        
        return summary
