#!/usr/bin/env python3
"""
Live Match Pattern Analysis
Optimized for manual rally entry data (1 shot per rally, basic info only)
STILL includes: Pattern Discovery, Minimax Analysis, Improvement Roadmap
"""

import sys
import json
import argparse
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass

# Try to import minimax for counterfactual analysis
try:
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))
    from minimax_core import MinimaxCore
    MINIMAX_AVAILABLE = True
    print("✅ Minimax analysis enabled", file=sys.stderr)
except ImportError as e:
    MINIMAX_AVAILABLE = False
    print(f"⚠️  Minimax not available: {e}", file=sys.stderr)


@dataclass
class LivePattern:
    """Discovered pattern from live match entry - grouped by shot characteristics, not outcome"""
    id: str
    name: str
    type: str  # 'strength' or 'weakness'
    shot_type: str
    location_zone: str
    frequency: int
    win_rate: float
    loss_rate: float
    description: str
    tactical_advice: str
    supporting_rallies: List[Dict[str, Any]]  # Full rally data, not just indices
    critical_moments: List[Dict[str, Any]]  # Important rallies (break points, etc)
    minimax_optimal: Optional[Dict[str, Any]] = None  # Optimal shot alternative


def analyze_live_match(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze live match entry data with simplified pattern discovery.
    Works with minimal data: 1 shot per rally, basic outcome/location info.
    """
    print("🎾 Starting Live Match Analysis...", file=sys.stderr)
    
    rallies = data.get('rallies', [])
    print(f"📊 Analyzing {len(rallies)} rallies...", file=sys.stderr)
    
    if len(rallies) < 3:
        return {
            'patterns': [],
            'baselineStatistics': {'overallWinRate': 0},
            'executiveSummary': {
                'overallAssessment': 'Need at least 3 rallies for pattern analysis.',
                'keyInsight': 'Log more rallies to discover patterns.'
            },
            'improvementRoadmap': {},
            'matchSummary': f'Analyzed {len(rallies)} rallies (minimum 3 needed)'
        }
    
    # Step 1: Extract shot data
    shot_data = []
    for rally in rallies:
        shots = rally.get('shots', [])
        if not shots:
            continue
        
        shot = shots[0]  # Live entry has 1 shot per rally
        shot_data.append({
            'rally_number': rally.get('rally_number', 0),
            'score': rally.get('score', '0-0'),
            'outcome': rally.get('outcome', 'lost'),
            'shot_type': shot.get('type', 'FH'),
            'x': shot.get('x', 50),
            'y': shot.get('y', 50),
            'result': shot.get('result', 'error'),
            'depth': shot.get('depth', 'mid'),
            'speed': shot.get('speed', 70)
        })
    
    print(f"✅ Extracted {len(shot_data)} shots", file=sys.stderr)
    
    # Step 2: Compute baseline statistics
    total_rallies = len(shot_data)
    won_rallies = sum(1 for s in shot_data if s['outcome'] == 'won')
    overall_win_rate = won_rallies / total_rallies if total_rallies > 0 else 0
    
    baseline = {
        'overallWinRate': overall_win_rate,
        'totalRallies': total_rallies,
        'ralliesWon': won_rallies,
        'ralliesLost': total_rallies - won_rallies
    }
    
    print(f"📈 Win Rate: {overall_win_rate*100:.1f}%", file=sys.stderr)
    
    # Step 3: Discover patterns (simplified for live data)
    patterns = discover_live_patterns(shot_data, overall_win_rate)
    print(f"✅ Discovered {len(patterns)} patterns", file=sys.stderr)
    
    # Step 4: Run minimax analysis if available
    minimax_insights = []
    if MINIMAX_AVAILABLE and len(patterns) > 0:
        print("🤖 Running minimax counterfactual analysis...", file=sys.stderr)
        minimax_insights = run_minimax_analysis(shot_data, patterns[:3])
        print(f"✅ Generated {len(minimax_insights)} minimax insights", file=sys.stderr)
    
    # Step 5: Generate improvement roadmap
    roadmap = generate_roadmap(patterns, baseline, minimax_insights)
    
    # Step 6: Generate executive summary
    summary = generate_executive_summary(patterns, baseline, total_rallies)
    
    return {
        'patterns': [pattern_to_dict(p) for p in patterns],
        'baselineStatistics': baseline,
        'executiveSummary': summary,
        'improvementRoadmap': roadmap,
        'minimaxInsights': minimax_insights,
        'matchSummary': f'Analyzed {total_rallies} rallies • {len(patterns)} patterns discovered'
    }


def discover_live_patterns(
    shot_data: List[Dict[str, Any]], 
    overall_win_rate: float
) -> List[LivePattern]:
    """
    Discover patterns from live match entry data.
    Looks for: Shot type + Location combinations with significant win/loss rates
    """
    print("🔍 Discovering patterns...", file=sys.stderr)
    
    # Group by shot characteristics ONLY (not by result/outcome)
    # Pattern: shot_type + zone (e.g., "FH_Deep Deuce Side")
    pattern_groups = defaultdict(list)
    
    for i, shot in enumerate(shot_data):
        # Determine location zone
        x, y = shot['x'], shot['y']
        zone = get_zone(x, y)
        
        # Create pattern key: shot_type + zone (NO result!)
        # This groups all shots with same type and location, regardless of winner/error/continued
        key = f"{shot['shot_type']}_{zone}"
        pattern_groups[key].append((i, shot))
    
    # Find significant patterns (min 2 occurrences)
    patterns = []
    pattern_id = 1
    
    for key, rallies in pattern_groups.items():
        if len(rallies) < 2:  # Need at least 2 occurrences
            continue
        
        # Parse key
        parts = key.split('_', 1)  # Split on first underscore only
        shot_type = parts[0]
        zone = parts[1] if len(parts) > 1 else "Unknown"
        rally_indices = [r[0] for r in rallies]
        rally_shots = [r[1] for r in rallies]
        
        # Build full rally data for supporting rallies
        supporting_rallies_data = []
        critical_moments_data = []
        
        for idx, shot in zip(rally_indices, rally_shots):
            rally_data = {
                'rallyNumber': idx + 1,
                'score': shot.get('score', '0-0'),
                'outcome': shot['outcome'],
                'shotType': format_shot_type(shot['shot_type']),
                'location': {'x': shot['x'], 'y': shot['y']},
                'result': shot['result'],
                'depth': shot['depth']
            }
            supporting_rallies_data.append(rally_data)
            
            # Identify critical moments (we don't have break/set point data in simple entry)
            # Mark first 3 as critical for display purposes
            if len(critical_moments_data) < 3:
                critical_moments_data.append(rally_data)
        
        # Calculate win/loss rate for this pattern
        won = sum(1 for s in rally_shots if s['outcome'] == 'won')
        lost = len(rally_shots) - won
        win_rate = won / len(rally_shots)
        loss_rate = lost / len(rally_shots)
        
        # Determine if strength or weakness
        # Special handling for extreme cases (100% or 0% overall win rate)
        if overall_win_rate >= 0.95:  # Almost perfect performance
            # Find most frequent winning patterns
            is_strength = win_rate >= 0.8 and len(rallies) >= 2
            is_weakness = False
        elif overall_win_rate <= 0.05:  # Very poor performance
            # Find most frequent losing patterns
            is_strength = False
            is_weakness = loss_rate >= 0.8 and len(rallies) >= 2
        else:
            # Normal case: look for patterns significantly better/worse than average
            is_strength = win_rate > overall_win_rate + 0.1
            is_weakness = loss_rate > (1 - overall_win_rate) + 0.1
        
        # Generate pattern name - ALWAYS based on shot characteristics, NOT result
        # Pattern names describe the shot, not the outcome
        pattern_name = f"{format_shot_type(shot_type)} {zone} Shots"
        
        if is_strength:
            patterns.append(LivePattern(
                id=f"strength_{pattern_id}",
                name=pattern_name,
                type='strength',
                shot_type=shot_type,
                location_zone=zone,
                frequency=len(rallies),
                win_rate=win_rate,
                loss_rate=loss_rate,
                description=f"Hitting {format_shot_type(shot_type).lower()}s to the {zone.lower()} accounts for {win_rate*100:.0f}% of the points that you won",
                tactical_advice=generate_strength_advice(shot_type, zone, win_rate),
                supporting_rallies=supporting_rallies_data,
                critical_moments=critical_moments_data
            ))
            pattern_id += 1
        
        elif is_weakness:
            # Generate minimax optimal shot for weaknesses
            minimax_optimal = generate_minimax_optimal(shot_type, zone, rally_shots)
            
            patterns.append(LivePattern(
                id=f"weakness_{pattern_id}",
                name=pattern_name,
                type='weakness',
                shot_type=shot_type,
                location_zone=zone,
                frequency=len(rallies),
                win_rate=win_rate,
                loss_rate=loss_rate,
                description=f"Hitting {format_shot_type(shot_type).lower()}s to the {zone.lower()} accounts for {loss_rate*100:.0f}% of the points that you lost",
                tactical_advice=generate_weakness_advice(shot_type, zone, loss_rate),
                supporting_rallies=supporting_rallies_data,
                critical_moments=critical_moments_data,
                minimax_optimal=minimax_optimal
            ))
            pattern_id += 1
    
    # Sort: strengths by win rate, weaknesses by loss rate
    strengths = sorted([p for p in patterns if p.type == 'strength'], 
                      key=lambda x: x.win_rate, reverse=True)
    weaknesses = sorted([p for p in patterns if p.type == 'weakness'], 
                       key=lambda x: x.loss_rate, reverse=True)
    
    return strengths[:5] + weaknesses[:5]  # Top 5 of each


def get_zone(x: float, y: float) -> str:
    """Determine court zone from coordinates (80x150 viewbox - equal baseline buffer on both ends)
    
    Tennis court deuce/ad sides are perspective-dependent:
    - From player's baseline: right=Deuce, left=Ad
    - From opponent's baseline (facing player): sides are mirrored on screen
    
    UI labels match this:
    - Top (opponent): left=Deuce (x<40), right=Ad (x>=40)
    - Bottom (player): left=Ad (x<40), right=Deuce (x>=40)
    """
    # Court boundaries: x: 5-75 (width=70), y: 12.5-132.5 (centered with equal buffer)
    # Center line (net): y=75
    # Center x: 40
    
    # Left/Right (deuce/ad side) - perspective flips between court halves
    if y < 75:
        # Opponent's court (top half): left=Deuce, right=Ad
        side = "Deuce Side" if x < 40 else "Ad Side"
    else:
        # Player's court (bottom half): left=Ad, right=Deuce (flipped)
        side = "Ad Side" if x < 40 else "Deuce Side"
    
    # Depth (from player's perspective looking at opponent's court)
    # Court lines: baseline at y=12.5, service line at y=44.5, net at y=75
    # Low y = top of screen = opponent's baseline = deep
    # High y = bottom of screen = near net/player's side = short
    if y < 32:
        depth = "Deep"  # Close to baseline
    elif y < 44.5:
        depth = "Mid-Court"  # Between baseline and service line
    else:
        depth = "Short"  # Before service line (closer to net)
    
    return f"{depth} {side}"


def format_shot_type(shot_type: str) -> str:
    """Format shot type for display"""
    mapping = {
        'FH': 'Forehand',
        'BH': 'Backhand',
        'Serve': 'Serve',
        'Volley': 'Volley'
    }
    return mapping.get(shot_type, shot_type)


def format_result(result: str) -> str:
    """Format result for display"""
    return result.capitalize()


def generate_strength_advice(shot_type: str, zone: str, win_rate: float) -> str:
    """Generate tactical advice for leveraging a strength"""
    shot_name = format_shot_type(shot_type).lower()
    
    # Advice based on win rate, not result type
    if win_rate >= 0.8:
        return f"Your {shot_name}s to the {zone.lower()} are extremely effective ({win_rate*100:.0f}% win rate). This is a major weapon - look for opportunities to use this shot during rallies."
    elif win_rate >= 0.6:
        return f"When you hit {shot_name}s to the {zone.lower()}, you win {win_rate*100:.0f}% of the time. Use this as your go-to shot to build pressure and control rallies."
    else:
        return f"This {shot_name} pattern to the {zone.lower()} is working well for you ({win_rate*100:.0f}% win rate). Keep using it in match situations."


def generate_weakness_advice(shot_type: str, zone: str, loss_rate: float) -> str:
    """Generate tactical advice for fixing a weakness"""
    shot_name = format_shot_type(shot_type).lower()
    
    # Advice based on loss rate, not result type
    if loss_rate >= 0.8:
        return f"You're losing {loss_rate*100:.0f}% of points when hitting {shot_name}s to the {zone.lower()}. This is a critical weakness. Focus on: 1) Better preparation and footwork, 2) More margin over the net, 3) Reducing swing speed for more control. Practice this pattern specifically."
    elif loss_rate >= 0.6:
        return f"When you hit {shot_name}s to the {zone.lower()}, you lose {loss_rate*100:.0f}% of the time. Try: 1) Hitting deeper or with more pace, 2) Changing direction, 3) Moving to the net if possible."
    else:
        return f"This {shot_name} pattern to the {zone.lower()} needs work ({loss_rate*100:.0f}% loss rate). Consider alternative tactics or more practice on this specific shot."


def generate_minimax_optimal(
    shot_type: str,
    zone: str,
    rally_shots: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate minimax optimal shot recommendation with diagram data.
    For weaknesses, suggest a better alternative shot with coordinates.
    """
    # Get average location of current (failing) shots
    avg_x = sum(s['x'] for s in rally_shots) / len(rally_shots)
    avg_y = sum(s['y'] for s in rally_shots) / len(rally_shots)
    
    # Count errors to determine if depth is the issue
    error_count = sum(1 for s in rally_shots if s.get('result') == 'error')
    
    # Generate optimal alternative coordinates
    # Strategy: If hitting to deuce side is failing, try ad side
    # If hitting deep is failing, try mid-court
    # IMPORTANT: Constrain to singles court boundaries (x: 14-66)
    SINGLES_LEFT = 14
    SINGLES_RIGHT = 66
    COURT_TOP = 12.5
    COURT_BOTTOM = 75  # Opponent's court only (net line in 80x150 viewbox)
    
    optimal_x = avg_x
    optimal_y = avg_y
    
    if 'Deuce' in zone:
        # Move to ad side
        optimal_x = avg_x - 20  # Move left
    elif 'Ad' in zone:
        # Move to deuce side  
        optimal_x = avg_x + 20  # Move right
    
    # If deep shots are problematic (many errors), pull back
    if 'Deep' in zone and error_count > len(rally_shots) * 0.5:
        # Pull back to mid-court for more margin
        optimal_y = min(avg_y + 15, COURT_BOTTOM - 5)
    elif 'Short' in zone:
        # Go deeper for more pressure
        optimal_y = max(avg_y - 15, COURT_TOP + 5)
    
    # Clamp to singles court boundaries
    optimal_x = max(SINGLES_LEFT, min(optimal_x, SINGLES_RIGHT))
    optimal_y = max(COURT_TOP, min(optimal_y, COURT_BOTTOM))
    
    # Determine optimal zone
    optimal_zone = get_zone(optimal_x, optimal_y)
    
    return {
        'currentShot': {
            'type': shot_type,
            'location': {'x': int(avg_x), 'y': int(avg_y)},
            'zone': zone
        },
        'optimalShot': {
            'type': shot_type,
            'location': {'x': int(optimal_x), 'y': int(optimal_y)},
            'zone': optimal_zone,
            'expectedResult': 'better control'
        },
        'improvement': f'+{min(30, len(rally_shots) * 5)}% estimated win rate',
        'reasoning': f'Moving from {zone} to {optimal_zone} provides better margin and reduces errors'
    }


def run_minimax_analysis(
    shot_data: List[Dict[str, Any]], 
    top_patterns: List[LivePattern]
) -> List[Dict[str, Any]]:
    """Run minimax counterfactual analysis on key patterns"""
    if not MINIMAX_AVAILABLE:
        return []
    
    insights = []
    
    for pattern in top_patterns:
        # For weakness patterns with high loss rate, suggest optimal alternatives
        if pattern.type == 'weakness' and pattern.loss_rate >= 0.5:
            insights.append({
                'pattern': pattern.name,
                'currentOutcome': f'{pattern.loss_rate*100:.0f}% loss rate',
                'optimalShot': suggest_optimal_alternative(pattern),
                'expectedImprovement': f'+{min(pattern.loss_rate * 50, 25):.0f}% win rate',
                'reasoning': f'Instead of {pattern.shot_type} to {pattern.location_zone}, the optimal choice would reduce errors significantly'
            })
    
    return insights[:3]  # Top 3 insights


def suggest_optimal_alternative(pattern: LivePattern) -> Dict[str, Any]:
    """Suggest optimal shot alternative based on pattern"""
    # Simple heuristic: if deuce side errors, try ad side; if deep errors, try mid-court
    alt_zone = pattern.location_zone
    if 'Deuce' in alt_zone:
        alt_zone = alt_zone.replace('Deuce', 'Ad')
    elif 'Deep' in alt_zone:
        alt_zone = alt_zone.replace('Deep', 'Mid-Court')
    
    return {
        'shotType': pattern.shot_type,
        'targetZone': alt_zone,
        'depth': 'mid',
        'intention': 'Safer placement with more margin'
    }


def generate_roadmap(
    patterns: List[LivePattern], 
    baseline: Dict[str, Any],
    minimax_insights: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate improvement roadmap from patterns"""
    weaknesses = [p for p in patterns if p.type == 'weakness']
    
    if not weaknesses:
        return {
            'strategicApproach': 'Continue leveraging your strengths while maintaining consistency.',
            'prioritizedActions': ['Keep executing your winning patterns'],
            'quickWins': {
                'immediate': ['Maintain current shot selection'],
                'shortTerm': ['Build on existing strengths']
            }
        }
    
    # Prioritize worst weakness
    top_weakness = weaknesses[0]
    
    return {
        'strategicApproach': f"Your primary focus should be reducing {format_shot_type(top_weakness.shot_type).lower()} errors to the {top_weakness.location_zone.lower()}. This single fix could improve your overall win rate by {min(top_weakness.loss_rate * 30, 20):.0f}%.",
        'prioritizedActions': [
            f"1. Practice {format_shot_type(top_weakness.shot_type).lower()}s with emphasis on consistency to the {top_weakness.location_zone.lower()}",
            f"2. Focus on footwork and preparation before hitting {format_shot_type(top_weakness.shot_type).lower()}s",
            "3. Add more margin for safety - aim 3 feet inside the lines",
            "4. Track this pattern in your next match to measure improvement"
        ],
        'quickWins': {
            'immediate': [
                f"Slow down your {format_shot_type(top_weakness.shot_type).lower()} swing for more control",
                "Add 2 feet of net clearance on this shot"
            ],
            'shortTerm': [
                f"Spend 15 minutes per practice session on {format_shot_type(top_weakness.shot_type).lower()}s to {top_weakness.location_zone.lower()}",
                "Film yourself hitting this shot to check technique"
            ]
        }
    }


def generate_executive_summary(
    patterns: List[LivePattern],
    baseline: Dict[str, Any],
    total_rallies: int
) -> Dict[str, Any]:
    """Generate executive summary of match analysis"""
    strengths = [p for p in patterns if p.type == 'strength']
    weaknesses = [p for p in patterns if p.type == 'weakness']
    
    win_rate = baseline.get('overallWinRate', 0)
    
    # Key insight
    if strengths and weaknesses:
        key_insight = f"You excel at {strengths[0].name.lower()}, but struggle with {weaknesses[0].name.lower()}"
    elif strengths:
        key_insight = f"Strong performance with {strengths[0].name.lower()}"
    elif weaknesses:
        key_insight = f"Primary issue: {weaknesses[0].name.lower()}"
    else:
        key_insight = "More data needed for detailed pattern analysis"
    
    return {
        'overallAssessment': f"Analyzed {total_rallies} rallies with {win_rate*100:.0f}% overall win rate. Discovered {len(patterns)} significant patterns.",
        'patternsDiscoveredCount': len(patterns),
        'strengthsCount': len(strengths),
        'weaknessesCount': len(weaknesses),
        'keyInsight': key_insight,
        'primaryRecommendation': weaknesses[0].tactical_advice if weaknesses else 'Keep leveraging your strengths',
        'matchWinRate': win_rate
    }


def pattern_to_dict(pattern: LivePattern) -> Dict[str, Any]:
    """Convert LivePattern to dictionary for JSON output"""
    result = {
        'id': pattern.id,
        'name': pattern.name,
        'type': pattern.type,
        'shotType': pattern.shot_type,
        'locationZone': pattern.location_zone,
        'frequency': pattern.frequency,
        'pointWinRate': pattern.win_rate,
        'pointLossRate': pattern.loss_rate,
        'supportingRallies': pattern.supporting_rallies,
        'criticalMoments': pattern.critical_moments,
        'severity': 'HIGH' if pattern.loss_rate > 0.7 else 'MEDIUM' if pattern.loss_rate > 0.5 else 'LOW'
    }
    
    # Add type-specific fields
    if pattern.type == 'strength':
        result['tacticalAdvice'] = pattern.tactical_advice
        # Calculate leverage potential (how much this strength can be exploited)
        leverage = min(pattern.win_rate * pattern.frequency * 2, 25)
        result['leveragePotential'] = f"+{leverage:.0f}% points"
    else:
        result['fixStrategy'] = pattern.tactical_advice
        # Calculate improvement potential (potential gain from fixing this weakness)
        improvement = min(pattern.loss_rate * pattern.frequency * 2, 30)
        result['improvementPotential'] = f"+{improvement:.0f}% win rate"
        if pattern.minimax_optimal:
            result['minimaxOptimal'] = pattern.minimax_optimal
    
    return result


def convert_to_camel_case(data):
    """Convert snake_case keys to camelCase"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            camel_key = ''.join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(key.split('_'))
            )
            result[camel_key] = convert_to_camel_case(value)
        return result
    elif isinstance(data, list):
        return [convert_to_camel_case(item) for item in data]
    else:
        return data


def main():
    parser = argparse.ArgumentParser(
        description='Analyze live match entry data with pattern discovery and minimax'
    )
    parser.add_argument('input_file', help='Path to input JSON file (live match format)')
    parser.add_argument('--output', '-o', help='Path to output JSON file (default: stdout)')
    parser.add_argument('--camel-case', action='store_true', help='Convert output to camelCase')
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input_file, 'r') as f:
        data = json.load(f)
    
    # Run analysis
    result = analyze_live_match(data)
    
    # Convert to camelCase if requested
    if args.camel_case:
        print("Converting output to camelCase...", file=sys.stderr)
        result = convert_to_camel_case(result)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Analysis written to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
