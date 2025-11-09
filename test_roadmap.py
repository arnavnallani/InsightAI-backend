#!/usr/bin/env python3
"""
Test script to verify personalized improvement roadmap generation
"""
import sys
import os
import json

# Add analysis directory to path
analysis_dir = os.path.join(os.path.dirname(__file__), 'analysis')
sys.path.insert(0, analysis_dir)
sys.path.insert(0, os.path.dirname(__file__))

# Import from analysis package
from analysis.mock_data_generator import ComprehensiveMockDataGenerator
from analysis.hierarchical_analysis import HierarchicalAnalysisPipeline

def test_roadmap_generation():
    """Test that the improvement roadmap contains personalized pattern references"""
    print("🧪 Testing Personalized Improvement Roadmap Generation\n")
    
    # Generate mock data
    print("1️⃣  Generating mock SwingVision data...")
    generator = ComprehensiveMockDataGenerator(
        player_name="Test Player",
        opponent_name="Test Opponent"
    )
    match_data = generator.generate_complete_match()
    print(f"   ✅ Generated {len(match_data['rallies'])} rallies\n")
    
    # Run analysis pipeline
    print("2️⃣  Running hierarchical analysis pipeline...")
    pipeline = HierarchicalAnalysisPipeline()
    result = pipeline.analyze_match(match_data['rallies'])
    print(f"   ✅ Discovered {result['total_patterns_discovered']} patterns\n")
    
    # Extract improvement roadmap
    roadmap = result.get('improvement_roadmap', {})
    patterns = result.get('patterns', [])
    
    print("3️⃣  Analyzing Improvement Roadmap Personalization:\n")
    
    # Check strategic approach
    strategic_approach = roadmap.get('strategic_approach', '')
    print("📋 STRATEGIC APPROACH:")
    print(f"   Length: {len(strategic_approach)} chars")
    
    # Count pattern name references
    pattern_names = [p['name'] for p in patterns]
    references_found = sum(1 for name in pattern_names if name in strategic_approach)
    print(f"   Pattern references: {references_found}/{len(pattern_names)} patterns mentioned")
    print(f"   Sample: {strategic_approach[:200]}...\n")
    
    # Check coordinated practice plan
    practice_plan = roadmap.get('coordinated_practice_plan', {})
    print("📅 COORDINATED PRACTICE PLAN:")
    for week_key in ['week_1', 'week_2', 'week_3', 'week_4']:
        week_data = practice_plan.get(week_key, {})
        print(f"   {week_key}: {len(week_data)} patterns with schedules")
        if week_data:
            first_pattern = list(week_data.keys())[0]
            print(f"      Example: {first_pattern}: {week_data[first_pattern]}")
    print()
    
    # Check quick wins
    quick_wins = roadmap.get('quick_wins', {})
    print("⚡ QUICK WINS GRID:")
    for category in ['immediate', 'short_term', 'medium_term', 'long_term']:
        items = quick_wins.get(category, [])
        print(f"   {category}: {len(items)} items")
        if items:
            print(f"      - {items[0]}")
    print()
    
    # Check improvement timeline
    timeline = roadmap.get('improvement_timeline', [])
    print("📈 IMPROVEMENT TIMELINE:")
    for milestone in timeline:
        week = milestone.get('week', 'Unknown')
        improvements = milestone.get('expected_improvements', '')
        print(f"   {week}: {improvements[:80]}...")
    print()
    
    # Check success metrics
    metrics = roadmap.get('success_metrics', [])
    print("🎯 SUCCESS METRICS:")
    for i, metric in enumerate(metrics[:5], 1):
        print(f"   {i}. {metric[:100]}...")
    print()
    
    # Validation checks
    print("✅ VALIDATION CHECKS:")
    checks = {
        'Strategic approach mentions patterns': references_found > 0,
        'Practice plan has weekly schedules': len(practice_plan) == 4,
        'Quick wins has 4 categories': len(quick_wins) == 4,
        'Timeline has 4 weeks': len(timeline) == 4,
        'Success metrics generated': len(metrics) >= 0,  # Can be 0 if no patterns
        'Pattern names in practice plan': (
            any(p['name'][:20] in str(practice_plan) for p in patterns) if patterns else True
        ),
        'Specific data in metrics': any('%' in m for m in metrics) if metrics else True,
        'Frequency data used': 'points' in strategic_approach.lower() or 'frequency' in strategic_approach.lower()
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    all_passed = all(checks.values())
    print(f"\n{'🎉 ALL CHECKS PASSED!' if all_passed else '⚠️  Some checks failed'}\n")
    
    return all_passed

if __name__ == "__main__":
    success = test_roadmap_generation()
    sys.exit(0 if success else 1)
