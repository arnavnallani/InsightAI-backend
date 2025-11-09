"""
Configuration settings for CourtIQ
"""

import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Upload settings
    UPLOAD_FOLDER = 'python_backend/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max file size
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv'}
    
    # Processing settings
    FRAME_SKIP = 3  # Process every 3rd frame (faster, good enough)
    BALL_DETECTION_CONFIDENCE = 0.3
    MAX_PROCESSING_TIME = 1800  # 30 minutes max
    
    # Match detection settings
    MIN_CONTINUOUS_GAMEPLAY = 10  # Seconds of continuous ball detection to confirm match started
    INTRO_SKIP_MAX = 300  # Skip first 5 minutes max looking for match start
    
    # Court dimensions (in meters)
    COURT_LENGTH = 23.77
    COURT_WIDTH = 10.97
    
    # Analysis settings
    MOMENTUM_WINDOW = 5
    FATIGUE_SEGMENT_MINUTES = 10
    PATTERN_MIN_OCCURRENCES = 3
    
    # Match scoring defaults
    DEFAULT_SCORING = {
        'set_format': 'best_of_3',
        'games_per_set': 6,
        'tiebreak_at': 6,
        'tiebreak_points': 7,
        'deciding_set_format': 'match_tiebreak',
        'match_tiebreak_points': 10,
        'use_ads': True,
        'use_no_ad': False
    }

    @staticmethod
    def init_app(app):
        """Initialize application"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
