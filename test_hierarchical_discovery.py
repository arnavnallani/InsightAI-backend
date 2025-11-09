#!/usr/bin/env python3
"""Test hierarchical pattern discovery on mock SwingVision data"""

import sys
import json
from analysis.hierarchical_pattern_discovery import HierarchicalPatternDiscovery
from analysis.pattern_utils import Rally, Shot

# Generate simple test rallies
def create_test_rallies():
    """Create test rallies with clear patterns"""
    rallies = []
    
    # Pattern 1: Deep Crosscourt Forehand (Strength) - 60% win rate
    for i in range(25):
        outcome = 'you' if i < 15 else 'opponent'  # 60% win rate
        rally_data = {
            'rallyId': f'rally-{i}',
            'setNumber': 1,
            'gameNumber': 1,
            'pointNumber': i,
            'pointScore': '30-30',
            'server': 'opponent',
            'pointWinner': outcome,
            'shots': [
                {'player': 'opponent', 'shotType': 'Serve', 'speed': 105, 'placement': {'x': 50, 'y': 5}, 'trajectory': 'Medium', 'spin': 'Flat', 'shotResult': 'In play'},
                {'player': 'you', 'shotType': 'Forehand', 'speed': 72, 'placement': {'x': 35, 'y': 80}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'In play'},
                {'player': 'opponent', 'shotType': 'Backhand', 'speed': 65, 'placement': {'x': 60, 'y': 75}, 'trajectory': 'Medium', 'spin': 'Slice', 'shotResult': 'In play'},
            ]
        }
        rally = Rally(rally_data)
        rallies.append(rally)
    
    # Pattern 2: Serve to T (Strength) - 70% win rate
    for i in range(30):
        outcome = 'you' if i < 21 else 'opponent'  # 70% win rate
        rally_data = {
            'rallyId': f'rally-serve-{i}',
            'setNumber': 1,
            'gameNumber': 2,
            'pointNumber': i,
            'pointScore': '15-0',
            'server': 'you',
            'pointWinner': outcome,
            'shots': [
                {'player': 'you', 'shotType': 'Serve', 'speed': 110, 'placement': {'x': 52, 'y': 5}, 'trajectory': 'Flat', 'spin': 'Flat', 'shotResult': 'In play'},
                {'player': 'opponent', 'shotType': 'Backhand', 'speed': 60, 'placement': {'x': 70, 'y': 50}, 'trajectory': 'High', 'spin': 'Slice', 'shotResult': 'In play'},
            ]
        }
        rally = Rally(rally_data)
        rallies.append(rally)
    
    # Pattern 3: Backhand Down the Line (Weakness) - 30% win rate
    for i in range(20):
        outcome = 'you' if i < 6 else 'opponent'  # 30% win rate
        rally_data = {
            'rallyId': f'rally-bh-{i}',
            'setNumber': 1,
            'gameNumber': 3,
            'pointNumber': i,
            'pointScore': '40-40',
            'server': 'opponent',
            'isDeuce': True,
            'pointWinner': outcome,
            'shots': [
                {'player': 'opponent', 'shotType': 'Forehand', 'speed': 70, 'placement': {'x': 20, 'y': 70}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'In play'},
                {'player': 'you', 'shotType': 'Backhand', 'speed': 58, 'placement': {'x': 85, 'y': 65}, 'trajectory': 'High', 'spin': 'Slice', 'shotResult': 'In play'},
                {'player': 'opponent', 'shotType': 'Forehand', 'speed': 75, 'placement': {'x': 15, 'y': 80}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'Winner'},
            ]
        }
        rally = Rally(rally_data)
        rallies.append(rally)
    
    # Pattern 4: Pressure Points (Weakness) - 36% win rate
    for i in range(25):
        outcome = 'you' if i < 9 else 'opponent'  # 36% win rate
        rally_data = {
            'rallyId': f'rally-pressure-{i}',
            'setNumber': 2,
            'gameNumber': 5,
            'pointNumber': i,
            'pointScore': 'Deuce',
            'server': 'opponent',
            'isDeuce': True,
            'pointWinner': outcome,
            'shots': [
                {'player': 'opponent', 'shotType': 'Serve', 'speed': 105, 'placement': {'x': 48, 'y': 5}, 'trajectory': 'Medium', 'spin': 'Flat', 'shotResult': 'In play'},
                {'player': 'you', 'shotType': 'Forehand', 'speed': 62, 'placement': {'x': 30, 'y': 60}, 'trajectory': 'High', 'spin': 'Topspin', 'shotResult': 'In play'},
                {'player': 'opponent', 'shotType': 'Forehand', 'speed': 78, 'placement': {'x': 25, 'y': 85}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'Winner'},
            ]
        }
        rally = Rally(rally_data)
        rallies.append(rally)
    
    # Add normal baseline rallies (50% win rate)
    for i in range(50):
        outcome = 'you' if i % 2 == 0 else 'opponent'
        rally_data = {
            'rallyId': f'rally-normal-{i}',
            'setNumber': 2,
            'gameNumber': i // 10,
            'pointNumber': i % 10,
            'pointScore': '15-15',
            'server': 'opponent' if i % 3 == 0 else 'you',
            'pointWinner': outcome,
            'shots': [
                {'player': 'opponent', 'shotType': 'Serve', 'speed': 100, 'placement': {'x': 45, 'y': 5}, 'trajectory': 'Medium', 'spin': 'Flat', 'shotResult': 'In play'},
                {'player': 'you', 'shotType': 'Backhand', 'speed': 68, 'placement': {'x': 65, 'y': 70}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'In play'},
                {'player': 'opponent', 'shotType': 'Forehand', 'speed': 70, 'placement': {'x': 25, 'y': 75}, 'trajectory': 'Medium', 'spin': 'Topspin', 'shotResult': 'In play'},
            ]
        }
        rally = Rally(rally_data)
        rallies.append(rally)
    
    return rallies

def main():
    print("🎾 Testing Hierarchical Pattern Discovery Engine\n")
    print("=" * 60)
    
    # Create test data
    rallies = create_test_rallies()
    print(f"✅ Generated {len(rallies)} test rallies")
    
    # Calculate baseline
    baseline_wins = sum(1 for r in rallies if r.outcome == 'won')
    baseline_rate = baseline_wins / len(rallies)
    print(f"📊 Baseline win rate: {baseline_rate:.1%}\n")
    
    # Run hierarchical discovery
    discovery = HierarchicalPatternDiscovery(
        min_sample_size=10,
        significance_threshold=0.10  # 10% difference from baseline
    )
    
    patterns = discovery.discover_patterns(rallies)
    
    print("=" * 60)
    print(f"🔍 DISCOVERED {len(patterns)} PATTERNS:\n")
    
    for i, p in enumerate(patterns, 1):
        print(f"{i}. {p.name}")
        print(f"   ID: {p.pattern_id}")
        print(f"   Type: {p.type.upper()}")
        print(f"   Features: {p.features}")
        print(f"   Frequency: {p.frequency} rallies")
        print(f"   Win Rate: {p.win_rate:.1%} (baseline: {p.baseline_win_rate:.1%})")
        print(f"   Significance Score: {p.significance_score:.2f}")
        
        if p.type == 'strength':
            print(f"   💪 Leverage Potential: {p.leverage_potential:.1f}%")
        else:
            print(f"   ⚠️  Improvement Potential: {p.improvement_potential:.1f}%")
        
        print()
    
    print("=" * 60)
    print("✅ Test complete!")
    
    # Summary
    strengths = [p for p in patterns if p.type == 'strength']
    weaknesses = [p for p in patterns if p.type == 'weakness']
    print(f"\n📈 Summary: {len(strengths)} strengths, {len(weaknesses)} weaknesses")

if __name__ == '__main__':
    main()
