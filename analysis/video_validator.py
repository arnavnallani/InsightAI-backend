"""
Video validation and quality checking
"""

import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class VideoValidator:
    """Validates uploaded videos for tennis match analysis"""
    
    @staticmethod
    def validate_video(video_path: str) -> dict:
        """
        Validate video file and check if it's suitable for analysis
        Returns: dict with 'valid' bool and 'issues' list
        """
        issues = []
        warnings = []
        
        # Check 1: File exists
        if not os.path.exists(video_path):
            return {
                'valid': False,
                'issues': ['Video file not found'],
                'warnings': []
            }
        
        # Check 2: File size
        file_size = os.path.getsize(video_path)
        if file_size < 1024 * 1024:  # Less than 1MB
            issues.append('Video file is too small (less than 1MB)')
        elif file_size > 5 * 1024 * 1024 * 1024:  # More than 5GB
            issues.append('Video file is too large (over 5GB)')
        
        # Check 3: Can open video
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                issues.append('Cannot open video file - format may not be supported')
                return {
                    'valid': False,
                    'issues': issues,
                    'warnings': warnings
                }
            
            # Check 4: Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if fps == 0 or fps is None:
                warnings.append('Could not detect frame rate')
            elif fps < 15:
                warnings.append(f'Low frame rate ({fps:.1f} fps) - results may be less accurate')
            
            if frame_count == 0:
                warnings.append('Could not detect video length')
            elif frame_count < 300:  # Less than 10 seconds at 30fps
                warnings.append('Video is very short - may not contain enough match data')
            
            if width < 640 or height < 480:
                warnings.append(f'Low resolution ({width}x{height}) - results may be less accurate')
            
            # Check 5: Sample frames
            ret, frame = cap.read()
            if not ret or frame is None:
                issues.append('Cannot read video frames')
                cap.release()
                return {
                    'valid': False,
                    'issues': issues,
                    'warnings': warnings
                }
            
            # Check 6: Look for green (tennis court)
            has_green = VideoValidator._check_for_tennis_court(frame)
            if not has_green:
                warnings.append('No tennis court detected in first frame - make sure video shows tennis match')
            
            cap.release()
            
            # Determine if valid
            valid = len(issues) == 0
            
            return {
                'valid': valid,
                'issues': issues,
                'warnings': warnings,
                'properties': {
                    'fps': fps,
                    'frame_count': frame_count,
                    'width': width,
                    'height': height,
                    'duration_seconds': frame_count / fps if fps > 0 else 0,
                    'file_size_mb': file_size / (1024 * 1024)
                }
            }
            
        except Exception as e:
            logger.error(f"Video validation error: {str(e)}")
            return {
                'valid': False,
                'issues': [f'Error validating video: {str(e)}'],
                'warnings': []
            }
    
    @staticmethod
    def _check_for_tennis_court(frame: np.ndarray) -> bool:
        """Check if frame contains a tennis court (green area)"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Look for green
            green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
            green_percentage = np.sum(green_mask > 0) / (frame.shape[0] * frame.shape[1])
            
            # At least 10% green suggests tennis court
            return green_percentage > 0.10
            
        except:
            return False
