"""
Momentum Topology Map - Visualize Psychological Flow
Maps momentum as a topological surface showing confidence peaks and valleys
"""

import numpy as np
from typing import Dict, List, Tuple
from models import Match, Rally
from scipy.interpolate import make_interp_spline
import logging

logger = logging.getLogger(__name__)

class MomentumAnalyzer:
    """Analyzes momentum swings throughout match"""
    
    def __init__(self, match: Match):
        self.match = match
        self.momentum_timeline = []
        
    def analyze(self) -> Dict:
        """
        Run complete momentum analysis
        Returns: Dictionary of momentum insights
        """
        logger.info("Starting Momentum analysis")
        
        # Calculate momentum for each point
        self._calculate_momentum_timeline()
        
        results = {
            'timeline': self.momentum_timeline,
            'turning_points': self._find_turning_points(),
            'momentum_peaks': self._find_momentum_peaks(),
            'momentum_valleys': self._find_momentum_valleys(),
            'biggest_swings': self._find_biggest_swings(),
            'momentum_statistics': self._calculate_statistics(),
            'visualization_data': self._prepare_visualization_data()
        }
        
        logger.info("Momentum analysis complete")
        return results
    
    def _calculate_momentum_timeline(self):
        """Calculate momentum score for each point in match"""
        self.momentum_timeline = []
        
        current_momentum = 0.0
        point_number = 0
        
        rallies = self.match.get_all_rallies()
        
        for rally_idx, rally in enumerate(rallies):
            point_number += 1
            
            # Get point context
            set_num, game_num = self._get_point_context(rally_idx)
            
            # Update momentum based on point outcome
            momentum_delta = self._calculate_momentum_delta(rally, current_momentum)
            current_momentum += momentum_delta
            
            # Momentum decay (returns toward neutral over time)
            current_momentum *= 0.95
            
            # Clamp momentum between -100 and +100
            current_momentum = max(-100, min(100, current_momentum))
            
            # Store momentum datapoint
            self.momentum_timeline.append({
                'point_number': point_number,
                'rally_index': rally_idx,
                'momentum': current_momentum,
                'delta': momentum_delta,
                'set': set_num,
                'game': game_num,
                'winner': rally.winner,
                'point_type': rally.point_type,
                'emotional_state': self._classify_emotional_state(current_momentum)
            })
    
    def _calculate_momentum_delta(self, rally: Rally, current_momentum: float) -> float:
        """Calculate momentum change from a point"""
        delta = 0.0
        
        # Base momentum from winning/losing
        if rally.winner == 1:
            delta = 5.0
        elif rally.winner == 2:
            delta = -5.0
        
        # Point type matters
        if rally.point_type == 'winner':
            delta *= 1.5  # Winners build more momentum
        elif rally.point_type == 'unforced_error':
            delta *= 1.3  # Errors hurt momentum
        
        # Rally length matters
        if rally.shot_count > 10:
            delta *= 1.2  # Long rallies have bigger impact
        
        # Momentum compounds (rich get richer)
        if (delta > 0 and current_momentum > 20) or (delta < 0 and current_momentum < -20):
            delta *= 1.2
        
        # Momentum reversal (comeback) is extra impactful
        if (delta > 0 and current_momentum < -30) or (delta < 0 and current_momentum > 30):
            delta *= 1.3
        
        return delta
    
    def _get_point_context(self, rally_idx: int) -> Tuple[int, int]:
        """Get set and game number for a rally"""
        rally_count = 0
        for set_data in self.match.sets:
            for game in set_data.games:
                for rally in game.rallies:
                    if rally_count == rally_idx:
                        return (set_data.set_number, game.game_number)
                    rally_count += 1
        return (1, 1)
    
    def _classify_emotional_state(self, momentum: float) -> str:
        """Classify emotional/psychological state based on momentum"""
        if momentum > 60:
            return "DOMINANT"
        elif momentum > 30:
            return "CONFIDENT"
        elif momentum > 10:
            return "POSITIVE"
        elif momentum > -10:
            return "NEUTRAL"
        elif momentum > -30:
            return "STRUGGLING"
        elif momentum > -60:
            return "FRUSTRATED"
        else:
            return "COLLAPSING"
    
    def _find_turning_points(self) -> List[Dict]:
        """Identify major momentum turning points"""
        if len(self.momentum_timeline) < 3:
            return []
        
        turning_points = []
        
        for i in range(2, len(self.momentum_timeline) - 2):
            prev_momentum = self.momentum_timeline[i-1]['momentum']
            curr_momentum = self.momentum_timeline[i]['momentum']
            next_momentum = self.momentum_timeline[i+1]['momentum']
            
            # Check for significant direction change
            prev_dir = curr_momentum - prev_momentum
            next_dir = next_momentum - curr_momentum
            
            # Turning point if direction reversed significantly
            if abs(prev_dir + next_dir) < abs(prev_dir) * 0.3:  # Direction changed
                if abs(curr_momentum - prev_momentum) > 15:  # Significant magnitude
                    turning_points.append({
                        'point_number': self.momentum_timeline[i]['point_number'],
                        'momentum_before': prev_momentum,
                        'momentum_after': next_momentum,
                        'magnitude': abs(next_momentum - prev_momentum),
                        'type': 'peak' if curr_momentum > prev_momentum else 'valley',
                        'description': self._describe_turning_point(self.momentum_timeline[i])
                    })
        
        return turning_points
    
    def _describe_turning_point(self, point: Dict) -> str:
        """Create description of what happened at turning point"""
        descriptions = []
        
        if point['point_type'] == 'winner':
            descriptions.append(f"Amazing winner by Player {point['winner']}")
        elif point['point_type'] == 'unforced_error':
            loser = 2 if point['winner'] == 1 else 1
            descriptions.append(f"Unforced error by Player {loser}")
        
        descriptions.append(f"Momentum shifted to {point['emotional_state']}")
        
        return " - ".join(descriptions)
    
    def _find_momentum_peaks(self) -> List[Dict]:
        """Find momentum peaks (local maxima)"""
        peaks = []
        
        for i in range(1, len(self.momentum_timeline) - 1):
            prev = self.momentum_timeline[i-1]['momentum']
            curr = self.momentum_timeline[i]['momentum']
            next = self.momentum_timeline[i+1]['momentum']
            
            if curr > prev and curr > next and curr > 40:  # Local maximum above threshold
                peaks.append({
                    'point_number': self.momentum_timeline[i]['point_number'],
                    'momentum': curr,
                    'dominant_player': 1 if curr > 0 else 2
                })
        
        return sorted(peaks, key=lambda x: abs(x['momentum']), reverse=True)[:5]
    
    def _find_momentum_valleys(self) -> List[Dict]:
        """Find momentum valleys (local minima)"""
        valleys = []
        
        for i in range(1, len(self.momentum_timeline) - 1):
            prev = self.momentum_timeline[i-1]['momentum']
            curr = self.momentum_timeline[i]['momentum']
            next = self.momentum_timeline[i+1]['momentum']
            
            if curr < prev and curr < next and abs(curr) > 40:  # Local minimum
                valleys.append({
                    'point_number': self.momentum_timeline[i]['point_number'],
                    'momentum': curr,
                    'struggling_player': 1 if curr < 0 else 2
                })
        
        return sorted(valleys, key=lambda x: abs(x['momentum']), reverse=True)[:5]
    
    def _find_biggest_swings(self) -> List[Dict]:
        """Find biggest momentum swings between consecutive points"""
        swings = []
        
        for i in range(1, len(self.momentum_timeline)):
            prev = self.momentum_timeline[i-1]['momentum']
            curr = self.momentum_timeline[i]['momentum']
            delta = abs(curr - prev)
            
            if delta > 10:  # Significant swing
                swings.append({
                    'from_point': self.momentum_timeline[i-1]['point_number'],
                    'to_point': self.momentum_timeline[i]['point_number'],
                    'momentum_before': prev,
                    'momentum_after': curr,
                    'swing_magnitude': delta,
                    'direction': 'positive' if curr > prev else 'negative',
                    'winner': self.momentum_timeline[i]['winner']
                })
        
        return sorted(swings, key=lambda x: x['swing_magnitude'], reverse=True)[:10]
    
    def _calculate_statistics(self) -> Dict:
        """Calculate overall momentum statistics"""
        if not self.momentum_timeline:
            return {}
        
        momentums = [p['momentum'] for p in self.momentum_timeline]
        
        return {
            'average_momentum': np.mean(momentums),
            'momentum_volatility': np.std(momentums),
            'max_momentum': max(momentums),
            'min_momentum': min(momentums),
            'total_range': max(momentums) - min(momentums),
            'time_in_positive': sum(1 for m in momentums if m > 10) / len(momentums),
            'time_in_negative': sum(1 for m in momentums if m < -10) / len(momentums),
            'time_in_neutral': sum(1 for m in momentums if -10 <= m <= 10) / len(momentums)
        }
    
    def _prepare_visualization_data(self) -> Dict:
        """Prepare data for visualization"""
        if not self.momentum_timeline:
            return {}
        
        # Extract data for plotting
        points = [p['point_number'] for p in self.momentum_timeline]
        momentums = [p['momentum'] for p in self.momentum_timeline]
        
        # Smooth the curve for better visualization
        if len(points) > 3:
            # Create smooth spline
            points_array = np.array(points)
            momentum_array = np.array(momentums)
            
            # Smooth points
            smooth_points = np.linspace(points_array.min(), points_array.max(), len(points) * 3)
            
            try:
                spline = make_interp_spline(points_array, momentum_array, k=3)
                smooth_momentum = spline(smooth_points)
            except:
                smooth_points = points
                smooth_momentum = momentums
        else:
            smooth_points = points
            smooth_momentum = momentums
        
        return {
            'raw': {
                'points': points,
                'momentum': momentums
            },
            'smooth': {
                'points': smooth_points.tolist() if isinstance(smooth_points, np.ndarray) else smooth_points,
                'momentum': smooth_momentum.tolist() if isinstance(smooth_momentum, np.ndarray) else smooth_momentum
            },
            'annotations': [
                {
                    'point': tp['point_number'],
                    'label': 'Turning Point',
                    'type': tp['type']
                }
                for tp in self._find_turning_points()[:5]
            ]
        }
