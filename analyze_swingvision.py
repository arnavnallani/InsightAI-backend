#!/usr/bin/env python3
"""
SWINGVISION ANALYSIS ENTRY POINT
==================================
Main entry point for AI Tennis Coach pattern discovery analysis.

Called by Node.js Express server with SwingVision match data.
Returns comprehensive AI pattern analysis with:
- 3-7 organically discovered patterns (strengths + weaknesses)
- Professional narratives and tactical strategies
- Pattern-specific drills and practice schedules
- Minimax counterfactual analysis (optional)
- Comprehensive improvement roadmap

USAGE:
    python analyze_swingvision.py <input_json_file> [--output <output_json_file>]

INPUT FORMAT (snake_case):
    {
        "match_metadata": {...},
        "rallies": [...],
        "player_stats": {...}
    }

OUTPUT FORMAT (camelCase for frontend):
    {
        "patterns": [...],
        "executiveSummary": {...},
        "improvementRoadmap": {...},
        "tacticalPlaybook": {...},
        "baselineStatistics": {...}
    }
"""

import sys
import json
import argparse
from typing import Dict, Any, List
import os

# Add analysis directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))

from organic_pattern_discovery import OrganicPatternDiscovery
from hierarchical_analysis import HierarchicalAnalysisPipeline


def convert_snake_to_camel(data: Any) -> Any:
    """
    Convert snake_case keys to camelCase recursively.
    
    Used for transforming Python output to frontend-friendly format.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Convert snake_case to camelCase
            camel_key = ''.join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(key.split('_'))
            )
            result[camel_key] = convert_snake_to_camel(value)
        return result
    elif isinstance(data, list):
        return [convert_snake_to_camel(item) for item in data]
    else:
        return data


def convert_camel_to_snake(data: Any) -> Any:
    """
    Convert camelCase keys to snake_case recursively.
    
    Used for transforming frontend input to Python-friendly format.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Convert camelCase to snake_case
            snake_key = ''.join(
                ['_' + c.lower() if c.isupper() else c for c in key]
            ).lstrip('_')
            result[snake_key] = convert_camel_to_snake(value)
        return result
    elif isinstance(data, list):
        return [convert_camel_to_snake(item) for item in data]
    else:
        return data


def pattern_to_dict(pattern: Any) -> Dict[str, Any]:
    """
    Convert pattern object to dictionary for JSON serialization.
    
    Handles nested Rally and Shot objects, converting them to dicts.
    Patterns from HierarchicalAnalysisPipeline are already dicts.
    """
    # If already a dict, just return it (HierarchicalAnalysisPipeline returns dicts)
    if isinstance(pattern, dict):
        return pattern
    
    # Otherwise convert object to dict (legacy support)
    result = {
        'id': pattern.pattern_id,
        'name': pattern.name,
        'type': pattern.type,
        'severity': pattern.severity,
        'frequency': pattern.frequency,
        'description': pattern.description,
        'patternBehavior': pattern.pattern_behavior,
        'significanceScore': pattern.significance_score
    }
    
    # Add type-specific fields
    if pattern.type == 'strength':
        result['pointWinRate'] = f'{pattern.point_win_rate:.1f}%' if pattern.point_win_rate else '0%'
        result['leveragePotential'] = pattern.leverage_potential or 'Medium'
    else:  # weakness
        result['pointLossRate'] = f'{pattern.point_loss_rate:.1f}%' if pattern.point_loss_rate else '0%'
        result['improvementPotential'] = f'{pattern.improvement_potential:.1f}%' if pattern.improvement_potential else 'Medium'
    
    # Convert supporting rallies to dicts
    result['supporting_rallies'] = [
        rally_to_dict(rally) for rally in pattern.supporting_rallies
    ]
    
    # Convert critical moments to dicts
    if hasattr(pattern, 'critical_moments'):
        result['critical_moments'] = [
            rally_to_dict(rally) for rally in pattern.critical_moments
        ]
    
    # Add professional strategy (required field)
    if hasattr(pattern, 'professional_strategy') and pattern.professional_strategy:
        result['professionalStrategy'] = pattern.professional_strategy
    
    # Add drills (required field)
    if hasattr(pattern, 'drills') and pattern.drills:
        result['drills'] = pattern.drills
    
    # Add practice schedule for weaknesses
    if pattern.type == 'weakness' and hasattr(pattern, 'practice_schedule') and pattern.practice_schedule:
        result['practiceSchedule'] = pattern.practice_schedule
    
    # Add strength connection for weaknesses (required in front_end_base.md)
    if pattern.type == 'weakness' and hasattr(pattern, 'strength_connection') and pattern.strength_connection:
        result['strengthPatternConnection'] = pattern.strength_connection
    
    return result


def rally_to_dict(rally: Any) -> Dict[str, Any]:
    """Convert Rally object to dictionary"""
    result = {
        'set': rally.set_number,
        'gameScore': rally.game_score,
        'pointScore': rally.point_score,
        'serving': rally.server == 'you',  # Convert to boolean
        'outcome': rally.outcome,
        'rallyLength': len(rally.shots),
        'yourCriticalShot': {
            'shotNumber': len(rally.shots) - 1,
            'description': 'Critical decision point',
            'speed': rally.shots[-1].speed if rally.shots else 0,
            'placement': f'x{rally.shots[-1].x}, y{rally.shots[-1].y}' if rally.shots else 'unknown'
        } if rally.shots else None
    }
    
    # Convert shots to dicts
    result['shots'] = [shot_to_dict(shot) for shot in rally.shots]
    
    # Add minimax analysis if available
    if hasattr(rally, 'minimax_optimal') and rally.minimax_optimal:
        result['minimaxOptimal'] = rally.minimax_optimal
    
    # Add importance/butterfly effect for critical moments
    if hasattr(rally, 'importance'):
        result['importance'] = rally.importance
    
    if hasattr(rally, 'butterfly_effect'):
        result['butterflyEffect'] = rally.butterfly_effect
    
    return result


def shot_to_dict(shot: Any) -> Dict[str, Any]:
    """Convert Shot object to dictionary"""
    return {
        'shot_number': shot.shot_number,
        'player': shot.player,
        'shot_type': shot.shot_type,
        'speed': shot.speed,
        'x': shot.x,
        'y': shot.y,
        'trajectory': shot.trajectory,
        'spin': shot.spin,
        'depth': shot.depth,
        'is_winner': shot.is_winner,
        'is_error': shot.is_error,
        'shot_result': shot.shot_result if hasattr(shot, 'shot_result') else None
    }


def analyze_swingvision_data(
    input_data: Dict[str, Any],
    include_minimax: bool = True,
    minimax_depth_supporting: int = 2,
    minimax_depth_critical: int = 3,
    use_hierarchical: bool = True
) -> Dict[str, Any]:
    """
    Main analysis pipeline.
    
    Args:
        input_data: SwingVision match data (snake_case format or camelCase)
        include_minimax: Whether to run minimax counterfactual analysis
        minimax_depth_supporting: Depth for supporting rally analysis
        minimax_depth_critical: Depth for critical moment analysis
        use_hierarchical: Whether to use new hierarchical discovery (default: True)
    
    Returns:
        Complete analysis with patterns, narratives, drills, roadmap (snake_case)
    """
    print("🎾 Starting AI Tennis Coach analysis...", file=sys.stderr)
    
    # Extract rallies (handle both snake_case and camelCase)
    rallies = input_data.get('rallies', input_data.get('rallies', []))
    
    print(f"📊 Analyzing {len(rallies)} rallies...", file=sys.stderr)
    
    if use_hierarchical:
        print("🔍 Using Hierarchical Pattern Discovery Engine...", file=sys.stderr)
        
        # Complete hierarchical analysis pipeline
        pipeline = HierarchicalAnalysisPipeline(
            min_sample_size=10,
            significance_threshold=0.10,  # 10% difference from baseline
            include_minimax=include_minimax,
            minimax_depth_supporting=minimax_depth_supporting,
            minimax_depth_critical=minimax_depth_critical
        )
        
        result = pipeline.analyze_match(rallies)
        
        print("✅ Hierarchical analysis complete!", file=sys.stderr)
        return result
    else:
        # Fall back to old hardcoded system
        print("⚠️  Using legacy hardcoded discovery...", file=sys.stderr)
        discovery = OrganicPatternDiscovery(
            minimax_depth_supporting=minimax_depth_supporting,
            minimax_depth_critical=minimax_depth_critical,
            minimax_branching=3,
            minimax_rollouts_supporting=10,
            minimax_rollouts_critical=15
        )
        
        result = discovery.analyze_match(rallies)
        print("✅ Legacy analysis complete!", file=sys.stderr)
        return result


def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze SwingVision tennis match data with AI pattern discovery'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file (SwingVision format)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Path to output JSON file (default: stdout)',
        default=None
    )
    parser.add_argument(
        '--no-minimax',
        action='store_true',
        help='Disable minimax counterfactual analysis (faster)'
    )
    parser.add_argument(
        '--camel-case',
        action='store_true',
        help='Convert output to camelCase (for frontend)'
    )
    
    args = parser.parse_args()
    
    # Read input data
    try:
        with open(args.input_file, 'r') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert from camelCase if needed (TypeScript → Python)
    if any(key[0].islower() and any(c.isupper() for c in key) for key in input_data.keys()):
        print("Converting input from camelCase to snake_case...", file=sys.stderr)
        input_data = convert_camel_to_snake(input_data)
    
    # Run analysis
    try:
        result = analyze_swingvision_data(
            input_data,
            include_minimax=not args.no_minimax
        )
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Convert patterns to dicts for JSON serialization
    if 'patterns' in result:
        result['patterns'] = [pattern_to_dict(p) for p in result['patterns']]
    
    # Convert to camelCase if requested (Python → TypeScript)
    if args.camel_case:
        print("Converting output to camelCase...", file=sys.stderr)
        result = convert_snake_to_camel(result)
    
    # Write output
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Analysis written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == '__main__':
    main()
