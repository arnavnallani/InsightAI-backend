"""
Tennis ball detection with improved robustness
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class BallDetector:
    """Detects tennis balls in video frames - enhanced for any video quality"""
    
    def __init__(self):
        # Multiple color ranges for different lighting conditions
        self.color_ranges = [
            # Standard yellow-green tennis ball
            (np.array([20, 100, 100]), np.array([40, 255, 255])),
            # Brighter tennis ball (sunny conditions)
            (np.array([15, 80, 150]), np.array([45, 255, 255])),
            # Darker tennis ball (shadows)
            (np.array([20, 60, 60]), np.array([40, 200, 200])),
        ]
        
        self.min_area = 15  # Smaller minimum for distant shots
        self.max_area = 8000  # Larger maximum for close-ups
        self.circularity_threshold = 0.5  # More lenient
        
    def detect(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect tennis ball with multiple strategies
        """
        # Strategy 1: Color-based detection (try multiple color ranges)
        for lower, upper in self.color_ranges:
            ball = self._detect_by_color(frame, lower, upper)
            if ball:
                return ball
        
        # Strategy 2: Look for any fast-moving small circular object
        ball = self._detect_by_motion(frame)
        if ball:
            return ball
        
        return None
    
    def _detect_by_color(self, frame: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> Optional[Tuple[int, int]]:
        """Detect ball by color range"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask
            mask = cv2.inRange(hsv, lower, upper)
            
            # Reduce noise
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find best candidate
            best_ball = None
            best_score = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if area < self.min_area or area > self.max_area:
                    continue
                
                # Check circularity
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                if circularity < self.circularity_threshold:
                    continue
                
                # Score based on circularity and reasonable size
                score = circularity * min(area / 100, 1.0)
                
                # Bonus for being in center area of frame
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Bonus for center position
                    height, width = frame.shape[:2]
                    center_x, center_y = width / 2, height / 2
                    dist_from_center = np.sqrt((cx - center_x)**2 + (cy - center_y)**2)
                    max_dist = np.sqrt(center_x**2 + center_y**2)
                    center_bonus = 1.0 - (dist_from_center / max_dist) * 0.5
                    score *= center_bonus
                    
                    if score > best_score:
                        best_score = score
                        best_ball = (cx, cy)
            
            return best_ball
            
        except Exception as e:
            logger.debug(f"Color detection error: {str(e)}")
            return None
    
    def _detect_by_motion(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect ball by finding small circular fast-moving objects
        (Simplified version - full implementation would track between frames)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Find circles using Hough transform
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=15,
            minRadius=3,
            maxRadius=40
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            # Return first circle found (most prominent)
            if len(circles[0]) > 0:
                x, y, r = circles[0][0]
                return (int(x), int(y))
        
        return None
    
    def detect_with_tracking(self, frame: np.ndarray, previous_position: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        Detect ball with tracking continuity
        Uses previous position to prefer nearby detections
        """
        ball_pos = self.detect(frame)
        
        if ball_pos is None or previous_position is None:
            return ball_pos
        
        # If ball is too far from previous position, might be false positive
        distance = np.sqrt((ball_pos[0] - previous_position[0])**2 + 
                          (ball_pos[1] - previous_position[1])**2)
        
        # Threshold: ball shouldn't move more than 200 pixels between frames
        if distance > 200:
            logger.debug(f"Ball detection too far from previous position: {distance} pixels")
            return None
        
        return ball_pos
