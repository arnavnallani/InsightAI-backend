"""
Intelligent shot detection and classification
Combines multiple signals: ball trajectory, player position, timing
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ShotClassifier:
    """Detect and classify tennis shots"""
    
    def __init__(self):
        self.last_shot_frame = -999
        self.min_frames_between_shots = 5  # Minimum gap between shots
        self.rally_shot_count = 0  # Track shots in current rally
    
    def detect_shots(self, ball_history: List[Dict], player_detections: List[Dict], 
                     frame_number: int) -> Optional[Dict]:
        """
        Detect if a shot occurred in current frame
        
        Returns: {
            'frame': int,
            'shot_type': str,  # serve, forehand, backhand, volley, etc.
            'player': int,  # 1 or 2
            'ball_position': (x, y),
            'confidence': float
        }
        """
        if len(ball_history) < 3:
            return None
        
        # Too soon after last shot
        if frame_number - self.last_shot_frame < self.min_frames_between_shots:
            return None
        
        # Analyze recent ball trajectory
        recent = ball_history[-5:] if len(ball_history) >= 5 else ball_history
        
        # Signal 1: Velocity change (ball direction reverses)
        velocity_change = self._detect_velocity_change(recent)
        
        # Signal 2: Ball near player
        near_player = self._detect_ball_near_player(recent[-1], player_detections)
        
        # Signal 3: Trajectory inflection
        inflection = self._detect_trajectory_inflection(recent)
        
        # Combine signals
        shot_confidence = 0.0
        
        if velocity_change:
            shot_confidence += 0.4
        
        if near_player is not None:
            shot_confidence += 0.4
        
        if inflection:
            shot_confidence += 0.2
        
        if shot_confidence < 0.5:
            return None  # Not confident this is a shot
        
        # Classify shot type
        shot_type = self._classify_shot_type(recent, near_player, player_detections)
        
        # Determine which player hit
        player_number = near_player.get('player_number') if near_player else None
        
        if player_number is None:
            # Fallback: determine by court position
            ball_y = recent[-1]['position'][1]
            # Assume frame split vertically
            player_number = 1 if ball_y > 500 else 2  # This is simplified
        
        self.last_shot_frame = frame_number
        self.rally_shot_count += 1
        
        return {
            'frame': frame_number,
            'shot_type': shot_type,
            'player': player_number,
            'ball_position': recent[-1]['position'],
            'confidence': shot_confidence
        }
    
    def _detect_velocity_change(self, ball_history: List[Dict]) -> bool:
        """Detect significant velocity change (indicates shot)"""
        if len(ball_history) < 3:
            return False
        
        positions = [item['position'] for item in ball_history]
        
        # Calculate velocities
        velocities = []
        for i in range(1, len(positions)):
            vx = positions[i][0] - positions[i-1][0]
            vy = positions[i][1] - positions[i-1][1]
            speed = np.sqrt(vx**2 + vy**2)
            velocities.append(speed)
        
        if len(velocities) < 2:
            return False
        
        # Check for sudden speed change
        speed_change = abs(velocities[-1] - velocities[-2])
        
        return speed_change > 20  # Significant speed change
    
    def _detect_ball_near_player(self, ball_position: Dict, 
                                  players: List[Dict]) -> Optional[Dict]:
        """Check if ball is near any player"""
        ball_pos = ball_position['position']
        
        for player in players:
            player_pos = player['position']
            
            # Calculate distance
            distance = np.sqrt(
                (ball_pos[0] - player_pos[0])**2 + 
                (ball_pos[1] - player_pos[1])**2
            )
            
            # Ball within player's reach
            if distance < 150:  # 150 pixels ~ arm's reach
                return player
        
        return None
    
    def _detect_trajectory_inflection(self, ball_history: List[Dict]) -> bool:
        """Detect trajectory inflection point (shot location)"""
        if len(ball_history) < 3:
            return False
        
        positions = [item['position'] for item in ball_history]
        
        # Check y-direction change (vertical component)
        y_positions = [p[1] for p in positions]
        
        if len(y_positions) < 3:
            return False
        
        # Calculate second derivative (curvature)
        dy1 = y_positions[-2] - y_positions[-3]
        dy2 = y_positions[-1] - y_positions[-2]
        
        # Inflection = change in direction
        if dy1 * dy2 < 0:  # Sign change
            return True
        
        # Or significant curvature change
        if abs(dy2 - dy1) > 30:
            return True
        
        return False
    
    def _classify_shot_type(self, ball_history: List[Dict], 
                           hitting_player: Optional[Dict],
                           all_players: List[Dict]) -> str:
        """Classify the type of shot"""
        if not hitting_player:
            return 'groundstroke'
        
        ball_pos = ball_history[-1]['position']
        player_pos = hitting_player['position']
        
        # Check for SERVE (first shot in rally with distinctive characteristics)
        is_first_shot = self.rally_shot_count == 0
        if is_first_shot:
            has_ball_toss = self._detect_ball_toss(ball_history)
            at_baseline = self._is_at_baseline(player_pos, all_players)
            
            if has_ball_toss or at_baseline:
                return 'serve'
        
        # Height of ball relative to player
        ball_height = ball_pos[1]
        player_height = player_pos[1]
        
        height_diff = player_height - ball_height
        
        # Classify by ball height
        if height_diff < -100:  # Ball well above player
            return 'overhead'
        elif height_diff < -30:  # Ball above player
            return 'volley'
        elif height_diff > 100:  # Ball well below player
            return 'groundstroke'
        else:
            # Check horizontal position relative to player
            x_diff = ball_pos[0] - player_pos[0]
            
            if abs(x_diff) < 50:
                return 'forehand'  # Simplified - would need more analysis
            else:
                return 'backhand'  # Simplified
        
        return 'groundstroke'
    
    def _detect_ball_toss(self, ball_history: List[Dict]) -> bool:
        """Detect ball toss characteristic of a serve"""
        if len(ball_history) < 3:
            return False
        
        # Check for upward trajectory at start
        positions = [item['position'] for item in ball_history[-3:]]
        y_positions = [p[1] for p in positions]
        
        # Ball should be moving upward initially (y decreasing in image coords)
        # and have relatively high initial position
        if len(y_positions) >= 2:
            is_moving_up = y_positions[-1] < y_positions[-2]
            is_high = y_positions[-1] < 400  # High in frame
            
            return is_moving_up and is_high
        
        return False
    
    def _is_at_baseline(self, player_pos: Tuple[int, int], all_players: List[Dict]) -> bool:
        """Check if player is at baseline (deep court position)"""
        # Baseline players are typically at extremes of court vertically
        # This is a simplified check - could be improved with court calibration
        y_pos = player_pos[1]
        
        # Consider baseline if player is in deep court position
        # (top or bottom 30% of frame for typical broadcast angles)
        return y_pos < 200 or y_pos > 800  # Rough estimate
    
    def reset_rally(self):
        """Reset rally counter for new rally"""
        self.rally_shot_count = 0
    
    def classify_shot_outcome(self, shot_position: Tuple[int, int], 
                             court_bounds: Dict, 
                             next_ball_positions: List[Dict]) -> str:
        """
        Classify shot outcome: winner, error, or in_play
        
        Args:
            shot_position: Where ball was hit
            court_bounds: Court boundary information
            next_ball_positions: Ball positions after shot
        """
        if not next_ball_positions:
            return 'unknown'
        
        # Check if ball went out
        for pos in next_ball_positions[:10]:  # Check next 10 positions
            x, y = pos['position']
            
            # Check if outside court bounds
            if self._is_out_of_bounds(x, y, court_bounds):
                return 'unforced_error'
        
        # Check if rally continues (opponent hits back)
        if len(next_ball_positions) > 15:  # Ball still in play after some time
            return 'in_play'
        
        # If rally ends quickly and ball was in bounds
        return 'winner'
    
    def _is_out_of_bounds(self, x: int, y: int, court_bounds: Dict) -> bool:
        """Check if position is out of court bounds"""
        if not court_bounds or 'corners' not in court_bounds:
            return False
        
        corners = court_bounds['corners']
        if len(corners) != 4:
            return False
        
        # Simple bounding box check (can be improved with precise geometry)
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Add margin for errors
        margin = 50
        
        return (x < min_x - margin or x > max_x + margin or 
                y < min_y - margin or y > max_y + margin)
