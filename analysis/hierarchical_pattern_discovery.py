"""
Hierarchical Pattern Discovery Engine
Discovers ALL tennis patterns automatically through feature mining
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pattern_utils import (
    Rally, Shot,
    calculate_win_rate,
    meets_minimum_sample_size
)

@dataclass
class PatternFeatures:
    """Features that define a tennis pattern"""
    shot_type: str = None  # Serve, Forehand, Backhand, Volley
    direction: str = None  # DTL, Crosscourt, Middle
    depth: str = None      # Short, Mid, Deep
    speed_category: str = None  # Slow, Medium, Fast
    context: str = None    # Pressure, Normal, Serving, Receiving
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def __str__(self):
        # Note: depth excluded from string representation per user request
        # Pattern names should be "Crosscourt Forehand" not "Mid Crosscourt Forehand"
        parts = []
        if self.direction:
            parts.append(self.direction)
        if self.shot_type:
            parts.append(self.shot_type)
        if self.context:
            parts.append(self.context)
        return " ".join(parts)

@dataclass
class DiscoveredPattern:
    """A pattern discovered through data mining"""
    pattern_id: str
    name: str
    type: str  # strength or weakness
    features: PatternFeatures
    frequency: int
    win_rate: float
    baseline_win_rate: float
    significance_score: float
    supporting_rallies: List[Rally] = field(default_factory=list)
    
    # For frontend compatibility
    severity: str = "medium"
    point_win_rate: float = None
    point_loss_rate: float = None
    improvement_potential: float = None
    leverage_potential: float = None
    description: str = ""
    pattern_behavior: str = ""
    professional_strategy: Dict = field(default_factory=dict)
    drills: List = field(default_factory=list)
    critical_moments: List = field(default_factory=list)
    significance_score: float = 0.0


class HierarchicalPatternDiscovery:
    """
    Discovers patterns through hierarchical feature mining.
    Automatically finds ALL significant patterns without hardcoding.
    """
    
    def __init__(self, min_sample_size: int = 10, significance_threshold: float = 0.10):
        self.min_sample_size = min_sample_size
        self.significance_threshold = significance_threshold  # 10% difference from baseline
    
    def discover_patterns(self, rallies: List[Rally]) -> List[DiscoveredPattern]:
        """
        Main discovery pipeline: mine all significant patterns from data.
        
        Returns patterns ranked by significance.
        """
        if not rallies:
            return []
        
        # Calculate baseline statistics
        baseline_win_rate = calculate_win_rate(rallies)
        
        # Tag all shots with features
        self._tag_shot_features(rallies)
        
        # Generate and evaluate all feature combinations
        all_patterns = []
        
        # Level 1: Shot type patterns
        shot_type_patterns = self._mine_shot_type_patterns(rallies, baseline_win_rate)
        all_patterns.extend(shot_type_patterns)
        
        # Level 2: Shot type + Direction patterns
        for shot_type in ['Serve', 'Forehand', 'Backhand']:
            direction_patterns = self._mine_direction_patterns(
                rallies, shot_type, baseline_win_rate
            )
            all_patterns.extend(direction_patterns)
        
        # Level 3: Shot type + Direction + Depth patterns
        for shot_type in ['Serve', 'Forehand', 'Backhand']:
            for direction in ['DTL', 'Crosscourt', 'Middle']:
                depth_patterns = self._mine_depth_patterns(
                    rallies, shot_type, direction, baseline_win_rate
                )
                all_patterns.extend(depth_patterns)
        
        # Level 4: Context patterns (Pressure vs Normal)
        context_patterns = self._mine_context_patterns(rallies, baseline_win_rate)
        all_patterns.extend(context_patterns)
        
        # Remove duplicates and rank by significance
        unique_patterns = self._deduplicate_patterns(all_patterns)
        ranked_patterns = sorted(
            unique_patterns, 
            key=lambda p: p.significance_score, 
            reverse=True
        )
        
        # Return top 10 most significant patterns
        top_patterns = ranked_patterns[:10]
        
        # Classify as strengths or weaknesses (round to 2 decimal places)
        for pattern in top_patterns:
            if pattern.win_rate > baseline_win_rate:
                pattern.type = 'strength'
                pattern.point_win_rate = round(pattern.win_rate * 100, 2)
                pattern.leverage_potential = round(pattern.win_rate * 100, 2)
            else:
                pattern.type = 'weakness'
                pattern.point_loss_rate = round((1 - pattern.win_rate) * 100, 2)
                pattern.improvement_potential = round((baseline_win_rate - pattern.win_rate) * 100, 2)
        
        return top_patterns
    
    def _tag_shot_features(self, rallies: List[Rally]):
        """Tag every shot with its feature classification"""
        for rally in rallies:
            for shot in rally.shots:
                # Direction classification
                shot.direction = self._classify_direction(shot)
                
                # Depth classification
                shot.depth_category = self._classify_depth(shot)
                
                # Speed classification
                shot.speed_category = self._classify_speed(shot)
    
    def _classify_direction(self, shot: Shot) -> str:
        """Classify shot direction"""
        x = shot.x
        
        if shot.shot_type == 'Serve':
            if 48 <= x <= 56:
                return 'T'
            elif x < 40:
                return 'Wide'
            else:
                return 'Body'
        
        # For groundstrokes
        if shot.shot_type == 'Forehand':
            if x < 20:
                return 'DTL'
            elif 20 <= x <= 45:
                return 'Crosscourt'
            else:
                return 'Middle'
        
        if shot.shot_type == 'Backhand':
            if x > 80:
                return 'DTL'
            elif 55 <= x <= 80:
                return 'Crosscourt'
            else:
                return 'Middle'
        
        return 'Unknown'
    
    def _classify_depth(self, shot: Shot) -> str:
        """Classify shot depth"""
        y = shot.y
        if y < 60:
            return 'Short'
        elif 60 <= y <= 75:
            return 'Mid'
        else:
            return 'Deep'
    
    def _classify_speed(self, shot: Shot) -> str:
        """Classify shot speed"""
        speed = shot.speed
        
        if shot.shot_type == 'Serve':
            if speed < 95:
                return 'Slow'
            elif speed < 110:
                return 'Medium'
            else:
                return 'Fast'
        else:
            if speed < 60:
                return 'Slow'
            elif speed < 75:
                return 'Medium'
            else:
                return 'Fast'
    
    def _mine_shot_type_patterns(
        self, 
        rallies: List[Rally], 
        baseline: float
    ) -> List[DiscoveredPattern]:
        """Mine patterns based on shot type alone"""
        patterns = []
        
        for shot_type in ['Serve', 'Forehand', 'Backhand', 'Volley']:
            matching_rallies = self._filter_rallies_with_shot(rallies, shot_type)
            
            if len(matching_rallies) >= self.min_sample_size:
                win_rate = calculate_win_rate(matching_rallies)
                significance = abs(win_rate - baseline)
                
                if significance >= self.significance_threshold:
                    features = PatternFeatures(shot_type=shot_type)
                    pattern = self._create_pattern(
                        features, matching_rallies, win_rate, baseline, significance
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _mine_direction_patterns(
        self,
        rallies: List[Rally],
        shot_type: str,
        baseline: float
    ) -> List[DiscoveredPattern]:
        """Mine patterns for shot type + direction combinations"""
        patterns = []
        
        directions = ['DTL', 'Crosscourt', 'Middle', 'T', 'Wide', 'Body']
        
        for direction in directions:
            matching_rallies = self._filter_rallies_with_shot_and_feature(
                rallies, shot_type, 'direction', direction
            )
            
            if len(matching_rallies) >= self.min_sample_size:
                win_rate = calculate_win_rate(matching_rallies)
                significance = abs(win_rate - baseline)
                
                if significance >= self.significance_threshold:
                    features = PatternFeatures(
                        shot_type=shot_type,
                        direction=direction
                    )
                    pattern = self._create_pattern(
                        features, matching_rallies, win_rate, baseline, significance
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _mine_depth_patterns(
        self,
        rallies: List[Rally],
        shot_type: str,
        direction: str,
        baseline: float
    ) -> List[DiscoveredPattern]:
        """Mine patterns for shot type + direction + depth"""
        patterns = []
        
        for depth in ['Short', 'Mid', 'Deep']:
            matching_rallies = []
            for rally in rallies:
                for shot in rally.shots:
                    if (shot.player == 'you' and
                        shot.shot_type == shot_type and
                        hasattr(shot, 'direction') and shot.direction == direction and
                        hasattr(shot, 'depth_category') and shot.depth_category == depth):
                        matching_rallies.append(rally)
                        break
            
            if len(matching_rallies) >= self.min_sample_size:
                win_rate = calculate_win_rate(matching_rallies)
                significance = abs(win_rate - baseline)
                
                if significance >= self.significance_threshold:
                    features = PatternFeatures(
                        shot_type=shot_type,
                        direction=direction,
                        depth=depth
                    )
                    pattern = self._create_pattern(
                        features, matching_rallies, win_rate, baseline, significance
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _mine_context_patterns(
        self,
        rallies: List[Rally],
        baseline: float
    ) -> List[DiscoveredPattern]:
        """Mine patterns based on context (pressure vs normal)"""
        patterns = []
        
        # Separate by context
        pressure_rallies = [r for r in rallies if r.is_pressure]
        normal_rallies = [r for r in rallies if not r.is_pressure]
        
        for context, context_rallies in [('Pressure', pressure_rallies), ('Normal', normal_rallies)]:
            if len(context_rallies) >= self.min_sample_size:
                win_rate = calculate_win_rate(context_rallies)
                significance = abs(win_rate - baseline)
                
                if significance >= self.significance_threshold:
                    features = PatternFeatures(context=context)
                    pattern = self._create_pattern(
                        features, context_rallies, win_rate, baseline, significance
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _filter_rallies_with_shot(
        self, 
        rallies: List[Rally], 
        shot_type: str
    ) -> List[Rally]:
        """Filter rallies containing a specific shot type by you"""
        matching = []
        for rally in rallies:
            for shot in rally.shots:
                if shot.player == 'you' and shot.shot_type == shot_type:
                    matching.append(rally)
                    break
        return matching
    
    def _filter_rallies_with_shot_and_feature(
        self,
        rallies: List[Rally],
        shot_type: str,
        feature_name: str,
        feature_value: str
    ) -> List[Rally]:
        """Filter rallies with specific shot type and feature"""
        matching = []
        for rally in rallies:
            for shot in rally.shots:
                if (shot.player == 'you' and 
                    shot.shot_type == shot_type and
                    hasattr(shot, feature_name) and
                    getattr(shot, feature_name) == feature_value):
                    matching.append(rally)
                    break
        return matching
    
    def _score_shot_match(self, shot: Shot, features: PatternFeatures) -> float:
        """
        Score how well a shot matches the pattern features (0.0 to 1.0).
        Higher score = better match
        """
        if shot.player != 'you':
            return 0.0
        
        score = 0.0
        matches = 0
        total_features = 0
        
        # Check shot type match
        if features.shot_type:
            total_features += 1
            if shot.shot_type == features.shot_type:
                matches += 1
        
        # Check direction match
        if features.direction:
            total_features += 1
            if hasattr(shot, 'direction') and shot.direction == features.direction:
                matches += 1
        
        # Check depth match
        if features.depth:
            total_features += 1
            if hasattr(shot, 'depth_category') and shot.depth_category == features.depth:
                matches += 1
        
        # Check speed match
        if features.speed_category:
            total_features += 1
            if hasattr(shot, 'speed_category') and shot.speed_category == features.speed_category:
                matches += 1
        
        if total_features > 0:
            score = matches / total_features
        
        return score
    
    def _create_pattern(
        self,
        features: PatternFeatures,
        rallies: List[Rally],
        win_rate: float,
        baseline: float,
        significance: float
    ) -> DiscoveredPattern:
        """Create a discovered pattern from features and data"""
        # Generate pattern ID and name
        pattern_id = str(features).lower().replace(' ', '-')
        name = self._generate_pattern_name(features, win_rate, baseline)
        
        # Determine if this is a strength or weakness
        is_strength = win_rate > baseline
        
        # NEW APPROACH: Find rallies where the weakest/strongest shot matches this pattern
        # For each rally, evaluate ALL your shots and find the one that best matches
        rallies_with_pattern_shot = []
        
        for rally in rallies:
            # CRITICAL: Only evaluate YOUR shots (not opponent's)
            your_shots = [(i, shot) for i, shot in enumerate(rally.shots) if shot.player == 'you']
            
            if not your_shots:
                continue
            
            # Score each of YOUR shots for pattern match
            shot_scores = []
            for shot_idx, shot in your_shots:
                # Double-check this is your shot (defensive)
                if shot.player != 'you':
                    continue
                    
                match_score = self._score_shot_match(shot, features)
                if match_score > 0:  # Only consider shots that match at least partially
                    shot_scores.append((match_score, shot_idx, shot))
            
            if not shot_scores:
                continue
            
            # For weakness patterns: Find the BEST matching shot (the weak pattern shot)
            # For strength patterns: Find the BEST matching shot (the strong pattern shot)
            # In both cases, we want the shot that best represents the pattern
            shot_scores.sort(key=lambda x: x[0], reverse=True)  # Best match first
            best_match_score, best_shot_idx, best_shot = shot_scores[0]
            
            # CRITICAL: Verify the shot index points to one of YOUR shots
            if best_shot_idx not in [idx for idx, _ in your_shots]:
                print(f"⚠️  Pattern shot index {best_shot_idx} not in your_shots, skipping rally", file=sys.stderr)
                continue
            
            # Only include if it's a good match (>= 50% of features match)
            if best_match_score >= 0.5:
                # Store which shot is the pattern shot (verified to be YOUR shot)
                rally.pattern_shot_index = best_shot_idx
                rallies_with_pattern_shot.append(rally)
        
        # Select 8-12 supporting rallies (diverse sample across match)
        supporting_count = min(12, max(8, len(rallies_with_pattern_shot)))
        if len(rallies_with_pattern_shot) <= supporting_count:
            supporting_rallies = rallies_with_pattern_shot
        else:
            # Sample evenly across the match timeline
            step = len(rallies_with_pattern_shot) / supporting_count
            indices = [int(i * step) for i in range(supporting_count)]
            supporting_rallies = [rallies_with_pattern_shot[i] for i in indices]
        
        # Select 1-2 critical moments (TRULY critical points only)
        # ONLY select break points, set points, match points, or deuce in crucial games
        critical_candidates = []
        for rally in rallies_with_pattern_shot:
            importance = self._calculate_rally_importance(rally)
            
            # Only consider truly critical moments (importance > 0.5)
            if importance > 0.5:
                critical_candidates.append((importance, rally))
        
        # Sort by importance and take top 1-2
        critical_candidates.sort(key=lambda x: x[0], reverse=True)
        critical_count = min(2, len(critical_candidates))
        critical_moments = [c[1] for c in critical_candidates[:critical_count]]
        
        # Debug log critical moments found
        print(f"[CRITICAL] Pattern '{name}': Found {len(critical_candidates)} critical candidates, selected {len(critical_moments)}", file=sys.stderr)
        
        pattern = DiscoveredPattern(
            pattern_id=pattern_id,
            name=name,
            type='unknown',  # Will be classified later
            features=features,
            frequency=len(rallies),
            win_rate=round(win_rate, 2),
            baseline_win_rate=round(baseline, 2),
            significance_score=round(significance * len(rallies), 2),  # Weight by frequency
            supporting_rallies=supporting_rallies,
            critical_moments=critical_moments
        )
        
        return pattern
    
    def _calculate_rally_importance(self, rally) -> float:
        """
        Calculate how important a rally was (0.0 to 1.0).
        
        ONLY truly critical moments qualify:
        - Break points (30-40, 40-Ad when opponent serving)
        - Deuce in crucial games (game 7+, especially 9+)
        """
        # Get point score
        point_score = rally.point_score if hasattr(rally, 'point_score') else '0-0'
        game_number = rally.game_number if hasattr(rally, 'game_number') else 1
        is_deuce = rally.is_deuce if hasattr(rally, 'is_deuce') else False
        
        # Normalize to uppercase for matching
        point_score_upper = point_score.upper() if isinstance(point_score, str) else ''
        
        # Break point - CRITICAL (30-40, 40-Ad, or BP marker)
        break_point_indicators = ['30-40', '40-AD', 'AD-OUT', 'BP']
        if any(indicator in point_score_upper for indicator in break_point_indicators):
            return 1.0
        
        # Deuce in crucial games - CRITICAL
        if is_deuce or 'DEUCE' in point_score_upper or '40-40' in point_score_upper:
            # Games 9-10+ are crucial (4-4, 5-4, 4-5, 5-5, etc.)
            if game_number >= 9:
                return 0.9
            # Also crucial if game 7-8 (3-3, 4-3, 3-4 game scores)
            if game_number >= 7:
                return 0.8
        
        # Not a critical moment
        return 0.0
    
    def _generate_pattern_name(
        self,
        features: PatternFeatures,
        win_rate: float,
        baseline: float
    ) -> str:
        """Generate human-readable pattern name"""
        parts = []
        
        # Note: depth (Short/Mid/Deep) removed from pattern names per user request
        # Pattern names should be like "Crosscourt Forehand" not "Mid Crosscourt Forehand"
        
        if features.direction:
            parts.append(features.direction)
        
        if features.shot_type:
            parts.append(features.shot_type)
        
        if features.context:
            parts.append(f"({features.context})")
        
        name = " ".join(parts)
        
        # Add outcome indicator
        if win_rate > baseline:
            name += " [Strong]"
        else:
            name += " [Weak]"
        
        return name
    
    def _deduplicate_patterns(
        self,
        patterns: List[DiscoveredPattern]
    ) -> List[DiscoveredPattern]:
        """Remove duplicate or overlapping patterns"""
        # Group by pattern_id, keep highest significance
        by_id = {}
        for pattern in patterns:
            if pattern.pattern_id not in by_id:
                by_id[pattern.pattern_id] = pattern
            elif pattern.significance_score > by_id[pattern.pattern_id].significance_score:
                by_id[pattern.pattern_id] = pattern
        
        unique_patterns = list(by_id.values())
        
        # Apply hierarchical filtering (remove parent patterns when child exists)
        filtered_patterns = self._filter_hierarchical_patterns(unique_patterns)
        
        return filtered_patterns
    
    def _filter_hierarchical_patterns(
        self,
        patterns: List[DiscoveredPattern]
    ) -> List[DiscoveredPattern]:
        """
        Remove parent patterns when more specific child patterns exist.
        
        Example: If "Deep Middle Backhand" exists, remove:
        - "Middle Backhand" (missing depth)
        - "Deep Backhand" (missing direction)
        - "Backhand" (missing both)
        """
        filtered = []
        
        for pattern in patterns:
            # Count non-None features in this pattern
            features = pattern.features.to_dict()
            num_features = len(features)
            
            # Check if any pattern is a more specific version of this one
            is_parent = False
            for other in patterns:
                if pattern.pattern_id == other.pattern_id:
                    continue
                
                other_features = other.features.to_dict()
                other_num_features = len(other_features)
                
                # Skip if other pattern has same or fewer features
                if other_num_features <= num_features:
                    continue
                
                # Check if this pattern is a subset of the other (making it a parent)
                is_subset = all(
                    key in other_features and other_features[key] == value
                    for key, value in features.items()
                )
                
                if is_subset:
                    # This pattern is a parent of the other (less specific)
                    is_parent = True
                    break
            
            # Only keep patterns that are NOT parents of more specific ones
            if not is_parent:
                filtered.append(pattern)
        
        return filtered
    
    # ==============================================================================
    # NEW CONTEXT-AWARE PATTERN DISCOVERY
    # ==============================================================================
    
    def discover_context_patterns(
        self,
        rallies: List[Rally],
        match_context: Dict,
        context_evaluator
    ) -> List[DiscoveredPattern]:
        """
        Discover 6 new pattern types using context evaluation:
        1. Positional errors
        2. Sequencing failures
        3. Score-situation patterns
        4. Energy mismanagement
        5. Opponent exploitation
        6. Break point conversion
        """
        all_context_patterns = []
        
        # 1. Positional errors (staying back when should attack)
        positional_patterns = self._discover_positional_errors(rallies, context_evaluator, match_context)
        all_context_patterns.extend(positional_patterns)
        
        # 2. Sequencing failures (setup without finish)
        sequence_patterns = self._discover_sequencing_failures(rallies)
        all_context_patterns.extend(sequence_patterns)
        
        # 3. Score-situation patterns (conservative on break points)
        score_patterns = self._discover_score_patterns(rallies)
        all_context_patterns.extend(score_patterns)
        
        # 4. Energy mismanagement (grinding when should shorten)
        energy_patterns = self._discover_energy_patterns(rallies, match_context)
        all_context_patterns.extend(energy_patterns)
        
        # 5. Opponent exploitation (not targeting weaknesses)
        opponent_patterns = self._discover_opponent_exploitation(rallies)
        all_context_patterns.extend(opponent_patterns)
        
        # 6. Break point conversion
        bp_patterns = self._discover_break_point_patterns(rallies)
        all_context_patterns.extend(bp_patterns)
        
        return all_context_patterns
    
    def _discover_positional_errors(self, rallies, context_evaluator, match_context):
        """Detect staying back when should attack short balls"""
        short_ball_failures = []
        
        for rally in rallies:
            if not hasattr(rally, 'shots') or not rally.shots:
                continue
            
            for i, shot in enumerate(rally.shots):
                if shot.player.lower() not in ['you', 'player']:
                    continue
                
                # Check if ball landed short (y < 60 = inside service line area)
                ball_y = getattr(shot, 'y', 50)
                if ball_y < 60:  # Short ball zone
                    # Check next shot - did we attack?
                    if i + 1 < len(rally.shots):
                        next_shot = rally.shots[i + 1]
                        if next_shot.player.lower() in ['you', 'player']:
                            speed = getattr(next_shot, 'speed', 0)
                            if speed < 75:  # Should attack with 75+ mph
                                short_ball_failures.append(rally)
                                break
        
        if len(short_ball_failures) >= self.min_sample_size:
            baseline_win_rate = calculate_win_rate(rallies)
            pattern_win_rate = calculate_win_rate(short_ball_failures)
            
            return [DiscoveredPattern(
                pattern_id="positional_short_ball_failure",
                name="Not Attacking Short Balls",
                type="weakness",
                features=PatternFeatures(context="Positional"),
                frequency=len(short_ball_failures),
                win_rate=pattern_win_rate,
                baseline_win_rate=baseline_win_rate,
                significance_score=abs(baseline_win_rate - pattern_win_rate),
                supporting_rallies=short_ball_failures[:12],
                description="Staying back when opponent gives short balls inside service line"
            )]
        
        return []
    
    def _discover_sequencing_failures(self, rallies):
        """Detect setup shots without finishing"""
        sequence_failures = []
        
        for rally in rallies:
            if not hasattr(rally, 'shots') or len(rally.shots) < 4:
                continue
            
            your_shots = [s for s in rally.shots if s.player.lower() in ['you', 'player']]
            if len(your_shots) < 3:
                continue
            
            # Check if hit 2+ crosscourts but never went DTL
            crosscourt_count = 0
            went_dtl = False
            
            for shot in your_shots:
                direction = getattr(shot, 'direction', '').lower()
                if 'cross' in direction:
                    crosscourt_count += 1
                elif 'dtl' in direction or 'down' in direction:
                    went_dtl = True
                    break
            
            # If 2+ crosscourts but never changed direction = sequencing failure
            if crosscourt_count >= 2 and not went_dtl and rally.outcome == 'lost':
                sequence_failures.append(rally)
        
        if len(sequence_failures) >= self.min_sample_size:
            baseline_win_rate = calculate_win_rate(rallies)
            pattern_win_rate = calculate_win_rate(sequence_failures)
            
            return [DiscoveredPattern(
                pattern_id="sequencing_no_dtl_after_crosscourt",
                name="Setup Without Finish",
                type="weakness",
                features=PatternFeatures(context="Sequencing"),
                frequency=len(sequence_failures),
                win_rate=pattern_win_rate,
                baseline_win_rate=baseline_win_rate,
                significance_score=abs(baseline_win_rate - pattern_win_rate),
                supporting_rallies=sequence_failures[:12],
                description="Building with crosscourts but not changing direction with down-the-line"
            )]
        
        return []
    
    def _discover_score_patterns(self, rallies):
        """Detect conservative play on break points"""
        break_point_rallies = [r for r in rallies if getattr(r, 'is_break_point', False)]
        
        if len(break_point_rallies) < 5:
            return []
        
        # Check for conservative play (lower average shot speed)
        conservative_bp = []
        for rally in break_point_rallies:
            if not hasattr(rally, 'shots'):
                continue
            
            your_shots = [s for s in rally.shots if s.player.lower() in ['you', 'player']]
            if not your_shots:
                continue
            
            avg_speed = sum(getattr(s, 'speed', 0) for s in your_shots) / len(your_shots)
            if avg_speed < 60 and rally.outcome == 'lost':  # Conservative and lost
                conservative_bp.append(rally)
        
        if len(conservative_bp) >= 3:
            baseline_win_rate = calculate_win_rate(rallies)
            pattern_win_rate = calculate_win_rate(conservative_bp)
            
            return [DiscoveredPattern(
                pattern_id="score_conservative_bp",
                name="Conservative on Break Points",
                type="weakness",
                features=PatternFeatures(context="Score"),
                frequency=len(conservative_bp),
                win_rate=pattern_win_rate,
                baseline_win_rate=baseline_win_rate,
                significance_score=abs(baseline_win_rate - pattern_win_rate),
                supporting_rallies=conservative_bp[:12],
                description="Playing too safely on break point opportunities"
            )]
        
        return []
    
    def _discover_energy_patterns(self, rallies, match_context):
        """Detect grinding when should shorten points"""
        # Group rallies by set
        by_set = defaultdict(list)
        for rally in rallies:
            set_num = getattr(rally, 'set_number', 1)
            by_set[set_num].append(rally)
        
        if len(by_set) < 2:
            return []
        
        # Calculate average rally length per set
        set_1_length = sum(len(getattr(r, 'shots', [])) for r in by_set[1]) / max(len(by_set[1]), 1)
        last_set = max(by_set.keys())
        last_set_length = sum(len(getattr(r, 'shots', [])) for r in by_set[last_set]) / max(len(by_set[last_set]), 1)
        
        # If rally length increased 20%+ in late sets = energy mismanagement
        if last_set_length > set_1_length * 1.2:
            long_late_rallies = [r for r in by_set[last_set] if len(getattr(r, 'shots', [])) > 8]
            
            if len(long_late_rallies) >= self.min_sample_size:
                baseline_win_rate = calculate_win_rate(rallies)
                pattern_win_rate = calculate_win_rate(long_late_rallies)
                
                return [DiscoveredPattern(
                    pattern_id="energy_grinding_late_sets",
                    name="Grinding When Tired",
                    type="weakness",
                    features=PatternFeatures(context="Energy"),
                    frequency=len(long_late_rallies),
                    win_rate=pattern_win_rate,
                    baseline_win_rate=baseline_win_rate,
                    significance_score=abs(baseline_win_rate - pattern_win_rate),
                    supporting_rallies=long_late_rallies[:12],
                    description=f"Rally length increased {((last_set_length/set_1_length - 1) * 100):.0f}% in late sets - should shorten points"
                )]
        
        return []
    
    def _discover_opponent_exploitation(self, rallies):
        """Detect lack of shot variety / not exploiting opponent weaknesses"""
        # Analyze shot direction distribution
        your_shots_by_rally = []
        
        for rally in rallies:
            if not hasattr(rally, 'shots') or not rally.shots:
                continue
            
            your_shots = [s for s in rally.shots if s.player.lower() in ['you', 'player']]
            if len(your_shots) >= 3:  # Need multiple shots to see variety
                directions = [getattr(s, 'direction', '').lower() for s in your_shots if getattr(s, 'direction', '')]
                
                # Check if hitting same direction repeatedly
                if directions:
                    crosscourt_pct = sum(1 for d in directions if 'cross' in d) / len(directions)
                    dtl_pct = sum(1 for d in directions if 'dtl' in d or 'down' in d) / len(directions)
                    
                    # If 80%+ to one side = predictable, not exploiting
                    if crosscourt_pct > 0.80 or dtl_pct > 0.80:
                        your_shots_by_rally.append(rally)
        
        if len(your_shots_by_rally) >= self.min_sample_size:
            baseline_win_rate = calculate_win_rate(rallies)
            pattern_win_rate = calculate_win_rate(your_shots_by_rally)
            
            # Calculate which direction is overused
            all_directions = []
            for rally in your_shots_by_rally:
                your_shots = [s for s in rally.shots if s.player.lower() in ['you', 'player']]
                directions = [getattr(s, 'direction', '').lower() for s in your_shots if getattr(s, 'direction', '')]
                all_directions.extend(directions)
            
            if all_directions:
                crosscourt_pct = sum(1 for d in all_directions if 'cross' in d) / len(all_directions)
                overused_direction = "crosscourt" if crosscourt_pct > 0.60 else "down-the-line"
                
                return [DiscoveredPattern(
                    pattern_id="opponent_predictable_direction",
                    name="Predictable Shot Placement",
                    type="weakness",
                    features=PatternFeatures(context="Opponent"),
                    frequency=len(your_shots_by_rally),
                    win_rate=pattern_win_rate,
                    baseline_win_rate=baseline_win_rate,
                    significance_score=abs(baseline_win_rate - pattern_win_rate),
                    supporting_rallies=your_shots_by_rally[:12],
                    description=f"Hitting {overused_direction} {crosscourt_pct*100:.0f}% of time - opponent can predict your shots"
                )]
        
        return []
    
    def _discover_break_point_patterns(self, rallies):
        """Analyze break point conversion/save rates"""
        bp_serving = [r for r in rallies if getattr(r, 'is_break_point', False) and getattr(r, 'serving', False)]
        bp_returning = [r for r in rallies if getattr(r, 'is_break_point', False) and not getattr(r, 'serving', False)]
        
        patterns = []
        
        # Analyze serving on BP
        if len(bp_serving) >= 5:
            saved = len([r for r in bp_serving if r.outcome == 'won'])
            save_rate = saved / len(bp_serving)
            
            if save_rate < 0.55:  # Below 55% = weakness
                patterns.append(DiscoveredPattern(
                    pattern_id="bp_low_save_rate",
                    name="Low Break Point Save Rate",
                    type="weakness",
                    features=PatternFeatures(context="Break Point"),
                    frequency=len(bp_serving),
                    win_rate=save_rate,
                    baseline_win_rate=0.60,
                    significance_score=0.60 - save_rate,
                    supporting_rallies=bp_serving[:12],
                    description=f"Saving only {save_rate*100:.0f}% of break points (benchmark: 60%+)"
                ))
        
        # Analyze returning on BP
        if len(bp_returning) >= 5:
            converted = len([r for r in bp_returning if r.outcome == 'won'])
            conversion_rate = converted / len(bp_returning)
            
            if conversion_rate < 0.25:  # Below 25% = weakness
                patterns.append(DiscoveredPattern(
                    pattern_id="bp_low_conversion",
                    name="Low Break Point Conversion",
                    type="weakness",
                    features=PatternFeatures(context="Break Point"),
                    frequency=len(bp_returning),
                    win_rate=conversion_rate,
                    baseline_win_rate=0.30,
                    significance_score=0.30 - conversion_rate,
                    supporting_rallies=bp_returning[:12],
                    description=f"Converting only {conversion_rate*100:.0f}% of break points (benchmark: 30%+)"
                ))
        
        return patterns
