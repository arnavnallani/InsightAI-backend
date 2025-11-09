"""
Advanced ball tracking with temporal consistency
Combines detection with tracking for robust ball following
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
from collections import deque
import logging

logger = logging.getLogger(__name__)

class BallTracker:
    """Track ball across frames with temporal consistency"""
    
    def __init__(self, max_history: int = 30):
        self.max_history = max_history
        self.ball_history = deque(maxlen=max_history)
        self.lost_frames = 0
        self.max_lost_frames = 15  # Max frames to track without detection
        
        # Kalman filter for prediction (simplified)
        self.predicted_position = None
        self.predicted_velocity = None
    
    def update(self, detected_position: Optional[Tuple[int, int]], 
               frame_number: int, confidence: float = 1.0) -> Optional[Dict]:
        """
        Update tracker with new detection
        Returns: {
            'position': (x, y),
            'confidence': float,
            'tracked': bool,  # True if using tracking, False if pure detection
            'velocity': (vx, vy)
        }
        """
        if detected_position is not None:
            # Good detection
            self.ball_history.append({
                'position': detected_position,
                'frame': frame_number,
                'confidence': confidence,
                'tracked': False
            })
            self.lost_frames = 0
            
            # Update prediction
            self._update_prediction()
            
            return {
                'position': detected_position,
                'confidence': confidence,
                'tracked': False,
                'velocity': self.predicted_velocity or (0, 0)
            }
        
        else:
            # No detection - try to track
            self.lost_frames += 1
            
            if self.lost_frames > self.max_lost_frames:
                # Lost track
                return None
            
            # Predict position based on history
            predicted = self._predict_position()
            
            if predicted:
                self.ball_history.append({
                    'position': predicted,
                    'frame': frame_number,
                    'confidence': max(0.1, 1.0 - self.lost_frames * 0.1),
                    'tracked': True
                })
                
                return {
                    'position': predicted,
                    'confidence': max(0.1, 1.0 - self.lost_frames * 0.1),
                    'tracked': True,
                    'velocity': self.predicted_velocity or (0, 0)
                }
            
            return None
    
    def _update_prediction(self):
        """Update velocity prediction from history"""
        if len(self.ball_history) < 2:
            return
        
        recent = list(self.ball_history)[-5:]  # Last 5 positions
        
        if len(recent) < 2:
            return
        
        # Calculate average velocity
        velocities = []
        for i in range(1, len(recent)):
            prev = recent[i-1]
            curr = recent[i]
            
            dt = curr['frame'] - prev['frame']
            if dt == 0:
                continue
            
            vx = (curr['position'][0] - prev['position'][0]) / dt
            vy = (curr['position'][1] - prev['position'][1]) / dt
            
            velocities.append((vx, vy))
        
        if velocities:
            # Average velocity
            avg_vx = np.mean([v[0] for v in velocities])
            avg_vy = np.mean([v[1] for v in velocities])
            self.predicted_velocity = (avg_vx, avg_vy)
            
            # Predicted next position
            last_pos = recent[-1]['position']
            self.predicted_position = (
                int(last_pos[0] + avg_vx),
                int(last_pos[1] + avg_vy)
            )
    
    def _predict_position(self) -> Optional[Tuple[int, int]]:
        """Predict ball position when no detection"""
        if not self.ball_history or not self.predicted_position:
            return None
        
        # Use linear prediction
        if self.predicted_velocity:
            last = self.ball_history[-1]
            dt = self.lost_frames
            
            pred_x = int(last['position'][0] + self.predicted_velocity[0] * dt)
            pred_y = int(last['position'][1] + self.predicted_velocity[1] * dt)
            
            return (pred_x, pred_y)
        
        return self.predicted_position
    
    def get_smooth_trajectory(self, window: int = 5) -> List[Tuple[int, int]]:
        """Get smoothed ball trajectory"""
        if len(self.ball_history) < window:
            return [item['position'] for item in self.ball_history]
        
        positions = [item['position'] for item in self.ball_history]
        smoothed = []
        
        for i in range(len(positions)):
            start = max(0, i - window // 2)
            end = min(len(positions), i + window // 2 + 1)
            
            window_positions = positions[start:end]
            avg_x = int(np.mean([p[0] for p in window_positions]))
            avg_y = int(np.mean([p[1] for p in window_positions]))
            
            smoothed.append((avg_x, avg_y))
        
        return smoothed
    
    def detect_bounce(self) -> bool:
        """Detect if ball just bounced (y-velocity reversal)"""
        if len(self.ball_history) < 3:
            return False
        
        recent = list(self.ball_history)[-3:]
        
        # Calculate y-velocities
        vy1 = recent[1]['position'][1] - recent[0]['position'][1]
        vy2 = recent[2]['position'][1] - recent[1]['position'][1]
        
        # Bounce = y-velocity reverses (going down -> going up)
        if vy1 > 5 and vy2 < -5:
            return True
        
        return False
    
    def is_tracking_reliable(self) -> bool:
        """Check if current tracking is reliable"""
        if not self.ball_history:
            return False
        
        recent_confidence = np.mean([item['confidence'] for item in list(self.ball_history)[-5:]])
        return recent_confidence > 0.6 and self.lost_frames < 5
    
    def reset(self):
        """Reset tracker"""
        self.ball_history.clear()
        self.lost_frames = 0
        self.predicted_position = None
        self.predicted_velocity = None
