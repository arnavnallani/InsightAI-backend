"""
Hybrid Ball Detection System
Combines 4 strategies for robust ball detection across various conditions
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

class HybridBallDetector:
    """
    Multi-strategy ball detector that combines:
    1. Color detection (fast, works for clear balls)
    2. Motion detection (works for fast balls regardless of color)
    3. Background subtraction (works for any moving object)
    4. Template matching (works for various ball appearances)
    """
    
    def __init__(self):
        # Color detection parameters
        self.color_ranges = [
            # Yellow-green tennis ball
            (np.array([20, 100, 100]), np.array([40, 255, 255])),
            # White (motion blur or bright lighting)
            (np.array([0, 0, 200]), np.array([180, 30, 255])),
            # Gray (shadows)
            (np.array([0, 0, 80]), np.array([180, 50, 200])),
        ]
        
        # Motion detection
        self.previous_frame = None
        
        # Background subtraction
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        self.bg_initialized = False
        self.bg_init_frames = 0
        
        # Template matching
        self.ball_templates = self._create_ball_templates()
        
        # Size constraints
        self.min_area = 10
        self.max_area = 3000
        self.min_circularity = 0.4
        
        logger.info("Hybrid ball detector initialized")
    
    def detect(self, frame: np.ndarray, frame_number: int = 0) -> Optional[Dict]:
        """
        Detect ball using hybrid approach
        
        Returns: {
            'position': (x, y),
            'confidence': float (0-1),
            'method': str (which strategy worked),
            'all_candidates': list of all detections from each method
        }
        """
        all_candidates = []
        
        # Strategy 1: Color Detection (fastest, try first)
        color_result = self._detect_by_color(frame)
        if color_result:
            all_candidates.append({
                'method': 'color',
                'position': color_result['position'],
                'confidence': color_result['confidence']
            })
            
            # If very confident, return immediately
            if color_result['confidence'] > 0.8:
                return {
                    'position': color_result['position'],
                    'confidence': color_result['confidence'],
                    'method': 'color',
                    'all_candidates': all_candidates
                }
        
        # Strategy 2: Motion Detection
        if self.previous_frame is not None:
            motion_result = self._detect_by_motion(frame, self.previous_frame)
            if motion_result:
                all_candidates.append({
                    'method': 'motion',
                    'position': motion_result['position'],
                    'confidence': motion_result['confidence']
                })
                
                # If very confident, return immediately
                if motion_result['confidence'] > 0.8:
                    self.previous_frame = frame.copy()
                    return {
                        'position': motion_result['position'],
                        'confidence': motion_result['confidence'],
                        'method': 'motion',
                        'all_candidates': all_candidates
                    }
        
        # Strategy 3: Background Subtraction
        if self.bg_initialized:
            bg_result = self._detect_by_background(frame)
            if bg_result:
                all_candidates.append({
                    'method': 'background',
                    'position': bg_result['position'],
                    'confidence': bg_result['confidence']
                })
        else:
            # Initialize background model
            self.bg_subtractor.apply(frame)
            self.bg_init_frames += 1
            if self.bg_init_frames > 30:  # Need 30 frames to build model
                self.bg_initialized = True
                logger.info("Background model initialized")
        
        # Strategy 4: Template Matching (slowest, only if others failed)
        if not all_candidates or max(c['confidence'] for c in all_candidates) < 0.6:
            template_result = self._detect_by_template(frame)
            if template_result:
                all_candidates.append({
                    'method': 'template',
                    'position': template_result['position'],
                    'confidence': template_result['confidence']
                })
        
        # Store frame for next motion detection
        self.previous_frame = frame.copy()
        
        # Combine all results
        if not all_candidates:
            return None
        
        final_result = self._combine_results(all_candidates)
        return final_result
    
    def _detect_by_color(self, frame: np.ndarray) -> Optional[Dict]:
        """Detect ball by color (yellow, white, or gray)"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Try each color range
            all_contours = []
            
            for lower, upper in self.color_ranges:
                mask = cv2.inRange(hsv, lower, upper)
                
                # Clean up mask
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                all_contours.extend(contours)
            
            if not all_contours:
                return None
            
            # Find best candidate
            best_candidate = None
            best_score = 0
            
            height, width = frame.shape[:2]
            center_x, center_y = width / 2, height / 2
            
            for contour in all_contours:
                area = cv2.contourArea(contour)
                
                if area < self.min_area or area > self.max_area:
                    continue
                
                # Check circularity
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                if circularity < self.min_circularity:
                    continue
                
                # Get center
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Score based on circularity and position
                # Prefer objects near center of frame
                dist_from_center = np.sqrt((cx - center_x)**2 + (cy - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                center_bonus = 1.0 - (dist_from_center / max_dist) * 0.3
                
                score = circularity * center_bonus * min(area / 500, 1.0)
                
                if score > best_score:
                    best_score = score
                    best_candidate = (cx, cy)
            
            if best_candidate:
                return {
                    'position': best_candidate,
                    'confidence': min(best_score, 0.9)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Color detection error: {str(e)}")
            return None
    
    def _detect_by_motion(self, current_frame: np.ndarray, 
                         previous_frame: np.ndarray) -> Optional[Dict]:
        """Detect ball by motion between frames"""
        try:
            # Convert to grayscale
            gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            gray_previous = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            frame_diff = cv2.absdiff(gray_current, gray_previous)
            
            # Threshold
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            
            # Clean up
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.dilate(thresh, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find best candidate (small, fast-moving object)
            best_candidate = None
            best_score = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Ball should be small to medium size
                if area < self.min_area or area > self.max_area:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate aspect ratio (ball should be roughly circular)
                aspect_ratio = float(w) / h if h > 0 else 0
                if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                    continue
                
                # Score based on size (prefer smaller objects) and intensity
                intensity = np.mean(frame_diff[y:y+h, x:x+w])
                size_score = 1.0 - min(area / self.max_area, 1.0)
                motion_score = min(intensity / 100, 1.0)
                
                score = size_score * 0.4 + motion_score * 0.6
                
                if score > best_score:
                    best_score = score
                    cx = x + w // 2
                    cy = y + h // 2
                    best_candidate = (cx, cy)
            
            if best_candidate:
                return {
                    'position': best_candidate,
                    'confidence': min(best_score * 1.2, 0.95)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Motion detection error: {str(e)}")
            return None
    
    def _detect_by_background(self, frame: np.ndarray) -> Optional[Dict]:
        """Detect ball using background subtraction"""
        try:
            # Apply background subtractor
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Clean up mask
            kernel = np.ones((3, 3), np.uint8)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find best candidate (small foreground object)
            best_candidate = None
            best_score = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if area < self.min_area or area > self.max_area:
                    continue
                
                # Get center
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Check circularity
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # Score based on size and circularity
                size_score = 1.0 - min(area / self.max_area, 1.0)
                score = size_score * 0.5 + circularity * 0.5
                
                if score > best_score:
                    best_score = score
                    best_candidate = (cx, cy)
            
            if best_candidate:
                return {
                    'position': best_candidate,
                    'confidence': min(best_score * 1.1, 0.9)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Background detection error: {str(e)}")
            return None
    
    def _detect_by_template(self, frame: np.ndarray) -> Optional[Dict]:
        """Detect ball using template matching"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            best_match = None
            best_score = 0
            
            for template in self.ball_templates:
                # Try multiple scales
                for scale in [0.5, 0.75, 1.0, 1.25, 1.5]:
                    # Resize template
                    template_h, template_w = template.shape
                    new_h, new_w = int(template_h * scale), int(template_w * scale)
                    
                    if new_h > gray.shape[0] or new_w > gray.shape[1]:
                        continue
                    
                    resized_template = cv2.resize(template, (new_w, new_h))
                    
                    # Template matching
                    result = cv2.matchTemplate(gray, resized_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_score:
                        best_score = max_val
                        # Center of match
                        cx = max_loc[0] + new_w // 2
                        cy = max_loc[1] + new_h // 2
                        best_match = (cx, cy)
            
            if best_match and best_score > 0.5:
                return {
                    'position': best_match,
                    'confidence': min(best_score, 0.95)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Template detection error: {str(e)}")
            return None
    
    def _create_ball_templates(self) -> List[np.ndarray]:
        """Create synthetic tennis ball templates"""
        templates = []
        
        # Template 1: Clear yellow ball
        template1 = np.zeros((30, 30), dtype=np.uint8)
        cv2.circle(template1, (15, 15), 12, 200, -1)
        templates.append(template1)
        
        # Template 2: White/bright ball
        template2 = np.zeros((30, 30), dtype=np.uint8)
        cv2.circle(template2, (15, 15), 12, 255, -1)
        templates.append(template2)
        
        # Template 3: Motion blurred ball (horizontal)
        template3 = np.zeros((30, 40), dtype=np.uint8)
        cv2.ellipse(template3, (20, 15), (18, 10), 0, 0, 360, 200, -1)
        templates.append(template3)
        
        # Template 4: Motion blurred ball (vertical)
        template4 = np.zeros((40, 30), dtype=np.uint8)
        cv2.ellipse(template4, (15, 20), (10, 18), 0, 0, 360, 200, -1)
        templates.append(template4)
        
        # Template 5: Small distant ball
        template5 = np.zeros((20, 20), dtype=np.uint8)
        cv2.circle(template5, (10, 10), 7, 200, -1)
        templates.append(template5)
        
        return templates
    
    def _combine_results(self, candidates: List[Dict]) -> Dict:
        """Combine results from multiple detection methods"""
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return {
                'position': candidates[0]['position'],
                'confidence': candidates[0]['confidence'],
                'method': candidates[0]['method'],
                'all_candidates': candidates
            }
        
        # Weight by confidence
        total_weight = sum(c['confidence'] for c in candidates)
        
        if total_weight == 0:
            return None
        
        # Weighted average position
        weighted_x = sum(c['position'][0] * c['confidence'] for c in candidates) / total_weight
        weighted_y = sum(c['position'][1] * c['confidence'] for c in candidates) / total_weight
        
        # Average confidence (boost if multiple methods agree)
        avg_confidence = total_weight / len(candidates)
        
        # Check if methods agree (positions close together)
        positions = [c['position'] for c in candidates]
        max_distance = max(
            np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            for i, p1 in enumerate(positions)
            for p2 in positions[i+1:]
        ) if len(positions) > 1 else 0
        
        # If methods agree closely, boost confidence
        if max_distance < 30:  # Within 30 pixels
            agreement_bonus = 0.2
        elif max_distance < 60:  # Within 60 pixels
            agreement_bonus = 0.1
        else:
            agreement_bonus = 0
        
        final_confidence = min(avg_confidence + agreement_bonus, 0.98)
        
        # Determine primary method (highest confidence)
        primary_method = max(candidates, key=lambda c: c['confidence'])['method']
        
        return {
            'position': (int(weighted_x), int(weighted_y)),
            'confidence': final_confidence,
            'method': f"{primary_method}+combined",
            'all_candidates': candidates,
            'agreement': max_distance < 50
        }
    
    def reset(self):
        """Reset detector state"""
        self.previous_frame = None
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        self.bg_initialized = False
        self.bg_init_frames = 0
        logger.info("Hybrid ball detector reset")
