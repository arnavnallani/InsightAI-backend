"""
Main video processing orchestrator - Enhanced for ANY tennis video
With Hybrid Ball Detection System + 7 Analytics Modules
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
from models import Match, Rally, Shot, CourtCalibration

# Import new detection modules
try:
    from detection.ball_detector_hybrid import HybridBallDetector
    from detection.ball_tracker import BallTracker
    from detection.shot_classifier import ShotClassifier
    HYBRID_DETECTION_AVAILABLE = True
except ImportError:
    HybridBallDetector = None
    BallTracker = None
    ShotClassifier = None
    HYBRID_DETECTION_AVAILABLE = False

# Import analytics modules
from analysis.shot_dna import ShotDNA
from analysis.counterfactual import CounterfactualAnalyzer
from analysis.momentum import MomentumAnalyzer
from analysis.shadow_ai import ShadowAI
from analysis.fatigue import FatigueAnalyzer
from analysis.decision_heatmap import DecisionHeatmap
from analysis.chaos import ChaosAnalyzer

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Processes tennis match videos with smart match detection and hybrid ball tracking"""
    
    def __init__(self, video_path: str, match: Match):
        self.video_path = video_path
        self.match = match
        self.cap = None
        self.fps = 30
        self.total_frames = 0
        self.transform_matrix = None
        self.match_start_frame = 0
        
        # Initialize hybrid detection system
        if HYBRID_DETECTION_AVAILABLE:
            self.hybrid_ball_detector = HybridBallDetector()
            self.ball_tracker = BallTracker(max_history=30)
            self.shot_classifier = ShotClassifier()
            logger.info("Initialized hybrid detection system (4 strategies)")
        else:
            self.hybrid_ball_detector = None
            self.ball_tracker = None
            self.shot_classifier = None
            logger.warning("Hybrid detection not available - using fallback methods")
        
    def open_video(self) -> bool:
        """Open video file with robust error handling"""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video: {self.video_path}")
                return False
            
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            if self.fps == 0 or self.fps is None:
                logger.warning("Could not detect FPS, using default 30")
                self.fps = 30
            
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if self.total_frames == 0:
                logger.warning("Could not detect total frames, will process until end")
                self.total_frames = 999999
            
            logger.info(f"Video opened: {self.total_frames} frames at {self.fps} fps")
            return True
            
        except Exception as e:
            logger.error(f"Error opening video: {str(e)}")
            return False
    
    def get_first_frame(self) -> Optional[np.ndarray]:
        """Get first usable frame for calibration"""
        if not self.cap:
            if not self.open_video():
                return None
        
        # Try to find a clear frame (skip black frames, intros, etc.)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        for attempt in range(100):  # Try first 100 frames
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Check if frame is not mostly black
            if np.mean(frame) > 20:  # Not a black frame
                # Check if frame has some green (tennis court)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
                green_percentage = np.sum(green_mask > 0) / (frame.shape[0] * frame.shape[1])
                
                if green_percentage > 0.1:  # At least 10% green (likely a court)
                    logger.info(f"Found good calibration frame at frame {attempt}")
                    return frame
        
        # If no good frame found, return first non-black frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def get_gameplay_frame(self) -> Optional[np.ndarray]:
        """
        Get FIRST BEST full court frame from the entire video
        Scans video until finding a high-quality full court view
        """
        if not self.cap:
            if not self.open_video():
                return None
        
        # Search ENTIRE video for the BEST full court frame
        # Don't stop early - find the absolute highest scoring frame
        best_frame = None
        best_score = 0
        best_frame_num = 0
        
        # Scan every 0.5 seconds through entire video (or max 10 minutes)
        max_search_time = min(self.total_frames, int(self.fps * 600))  # 10 minutes max
        
        for frame_num in range(0, max_search_time, int(self.fps / 2)):  # Check every 1 second from start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            
            if not ret:
                continue
            
            # Score this frame based on full court visibility
            score = self._score_full_court_frame(frame, frame_num/self.fps)
            
            # Log high-scoring frames for debugging
            if score > 80:
                logger.info(f"High score frame at {frame_num/self.fps:.1f}s: score={score:.1f}")
            
            # Update best frame strategy: 
            # Prefer frames that appear in the 2-5 second range (camera has settled)
            # Only replace if new frame is much better OR if we're in the optimal range
            timestamp = frame_num / self.fps
            in_optimal_range = 2.0 <= timestamp <= 5.0
            
            if best_frame is None:
                # First good frame - only accept if score > 200
                if score > 200:
                    best_score = score
                    best_frame = frame.copy()
                    best_frame_num = frame_num
                    logger.info(f"First good frame at {timestamp:.1f}s with score {score:.1f}")
            else:
                best_timestamp = best_frame_num / self.fps
                best_in_optimal = 2.0 <= best_timestamp <= 5.0
                
                # Replace if:
                # 1. New score much better (>10% improvement), OR
                # 2. Similar score but new frame is in optimal range and current isn't, OR
                # 3. Both in optimal range and new score >= current (prefer later)
                
                should_replace = False
                if score > best_score * 1.10:
                    should_replace = True  # Much better score
                    logger.info(f"Better frame at {timestamp:.1f}s: {score:.1f} vs {best_score:.1f}")
                elif in_optimal_range and not best_in_optimal and score >= best_score * 0.95:
                    should_replace = True  # Prefer optimal range
                    logger.info(f"Optimal range frame at {timestamp:.1f}s: {score:.1f}")
                elif in_optimal_range and best_in_optimal and score >= best_score:
                    should_replace = True  # Both optimal, prefer later
                    logger.info(f"Later optimal frame at {timestamp:.1f}s: {score:.1f}")
                
                if should_replace:
                    best_score = score
                    best_frame = frame.copy()
                    best_frame_num = frame_num
        
        # We found the first good frame or best frame within threshold
        
        if best_frame is not None and best_score > 20:
            # Update match_start_frame for the timestamp
            self.match_start_frame = best_frame_num
            return best_frame
        else:
            # Fallback: just get first frame with green court
            return self.get_first_frame()
    
    def _score_full_court_frame(self, frame: np.ndarray, debug_timestamp: float = 0.0) -> float:
        """
        Score frame to find ideal full court calibration view:
        - Both players visible (one near, one far)
        - Entire court with white lines visible
        - Net across middle
        - Wide camera angle
        Works for any court color (blue, green, orange, etc.)
        """
        height, width = frame.shape[:2]
        score = 0.0
        debug_info = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # FACTOR 1: WIDE CAMERA ANGLE (edges distributed, not concentrated in center)
        edge_center = edges[height//3:2*height//3, width//3:2*width//3]
        center_edges = np.sum(edge_center > 0)
        total_edges = np.sum(edges > 0)
        
        if total_edges > 100:
            center_ratio = center_edges / total_edges
            debug_info.append(f"center={center_ratio:.1%}")
            
            # IDEAL: <8% edges in center (very wide angle showing full court)
            if center_ratio < 0.08:
                score += 150.0
                debug_info.append("WIDE:+150")
            elif center_ratio < 0.12:
                score += 100.0
                debug_info.append("wide:+100")
            elif center_ratio < 0.20:
                score += 50.0
                debug_info.append("semi:+50")
            # Penalty for concentrated edges (close-ups)
            elif center_ratio > 0.40:
                score -= 100.0
                debug_info.append("CLOSEUP:-100")
        
        # FACTOR 2: BOTH COURT HALVES VISIBLE
        # Must detect TWO baselines (one near, one far) at the VERY edges of frame
        # STRICT: Baselines must be in the extreme top/bottom 15% of frame
        
        # Extreme bottom (bottom 15% - near baseline area)
        bottom_edge = edges[int(height*0.85):, :]
        # Extreme top (top 15% - far baseline area)  
        top_edge = edges[:int(height*0.15), :]
        # Middle area (net area)
        middle_section = edges[int(height*0.40):int(height*0.60), :]
        
        # Detect horizontal lines
        bottom_lines = cv2.HoughLinesP(bottom_edge, 1, np.pi/180, threshold=40, 
                                       minLineLength=width//2, maxLineGap=50)
        top_lines = cv2.HoughLinesP(top_edge, 1, np.pi/180, threshold=40,
                                    minLineLength=width//2, maxLineGap=50)
        middle_lines = cv2.HoughLinesP(middle_section, 1, np.pi/180, threshold=40,
                                       minLineLength=width//3, maxLineGap=40)
        
        has_near_baseline = False
        has_far_baseline = False
        has_net = False
        
        # Near baseline: VERY long horizontal line in bottom 15%
        if bottom_lines is not None:
            for line in bottom_lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                line_length = abs(x2 - x1)
                # Must be very horizontal and span >60% of width
                if (angle < 10 or angle > 170) and line_length > width * 0.6:
                    has_near_baseline = True
                    break
        
        # Far baseline: VERY long horizontal line in top 15%
        if top_lines is not None:
            for line in top_lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                line_length = abs(x2 - x1)
                # Must be very horizontal and span >60% of width
                if (angle < 10 or angle > 170) and line_length > width * 0.6:
                    has_far_baseline = True
                    break
        
        # Net: horizontal line in middle
        if middle_lines is not None:
            for line in middle_lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                if (angle < 15 or angle > 165) and abs(x2 - x1) > width * 0.4:
                    has_net = True
                    break
        
        # CRITICAL: Must have BOTH baselines at frame edges (full court view)
        if has_near_baseline and has_far_baseline:
            score += 200.0  # HUGE bonus for true full court
            debug_info.append("FULL_COURT:+200")
            
            if has_net:
                score += 50.0  # Extra bonus if net also visible
                debug_info.append("NET:+50")
        elif has_near_baseline or has_far_baseline:
            # Only one baseline = half court view = SEVERE PENALTY
            score -= 150.0
            debug_info.append("HALF_COURT:-150")
        else:
            # No baselines at edges = not a valid court view
            score -= 200.0
            debug_info.append("NO_BASELINES:-200")
        
        # FACTOR 3: COURT LINES (white lines visible across full width)
        _, white_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        white_percentage = np.sum(white_mask > 0) / (height * width)
        
        # Check white lines span horizontally
        white_left = np.sum(white_mask[:, :width//3] > 0)
        white_middle = np.sum(white_mask[:, width//3:2*width//3] > 0)
        white_right = np.sum(white_mask[:, 2*width//3:] > 0)
        
        # Court lines should span all three sections
        if white_left > 100 and white_middle > 100 and white_right > 100:
            score += 50.0
            debug_info.append("lines_span:+50")
            
            # Good white percentage for court lines (0.5-6%)
            if 0.005 <= white_percentage <= 0.06:
                score += 30.0
        elif 0.003 <= white_percentage <= 0.08:
            score += 15.0
        
        # FACTOR 4: Already handled in FACTOR 2 (net detection)
        
        # FACTOR 5: FULL WIDTH COURT LINES (baselines spanning frame)
        # Look for multiple long horizontal lines
        all_lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=60, 
                                    minLineLength=width//2, maxLineGap=30)
        
        long_horizontal_count = 0
        if all_lines is not None:
            for line in all_lines:
                x1, y1, x2, y2 = line[0]
                line_length = abs(x2 - x1)
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # Long horizontal lines (baselines, service lines)
                if (angle < 15 or angle > 165) and line_length > width * 0.5:
                    long_horizontal_count += 1
        
        debug_info.append(f"long_lines={long_horizontal_count}")
        if long_horizontal_count >= 4:
            score += 70.0
            debug_info.append("LINES:+70")
        elif long_horizontal_count >= 3:
            score += 50.0
            debug_info.append("lines:+50")
        elif long_horizontal_count >= 2:
            score += 30.0
            debug_info.append("lines:+30")
        
        # FACTOR 6: Good lighting
        mean_brightness = np.mean(gray)
        if 70 < mean_brightness < 170:
            score += 10.0
        
        # Debug output disabled for production
        # if debug_timestamp < 6 or (44 <= debug_timestamp <= 47):
        #     import sys
        #     print(f"🔍 {debug_timestamp:.1f}s: {score:.0f} | {' '.join(debug_info)}", file=sys.stderr, flush=True)
        
        return score
    
    def detect_match_start(self) -> int:
        """
        Automatically detect when actual match play starts
        Skips intros, replays, advertisements, commentary
        """
        logger.info("Detecting match start...")
        
        if not self.cap:
            if not self.open_video():
                return 0
        
        from .ball_detector import BallDetector
        ball_detector = BallDetector()
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        consecutive_detections = 0
        required_consecutive = int(self.fps * 5)  # 5 seconds of continuous ball detection
        frame_num = 0
        max_frames_to_check = int(self.fps * 300)  # Check first 5 minutes
        
        logger.info(f"Scanning first {max_frames_to_check / self.fps:.0f} seconds for match start...")
        
        while frame_num < max_frames_to_check:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_num += 1
            
            # Skip frames for speed
            if frame_num % 5 != 0:
                continue
            
            # Check if this looks like gameplay
            if self._is_gameplay_frame(frame, ball_detector):
                consecutive_detections += 1
                
                if consecutive_detections >= required_consecutive:
                    start_frame = max(0, frame_num - required_consecutive)
                    logger.info(f"Match start detected at frame {start_frame} ({start_frame/self.fps:.1f} seconds)")
                    self.match_start_frame = start_frame
                    return start_frame
            else:
                consecutive_detections = 0
        
        # If no match start detected, assume it starts at beginning
        logger.warning("Could not auto-detect match start, starting from beginning")
        self.match_start_frame = 0
        return 0
    
    def _is_gameplay_frame(self, frame: np.ndarray, ball_detector) -> bool:
        """
        Determine if a frame shows actual gameplay
        Checks for: tennis court visible, ball present, not a replay/intro
        """
        # Check 1: Is there a tennis court (green area)?
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        green_percentage = np.sum(green_mask > 0) / (frame.shape[0] * frame.shape[1])
        
        if green_percentage < 0.15:  # Less than 15% green - probably not court view
            return False
        
        # Check 2: Is there a ball?
        ball_pos = ball_detector.detect(frame)
        
        if ball_pos is None:
            return False
        
        # Check 3: Not a scoreboard/overlay (ball should be in middle area of frame)
        height, width = frame.shape[:2]
        ball_x, ball_y = ball_pos
        
        # Ball should be in main court area (not in scoreboard region)
        if ball_y < height * 0.1 or ball_y > height * 0.9:  # Too high or low
            return False
        
        if ball_x < width * 0.1 or ball_x > width * 0.9:  # Too far left or right
            return False
        
        return True
    
    def calibrate_court(self, corners: List[Tuple[int, int]]) -> bool:
        """
        Calibrate court from 4 corner points
        """
        if len(corners) != 4:
            logger.error("Need exactly 4 corners for calibration")
            return False
        
        try:
            # Source points (pixel coordinates)
            src_points = np.float32(corners)
            
            # Destination points (court coordinates in meters)
            dst_points = np.float32([
                [0, 0],  # Top-left
                [10.97, 0],  # Top-right
                [0, 23.77],  # Bottom-left
                [10.97, 23.77]  # Bottom-right
            ])
            
            # Calculate perspective transform matrix
            self.transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Store calibration
            self.match.calibration = CourtCalibration(
                top_left=corners[0],
                top_right=corners[1],
                bottom_left=corners[2],
                bottom_right=corners[3],
                transform_matrix=self.transform_matrix.tolist()
            )
            
            logger.info("Court calibration complete")
            return True
            
        except Exception as e:
            logger.error(f"Calibration failed: {str(e)}")
            return False
    
    def pixel_to_court(self, pixel_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert pixel coordinates to court coordinates"""
        if self.transform_matrix is None:
            return (0.0, 0.0)
        
        try:
            point = np.array([[[float(pixel_pos[0]), float(pixel_pos[1])]]], dtype=np.float32)
            court_pos = cv2.perspectiveTransform(point, self.transform_matrix)
            return (float(court_pos[0][0][0]), float(court_pos[0][0][1]))
        except:
            return (0.0, 0.0)
    
    def process_video(self, frame_skip: int = 3) -> bool:
        """
        Process entire video with smart match detection
        """
        if not self.cap:
            if not self.open_video():
                return False
        
        # Detect where match actually starts
        match_start = self.detect_match_start()
        
        # Start processing from match start
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, match_start)
        
        # Use hybrid detection if available, otherwise fallback to legacy
        if HYBRID_DETECTION_AVAILABLE and self.hybrid_ball_detector:
            logger.info("Using HYBRID ball detection (4 strategies)")
            use_hybrid = True
        else:
            from .ball_detector import BallDetector
            ball_detector = BallDetector()
            logger.info("Using legacy ball detection (fallback)")
            use_hybrid = False
        
        frame_number = match_start
        ball_positions = []
        shot_events = []
        last_detection_frame = match_start
        last_detection_timestamp = 0
        
        logger.info(f"Processing video from frame {match_start} with frame skip={frame_skip}")
        
        frames_processed = 0
        max_gap = int(self.fps * 30)  # 30 seconds without detection = probably end of match
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_number += 1
            frames_processed += 1
            
            # Skip frames for performance
            if frame_number % frame_skip != 0:
                continue
            
            # Stop if we haven't detected ball in 30 seconds (match probably ended)
            if frame_number - last_detection_frame > max_gap:
                logger.info(f"No ball detected for 30 seconds, assuming match ended at frame {frame_number}")
                break
            
            # Detect ball using hybrid or legacy detector
            if use_hybrid:
                # Use hybrid detection system
                detection_result = self.hybrid_ball_detector.detect(frame, frame_number)
                
                if detection_result:
                    ball_pixel = detection_result['position']
                    confidence = detection_result['confidence']
                    
                    # Update ball tracker with detection
                    tracked_ball = self.ball_tracker.update(ball_pixel, frame_number, confidence)
                    
                    if tracked_ball and tracked_ball['confidence'] > 0.5:
                        ball_pixel = tracked_ball['position']
                else:
                    # No detection, but tracker might predict position
                    tracked_ball = self.ball_tracker.update(None, frame_number, 0.0)
                    ball_pixel = tracked_ball['position'] if tracked_ball else None
                
                # Detect rally gaps and reset shot counter
                if self.shot_classifier and last_detection_timestamp > 0:
                    current_time = frame_number / self.fps
                    time_gap = current_time - last_detection_timestamp
                    
                    # Rally ended if there's a 4+ second gap
                    if time_gap > 4.0:
                        self.shot_classifier.reset_rally()
                        logger.debug(f"Rally gap detected ({time_gap:.1f}s), reset shot counter")
                
                # Try to detect shots using shot classifier
                if len(ball_positions) > 3 and self.shot_classifier:
                    # Convert ball_positions to format expected by shot classifier
                    ball_history = [
                        {'position': pos['pixel'], 'frame': pos['frame'], 'confidence': 1.0}
                        for pos in ball_positions[-10:]  # Last 10 positions
                    ]
                    
                    shot_event = self.shot_classifier.detect_shots(ball_history, [], frame_number)
                    if shot_event:
                        # Enrich shot event with court coordinates and timestamp
                        ball_pixel = shot_event['ball_position']
                        ball_court = self.pixel_to_court(ball_pixel)
                        timestamp = frame_number / self.fps
                        
                        shot_event['court'] = ball_court
                        shot_event['pixel'] = ball_pixel
                        shot_event['timestamp'] = timestamp
                        
                        shot_events.append(shot_event)
                        logger.debug(f"Shot detected at frame {frame_number}: {shot_event['shot_type']}")
            else:
                # Legacy detection
                ball_pixel = ball_detector.detect(frame)
            
            if ball_pixel:
                ball_court = self.pixel_to_court(ball_pixel)
                timestamp = frame_number / self.fps
                
                # Validate court position (filter out false positives)
                x, y = ball_court
                if -2 < x < 13 and -2 < y < 26:  # Reasonable court bounds with margin
                    ball_positions.append({
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'pixel': ball_pixel,
                        'court': ball_court
                    })
                    last_detection_frame = frame_number
                    last_detection_timestamp = timestamp
            
            # Progress logging
            if frames_processed % 300 == 0:
                elapsed = frames_processed / self.fps
                detections = len(ball_positions)
                detection_rate = (detections / (frames_processed / frame_skip)) * 100 if frames_processed > 0 else 0
                logger.info(f"Processed {elapsed:.0f}s of video, detected ball in {detections} frames ({detection_rate:.1f}% detection rate)")
                if use_hybrid:
                    logger.info(f"  - Detected {len(shot_events)} shot events via hybrid classifier")
        
        logger.info(f"Video processing complete. Detected ball in {len(ball_positions)} frames")
        
        if len(ball_positions) < 10:
            logger.warning("Very few ball detections - video may not contain tennis match")
            return False
        
        # Convert ball positions to shots and rallies
        # Pass shot_events from hybrid detection (if available)
        self._build_rallies_from_positions(ball_positions, shot_events if use_hybrid else None)
        
        self.cap.release()
        return True
    
    def _build_rallies_from_positions(self, ball_positions: List[dict], hybrid_shot_events: List[dict] = None):
        """Convert ball positions into structured rally/shot data"""
        if not ball_positions:
            return
        
        # Use hybrid shot events if available, otherwise detect from trajectories
        if hybrid_shot_events and len(hybrid_shot_events) > 0:
            logger.info(f"Using {len(hybrid_shot_events)} hybrid-detected shot events with shot types")
            shot_events = hybrid_shot_events
        else:
            logger.info("No hybrid shot events, detecting from ball trajectories")
            shot_events = self._detect_shot_events(ball_positions)
        
        if not shot_events:
            logger.warning("No shot events detected")
            return
        
        # Group shots into rallies
        from models import Set, Game
        
        # Initialize match structure
        if not self.match.sets:
            self.match.sets = [Set(set_number=1, games=[Game(game_number=1, set_number=1, server=1)])]
        
        current_rally = Rally(rally_number=1)
        rally_number = 1
        shot_in_rally = 0
        
        for i, event in enumerate(shot_events):
            # Get shot type from hybrid detection if available
            shot_type = event.get('shot_type', 'groundstroke')
            player = event.get('player', self._determine_player(event.get('court', (0, 0))))
            
            shot = Shot(
                frame_number=event.get('frame', 0),
                timestamp=event.get('timestamp', 0),
                ball_position=event.get('court', (0, 0)),
                ball_position_pixels=event.get('pixel', (0, 0)),
                shot_type=shot_type,  # From hybrid detection or default
                direction='unknown',
                depth='mid',
                player=player,
                outcome='in_play'
            )
            
            current_rally.shots.append(shot)
            shot_in_rally += 1
            
            # Detect end of rally (long pause or ball way out)
            is_last = (i == len(shot_events) - 1)
            next_gap = 0 if is_last else shot_events[i+1]['timestamp'] - event['timestamp']
            
            if next_gap > 4.0 or is_last:  # 4 second gap = new rally
                if shot_in_rally > 0:
                    current_rally.shot_count = len(current_rally.shots)
                    current_rally.duration = current_rally.shots[-1].timestamp - current_rally.shots[0].timestamp
                    
                    # Determine rally winner
                    current_rally.winner = self._determine_rally_winner(current_rally)
                    
                    # Add to match
                    self.match.sets[0].games[0].rallies.append(current_rally)
                    
                    # Reset shot classifier for new rally
                    if hasattr(self, 'shot_classifier') and self.shot_classifier:
                        self.shot_classifier.reset_rally()
                    
                    # Start new rally
                    rally_number += 1
                    current_rally = Rally(rally_number=rally_number)
                    shot_in_rally = 0
        
        logger.info(f"Built {rally_number} rallies from ball positions")
    
    def _detect_shot_events(self, ball_positions: List[dict]) -> List[dict]:
        """Detect when shots occurred based on ball trajectory changes"""
        if len(ball_positions) < 3:
            return ball_positions
        
        shot_events = []
        
        # Use velocity changes to detect shots
        for i in range(2, len(ball_positions)):
            prev = ball_positions[i-2]
            curr = ball_positions[i-1]
            next_pos = ball_positions[i]
            
            # Calculate velocities
            dt1 = curr['timestamp'] - prev['timestamp']
            dt2 = next_pos['timestamp'] - curr['timestamp']
            
            if dt1 == 0 or dt2 == 0:
                continue
            
            # Y-direction velocity
            vy1 = (curr['court'][1] - prev['court'][1]) / dt1
            vy2 = (next_pos['court'][1] - curr['court'][1]) / dt2
            
            # Shot detected if Y velocity reverses significantly
            if abs(vy1) > 0.5 and abs(vy2) > 0.5:  # Ball moving
                if vy1 * vy2 < 0:  # Direction reversed
                    shot_events.append(curr)
        
        # If very few shots detected, just sample every few ball positions
        if len(shot_events) < 5:
            logger.warning("Few shot events detected, using sampling method")
            shot_events = [ball_positions[i] for i in range(0, len(ball_positions), 10)]
        
        logger.info(f"Detected {len(shot_events)} shot events")
        return shot_events
    
    def _determine_player(self, court_pos: Tuple[float, float]) -> int:
        """Determine which player hit based on court position"""
        y = court_pos[1]
        # Player 1 (bottom) if y > 11.885 (half court)
        # Player 2 (top) if y < 11.885
        return 1 if y > 11.885 else 2
    
    def _determine_rally_winner(self, rally: Rally) -> int:
        """
        Determine who won the rally based on simple tennis logic:
        - If ball went out of bounds → last player made error → opponent wins
        - If ball stayed in bounds → last player hit winner → last player wins
        
        Returns: 1 or 2 (player number who won)
        """
        if not rally.shots:
            # No shots detected - shouldn't happen, but default to player 1
            return 1
        
        last_shot = rally.shots[-1]
        last_player = last_shot.player
        opponent = 2 if last_player == 1 else 1
        
        # Tennis court dimensions in court coordinates
        # Court is 23.77m long and 10.97m wide
        COURT_LENGTH = 23.77
        COURT_WIDTH = 10.97
        
        x, y = last_shot.ball_position
        
        # Check if ball went out of bounds (error by last player)
        out_margin = 1.5  # Generous margin for detection noise
        is_out = (
            x < -out_margin or 
            x > COURT_WIDTH + out_margin or
            y < -out_margin or 
            y > COURT_LENGTH + out_margin
        )
        
        if is_out:
            # Last player hit the ball out → opponent wins
            rally.point_type = 'unforced_error'
            last_shot.outcome = 'error'
            return opponent
        
        # Ball stayed in bounds → last player hit a winner
        # (Rally ended because opponent couldn't/didn't return it)
        rally.point_type = 'winner'
        last_shot.outcome = 'winner'
        return last_player
    
    def run_analytics(self) -> Dict:
        """
        Run all 7 analytics modules and transform to match frontend schema
        Returns: Dictionary matching CompleteAnalysisData TypeScript interface
        """
        logger.info("Running all 7 analytics modules...")
        
        try:
            # Initialize analytics modules
            shot_dna = ShotDNA(self.match)
            counterfactual = CounterfactualAnalyzer(self.match)
            momentum = MomentumAnalyzer(self.match)
            shadow_ai = ShadowAI(self.match)
            fatigue = FatigueAnalyzer(self.match)
            decision_heatmap = DecisionHeatmap(self.match)
            chaos = ChaosAnalyzer(self.match)
            
            # Run each analysis
            logger.info("  1/7 Shot DNA...")
            shot_dna_raw = shot_dna.analyze()
            
            logger.info("  2/7 Counterfactual Analysis...")
            counterfactual_raw = counterfactual.analyze()
            
            logger.info("  3/7 Momentum Topology...")
            momentum_raw = momentum.analyze()
            
            logger.info("  4/7 Shadow AI...")
            shadow_ai_raw = shadow_ai.analyze()
            
            logger.info("  5/7 Fatigue Fingerprint...")
            fatigue_raw = fatigue.analyze()
            
            logger.info("  6/7 Decision Heatmap...")
            decision_heatmap_raw = decision_heatmap.analyze()
            
            logger.info("  7/7 Chaos Theory...")
            chaos_raw = chaos.analyze()
            
            # Transform results to match TypeScript interface
            logger.info("Transforming analytics to frontend format...")
            
            # Detect match start (first serve) to skip warmup
            all_rallies = self.match.get_all_rallies()
            match_start_idx = 0
            
            for idx, rally in enumerate(all_rallies):
                if rally.shots and rally.shots[0].shot_type == 'serve':
                    match_start_idx = idx
                    logger.info(f"Match start detected at rally {idx+1} (first serve)")
                    break
            
            # Use only rallies from match start onwards
            match_rallies = all_rallies[match_start_idx:]
            total_rallies = len(match_rallies)
            
            # Calculate total shots
            total_shots = sum(len(rally.shots) for rally in match_rallies)
            
            # Calculate scores
            p1_points = sum(1 for r in match_rallies if r.winner == 1)
            p2_points = sum(1 for r in match_rallies if r.winner == 2)
            
            # Calculate duration
            if match_rallies and match_rallies[0].shots and match_rallies[-1].shots:
                duration = match_rallies[-1].shots[-1].timestamp - match_rallies[0].shots[0].timestamp
            else:
                duration = 0
            
            logger.info(f"Match summary: {total_rallies} rallies, {total_shots} shots (skipped {match_start_idx} warmup rallies)")
            
            # Format results with camelCase conversion
            analytics_data = {
                'shotDNA': self._to_camel_case(shot_dna_raw),
                'counterfactual': self._to_camel_case(counterfactual_raw),
                'momentum': self._to_camel_case(momentum_raw),
                'shadowSelf': self._to_camel_case(shadow_ai_raw),
                'fatigue': self._to_camel_case(fatigue_raw),
                'decisionHeatmap': self._to_camel_case(decision_heatmap_raw),
                'chaosTheory': self._to_camel_case(chaos_raw),
                'matchSummary': {
                    'duration': round(duration, 1),
                    'totalPoints': total_rallies,
                    'totalRallies': total_rallies,  # Alias for compatibility
                    'totalShots': total_shots,
                    'yourScore': str(p1_points),
                    'opponentScore': str(p2_points),
                    'finalScore': f"{p1_points}-{p2_points}",
                    'totalSets': 1,  # Single set for now
                    'playerName': 'You',
                    'opponentName': 'Opponent'
                }
            }
            
            logger.info("All analytics complete!")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error running analytics: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _to_camel_case(self, data: any) -> any:
        """
        Recursively convert all snake_case keys to camelCase
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Convert snake_case to camelCase
                camel_key = self._snake_to_camel(key)
                result[camel_key] = self._to_camel_case(value)
            return result
        elif isinstance(data, list):
            return [self._to_camel_case(item) for item in data]
        else:
            return data
    
    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case string to camelCase"""
        components = snake_str.split('_')
        # First component stays lowercase, rest are title-cased
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def detect_balls(self):
        """
        Legacy compatibility method for old async processing flow
        Calls the new process_video() method internally
        """
        logger.info("detect_balls() called (legacy compatibility mode)")
        return self.process_video(frame_skip=3)


def extract_gameplay_frame(video_path: str) -> dict:
    """
    Standalone function to extract first gameplay frame from video
    Returns frame as base64-encoded image
    """
    import base64
    
    try:
        # Create a minimal Match object (not used for frame extraction)
        from models import Match
        from datetime import datetime
        match = Match(match_id="temp", video_path=video_path, upload_date=datetime.now())
        
        # Create processor
        processor = VideoProcessor(video_path, match)
        
        # Get gameplay frame
        frame = processor.get_gameplay_frame()
        
        if frame is None:
            return {
                "success": False,
                "error": "Could not extract gameplay frame from video"
            }
        
        # Encode frame as JPEG then base64
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Get frame position info
        frame_num = processor.match_start_frame
        timestamp = frame_num / processor.fps if processor.fps > 0 else 0
        
        # DEBUG: Check score at 45 seconds to compare
        debug_info = {}
        if processor.cap:
            frame_45s = int(processor.fps * 45)
            processor.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_45s)
            ret, test_frame = processor.cap.read()
            if ret:
                score_45s = processor._score_full_court_frame(test_frame)
                debug_info["score_at_45s"] = round(score_45s, 1)
                debug_info["selected_score"] = round(processor._score_full_court_frame(frame), 1)
        
        return {
            "success": True,
            "frame": frame_base64,
            "timestamp": round(timestamp, 2),
            "width": frame.shape[1],
            "height": frame.shape[0],
            "match_detected": frame_num > 0,
            "debug": debug_info
        }
        
    except Exception as e:
        logger.error(f"Error extracting gameplay frame: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
