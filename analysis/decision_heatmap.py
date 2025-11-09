"""
Decision Heatmap - Where You Think Wrong
Maps decision quality across different court positions
"""

import numpy as np
from typing import Dict, List, Tuple
from models import Match, Shot
import logging

logger = logging.getLogger(__name__)

class DecisionHeatmap:
    """Analyzes decision quality by court position"""
    
    def __init__(self, match: Match):
        self.match = match
        self.grid_size = (20, 40)  # 20x40 grid covering court
        
    def analyze(self) -> Dict:
        """
        Run complete decision heatmap analysis
        Returns: Dictionary of decision quality data
        """
        logger.info("Starting Decision Heatmap analysis")
        
        results = {
            'heatmap_data': self._generate_heatmap(),
            'worst_zones': self._find_worst_zones(),
            'best_zones': self._find_best_zones(),
            'position_specific_advice': self._generate_position_advice()
        }
        
        logger.info("Decision Heatmap analysis complete")
        return results
    
    def _position_to_grid(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """Convert court coordinates to grid indices"""
        x, y = position
        
        # Court dimensions: 10.97m x 23.77m
        # Map to grid
        grid_x = int((x / 10.97) * self.grid_size[0])
        grid_y = int((y / 23.77) * self.grid_size[1])
        
        # Clamp to valid range
        grid_x = max(0, min(self.grid_size[0] - 1, grid_x))
        grid_y = max(0, min(self.grid_size[1] - 1, grid_y))
        
        return (grid_x, grid_y)
    
    def _evaluate_shot_decision(self, shot: Shot, rally_outcome: str) -> float:
        """
        Evaluate quality of shot decision
        Returns: Quality score from 0 (bad) to 1 (good)
        """
        quality = 0.5  # Baseline
        
        # Outcome-based adjustment
        if shot.outcome == 'winner':
            quality = 1.0
        elif shot.outcome == 'error':
            quality = 0.0
        elif rally_outcome == 'won':
            quality = 0.7
        elif rally_outcome == 'lost':
            quality = 0.3
        
        # Adjust based on shot selection
        # Aggressive shots from good positions = good decision
        x, y = shot.ball_position
        
        if y < 8:  # Attacking position (near net)
            if shot.shot_type in ['volley', 'winner']:
                quality += 0.1
            if shot.depth == 'shallow' or shot.outcome == 'error':
                quality -= 0.1
        
        elif y > 18:  # Defensive position (deep in court)
            if shot.depth == 'deep':  # Good to go deep from defense
                quality += 0.1
            if shot.shot_type == 'winner':  # Risky from defense
                quality -= 0.05
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, quality))
    
    def _generate_heatmap(self) -> Dict:
        """Generate decision quality heatmap for each player"""
        heatmaps = {
            1: {
                'quality': np.zeros(self.grid_size),
                'count': np.zeros(self.grid_size)
            },
            2: {
                'quality': np.zeros(self.grid_size),
                'count': np.zeros(self.grid_size)
            }
        }
        
        # Process each rally
        for rally in self.match.get_all_rallies():
            rally_outcome = 'won' if rally.winner else 'unknown'
            
            for shot in rally.shots:
                # Determine if shot's player won this rally
                shot_outcome = 'won' if shot.player == rally.winner else 'lost'
                
                # Evaluate decision
                quality = self._evaluate_shot_decision(shot, shot_outcome)
                
                # Add to heatmap
                grid_pos = self._position_to_grid(shot.ball_position)
                
                heatmaps[shot.player]['quality'][grid_pos] += quality
                heatmaps[shot.player]['count'][grid_pos] += 1
        
        # Calculate average quality per cell
        result = {}
        for player in [1, 2]:
            quality_grid = heatmaps[player]['quality']
            count_grid = heatmaps[player]['count']
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                avg_quality = quality_grid / count_grid
                avg_quality = np.nan_to_num(avg_quality, nan=0.5)  # Default to neutral
            
            result[f'player_{player}'] = {
                'quality_grid': avg_quality.tolist(),
                'count_grid': count_grid.tolist(),
                'grid_size': self.grid_size
            }
        
        return result
    
    def _find_worst_zones(self) -> Dict:
        """Find zones with worst decision-making"""
        heatmap_data = self._generate_heatmap()
        
        worst_zones = {}
        
        for player in [1, 2]:
            quality_grid = np.array(heatmap_data[f'player_{player}']['quality_grid'])
            count_grid = np.array(heatmap_data[f'player_{player}']['count_grid'])
            
            # Find cells with poor quality and sufficient sample size
            poor_decisions = []
            
            for i in range(self.grid_size[0]):
                for j in range(self.grid_size[1]):
                    if count_grid[i, j] >= 3:  # Minimum sample size
                        quality = quality_grid[i, j]
                        
                        if quality < 0.4:  # Poor quality threshold
                            # Convert grid back to court coordinates
                            court_x = (i / self.grid_size[0]) * 10.97
                            court_y = (j / self.grid_size[1]) * 23.77
                            
                            poor_decisions.append({
                                'position': (court_x, court_y),
                                'quality': quality,
                                'sample_size': int(count_grid[i, j]),
                                'zone_description': self._describe_zone(court_x, court_y)
                            })
            
            # Sort by quality (worst first)
            poor_decisions.sort(key=lambda x: x['quality'])
            worst_zones[f'player_{player}'] = poor_decisions[:5]
        
        return worst_zones
    
    def _find_best_zones(self) -> Dict:
        """Find zones with best decision-making"""
        heatmap_data = self._generate_heatmap()
        
        best_zones = {}
        
        for player in [1, 2]:
            quality_grid = np.array(heatmap_data[f'player_{player}']['quality_grid'])
            count_grid = np.array(heatmap_data[f'player_{player}']['count_grid'])
            
            good_decisions = []
            
            for i in range(self.grid_size[0]):
                for j in range(self.grid_size[1]):
                    if count_grid[i, j] >= 3:
                        quality = quality_grid[i, j]
                        
                        if quality > 0.7:  # Good quality threshold
                            court_x = (i / self.grid_size[0]) * 10.97
                            court_y = (j / self.grid_size[1]) * 23.77
                            
                            good_decisions.append({
                                'position': (court_x, court_y),
                                'quality': quality,
                                'sample_size': int(count_grid[i, j]),
                                'zone_description': self._describe_zone(court_x, court_y)
                            })
            
            good_decisions.sort(key=lambda x: x['quality'], reverse=True)
            best_zones[f'player_{player}'] = good_decisions[:5]
        
        return best_zones
    
    def _describe_zone(self, x: float, y: float) -> str:
        """Create human-readable zone description"""
        # Horizontal position
        if x < 3.66:
            h_pos = "left side"
        elif x < 7.31:
            h_pos = "center"
        else:
            h_pos = "right side"
        
        # Vertical position
        if y < 5:
            v_pos = "at net"
        elif y < 10:
            v_pos = "in service box"
        elif y < 15:
            v_pos = "mid-court"
        elif y < 20:
            v_pos = "near baseline"
        else:
            v_pos = "deep behind baseline"
        
        return f"{h_pos}, {v_pos}"
    
    def _generate_position_advice(self) -> Dict:
        """Generate specific advice for problematic zones"""
        worst_zones = self._find_worst_zones()
        
        advice = {}
        
        for player in [1, 2]:
            player_advice = []
            
            zones = worst_zones.get(f'player_{player}', [])
            for zone in zones:
                zone_desc = zone['zone_description']
                quality = zone['quality']
                
                # Generate specific advice based on zone
                if "at net" in zone_desc:
                    suggestion = "At net: Be more aggressive with volleys. Aim for angles or put-aways."
                elif "deep behind baseline" in zone_desc:
                    suggestion = "Deep position: Focus on getting back in the point. Hit deep with margin."
                elif "service box" in zone_desc:
                    suggestion = "Mid-court: Move forward on short balls. Don't give opponent time to recover."
                elif "near baseline" in zone_desc:
                    suggestion = "Baseline: Mix up direction and depth. You're being too predictable."
                else:
                    suggestion = f"In {zone_desc}: Review your shot selection. Currently making poor choices."
                
                player_advice.append({
                    'zone': zone_desc,
                    'quality_score': quality,
                    'advice': suggestion
                })
            
            advice[f'player_{player}'] = player_advice
        
        return advice
