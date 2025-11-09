"""
Advanced detection modules for tennis analysis
"""

from .ball_detector_hybrid import HybridBallDetector
from .ball_tracker import BallTracker
from .shot_classifier import ShotClassifier

# Note: CourtDetector and PlayerDetector require ML models (YOLOv8)
# They are optional and can be added later
CourtDetector = None
PlayerDetector = None
ADVANCED_DETECTION_AVAILABLE = False

__all__ = [
    'HybridBallDetector',
    'BallTracker',
    'ShotClassifier',
    'ADVANCED_DETECTION_AVAILABLE'
]
