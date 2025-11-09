"""
ORGANIC PATTERN DISCOVERY ENGINE
==================================
Revolutionary tennis analysis that discovers behavioral patterns from pure SwingVision data.

Input: Raw shot statistics (type, speed, trajectory, spin, placement, result, handedness)
Output: Discovered patterns (strengths + weaknesses) with professional coaching narratives

NO PRE-INJECTED PATTERNS - Pure statistical and behavioral analysis.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pattern_utils import (
    Rally, Shot,
    compute_baseline_statistics,
    classify_shot_direction, classify_shot_depth,
    is_attacking_shot, is_defensive_shot,
    tag_pressure_rallies, calculate_leverage_score,
    find_short_balls, find_serve_opportunities,
    calculate_win_rate, calculate_comparative_stats,
    calculate_speed_stats, compare_shot_speeds,
    calculate_trajectory_distribution,
    analyze_serve_placement,
    meets_minimum_sample_size, calculate_significance_score
)

from content_generators import (
    generate_description,
    generate_pattern_behavior,
    generate_professional_strategy,
    generate_drills,
    generate_practice_schedule,
    generate_improvement_roadmap
)

try:
    from minimax_adapter import SimplifiedMinimaxAdapter
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False
    print("Warning: minimax_adapter not available, counterfactual analysis disabled", file=sys.stderr)


# ============================================================================
# PATTERN DATA STRUCTURES
# ============================================================================

@dataclass
class DiscoveredPattern:
    """Pattern discovered by analysis engine"""
    pattern_id: str
    name: str
    type: str  # "strength" or "weakness"
    severity: str  # "high", "medium", "low" for weaknesses; "strength" for strengths
    frequency: int
    significance_score: float = 0.0
    
    # Win/loss rates
    point_win_rate: Optional[float] = None  # For strengths (percentage)
    point_loss_rate: Optional[float] = None  # For weaknesses (percentage)
    improvement_potential: Optional[float] = None  # For weaknesses
    leverage_potential: Optional[float] = None  # For strengths
    
    # Statistical evidence
    statistical_signature: Dict[str, Any] = field(default_factory=dict)
    supporting_rallies: List[Rally] = field(default_factory=list)
    critical_moments: List[Rally] = field(default_factory=list)
    
    # Generated coaching content
    description: str = ""
    pattern_behavior: str = ""
    professional_strategy: Dict[str, Any] = field(default_factory=dict)
    drills: List[Dict[str, Any]] = field(default_factory=list)
    strength_connection: Optional[Dict[str, str]] = None  # For weaknesses only


# ============================================================================
# PATTERN DISCOVERY ENGINE
# ============================================================================

class OrganicPatternDiscovery:
    """
    Discovers tennis patterns from raw SwingVision data using statistical analysis.
    
    Initial implementation: 6 representative patterns
    - 3 Weaknesses: Serve predictability, Pressure conservatism, Missed attacks
    - 3 Strengths: Forehand DTL aggression, Deep crosscourt control, Serve to T
    """
    
    def __init__(
        self,
        minimax_depth_supporting: int = 2,
        minimax_depth_critical: int = 3,
        minimax_branching: int = 3,
        minimax_rollouts_supporting: int = 10,
        minimax_rollouts_critical: int = 15
    ):
        """
        Initialize pattern discovery engine with minimax parameters.
        
        Args:
            minimax_depth_supporting: Depth for supporting rally analysis (default: 2)
            minimax_depth_critical: Depth for critical moment analysis (default: 3)
            minimax_branching: Branching factor for minimax (default: 3)
            minimax_rollouts_supporting: Monte Carlo rollouts for supporting (default: 10)
            minimax_rollouts_critical: Monte Carlo rollouts for critical (default: 15)
        """
        self.minimax_depth_supporting = minimax_depth_supporting
        self.minimax_depth_critical = minimax_depth_critical
        self.minimax_branching = minimax_branching
        self.minimax_rollouts_supporting = minimax_rollouts_supporting
        self.minimax_rollouts_critical = minimax_rollouts_critical
        
        # Initialize minimax adapter if available
        if MINIMAX_AVAILABLE:
            self.minimax_adapter = SimplifiedMinimaxAdapter(
                depth_supporting=minimax_depth_supporting,
                depth_critical=minimax_depth_critical,
                branching=minimax_branching,
                rollouts_supporting=minimax_rollouts_supporting,
                rollouts_critical=minimax_rollouts_critical
            )
        else:
            self.minimax_adapter = None
        
    def analyze_match(self, rallies_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main analysis pipeline - discovers patterns from raw SwingVision data.
        
        Args:
            rallies_data: List of rally dictionaries from SwingVision
            
        Returns:
            Complete analysis with discovered patterns
        """
        # Convert to Rally objects
        rallies = [Rally(r) for r in rallies_data]
        
        # Step 1: Compute baseline statistics
        baseline_stats = compute_baseline_statistics(rallies)
        
        # Step 2: Detect weakness patterns (initial 3)
        weakness_patterns = []
        weakness_patterns.extend(self._detect_serve_predictability(rallies, baseline_stats))
        weakness_patterns.extend(self._detect_pressure_conservatism(rallies, baseline_stats))
        weakness_patterns.extend(self._detect_missed_attacks(rallies, baseline_stats))
        
        # Step 3: Detect strength patterns (initial 3)
        strength_patterns = []
        strength_patterns.extend(self._detect_forehand_dtl_aggression(rallies, baseline_stats))
        strength_patterns.extend(self._detect_deep_crosscourt_control(rallies, baseline_stats))
        strength_patterns.extend(self._detect_serve_to_t_dominance(rallies, baseline_stats))
        
        # Step 4: Calculate significance scores
        for pattern in weakness_patterns + strength_patterns:
            impact_rate = pattern.point_loss_rate if pattern.type == 'weakness' else pattern.point_win_rate
            pattern.significance_score = calculate_significance_score(
                frequency=pattern.frequency,
                impact_rate=impact_rate / 100 if impact_rate else 0.5,
                leverage_avg=5.0  # Default leverage
            )
        
        # Step 5: Select top patterns (for now, keep all since we only have 6)
        all_patterns = strength_patterns + weakness_patterns
        top_patterns = sorted(all_patterns, key=lambda p: p.significance_score, reverse=True)
        
        # Step 6: Apply minimax counterfactual analysis to rallies
        for pattern in all_patterns:
            # Apply to supporting rallies
            pattern.supporting_rallies = self._apply_minimax_to_rallies(
                pattern.supporting_rallies, 
                is_critical=False
            )
            # Apply to critical moments with deeper analysis
            pattern.critical_moments = self._apply_minimax_to_rallies(
                pattern.critical_moments, 
                is_critical=True
            )
        
        # Step 7: Find strength-weakness connections
        self._connect_weaknesses_to_strengths(weakness_patterns, strength_patterns)
        
        # Step 8: Generate professional coaching content
        for pattern in top_patterns:
            pattern.description = generate_description(pattern, baseline_stats)
            pattern.pattern_behavior = generate_pattern_behavior(pattern)
            pattern.professional_strategy = generate_professional_strategy(pattern)
            pattern.drills = generate_drills(pattern)
        
        # Step 9: Generate improvement roadmap
        improvement_roadmap = generate_improvement_roadmap(top_patterns, baseline_stats)
        
        return {
            'patterns': top_patterns,
            'baseline_statistics': baseline_stats,
            'improvement_roadmap': improvement_roadmap,
            'total_patterns_discovered': len(top_patterns),
            'strengths_count': len(strength_patterns),
            'weaknesses_count': len(weakness_patterns)
        }
    
    def _apply_minimax_to_rallies(
        self, 
        rallies: List[Rally], 
        is_critical: bool = False
    ) -> List[Rally]:
        """
        Apply minimax counterfactual analysis to rallies.
        
        Args:
            rallies: List of Rally objects
            is_critical: If True, use deeper analysis for critical moments
            
        Returns:
            List of Rally objects with minimax_optimal attribute added
        """
        if not self.minimax_adapter:
            return rallies
        
        for rally in rallies:
            # Analyze all rallies with shots (both won and lost for comprehensive coverage)
            if rally.shots:
                # Find your last shot
                your_shots = [i for i, shot in enumerate(rally.shots) if shot.player == 'you']
                if your_shots:
                    last_shot_idx = your_shots[-1]
                    
                    # Run minimax analysis
                    counterfactual = self.minimax_adapter.analyze_rally_counterfactual(
                        rally, 
                        last_shot_idx,
                        is_critical=is_critical
                    )
                    
                    # Add minimax_optimal to rally ONLY if there's meaningful improvement
                    # For won rallies, usually no improvement needed
                    if counterfactual.get('improvement', 0) > 0.05:  # 5%+ improvement
                        # Convert direction string to placement coordinates for visualization
                        direction = counterfactual.get('optimal_shot', {}).get('direction', 'crosscourt')
                        depth = counterfactual.get('optimal_shot', {}).get('depth', 'deep')
                        
                        # Map direction to x coordinate (tennis court is 0-100, left to right)
                        if direction == 'crosscourt':
                            placement_x = 85  # deep deuce side for crosscourt
                        elif direction == 'down-the-line' or direction == 'dtl':
                            placement_x = 15  # deep ad side for DTL
                        else:
                            placement_x = 50  # center
                        
                        # Map depth to y coordinate (0 = opponent baseline, 100 = your baseline)
                        if depth == 'deep':
                            placement_y = 15  # deep near opponent baseline
                        elif depth == 'short':
                            placement_y = 60  # mid court
                        else:
                            placement_y = 30  # medium depth
                        
                        rally.minimax_optimal = {
                            'shotType': counterfactual.get('optimal_shot', {}).get('shot_type', 'Unknown'),
                            'placement': {'x': placement_x, 'y': placement_y},
                            'speed': counterfactual.get('optimal_shot', {}).get('speed'),
                            'reasoning': counterfactual.get('tactical_reasoning', 'Better tactical choice'),
                            'expectedValueImprovement': round(counterfactual.get('improvement', 0) * 100, 1)
                        }
                    else:
                        # Well-executed or won rally - no optimization needed
                        rally.minimax_optimal = None
        
        return rallies
    
    # ========================================================================
    # WEAKNESS PATTERN DETECTORS (Initial 3)
    # ========================================================================
    
    def _detect_serve_predictability(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects predictable serve patterns.
        
        Analysis:
        - Measure serve direction distribution (T, Wide, Body)
        - Detect if >65% of serves go to one location
        - Check if opponent has adapted (tracking across sets)
        
        Example Detection:
        - 68% of serves to T
        - Opponent return win rate increases from Set 1 to Set 3
        → Pattern: Predictable serve to T
        """
        patterns = []
        
        # Get service rallies
        service_rallies = find_serve_opportunities(rallies, serving=True)
        if not meets_minimum_sample_size(service_rallies, minimum=10):
            return patterns
        
        # Analyze serve placement
        serve_stats = analyze_serve_placement(service_rallies)
        
        # DETECTION: One direction >50% (lowered from 65% for realistic detection)
        max_direction_rate = max(serve_stats['t_rate'], serve_stats['wide_rate'], serve_stats['body_rate'])
        
        if max_direction_rate >= 0.50:
            # Determine which direction is predictable
            if serve_stats['t_rate'] == max_direction_rate:
                direction = 'T'
                direction_rallies = serve_stats['serves_t']
                win_rate = serve_stats['t_win_rate']
            elif serve_stats['wide_rate'] == max_direction_rate:
                direction = 'Wide'
                direction_rallies = serve_stats['serves_wide']
                win_rate = serve_stats['wide_win_rate']
            else:
                direction = 'Body'
                direction_rallies = serve_stats['serves_body']
                win_rate = serve_stats['body_win_rate']
            
            # Select supporting rallies and critical moments
            supporting = direction_rallies[:10] if len(direction_rallies) >= 10 else direction_rallies
            critical = [r for r in direction_rallies if r.is_pressure][:2]
            
            pattern = DiscoveredPattern(
                pattern_id='predictable-serve',
                name=f'Predictable Serve Pattern (Too Many to {direction})',
                type='weakness',
                severity='medium' if max_direction_rate < 0.75 else 'high',
                frequency=len(direction_rallies),
                point_loss_rate=(1 - win_rate) * 100,
                improvement_potential=max_direction_rate * 30,  # Estimate: 30% improvement possible
                statistical_signature={
                    'dominant_direction': direction,
                    'direction_rate': max_direction_rate,
                    't_rate': serve_stats['t_rate'],
                    'wide_rate': serve_stats['wide_rate'],
                    'body_rate': serve_stats['body_rate'],
                    'win_rate': win_rate,
                    'total_serves': len(service_rallies)
                },
                supporting_rallies=supporting,
                critical_moments=critical
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_pressure_conservatism(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects conservative play under pressure.
        
        Analysis:
        - Compare shot speeds: pressure points vs normal points
        - Compare trajectory: high balls on pressure vs normal
        - Check win rate differential
        
        Example Detection:
        - Pressure shots 10% slower than normal
        - 23% more high-trajectory balls on pressure
        - Pressure win rate 15% lower than normal
        → Pattern: Conservative under pressure
        """
        patterns = []
        
        # Separate pressure vs normal rallies
        pressure_rallies, normal_rallies = tag_pressure_rallies(rallies)
        
        if not meets_minimum_sample_size(pressure_rallies, minimum=8):
            return patterns
        
        # Compare shot speeds
        speed_comparison = compare_shot_speeds(pressure_rallies, normal_rallies)
        speed_drop_pct = abs(speed_comparison['speed_difference_percent'])
        
        # Compare trajectories
        pressure_traj = calculate_trajectory_distribution(pressure_rallies)
        normal_traj = calculate_trajectory_distribution(normal_rallies)
        high_traj_increase = pressure_traj['high_rate'] - normal_traj['high_rate']
        
        # Win rates
        stats = calculate_comparative_stats(pressure_rallies, normal_rallies)
        
        # DETECTION: Speed drops 5%+ (lowered from 8%) AND high trajectory increases 10%+ (lowered from 15%) AND worse win rate
        if (speed_drop_pct >= 5 and high_traj_increase >= 0.10 and 
            stats['group_a_win_rate'] < stats['group_b_win_rate']):
            
            # Select critical moments (highest leverage pressure points)
            critical = sorted(
                pressure_rallies,
                key=lambda r: calculate_leverage_score(r),
                reverse=True
            )[:2]
            
            pattern = DiscoveredPattern(
                pattern_id='conservative-pressure',
                name='Conservative Play Under Pressure',
                type='weakness',
                severity='high' if speed_drop_pct >= 12 else 'medium',
                frequency=len(pressure_rallies),
                point_loss_rate=stats['group_a_loss_rate'] * 100,
                improvement_potential=(stats['group_b_win_rate'] - stats['group_a_win_rate']) * 100,
                statistical_signature={
                    'speed_drop_percent': speed_drop_pct,
                    'avg_pressure_speed': speed_comparison['group_a_avg'],
                    'avg_normal_speed': speed_comparison['group_b_avg'],
                    'pressure_high_traj_rate': pressure_traj['high_rate'],
                    'normal_high_traj_rate': normal_traj['high_rate'],
                    'high_traj_increase': high_traj_increase,
                    'pressure_win_rate': stats['group_a_win_rate'],
                    'normal_win_rate': stats['group_b_win_rate']
                },
                supporting_rallies=pressure_rallies[:10],
                critical_moments=critical
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_missed_attacks(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects when player fails to attack short balls.
        
        Analysis:
        - Find all short balls (opponent y < 55)
        - Classify response: attacked (speed >75, aggressive) vs defended
        - Compare win rates: attacked vs defended
        
        Example Detection:
        - 38 short balls received
        - Attacked 12 times → 75% win rate
        - Defended 26 times → 27% win rate
        → Pattern: Missed attack opportunities
        """
        patterns = []
        
        # Find all short ball opportunities
        opportunities = find_short_balls(rallies)
        if not meets_minimum_sample_size([r for r, _ in opportunities], minimum=10):
            return patterns
        
        # Classify responses
        attacked_rallies = []
        defended_rallies = []
        
        for rally, short_shot in opportunities:
            # Find your response shot
            short_shot_idx = rally.shots.index(short_shot)
            if short_shot_idx + 1 < len(rally.shots):
                response_shot = rally.shots[short_shot_idx + 1]
                
                if is_attacking_shot(response_shot):
                    attacked_rallies.append(rally)
                else:
                    defended_rallies.append(rally)
        
        if not meets_minimum_sample_size(defended_rallies, minimum=8):
            return patterns
        
        # Calculate comparative stats
        stats = calculate_comparative_stats(attacked_rallies, defended_rallies)
        attack_rate = len(attacked_rallies) / len(opportunities) if opportunities else 0
        
        # DETECTION: Attack rate <50% (lowered from 40%) AND defended win rate <50% (lowered from 45%)
        if attack_rate < 0.50 and stats['group_b_win_rate'] < 0.50:
            # Select high-leverage missed opportunities as critical moments
            critical = sorted(
                defended_rallies,
                key=lambda r: calculate_leverage_score(r),
                reverse=True
            )[:2]
            
            pattern = DiscoveredPattern(
                pattern_id='missed-attacks',
                name='Missed Attack Opportunities on Short Balls',
                type='weakness',
                severity='high',
                frequency=len(defended_rallies),
                point_loss_rate=stats['group_b_loss_rate'] * 100,
                improvement_potential=(stats['group_a_win_rate'] - stats['group_b_win_rate']) * 100,
                statistical_signature={
                    'total_opportunities': len(opportunities),
                    'attacked_count': len(attacked_rallies),
                    'defended_count': len(defended_rallies),
                    'attack_rate': attack_rate,
                    'attacked_win_rate': stats['group_a_win_rate'],
                    'defended_win_rate': stats['group_b_win_rate'],
                    'win_rate_difference': stats['win_rate_difference']
                },
                supporting_rallies=defended_rallies[:10],
                critical_moments=critical
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # STRENGTH PATTERN DETECTORS (Initial 3)
    # ========================================================================
    
    def _detect_forehand_dtl_aggression(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects aggressive forehand down-the-line strength.
        
        Analysis:
        - Find forehand DTL shots (x < 20 for right-handed)
        - Check if aggressive (speed >75, low trajectory)
        - High win rate (>65%)
        
        Example Detection:
        - 18 aggressive FH DTL attempts
        - 72% win rate
        → Strength: Aggressive forehand down-the-line
        """
        patterns = []
        
        # Find forehand DTL rallies
        fh_dtl_rallies = []
        for rally in rallies:
            for shot in rally.shots:
                if (shot.player == 'you' and shot.shot_type == 'Forehand' and 
                    classify_shot_direction(shot) == 'down-the-line' and
                    is_attacking_shot(shot)):
                    fh_dtl_rallies.append(rally)
                    break  # One per rally
        
        if not meets_minimum_sample_size(fh_dtl_rallies, minimum=8):
            return patterns
        
        # Calculate win rate
        win_rate = calculate_win_rate(fh_dtl_rallies)
        
        # DETECTION: Win rate >50% (lowered from 65% for realistic detection)
        if win_rate >= 0.50:
            # Select high-leverage successful rallies as critical moments
            critical = sorted(
                [r for r in fh_dtl_rallies if r.outcome == 'won' and r.is_pressure],
                key=lambda r: calculate_leverage_score(r),
                reverse=True
            )[:2]
            
            pattern = DiscoveredPattern(
                pattern_id='forehand-dtl-aggression',
                name='Aggressive Forehand Down-the-Line',
                type='strength',
                severity='strength',
                frequency=len(fh_dtl_rallies),
                point_win_rate=win_rate * 100,
                leverage_potential=win_rate * 100,
                statistical_signature={
                    'win_rate': win_rate,
                    'total_attempts': len(fh_dtl_rallies),
                    'wins': sum(1 for r in fh_dtl_rallies if r.outcome == 'won')
                },
                supporting_rallies=fh_dtl_rallies[:10],
                critical_moments=critical if critical else fh_dtl_rallies[:2]
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_deep_crosscourt_control(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects deep crosscourt baseline control strength.
        
        Analysis:
        - Find deep crosscourt shots (y >75, x in crosscourt zone)
        - Heavy topspin or medium trajectory
        - High win rate
        
        Example Detection:
        - 24 deep crosscourt rallies
        - 68% win rate
        → Strength: Deep crosscourt control
        """
        patterns = []
        
        # Find deep crosscourt patterns
        deep_cc_rallies = []
        for rally in rallies:
            for shot in rally.shots:
                if (shot.player == 'you' and 
                    shot.shot_type in ['Forehand', 'Backhand'] and
                    classify_shot_depth(shot) == 'deep' and
                    classify_shot_direction(shot) == 'crosscourt'):
                    deep_cc_rallies.append(rally)
                    break
        
        if not meets_minimum_sample_size(deep_cc_rallies, minimum=10):
            return patterns
        
        # Calculate win rate
        win_rate = calculate_win_rate(deep_cc_rallies)
        
        # DETECTION: Win rate >50% (lowered from 60% for realistic detection)
        if win_rate >= 0.50:
            # Select successful pressure point rallies
            critical = sorted(
                [r for r in deep_cc_rallies if r.outcome == 'won' and r.is_pressure],
                key=lambda r: calculate_leverage_score(r),
                reverse=True
            )[:2]
            
            pattern = DiscoveredPattern(
                pattern_id='deep-crosscourt-control',
                name='Deep Crosscourt Control',
                type='strength',
                severity='strength',
                frequency=len(deep_cc_rallies),
                point_win_rate=win_rate * 100,
                leverage_potential=win_rate * 100,
                statistical_signature={
                    'win_rate': win_rate,
                    'total_attempts': len(deep_cc_rallies)
                },
                supporting_rallies=deep_cc_rallies[:10],
                critical_moments=critical if critical else deep_cc_rallies[:2]
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_serve_to_t_dominance(
        self, 
        rallies: List[Rally], 
        baseline: Dict
    ) -> List[DiscoveredPattern]:
        """
        Detects dominant serve to T strength.
        
        Analysis:
        - Find serves to T (x near 50, centerline)
        - High win rate on T serves
        - Effective even if predictable
        
        Example Detection:
        - 42 serves to T
        - 71% win rate
        → Strength: Dominant serve to T
        """
        patterns = []
        
        # Analyze serve placement
        service_rallies = find_serve_opportunities(rallies, serving=True)
        if not meets_minimum_sample_size(service_rallies, minimum=10):
            return patterns
        
        serve_stats = analyze_serve_placement(service_rallies)
        
        # DETECTION: T serves have >55% win rate (lowered from 65%) AND sufficient volume
        if serve_stats['t_count'] >= 10 and serve_stats['t_win_rate'] >= 0.55:
            # Select successful T serves on pressure points
            t_serves = serve_stats['serves_t']
            critical = sorted(
                [r for r in t_serves if r.outcome == 'won' and r.is_pressure],
                key=lambda r: calculate_leverage_score(r),
                reverse=True
            )[:2]
            
            pattern = DiscoveredPattern(
                pattern_id='serve-to-t-dominance',
                name='Dominant Serve to T',
                type='strength',
                severity='strength',
                frequency=serve_stats['t_count'],
                point_win_rate=serve_stats['t_win_rate'] * 100,
                leverage_potential=serve_stats['t_win_rate'] * 100,
                statistical_signature={
                    'win_rate': serve_stats['t_win_rate'],
                    't_count': serve_stats['t_count'],
                    't_rate': serve_stats['t_rate']
                },
                supporting_rallies=t_serves[:10],
                critical_moments=critical if critical else t_serves[:2]
            )
            patterns.append(pattern)
        
        return patterns
    
    # ========================================================================
    # STRENGTH-WEAKNESS CONNECTIONS
    # ========================================================================
    
    def _connect_weaknesses_to_strengths(
        self, 
        weaknesses: List[DiscoveredPattern], 
        strengths: List[DiscoveredPattern]
    ):
        """
        Find logical connections between weaknesses and strengths.
        
        Examples:
        - Fix missed attacks → Use forehand DTL strength more
        - Fix serve predictability → Make T serve strength more effective
        - Fix pressure conservatism → Use deep crosscourt strength confidently
        """
        for weakness in weaknesses:
            if 'attack' in weakness.pattern_id:
                # Fixing missed attacks enables forehand DTL
                fh_strength = next((s for s in strengths if 'forehand' in s.pattern_id), None)
                if fh_strength:
                    weakness.strength_connection = {
                        'enabled_strength': fh_strength.name,
                        'how_it_connects': f"Every short ball you attack becomes an opportunity to use your {fh_strength.name}. Stop defending short balls, start winning with your strength."
                    }
            
            elif 'serve' in weakness.pattern_id and 'predictable' in weakness.pattern_id:
                # Fixing serve variety makes T serve more effective
                serve_strength = next((s for s in strengths if 'serve' in s.pattern_id), None)
                if serve_strength:
                    weakness.strength_connection = {
                        'enabled_strength': serve_strength.name,
                        'how_it_connects': f"Adding serve variety prevents opponents from camping for your T serve. Makes your already-dominant {serve_strength.name} even more effective by keeping opponents guessing."
                    }
            
            elif 'pressure' in weakness.pattern_id or 'conservative' in weakness.pattern_id:
                # Fixing pressure conservatism enables crosscourt strength
                cc_strength = next((s for s in strengths if 'crosscourt' in s.pattern_id), None)
                if cc_strength:
                    weakness.strength_connection = {
                        'enabled_strength': cc_strength.name,
                        'how_it_connects': f"Playing aggressive under pressure means using your {cc_strength.name} on big points. Trust your strength when it matters most."
                    }
    
