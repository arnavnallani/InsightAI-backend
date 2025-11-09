"""
Complete Hierarchical Pattern Analysis Pipeline
Integrates: Discovery → Enrichment → Minimax → Connections → Roadmap
"""

import sys
import os
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hierarchical_pattern_discovery import HierarchicalPatternDiscovery, DiscoveredPattern
from pattern_enrichment import enrich_pattern_with_narratives
from pattern_utils import Rally, compute_baseline_statistics
from content_generators import generate_improvement_roadmap
from context_aware_shot_evaluator import ContextAwareShotEvaluator
from tactical_playbook_generator import TacticalPlaybookGenerator

try:
    from minimax_adapter import SimplifiedMinimaxAdapter
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False
    print("Warning: minimax_adapter not available, counterfactual analysis disabled", file=sys.stderr)


class HierarchicalAnalysisPipeline:
    """
    Complete analysis pipeline using hierarchical pattern discovery.
    
    Replaces hardcoded OrganicPatternDiscovery with truly organic discovery.
    """
    
    def __init__(
        self,
        min_sample_size: int = 10,
        significance_threshold: float = 0.10,
        include_minimax: bool = True,
        minimax_depth_supporting: int = 2,
        minimax_depth_critical: int = 3
    ):
        self.min_sample_size = min_sample_size
        self.significance_threshold = significance_threshold
        self.include_minimax = include_minimax
        
        # Initialize minimax adapter if available
        if include_minimax and MINIMAX_AVAILABLE:
            self.minimax_adapter = SimplifiedMinimaxAdapter(
                depth_supporting=minimax_depth_supporting,
                depth_critical=minimax_depth_critical,
                branching=3,
                rollouts_supporting=10,
                rollouts_critical=15
            )
        else:
            self.minimax_adapter = None
    
    def analyze_match(self, rallies_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete analysis pipeline.
        
        Args:
            rallies_data: List of rally dictionaries (SwingVision format)
        
        Returns:
            Complete analysis with patterns, roadmap, executive summary
        """
        print("🎾 Starting Hierarchical Analysis Pipeline...", file=sys.stderr)
        
        # Step 1: Normalize and convert to Rally objects
        # Filter out rallies with missing/empty shots (defensive guard)
        valid_rallies_data = [
            r for r in rallies_data 
            if r.get('shots') and isinstance(r.get('shots'), list) and len(r.get('shots')) > 0
        ]
        
        if len(valid_rallies_data) < len(rallies_data):
            skipped = len(rallies_data) - len(valid_rallies_data)
            print(f"⚠️  Skipped {skipped} rallies with missing/empty shots", file=sys.stderr)
        
        rallies = [Rally(r) for r in valid_rallies_data]
        print(f"📊 Loaded {len(rallies)} valid rallies", file=sys.stderr)
        
        # Early exit if no valid rallies
        if not rallies:
            print("❌ No valid rallies to analyze", file=sys.stderr)
            return {
                'patterns': [],
                'executive_summary': {
                    'overall_assessment': 'No valid rally data available for analysis.',
                    'patterns_discovered_count': 0,
                    'strengths_count': 0,
                    'weaknesses_count': 0,
                    'key_insight': 'Unable to analyze match.',
                    'primary_recommendation': 'Ensure rally data includes shot information.',
                    'match_win_rate': 0
                },
                'improvement_roadmap': {},
                'baseline_statistics': {},
                'total_patterns_discovered': 0,
                'strengths_count': 0,
                'weaknesses_count': 0
            }
        
        # Step 2: Compute baseline statistics
        baseline_stats = compute_baseline_statistics(rallies)
        
        # Step 3: Discover patterns organically
        print("🔍 Discovering patterns...", file=sys.stderr)
        discovery = HierarchicalPatternDiscovery(
            min_sample_size=self.min_sample_size,
            significance_threshold=self.significance_threshold
        )
        raw_patterns = discovery.discover_patterns(rallies)
        print(f"✅ Discovered {len(raw_patterns)} shot-based patterns", file=sys.stderr)
        
        # Step 3.5: Discover context-aware patterns (NEW!)
        print("🎯 Discovering context-aware patterns...", file=sys.stderr)
        context_evaluator = ContextAwareShotEvaluator()
        match_context = self._compute_match_context(rallies)
        context_patterns = discovery.discover_context_patterns(
            rallies, match_context, context_evaluator
        )
        print(f"✅ Discovered {len(context_patterns)} context-aware patterns", file=sys.stderr)
        
        # Merge patterns
        raw_patterns.extend(context_patterns)
        print(f"📊 Total patterns: {len(raw_patterns)}", file=sys.stderr)
        
        # Step 4: Apply minimax counterfactual analysis
        if self.minimax_adapter:
            print("🤖 Running minimax counterfactual analysis...", file=sys.stderr)
            for pattern in raw_patterns:
                pattern.supporting_rallies = self._apply_minimax_to_rallies(
                    pattern.supporting_rallies, is_critical=False
                )
                pattern.critical_moments = self._apply_minimax_to_rallies(
                    pattern.critical_moments, is_critical=True
                )
            print("✅ Minimax analysis complete", file=sys.stderr)
        
        # Step 5: Connect weaknesses to strengths
        weaknesses = [p for p in raw_patterns if p.type == 'weakness']
        strengths = [p for p in raw_patterns if p.type == 'strength']
        self._connect_weaknesses_to_strengths(weaknesses, strengths)
        
        # Step 6: Enrich patterns with narratives
        print("📝 Enriching patterns with narratives and drills...", file=sys.stderr)
        enriched_patterns = []
        for pattern in raw_patterns:
            enriched = enrich_pattern_with_narratives(pattern)
            
            # Add strength connection if it exists
            if hasattr(pattern, 'strength_connection') and pattern.strength_connection:
                enriched['strength_pattern_connection'] = pattern.strength_connection
            
            enriched_patterns.append(enriched)
        
        # Step 7: Generate improvement roadmap
        print("🗺️  Generating improvement roadmap...", file=sys.stderr)
        improvement_roadmap = generate_improvement_roadmap(raw_patterns, baseline_stats)
        
        # Step 8: Generate executive summary
        executive_summary = self._generate_executive_summary(
            enriched_patterns, baseline_stats
        )
        
        # Step 9: Generate tactical playbook (NEW!)
        print("📖 Generating tactical playbook...", file=sys.stderr)
        playbook_generator = TacticalPlaybookGenerator()
        tactical_playbook = playbook_generator.generate_complete_playbook(
            raw_patterns, baseline_stats, opponent_style="baseliner"
        )
        print("✅ Tactical playbook complete!", file=sys.stderr)
        
        print("✅ Analysis complete!", file=sys.stderr)
        
        return {
            'patterns': enriched_patterns,
            'executive_summary': executive_summary,
            'improvement_roadmap': improvement_roadmap,
            'tactical_playbook': tactical_playbook,  # NEW!
            'baseline_statistics': baseline_stats,
            'total_patterns_discovered': len(enriched_patterns),
            'strengths_count': len(strengths),
            'weaknesses_count': len(weaknesses)
        }
    
    def _apply_minimax_to_rallies(
        self, 
        rallies: List[Rally], 
        is_critical: bool = False
    ) -> List[Rally]:
        """Apply minimax counterfactual analysis to rallies"""
        if not self.minimax_adapter:
            return rallies
        
        # Defensive: ensure all rallies are proper Rally objects with shots
        validated_rallies = []
        for rally in rallies:
            # Skip if rally is not a Rally object or has no shots
            if not isinstance(rally, Rally):
                print(f"⚠️  Skipping non-Rally object in minimax analysis", file=sys.stderr)
                continue
            
            if not hasattr(rally, 'shots') or not rally.shots:
                continue
            
            validated_rallies.append(rally)
        
        for rally in validated_rallies:
            if rally.shots:
                # Find your shots
                your_shots = [i for i, shot in enumerate(rally.shots) if shot.player == 'you']
                if your_shots:
                    # CRITICAL: Only optimize if we have a valid pattern_shot_index
                    # This ensures we're optimizing the EXACT shot that represents the pattern
                    if not hasattr(rally, 'pattern_shot_index') or rally.pattern_shot_index is None:
                        # No pattern shot identified - skip this rally
                        continue
                    
                    # Verify pattern_shot_index points to one of YOUR shots
                    if rally.pattern_shot_index not in your_shots:
                        # Invalid index - skip this rally
                        print(f"⚠️  Invalid pattern_shot_index {rally.pattern_shot_index}, skipping rally", file=sys.stderr)
                        continue
                    
                    # Use the pattern shot (verified to be valid)
                    shot_to_optimize_idx = rally.pattern_shot_index
                    shot_to_optimize = rally.shots[shot_to_optimize_idx]
                    
                    # Check if point was lost
                    point_lost = rally.outcome == 'lost'
                    
                    # For lost points: ALWAYS show minimax (user requirement)
                    # For won points: only show if significant improvement available
                    if point_lost:
                        # Run minimax analysis for all lost points
                        counterfactual = self.minimax_adapter.analyze_rally_counterfactual(
                            rally, 
                            shot_to_optimize_idx,
                            is_critical=is_critical
                        )
                        
                        # Always add minimax_optimal for lost points
                        optimal_shot = counterfactual.get('optimal_shot', {})
                        
                        # CRITICAL: Check if optimal shot type matches original shot type
                        # If pattern shot is a serve but optimal is groundstroke, skip this rally
                        original_shot_type = shot_to_optimize.shot_type.lower() if hasattr(shot_to_optimize, 'shot_type') else ''
                        optimal_shot_type = optimal_shot.get('shot_type', '').lower()
                        
                        print(f"🔍 Shot type check: original='{original_shot_type}', optimal='{optimal_shot_type}'", file=sys.stderr)
                        
                        # Skip if serve pattern but optimal is a groundstroke
                        if 'serve' in original_shot_type and optimal_shot_type not in ['serve', ''] and 'serve' not in optimal_shot_type:
                            print(f"⚠️  SKIPPING: Serve pattern but optimal is '{optimal_shot_type}' (groundstroke)", file=sys.stderr)
                            continue
                        
                        # Check if the shot we're optimizing is a serve
                        is_serve = 'serve' in original_shot_type
                        
                        if is_serve:
                            print(f"[SERVE] Optimizing serve shot", file=sys.stderr)
                            # Map current serve placement to alternative
                            serve_placement_map = {
                                'wide': 'T',
                                'ad-side': 'T',
                                'deuce-side': 'T',
                                't': 'wide',
                                'body': 'wide',
                                'middle': 'wide'
                            }
                            
                            # Get current placement from the serve shot
                            current_placement = optimal_shot.get('direction', '').lower()
                            if not current_placement and hasattr(shot_to_optimize, 'direction'):
                                current_placement = shot_to_optimize.direction.lower()
                            
                            # Determine alternative serve placement
                            alternative_placement = serve_placement_map.get(current_placement, 'T')
                            
                            # Override optimal shot to be a serve with different placement
                            shot_type = 'Serve'
                            direction = alternative_placement
                            spin = getattr(shot_to_optimize, 'spin', 'flat')
                            if not spin or spin.lower() in ['none', '']:
                                spin = 'flat'
                            
                            # Update tactical reasoning for serves
                            if alternative_placement == 'T':
                                serve_reasoning = "T serve forces opponent into body, limiting swing options and creating weak returns up the middle"
                            else:
                                serve_reasoning = "Wide serve pulls opponent off court, opening up angles for next shot and creating space"
                            
                            shot_desc = f"{spin.capitalize()} Serve to {alternative_placement.upper()}"
                            
                            # Determine coordinate placement for serve targets (normalize to lowercase)
                            placement_lower = alternative_placement.lower()
                            placement_coords = {'x': 50, 'y': 5}  # Default to T
                            if placement_lower == 't':
                                placement_coords = {'x': 50, 'y': 5}
                            elif placement_lower == 'body':
                                placement_coords = {'x': 45, 'y': 10}
                            elif placement_lower == 'wide':
                                placement_coords = {'x': 20, 'y': 8}
                            
                            rally.minimax_optimal = {
                                'optimalShot': {
                                    'shotType': 'Serve',
                                    'spin': spin,
                                    'placement': placement_coords,
                                    'playerPosition': shot_to_optimize.player_position if hasattr(shot_to_optimize, 'player_position') else {'x': 50, 'y': 95},
                                    'speed': optimal_shot.get('speed', 110),
                                },
                                'description': shot_desc,
                                'reasoning': serve_reasoning,
                                'expectedValueImprovement': round(counterfactual.get('improvement', 0) * 100, 2)
                            }
                        else:
                            # Groundstroke - use minimax recommendation
                            print(f"[GROUNDSTROKE] Optimizing {shot_to_optimize.shot_type}", file=sys.stderr)
                            shot_type_raw = optimal_shot.get('shot_type', 'Unknown')
                            
                            # Clean up shot type: remove "_volley" suffix if shot is from baseline
                            # Volleys should only be at net (Y < 70), not at baseline (Y > 70)
                            player_y = getattr(shot_to_optimize, 'player_position', {}).get('y', 85) if hasattr(shot_to_optimize, 'player_position') else 85
                            if player_y > 70 and '_volley' in shot_type_raw.lower():
                                # At baseline but shot type says volley - clean it up
                                shot_type = shot_type_raw.replace('_volley', '').replace('_Volley', '').strip()
                                print(f"⚠️  Cleaned shot type from '{shot_type_raw}' to '{shot_type}' (baseline position)", file=sys.stderr)
                            else:
                                shot_type = shot_type_raw
                            
                            direction = optimal_shot.get('direction', '')
                            spin = optimal_shot.get('spin', 'flat')
                            
                            # Format: "{Spin} {Shot Type} {direction}"
                            spin_cap = spin.capitalize()
                            shot_desc = f"{spin_cap} {shot_type}"
                            if direction:
                                shot_desc += f" {direction}"
                            
                            # Get placement coordinates from minimax (NO FALLBACK - must come from minimax)
                            placement_coords = optimal_shot.get('placement')
                            if not placement_coords:
                                print(f"⚠️  WARNING: Minimax did not return placement coordinates!", file=sys.stderr)
                                placement_coords = {'x': 50, 'y': 25}  # Emergency fallback only
                            else:
                                print(f"✅ Using minimax placement: {placement_coords}", file=sys.stderr)
                            
                            rally.minimax_optimal = {
                                'optimalShot': {
                                    'shotType': shot_type,
                                    'spin': spin,
                                    'placement': placement_coords,
                                    'playerPosition': shot_to_optimize.player_position if hasattr(shot_to_optimize, 'player_position') else {'x': 50, 'y': 85},
                                    'speed': optimal_shot.get('speed', 70),
                                },
                                'description': shot_desc,
                                'reasoning': counterfactual.get('tactical_reasoning', 'Better tactical choice'),
                                'expectedValueImprovement': round(counterfactual.get('improvement', 0) * 100, 2)
                            }
                        
                        # For critical moments, add sophisticated butterfly effect visualization
                        if is_critical:
                            rally.butterfly_effect = self._generate_butterfly_effect(
                                rally, shot_to_optimize, optimal_shot, counterfactual
                            )
                    else:
                        # For won points, only show if meaningful improvement
                        counterfactual = self.minimax_adapter.analyze_rally_counterfactual(
                            rally, 
                            shot_to_optimize_idx,
                            is_critical=is_critical
                        )
                        
                        if counterfactual.get('improvement', 0) > 0.05:
                            optimal_shot = counterfactual.get('optimal_shot', {})
                            
                            # Check if the shot we're optimizing is a serve
                            is_serve = shot_to_optimize.shot_type.lower() == 'serve' if hasattr(shot_to_optimize, 'shot_type') else False
                            
                            if is_serve:
                                # Map current serve placement to alternative
                                serve_placement_map = {
                                    'wide': 'T',
                                    'ad-side': 'T',
                                    'deuce-side': 'T',
                                    't': 'wide',
                                    'body': 'wide',
                                    'middle': 'wide'
                                }
                                
                                # Get current placement
                                current_placement = optimal_shot.get('direction', '').lower()
                                if not current_placement and hasattr(shot_to_optimize, 'direction'):
                                    current_placement = shot_to_optimize.direction.lower()
                                
                                # Determine alternative serve placement
                                alternative_placement = serve_placement_map.get(current_placement, 'T')
                                
                                # Override optimal shot to be a serve with different placement
                                spin = getattr(shot_to_optimize, 'spin', 'flat')
                                if not spin or spin.lower() in ['none', '']:
                                    spin = 'flat'
                                
                                # Update tactical reasoning for serves
                                if alternative_placement == 'T':
                                    serve_reasoning = "T serve forces opponent into body, limiting swing options and creating weak returns up the middle"
                                else:
                                    serve_reasoning = "Wide serve pulls opponent off court, opening up angles for next shot and creating space"
                                
                                shot_desc = f"{spin.capitalize()} Serve to {alternative_placement.upper()}"
                                
                                # Determine coordinate placement for serve targets (normalize to lowercase)
                                placement_lower = alternative_placement.lower()
                                placement_coords = {'x': 50, 'y': 5}  # Default to T
                                if placement_lower == 't':
                                    placement_coords = {'x': 50, 'y': 5}
                                elif placement_lower == 'body':
                                    placement_coords = {'x': 45, 'y': 10}
                                elif placement_lower == 'wide':
                                    placement_coords = {'x': 20, 'y': 8}
                                
                                rally.minimax_optimal = {
                                    'optimalShot': {
                                        'shotType': 'Serve',
                                        'spin': spin,
                                        'placement': placement_coords,
                                        'playerPosition': shot_to_optimize.player_position if hasattr(shot_to_optimize, 'player_position') else {'x': 50, 'y': 95},
                                        'speed': optimal_shot.get('speed', 110),
                                    },
                                    'description': shot_desc,
                                    'reasoning': serve_reasoning,
                                    'expectedValueImprovement': round(counterfactual.get('improvement', 0) * 100, 2)
                                }
                            else:
                                # Groundstroke
                                shot_type_raw = optimal_shot.get('shot_type', 'Unknown')
                                
                                # Clean up shot type: remove "_volley" suffix if shot is from baseline
                                player_y = getattr(shot_to_optimize, 'player_position', {}).get('y', 85) if hasattr(shot_to_optimize, 'player_position') else 85
                                if player_y > 70 and '_volley' in shot_type_raw.lower():
                                    shot_type = shot_type_raw.replace('_volley', '').replace('_Volley', '').strip()
                                    print(f"⚠️  Cleaned shot type from '{shot_type_raw}' to '{shot_type}' (baseline, won point)", file=sys.stderr)
                                else:
                                    shot_type = shot_type_raw
                                
                                direction = optimal_shot.get('direction', '')
                                spin = optimal_shot.get('spin', 'flat')
                                
                                # Format: "{Spin} {Shot Type} {direction}"
                                spin_cap = spin.capitalize()
                                shot_desc = f"{spin_cap} {shot_type}"
                                if direction:
                                    shot_desc += f" {direction}"
                                
                                # Get placement coordinates from minimax (NO FALLBACK - must come from minimax)
                                placement_coords = optimal_shot.get('placement')
                                if not placement_coords:
                                    print(f"⚠️  WARNING: Minimax did not return placement coordinates for won point!", file=sys.stderr)
                                    placement_coords = {'x': 50, 'y': 25}  # Emergency fallback only
                                else:
                                    print(f"✅ Using minimax placement (won point): {placement_coords}", file=sys.stderr)
                                
                                rally.minimax_optimal = {
                                    'optimalShot': {
                                        'shotType': shot_type,
                                        'spin': spin,
                                        'placement': placement_coords,
                                        'playerPosition': shot_to_optimize.player_position if hasattr(shot_to_optimize, 'player_position') else {'x': 50, 'y': 85},
                                        'speed': optimal_shot.get('speed', 70),
                                    },
                                    'description': shot_desc,
                                    'reasoning': counterfactual.get('tactical_reasoning', 'Better tactical choice'),
                                    'expectedValueImprovement': round(counterfactual.get('improvement', 0) * 100, 2)
                                }
                        else:
                            rally.minimax_optimal = None
        
        return validated_rallies
    
    def _generate_butterfly_effect(self, rally, actual_shot, optimal_shot_dict, counterfactual):
        """
        Generate sophisticated multi-step butterfly effect timeline.
        Shows how one shot decision cascades through immediate, short-term, medium-term, and long-term consequences.
        """
        # Get context
        point_score = getattr(rally, 'point_score', '0-0')
        game_score = getattr(rally, 'game_score', '0-0')
        set_number = getattr(rally, 'set_number', 1)
        game_number = getattr(rally, 'game_number', 1)
        is_serving = getattr(rally, 'serving', False)
        
        # Determine criticality level
        is_break_point = '30-40' in point_score or '40-AD' in point_score or 'BP' in point_score
        is_deuce = 'DEUCE' in point_score.upper() or '40-40' in point_score
        is_crucial_game = game_number >= 7
        
        # Format shots
        actual_shot_desc = f"{actual_shot.shot_type} {getattr(actual_shot, 'direction', '')}".strip()
        optimal_shot_desc = f"{optimal_shot_dict.get('shot_type', 'Unknown')} {optimal_shot_dict.get('direction', '')}".strip()
        
        # Generate context-aware narratives
        improvement_pct = round(counterfactual.get('improvement', 0) * 100, 2)
        
        # ACTUAL TIMELINE (what happened)
        actual_timeline = {
            'immediate': {
                'title': 'Immediate (0-3s)',
                'description': f"Hit {actual_shot_desc} at {round(actual_shot.speed, 1)}mph",
                'outcome': 'Point Lost',
                'severity': 'high'
            },
            'short_term': {
                'title': 'Short-term (rest of point)',
                'description': self._generate_actual_point_narrative(rally, is_break_point, is_deuce),
                'outcome': 'Momentum Lost',
                'severity': 'high'
            },
            'medium_term': {
                'title': 'Medium-term (rest of game/set)',
                'description': self._generate_actual_game_narrative(rally, is_break_point, is_crucial_game, is_serving),
                'outcome': 'Pressure Increased',
                'severity': 'medium'
            },
            'long_term': {
                'title': 'Long-term (match impact)',
                'description': self._generate_actual_match_narrative(rally, is_break_point, set_number),
                'outcome': 'Confidence Shaken',
                'severity': 'medium'
            }
        }
        
        # OPTIMAL TIMELINE (what could have been)
        optimal_timeline = {
            'immediate': {
                'title': 'Immediate (0-3s)',
                'description': f"Hit {optimal_shot_desc} - forces weak return",
                'outcome': 'Point Won',
                'severity': 'low'
            },
            'short_term': {
                'title': 'Short-term (rest of point)',
                'description': self._generate_optimal_point_narrative(optimal_shot_dict, improvement_pct),
                'outcome': 'Momentum Gained',
                'severity': 'low'
            },
            'medium_term': {
                'title': 'Medium-term (rest of game/set)',
                'description': self._generate_optimal_game_narrative(is_break_point, is_crucial_game, is_serving),
                'outcome': 'Pressure Released',
                'severity': 'low'
            },
            'long_term': {
                'title': 'Long-term (match impact)',
                'description': self._generate_optimal_match_narrative(is_break_point, set_number),
                'outcome': 'Confidence Boosted',
                'severity': 'low'
            }
        }
        
        return {
            'context': f"Set {set_number}, Game {game_number} - {game_score}, {point_score}",
            'criticalityLevel': 'break_point' if is_break_point else 'crucial' if is_crucial_game else 'important',
            'actualTimeline': actual_timeline,
            'optimalTimeline': optimal_timeline
        }
    
    def _generate_actual_point_narrative(self, rally, is_break_point, is_deuce):
        """Generate narrative for what actually happened in the point"""
        if is_break_point:
            return "Opponent seized opportunity, attacking your weak shot. Break point converted, game lost."
        elif is_deuce:
            return "Opponent capitalized on your defensive position. Lost the deuce point, now at disadvantage."
        else:
            return "Opponent controlled the rally from that moment, forcing you into defensive position until error."
    
    def _generate_actual_game_narrative(self, rally, is_break_point, is_crucial_game, is_serving):
        """Generate narrative for game/set impact of actual shot"""
        if is_break_point and is_serving:
            return "Service broken. Opponent now serving for the set. Mental edge lost."
        elif is_crucial_game:
            return "Failed to hold momentum in crucial game. Opponent's confidence surged, yours wavered."
        else:
            return "Lost the game, giving opponent psychological advantage and momentum shift."
    
    def _generate_actual_match_narrative(self, rally, is_break_point, set_number):
        """Generate narrative for match-level impact of actual shot"""
        if is_break_point and set_number >= 2:
            return "Critical break lost in late-set situation. Second-guessing shot selection for remainder of match."
        elif set_number >= 3:
            return "In deciding set, this moment planted doubt. Hesitation crept into future shot selection."
        else:
            return "Reinforced pattern of passive play. Opponent identified exploitable weakness."
    
    def _generate_optimal_point_narrative(self, optimal_shot, improvement_pct):
        """Generate narrative for optimal shot point outcome"""
        direction = optimal_shot.get('direction', 'optimal placement')
        return f"Aggressive {direction} shot ({improvement_pct}% better) puts opponent on defensive. Forces weak return, you control point to finish."
    
    def _generate_optimal_game_narrative(self, is_break_point, is_crucial_game, is_serving):
        """Generate narrative for game impact of optimal shot"""
        if is_break_point and is_serving:
            return "Hold serve under pressure. Send message: 'I can execute when it matters.' Opponent's doubt grows."
        elif is_crucial_game:
            return "Clutch performance in crucial game. Confidence soars, opponent feels the shift in momentum."
        else:
            return "Win game with authority. Establish tactical dominance and control tempo of match."
    
    def _generate_optimal_match_narrative(self, is_break_point, set_number):
        """Generate narrative for match impact of optimal shot"""
        if is_break_point and set_number >= 2:
            return "Crucial hold demonstrates mental toughness. Builds belief: 'I can win tight moments.' Carries forward."
        elif set_number >= 3:
            return "In deciding moments, aggressive execution pays off. Pattern established: attack works."
        else:
            return "Reinforces winning pattern. Opponent now must defend against your attacking game."
    
    def _connect_weaknesses_to_strengths(
        self,
        weaknesses: List[DiscoveredPattern],
        strengths: List[DiscoveredPattern]
    ):
        """Find logical connections between weaknesses and strengths"""
        for weakness in weaknesses:
            features = weakness.features
            weakness_id = weakness.pattern_id
            
            # DTL/Attack patterns → Connect to aggressive forehand/backhand strengths
            if features.direction == 'DTL' or 'attack' in weakness_id.lower():
                # Find matching shot type strength
                matching_strength = next(
                    (s for s in strengths 
                     if s.features.shot_type == features.shot_type),
                    None
                )
                if matching_strength:
                    weakness.strength_connection = {
                        'enabled_strength': matching_strength.name,
                        'how_it_connects': f"Fixing your {weakness.name} allows you to confidently use your {matching_strength.name} more often."
                    }
            
            # Serve pattern weaknesses → Connect to serve strengths
            elif features.shot_type == 'Serve':
                serve_strength = next((s for s in strengths if s.features.shot_type == 'Serve'), None)
                if serve_strength:
                    weakness.strength_connection = {
                        'enabled_strength': serve_strength.name,
                        'how_it_connects': f"Adding variety to your serve pattern makes your {serve_strength.name} even more effective by keeping opponents guessing."
                    }
            
            # Pressure/context weaknesses → Connect to any strength
            elif features.context == 'Pressure':
                if strengths:
                    primary_strength = strengths[0]
                    weakness.strength_connection = {
                        'enabled_strength': primary_strength.name,
                        'how_it_connects': f"Playing confidently under pressure means trusting your {primary_strength.name} on big points."
                    }
    
    def _generate_executive_summary(
        self,
        patterns: List[Dict],
        baseline: Dict
    ) -> Dict[str, Any]:
        """Generate executive summary of match analysis"""
        weaknesses = [p for p in patterns if p['type'] == 'weakness']
        strengths = [p for p in patterns if p['type'] == 'strength']
        
        # Overall assessment (round to 2 decimal places)
        if not weaknesses:
            overall_assessment = "Your game shows strong fundamentals across all patterns analyzed."
        else:
            primary_weakness = weaknesses[0]
            improvement_pct = round(primary_weakness.get('improvement_potential', 0), 2)
            overall_assessment = (
                f"Analysis of {baseline.get('total_rallies', 0)} rallies reveals {len(patterns)} key patterns. "
                f"Your primary area for improvement is {primary_weakness['name']}, "
                f"which offers {improvement_pct}% improvement potential."
            )
        
        # Key insight (round to 2 decimal places)
        if strengths:
            win_rate = round(strengths[0].get('point_win_rate', 0), 2)
            key_insight = f"Your {strengths[0]['name']} is a proven weapon with {win_rate}% success rate."
        else:
            key_insight = "Focus on converting identified opportunities into consistent execution."
        
        # Primary recommendation
        if weaknesses:
            primary_recommendation = f"Prioritize fixing {weaknesses[0]['name']} through targeted drills and match practice."
        else:
            primary_recommendation = "Continue leveraging your existing strengths to dominate matches."
        
        return {
            'overall_assessment': overall_assessment,
            'patterns_discovered_count': len(patterns),
            'strengths_count': len(strengths),
            'weaknesses_count': len(weaknesses),
            'key_insight': key_insight,
            'primary_recommendation': primary_recommendation,
            'match_win_rate': round(baseline.get('baseline_win_rate', 0.5) * 100, 2)
        }
    
    def _compute_match_context(self, rallies: List[Rally]) -> Dict[str, Any]:
        """Compute match-level context from rallies"""
        # Get set numbers
        set_numbers = [getattr(r, 'set_number', 1) for r in rallies]
        max_set = max(set_numbers) if set_numbers else 1
        
        # Get game numbers
        game_numbers = [getattr(r, 'game_number', 1) for r in rallies]
        max_game = max(game_numbers) if game_numbers else 1
        
        # Compute break point stats
        bp_serving = [r for r in rallies if getattr(r, 'is_break_point', False) and getattr(r, 'serving', False)]
        bp_returning = [r for r in rallies if getattr(r, 'is_break_point', False) and not getattr(r, 'serving', False)]
        
        bp_saved = len([r for r in bp_serving if r.outcome == 'won'])
        bp_converted = len([r for r in bp_returning if r.outcome == 'won'])
        
        # Compute rally lengths by set
        rally_lengths_by_set = {}
        for set_num in range(1, max_set + 1):
            set_rallies = [r for r in rallies if getattr(r, 'set_number', 1) == set_num]
            if set_rallies:
                avg_length = sum(len(getattr(r, 'shots', [])) for r in set_rallies) / len(set_rallies)
                rally_lengths_by_set[f'set_{set_num}_rally_length'] = avg_length
        
        overall_avg_rally_length = sum(len(getattr(r, 'shots', [])) for r in rallies) / max(len(rallies), 1)
        
        return {
            'set_number': max_set,
            'game_number': max_game,
            'break_points_faced': len(bp_serving),
            'break_points_saved': bp_saved,
            'break_point_chances': len(bp_returning),
            'break_points_converted': bp_converted,
            'average_rally_length': overall_avg_rally_length,
            **rally_lengths_by_set
        }
