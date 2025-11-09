#!/usr/bin/env python3
"""
Test personalized improvement roadmap with actual pattern data
"""
import sys
import os

# Add analysis directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))

from content_generators import (
    generate_improvement_roadmap,
    generate_strategic_approach,
    generate_coordinated_practice_plan,
    generate_quick_wins_grid,
    generate_improvement_timeline,
    generate_success_metrics
)

# Mock discovered pattern class
class MockPattern:
    def __init__(self, name, pattern_id, pattern_type, frequency, win_rate, statistical_signature=None, strength_connection=None):
        self.name = name
        self.pattern_id = pattern_id
        self.type = pattern_type
        self.frequency = frequency
        self.win_rate = win_rate
        self.point_win_rate = win_rate if pattern_type == 'strength' else 0
        self.point_loss_rate = (1 - win_rate) if pattern_type == 'weakness' else 0
        self.improvement_potential = (1 - win_rate) * 100 if pattern_type == 'weakness' else 0
        self.statistical_signature = statistical_signature or {}
        self.strength_connection = strength_connection
        # Add features for compatibility
        class Features:
            shot_type = pattern_id.split('-')[0] if '-' in pattern_id else None
            direction = None
            depth = None
        self.features = Features()

def test_personalized_roadmap():
    """Test roadmap with realistic discovered patterns"""
    print("🧪 Testing Personalized Improvement Roadmap with Real Pattern Data\n")
    
    # Create realistic discovered patterns
    weaknesses = [
        MockPattern(
            name="Middle Backhand Vulnerability",
            pattern_id="backhand-middle-weak",
            pattern_type="weakness",
            frequency=18,
            win_rate=0.35,  # 65% loss rate
            statistical_signature={
                'avg_speed': 58,
                'depth_rate': 0.42
            },
            strength_connection={
                'enabled_strength': 'Forehand Down-the-Line Aggression',
                'explanation': 'When your backhand is neutralized, you can set up forehand attacks',
                'synergy': 'Better backhand depth → more forehand opportunities'
            }
        ),
        MockPattern(
            name="Predictable Serve Pattern",
            pattern_id="serve-predictable",
            pattern_type="weakness",
            frequency=24,
            win_rate=0.42,  # 58% loss rate
            statistical_signature={
                'dominant_direction': 'T',
                'direction_rate': 0.68,
                'avg_speed': 95
            }
        ),
        MockPattern(
            name="Missed Attack Opportunities",
            pattern_id="missed-attacks",
            pattern_type="weakness",
            frequency=15,
            win_rate=0.27,  # 73% loss rate
            statistical_signature={
                'attack_rate': 0.32,
                'attacked_win_rate': 0.75,
                'defended_win_rate': 0.27,
                'total_opportunities': 47
            }
        ),
        MockPattern(
            name="Pressure Point Conservatism",
            pattern_id="conservative-pressure",
            pattern_type="weakness",
            frequency=12,
            win_rate=0.33,  # 67% loss rate
            statistical_signature={
                'speed_drop_percent': 12,
                'high_traj_increase': 0.48
            }
        )
    ]
    
    strengths = [
        MockPattern(
            name="Forehand Down-the-Line Aggression",
            pattern_id="forehand-dtl-aggression",
            pattern_type="strength",
            frequency=12,
            win_rate=0.75,
            statistical_signature={
                'avg_speed': 72,
                'win_rate': 0.75
            }
        ),
        MockPattern(
            name="Deep Crosscourt Control",
            pattern_id="deep-crosscourt-control",
            pattern_type="strength",
            frequency=28,
            win_rate=0.68,
            statistical_signature={
                'depth_rate': 0.82,
                'win_rate': 0.68
            }
        ),
        MockPattern(
            name="Serve to T Dominance",
            pattern_id="serve-to-t-dominance",
            pattern_type="strength",
            frequency=16,
            win_rate=0.71,
            statistical_signature={
                't_rate': 0.68,
                'win_rate': 0.71
            }
        )
    ]
    
    # Convert to list format expected by generate_improvement_roadmap
    patterns = weaknesses + strengths
    baseline_stats = {'total_rallies': 89, 'total_points': 156}
    
    print("1️⃣  Testing Strategic Approach...")
    strategic_approach = generate_strategic_approach(weaknesses, strengths)
    print(f"   Length: {len(strategic_approach)} chars")
    print(f"   Content: {strategic_approach}\n")
    
    # Validate personalization
    pattern_names_found = sum(1 for p in patterns if p.name in strategic_approach)
    print(f"   ✅ Pattern names referenced: {pattern_names_found}/{len(patterns)}")
    print(f"   ✅ Contains loss rates: {'65%' in strategic_approach or 'loss rate' in strategic_approach}")
    print(f"   ✅ Contains frequencies: {any(str(p.frequency) in strategic_approach for p in patterns)}")
    print(f"   ✅ Contains cascade: {'CASCADE' in strategic_approach or 'unlock' in strategic_approach.lower()}\n")
    
    print("2️⃣  Testing Coordinated Practice Plan...")
    practice_plan = generate_coordinated_practice_plan(weaknesses)
    print(f"   Weeks with schedules: {len(practice_plan)}")
    for week_key in ['week_1', 'week_2']:
        week_data = practice_plan.get(week_key, {})
        if week_data:
            pattern_name = list(week_data.keys())[0]
            print(f"   {week_key}: {pattern_name[:40]}... = {week_data[pattern_name]}")
    
    # Validate
    plan_str = str(practice_plan)
    pattern_names_in_plan = sum(1 for w in weaknesses if w.name[:20] in plan_str)
    print(f"   ✅ Weakness patterns in plan: {pattern_names_in_plan}/{len(weaknesses)}")
    print(f"   ✅ Contains specific volumes: {'40 min' in plan_str or '30 min' in plan_str}\n")
    
    print("3️⃣  Testing Quick Wins Grid...")
    quick_wins = generate_quick_wins_grid(weaknesses, strengths)
    for category in ['immediate', 'short_term']:
        items = quick_wins.get(category, [])
        if items:
            print(f"   {category}: {items[0][:80]}...")
    
    quick_wins_str = str(quick_wins)
    pattern_names_in_wins = sum(1 for p in patterns if p.name in quick_wins_str)
    print(f"   ✅ Pattern names in quick wins: {pattern_names_in_wins}/{len(patterns)}")
    print(f"   ✅ Contains specific data: {'%' in quick_wins_str and 'loss rate' in quick_wins_str.lower()}\n")
    
    print("4️⃣  Testing Improvement Timeline...")
    timeline = generate_improvement_timeline(weaknesses)
    for milestone in timeline[:2]:
        print(f"   {milestone['week']}: {milestone['expected_improvements'][:80]}...")
    
    timeline_str = str(timeline)
    print(f"   ✅ References top weakness: {weaknesses[0].name[:20] in timeline_str}")
    print(f"   ✅ Contains specific targets: {'%' in timeline_str and 'loss rate' in timeline_str.lower()}")
    print(f"   ✅ Contains cascade effect: {'CASCADE' in timeline_str}\n")
    
    print("5️⃣  Testing Success Metrics...")
    metrics = generate_success_metrics(weaknesses, strengths)
    print(f"   Total metrics: {len(metrics)}")
    for i, metric in enumerate(metrics[:3], 1):
        print(f"   {i}. {metric[:100]}...")
    
    metrics_str = ' '.join(metrics)
    pattern_names_in_metrics = sum(1 for p in patterns if p.name in metrics_str)
    print(f"   ✅ Pattern names in metrics: {pattern_names_in_metrics}/{len(patterns)}")
    print(f"   ✅ Contains behavioral targets: {'mph' in metrics_str or '%' in metrics_str}\n")
    
    print("6️⃣  Testing Complete Roadmap Generation...")
    roadmap = generate_improvement_roadmap(patterns, baseline_stats)
    print(f"   ✅ Strategic approach: {len(roadmap['strategic_approach'])} chars")
    print(f"   ✅ Prioritized actions: {len(roadmap['prioritized_actions'])} items")
    print(f"   ✅ Practice plan weeks: {len(roadmap['coordinated_practice_plan'])}")
    print(f"   ✅ Quick wins categories: {len(roadmap['quick_wins'])}")
    print(f"   ✅ Timeline milestones: {len(roadmap['improvement_timeline'])}")
    print(f"   ✅ Success metrics: {len(roadmap['success_metrics'])}\n")
    
    # Final validation
    print("✅ FINAL VALIDATION:")
    roadmap_str = str(roadmap)
    checks = {
        'All weakness names appear': all(w.name in roadmap_str for w in weaknesses),
        'All strength names appear': all(s.name in roadmap_str for s in strengths),
        'Loss rates included': '65%' in roadmap_str or '58%' in roadmap_str,
        'Frequencies included': any(str(w.frequency) in roadmap_str for w in weaknesses),
        'Cascade connections': 'unlock' in roadmap_str.lower() or 'cascade' in roadmap_str.lower(),
        'Behavioral metrics': 'mph' in roadmap_str or 'attack rate' in roadmap_str.lower(),
        'Specific volumes': '40 min' in roadmap_str or '30 min' in roadmap_str,
        'Week-by-week targets': all(f'week_{i}' in str(roadmap['coordinated_practice_plan']) for i in range(1, 5))
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    all_passed = all(checks.values())
    print(f"\n{'🎉 ALL PERSONALIZATION CHECKS PASSED!' if all_passed else '⚠️  Some checks failed'}\n")
    
    return all_passed

if __name__ == "__main__":
    success = test_personalized_roadmap()
    sys.exit(0 if success else 1)
