"""
Fatigue Fingerprint - When Do You Break Down?
Measures how decision-making and physical performance degrade over time
"""

import numpy as np
from typing import Dict, List
from models import Match, Shot
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class FatigueAnalyzer:
    """Analyzes performance degradation due to fatigue"""
    
    def __init__(self, match: Match):
        self.match = match
        self.segment_duration = 10 * 60  # 10 minutes in seconds
        
    def analyze(self) -> Dict:
        """
        Run complete fatigue analysis
        Returns: Dictionary of fatigue insights
        """
        logger.info("Starting Fatigue analysis")
        
        results = {
            'time_segments': self._segment_match(),
            'degradation_metrics': self._calculate_degradation(),
            'fatigue_patterns': self._identify_fatigue_patterns(),
            'breaking_point': self._predict_breaking_point(),
            'recommendations': self._generate_recommendations()
        }
        
        logger.info("Fatigue analysis complete")
        return results
    
    def _segment_match(self) -> List[Dict]:
        """Divide match into time segments"""
        segments = []
        shots = self.match.get_all_shots()
        
        if not shots:
            return segments
        
        start_time = shots[0].timestamp
        end_time = shots[-1].timestamp
        
        segment_num = 0
        segment_start = start_time
        
        while segment_start < end_time:
            segment_end = segment_start + self.segment_duration
            
            # Get shots in this segment
            segment_shots = [s for s in shots 
                           if segment_start <= s.timestamp < segment_end]
            
            if segment_shots:
                segment_data = {
                    'segment': segment_num,
                    'start_time': segment_start,
                    'end_time': min(segment_end, end_time),
                    'duration': min(segment_end, end_time) - segment_start,
                    'metrics': self._calculate_segment_metrics(segment_shots)
                }
                segments.append(segment_data)
            
            segment_start = segment_end
            segment_num += 1
        
        return segments
    
    def _calculate_segment_metrics(self, shots: List[Shot]) -> Dict:
        """Calculate performance metrics for a time segment"""
        if not shots:
            return {}
        
        # Separate by player
        p1_shots = [s for s in shots if s.player == 1]
        p2_shots = [s for s in shots if s.player == 2]
        
        metrics = {}
        
        for player, player_shots in [(1, p1_shots), (2, p2_shots)]:
            if not player_shots:
                continue
            
            # Shot variety (number of unique shot types)
            shot_types = set(f"{s.shot_type}_{s.direction}" for s in player_shots)
            variety = len(shot_types)
            
            # Error rate
            errors = sum(1 for s in player_shots if s.outcome == 'error')
            error_rate = errors / len(player_shots) if player_shots else 0
            
            # Winners
            winners = sum(1 for s in player_shots if s.outcome == 'winner')
            winner_rate = winners / len(player_shots) if player_shots else 0
            
            # Shot depth (percentage of deep shots)
            deep_shots = sum(1 for s in player_shots if s.depth == 'deep')
            depth_rate = deep_shots / len(player_shots) if player_shots else 0
            
            metrics[f'player_{player}'] = {
                'shot_count': len(player_shots),
                'variety': variety,
                'error_rate': error_rate,
                'winner_rate': winner_rate,
                'depth_rate': depth_rate,
                'aggression': winner_rate + depth_rate  # Combined metric
            }
        
        return metrics
    
    def _calculate_degradation(self) -> Dict:
        """Calculate how each metric degrades over time"""
        segments = self._segment_match()
        
        if len(segments) < 2:
            return {'insufficient_data': True}
        
        degradation = {}
        
        for player in [1, 2]:
            metric_timelines = {
                'variety': [],
                'error_rate': [],
                'winner_rate': [],
                'depth_rate': [],
                'aggression': []
            }
            
            # Extract metrics over time
            for segment in segments:
                player_metrics = segment['metrics'].get(f'player_{player}', {})
                for metric in metric_timelines:
                    if metric in player_metrics:
                        metric_timelines[metric].append(player_metrics[metric])
            
            # Calculate degradation rate (slope) for each metric
            player_degradation = {}
            
            for metric, values in metric_timelines.items():
                if len(values) >= 2:
                    # Linear regression
                    x = np.arange(len(values))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                    
                    player_degradation[metric] = {
                        'rate': slope,
                        'initial': values[0],
                        'final': values[-1],
                        'change': values[-1] - values[0],
                        'r_squared': r_value ** 2,
                        'significant': p_value < 0.05
                    }
            
            degradation[f'player_{player}'] = player_degradation
        
        return degradation
    
    def _identify_fatigue_patterns(self) -> Dict:
        """Identify specific fatigue patterns"""
        degradation = self._calculate_degradation()
        
        if degradation.get('insufficient_data'):
            return {}
        
        patterns = {}
        
        for player in [1, 2]:
            player_deg = degradation.get(f'player_{player}', {})
            player_patterns = []
            
            # Check each metric for significant degradation
            for metric, data in player_deg.items():
                if not data.get('significant'):
                    continue
                
                # Negative slope for good metrics = degradation
                if metric in ['variety', 'winner_rate', 'depth_rate', 'aggression']:
                    if data['rate'] < -0.01:  # Decreasing
                        severity = abs(data['change'] / data['initial']) if data['initial'] != 0 else 0
                        player_patterns.append({
                            'metric': metric,
                            'type': 'degradation',
                            'severity': min(severity, 1.0),
                            'description': self._describe_fatigue_pattern(metric, data)
                        })
                
                # Positive slope for bad metrics = degradation
                elif metric in ['error_rate']:
                    if data['rate'] > 0.01:  # Increasing
                        severity = abs(data['change'])
                        player_patterns.append({
                            'metric': metric,
                            'type': 'degradation',
                            'severity': min(severity, 1.0),
                            'description': self._describe_fatigue_pattern(metric, data)
                        })
            
            # Sort by severity
            player_patterns.sort(key=lambda x: x['severity'], reverse=True)
            patterns[f'player_{player}'] = player_patterns
        
        return patterns
    
    def _describe_fatigue_pattern(self, metric: str, data: Dict) -> str:
        """Create human-readable description of fatigue pattern"""
        change_pct = (data['change'] / data['initial'] * 100) if data['initial'] != 0 else 0
        
        descriptions = {
            'variety': f"Shot variety decreased by {abs(change_pct):.0f}% - becoming more predictable when tired",
            'error_rate': f"Error rate increased by {abs(change_pct):.0f}% - losing consistency",
            'winner_rate': f"Winner rate decreased by {abs(change_pct):.0f}% - less aggressive finishing",
            'depth_rate': f"Deep shot percentage decreased by {abs(change_pct):.0f}% - shots getting shorter",
            'aggression': f"Overall aggression decreased by {abs(change_pct):.0f}% - playing more conservative"
        }
        
        return descriptions.get(metric, f"{metric} degraded significantly")
    
    def _predict_breaking_point(self) -> Dict:
        """Predict when player will hit their breaking point"""
        degradation = self._calculate_degradation()
        segments = self._segment_match()
        
        if degradation.get('insufficient_data') or not segments:
            return {}
        
        breaking_points = {}
        
        for player in [1, 2]:
            player_deg = degradation.get(f'player_{player}', {})
            
            # Find metric degrading fastest
            fastest_degradation = None
            fastest_rate = 0
            
            for metric, data in player_deg.items():
                if metric == 'error_rate':
                    rate = data['rate']  # Positive = bad
                else:
                    rate = -data['rate']  # Negative = bad
                
                if rate > fastest_rate:
                    fastest_rate = rate
                    fastest_degradation = (metric, data)
            
            if fastest_degradation:
                metric, data = fastest_degradation
                
                # Extrapolate to critical threshold
                current_value = data['final']
                rate = data['rate']
                
                # Define critical thresholds
                thresholds = {
                    'error_rate': 0.4,  # 40% error rate
                    'variety': 2.0,  # Only 2 shot types
                    'winner_rate': 0.05,  # 5% winners
                    'aggression': 0.2  # Very low aggression
                }
                
                threshold = thresholds.get(metric, 0)
                
                if rate != 0:
                    segments_to_threshold = (threshold - current_value) / rate
                    minutes_to_threshold = segments_to_threshold * (self.segment_duration / 60)
                    
                    breaking_points[f'player_{player}'] = {
                        'critical_metric': metric,
                        'current_value': current_value,
                        'threshold': threshold,
                        'estimated_minutes_remaining': max(0, minutes_to_threshold),
                        'warning': minutes_to_threshold < 20
                    }
        
        return breaking_points
    
    def _generate_recommendations(self) -> Dict:
        """Generate fatigue management recommendations"""
        patterns = self._identify_fatigue_patterns()
        breaking_points = self._predict_breaking_point()
        
        recommendations = {}
        
        for player in [1, 2]:
            player_recs = []
            
            # Based on fatigue patterns
            player_patterns = patterns.get(f'player_{player}', [])
            for pattern in player_patterns[:3]:  # Top 3
                if pattern['metric'] == 'variety':
                    player_recs.append("Work on maintaining shot variety even when tired. Practice high-intensity drills.")
                elif pattern['metric'] == 'error_rate':
                    player_recs.append("Focus on consistency and margin for error when fatigued. Play higher over net.")
                elif pattern['metric'] == 'depth_rate':
                    player_recs.append("Shots getting shallow - work on maintaining depth. Strengthen legs and core.")
                elif pattern['metric'] == 'aggression':
                    player_recs.append("You become too passive when tired. Practice finishing points under fatigue.")
            
            # Based on breaking point
            bp = breaking_points.get(f'player_{player}')
            if bp and bp.get('warning'):
                player_recs.append(f"Critical: Your {bp['critical_metric']} reaches breaking point quickly. Prioritize conditioning.")
            
            # General recommendations
            if len(player_patterns) >= 2:
                player_recs.append("Multiple metrics degrading - focus on overall fitness and match endurance.")
            
            recommendations[f'player_{player}'] = player_recs
        
        return recommendations
