"""
Chaos Theory - Butterfly Effect Moments
Identifies single points where different outcomes would have changed match result
"""

import numpy as np
from typing import Dict, List
from models import Match, Rally
import logging

logger = logging.getLogger(__name__)

class ChaosAnalyzer:
    """Analyzes butterfly effect moments in match"""
    
    def __init__(self, match: Match):
        self.match = match
        
    def analyze(self) -> Dict:
        """
        Run complete chaos/butterfly effect analysis
        Returns: Dictionary of critical moments
        """
        logger.info("Starting Chaos Theory analysis")
        
        results = {
            'butterfly_points': self._find_butterfly_points(),
            'alternate_timelines': self._simulate_alternate_timelines(),
            'critical_moments': self._rank_critical_moments(),
            'what_if_scenarios': self._generate_what_if_scenarios()
        }
        
        logger.info("Chaos Theory analysis complete")
        return results
    
    def _calculate_win_probability(self, set_score: Dict, game_score: Dict, 
                                   server: int, current_player: int) -> float:
        """
        Calculate win probability for current player given current score
        Simplified model - real version would be much more sophisticated
        """
        p1_sets = set_score.get(1, 0)
        p2_sets = set_score.get(2, 0)
        p1_games = game_score.get(1, 0)
        p2_games = game_score.get(2, 0)
        
        # Base probability
        prob = 0.5
        
        # Set advantage
        set_diff = p1_sets - p2_sets if current_player == 1 else p2_sets - p1_sets
        prob += set_diff * 0.2
        
        # Game advantage
        game_diff = p1_games - p2_games if current_player == 1 else p2_games - p1_games
        prob += game_diff * 0.05
        
        # Serving advantage
        if server == current_player:
            prob += 0.05
        
        # Clamp to reasonable range
        return max(0.05, min(0.95, prob))
    
    def _simulate_from_point(self, rally_index: int, flip_outcome: bool = False) -> Dict:
        """
        Simulate match continuation from a specific point
        If flip_outcome=True, simulate as if the point went the other way
        """
        rallies = self.match.get_all_rallies()
        
        if rally_index >= len(rallies):
            return {'winner': 0}
        
        # Get actual winner
        actual_winner = self.match.winner
        
        # Simple simulation: if we flip a close point, estimate impact
        rally = rallies[rally_index]
        
        # Get score context at this point
        set_num, game_num = self._get_rally_context(rally_index)
        
        # Estimate if flipping this point changes match outcome
        # This is simplified - real version would run Monte Carlo simulations
        
        if flip_outcome:
            # Flipped winner
            alt_winner = 2 if rally.winner == 1 else 1
            
            # Estimate probability this leads to different match outcome
            # Depends on how close the match was at this point
            closeness = self._calculate_match_closeness(rally_index)
            
            flip_probability = closeness * 0.5  # 50% chance if very close
            
            if np.random.random() < flip_probability:
                return {'winner': alt_winner}
        
        return {'winner': actual_winner}
    
    def _calculate_match_closeness(self, rally_index: int) -> float:
        """
        Calculate how close the match was at a given point
        Returns: 0 (one-sided) to 1 (very close)
        """
        # Get score at this point
        # Simplified: just use rally index as proxy
        total_rallies = len(self.match.get_all_rallies())
        
        if total_rallies == 0:
            return 0.5
        
        # Points in middle of match are typically more impactful
        position = rally_index / total_rallies
        
        # Bell curve: most impactful in middle, less at start/end
        closeness = 1.0 - abs(position - 0.5) * 2
        
        return max(0.1, closeness)
    
    def _get_rally_context(self, rally_index: int) -> tuple:
        """Get set and game number for a rally"""
        count = 0
        for set_data in self.match.sets:
            for game in set_data.games:
                for rally in game.rallies:
                    if count == rally_index:
                        return (set_data.set_number, game.game_number)
                    count += 1
        return (1, 1)
    
    def _find_butterfly_points(self) -> List[Dict]:
        """Find points that could have changed match outcome"""
        rallies = self.match.get_all_rallies()
        butterfly_points = []
        
        actual_winner = self.match.winner
        
        for rally_idx, rally in enumerate(rallies):
            # Simulate alternate timeline where this point went the other way
            simulations = []
            
            for _ in range(100):  # Monte Carlo simulation
                result = self._simulate_from_point(rally_idx, flip_outcome=True)
                simulations.append(result['winner'])
            
            # Calculate probability of different outcome
            if simulations:
                alt_winner_count = sum(1 for w in simulations if w != actual_winner)
                flip_probability = alt_winner_count / len(simulations)
            else:
                flip_probability = 0.0
            
            # If flipping this point significantly changes outcome
            if flip_probability > 0.3:  # 30% chance of different outcome
                set_num, game_num = self._get_rally_context(rally_idx)
                
                butterfly_points.append({
                    'rally_index': rally_idx,
                    'point_number': rally_idx + 1,
                    'set': set_num,
                    'game': game_num,
                    'actual_winner': rally.winner,
                    'flip_probability': flip_probability,
                    'impact': flip_probability,
                    'description': self._describe_butterfly_point(rally, flip_probability)
                })
        
        # Sort by impact
        butterfly_points.sort(key=lambda x: x['impact'], reverse=True)
        
        return butterfly_points
    
    def _describe_butterfly_point(self, rally: Rally, flip_prob: float) -> str:
        """Create description of butterfly point"""
        impact_level = "HIGH" if flip_prob > 0.6 else ("MEDIUM" if flip_prob > 0.4 else "LOW")
        
        return (f"{impact_level} IMPACT: If this point had gone the other way, "
                f"{flip_prob*100:.0f}% chance the match outcome would have changed")
    
    def _simulate_alternate_timelines(self) -> Dict:
        """Simulate multiple alternate timelines"""
        butterfly_points = self._find_butterfly_points()
        
        if not butterfly_points:
            return {'timelines': []}
        
        # Take top 5 butterfly points
        top_butterflies = butterfly_points[:5]
        
        timelines = []
        
        for bp in top_butterflies:
            timeline = {
                'flip_point': bp['point_number'],
                'original_outcome': self.match.winner,
                'alternate_outcomes': [],
                'probability_distribution': {}
            }
            
            # Simulate 1000 alternate matches from this point
            outcomes = []
            for _ in range(1000):
                result = self._simulate_from_point(bp['rally_index'], flip_outcome=True)
                outcomes.append(result['winner'])
            
            # Count outcomes
            outcome_counts = {}
            for outcome in outcomes:
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            
            # Convert to probabilities
            timeline['probability_distribution'] = {
                player: count/len(outcomes) 
                for player, count in outcome_counts.items()
            }
            
            timelines.append(timeline)
        
        return {'timelines': timelines}
    
    def _rank_critical_moments(self) -> List[Dict]:
        """Rank all moments by criticality"""
        butterfly_points = self._find_butterfly_points()
        
        # Add additional context to each
        for bp in butterfly_points:
            bp['criticality_score'] = self._calculate_criticality(bp)
        
        # Sort by criticality
        butterfly_points.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        return butterfly_points[:10]  # Top 10
    
    def _calculate_criticality(self, butterfly_point: Dict) -> float:
        """Calculate overall criticality score"""
        # Base score from flip probability
        score = butterfly_point['flip_probability']
        
        # Bonus for being in later stages of match
        rally_idx = butterfly_point['rally_index']
        total_rallies = len(self.match.get_all_rallies())
        position = rally_idx / total_rallies if total_rallies > 0 else 0
        
        # Later points are more critical
        if position > 0.7:
            score *= 1.3
        elif position > 0.5:
            score *= 1.1
        
        return score
    
    def _generate_what_if_scenarios(self) -> List[Dict]:
        """Generate interesting what-if scenarios"""
        critical_moments = self._rank_critical_moments()
        
        scenarios = []
        
        for moment in critical_moments[:5]:
            scenario = {
                'point': moment['point_number'],
                'actual': f"Player {moment['actual_winner']} won this point",
                'what_if': f"If Player {2 if moment['actual_winner']==1 else 1} had won this point",
                'impact': f"{moment['flip_probability']*100:.0f}% chance match outcome changes",
                'context': f"Set {moment['set']}, Game {moment['game']}",
                'takeaway': self._generate_takeaway(moment)
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_takeaway(self, moment: Dict) -> str:
        """Generate actionable takeaway from critical moment"""
        if moment['flip_probability'] > 0.7:
            return "THIS WAS THE TURNING POINT. Practice pressure situations like this."
        elif moment['flip_probability'] > 0.5:
            return "Major impact point. Focus on winning crucial moments."
        else:
            return "Moderately important point. Every point matters in close matches."
