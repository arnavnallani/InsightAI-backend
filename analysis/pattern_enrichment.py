"""
Pattern Enrichment Layer
Converts raw discovered patterns into frontend-ready analysis with narratives, drills, and strategies
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from hierarchical_pattern_discovery import DiscoveredPattern
from pattern_utils import Rally
from tennis_strategy_knowledge import POSITION_BASED_TACTICS, SCORE_BASED_TACTICS, OPPONENT_STYLE_TACTICS, ENERGY_MANAGEMENT, BREAK_POINT_TACTICS


def serialize_rally(rally: Rally, pattern_features=None) -> Dict[str, Any]:
    """
    Convert Rally object to JSON-serializable dict.
    Defensive: handles None/partial rally data gracefully.
    
    Args:
        rally: Rally object to serialize
        pattern_features: Optional PatternFeatures to find the matching shot
    """
    if rally is None:
        return {
            'set': 0,
            'game_score': 'N/A',
            'point_score': 'N/A',
            'serving': False,
            'outcome': 'unknown',
            'rally_length': 0,
            'shots': [],
            'yourShot': 'No shot data available',
            'speed': 0,
            'placement': 'N/A'
        }
    
    # Defensive attribute access with fallbacks
    rally_dict = {
        'set': getattr(rally, 'set_number', 0),
        'game_score': getattr(rally, 'game_score', 'N/A'),
        'point_score': getattr(rally, 'point_score', 'N/A'),
        'serving': getattr(rally, 'serving', False),
        'outcome': getattr(rally, 'outcome', 'unknown'),
        'rally_length': len(rally.shots) if hasattr(rally, 'shots') and rally.shots else 0,
        'shots': []
    }
    
    # Find the shot that matches the pattern features (CRITICAL FIX!)
    # If pattern_features provided, show the shot that matched the pattern
    # Otherwise, fall back to showing your last shot
    your_matching_shot = None
    if hasattr(rally, 'shots') and rally.shots:
        if pattern_features:
            # Find the shot that matches ALL pattern features
            for shot in rally.shots:
                if shot and getattr(shot, 'player', '').lower() in ['player', 'you']:
                    # Check if shot matches all pattern features
                    matches = True
                    
                    if pattern_features.shot_type:
                        if getattr(shot, 'shot_type', '') != pattern_features.shot_type:
                            matches = False
                    
                    if pattern_features.direction:
                        shot_direction = getattr(shot, 'direction', 'unknown')
                        if shot_direction != pattern_features.direction:
                            matches = False
                            # Debug logging
                            import sys
                            print(f"  🔍 Direction mismatch: shot={shot_direction}, pattern={pattern_features.direction}", file=sys.stderr)
                    
                    if pattern_features.depth:
                        if not hasattr(shot, 'depth_category') or getattr(shot, 'depth_category', '') != pattern_features.depth:
                            matches = False
                    
                    if matches:
                        your_matching_shot = shot
                        break  # Found the matching shot!
        
        # Fallback to last shot if no pattern match found
        if not your_matching_shot:
            for shot in reversed(rally.shots):
                if shot:
                    player_name = getattr(shot, 'player', '').lower()
                    if player_name in ['player', 'you']:
                        your_matching_shot = shot
                        break
    
    # Generate yourShot description and extract details
    if your_matching_shot:
        shot_type = getattr(your_matching_shot, 'shot_type', 'Unknown')
        speed = getattr(your_matching_shot, 'speed', 0)
        spin = getattr(your_matching_shot, 'spin', 'flat')
        
        # Determine placement from x, y coordinates
        x = getattr(your_matching_shot, 'x', 50)
        y_raw = getattr(your_matching_shot, 'y', 50)
        
        # FIX: Transform Y coordinate to match visualization coordinate system
        # SwingVision uses: Y=0 (opponent baseline) to Y=100 (your baseline)
        # Visualization expects: Y=0 (opponent baseline) to Y=100 (your baseline)
        # BUT SwingVision data has shots landing at Y=55-95 (your side)
        # We need to FLIP so shots land on opponent's side (Y=5-45)
        y = 100 - y_raw
        
        # Detect error shots (out of bounds or in net)
        is_error = False
        shot_result = 'in-play'
        
        # Check if shot is out (outside court boundaries)
        if y < 0 or y > 100 or x < 0 or x > 100:
            is_error = True
            shot_result = 'error'
        # Check if shot landed on player's own side (didn't cross net)
        elif y > 50:
            is_error = True
            shot_result = 'error'
        
        # Store placement as coordinate object for tennis court visualization
        placement = {'x': x, 'y': y}
        
        # Extract player position (where you were when you hit the shot)
        # from SwingVision data - this is the actual position on court
        if hasattr(your_matching_shot, 'player_position'):
            player_position = your_matching_shot.player_position
        else:
            # Fallback if no position data available
            player_position = {'x': 50, 'y': 85}
        
        # Create descriptive text - Format: "{Spin} {Shot Type}"
        # Normalize spin: none/empty/null → Flat, otherwise capitalize
        if not spin or spin.lower() in ['none', 'flat', '']:
            spin_display = 'Flat'
        else:
            spin_display = spin.capitalize()
        
        your_shot_desc = f"{spin_display} {shot_type}"
        
        rally_dict['your_shot'] = your_shot_desc
        rally_dict['shot_type'] = shot_type  # Add individual field for frontend
        rally_dict['spin'] = spin  # Add individual field for frontend
        rally_dict['speed'] = speed
        rally_dict['placement'] = placement
        rally_dict['player_position'] = player_position
        rally_dict['is_error'] = is_error
        rally_dict['shot_result'] = shot_result
        
        # Estimate opponent position based on where your previous shot landed
        # This is where they would be positioned to return your shot
        opponent_position = {'x': 50, 'y': 10}  # default opponent baseline
        if hasattr(rally, 'shots') and rally.shots:
            # Find the previous shot (opponent's shot before yours)
            shot_index = rally.shots.index(your_matching_shot) if your_matching_shot in rally.shots else -1
            if shot_index > 0:
                prev_shot = rally.shots[shot_index - 1]
                if prev_shot and getattr(prev_shot, 'player', '').lower() in ['opponent', 'opp']:
                    # Opponent is near where they hit their last shot
                    prev_x = getattr(prev_shot, 'x', 50)
                    prev_y = getattr(prev_shot, 'y', 10)
                    # Opponent is on the opposite side of court (y-axis flipped)
                    opponent_position = {'x': prev_x, 'y': 100 - prev_y}
        
        rally_dict['opponent_position'] = opponent_position
    else:
        # No player shot found - rally might have ended on opponent's shot
        rally_dict['your_shot'] = "Point ended on opponent's shot"
        rally_dict['shot_type'] = 'Unknown'
        rally_dict['spin'] = 'flat'
        rally_dict['speed'] = 0
        rally_dict['placement'] = 'N/A'
        rally_dict['player_position'] = {'x': 50, 'y': 85}  # Default player position
        rally_dict['opponent_position'] = {'x': 50, 'y': 10}
    
    # Serialize shots with defensive checks
    if hasattr(rally, 'shots') and rally.shots:
        for shot in rally.shots:
            if shot is None:
                continue
            
            # Normalize spin for display (none/empty → flat)
            raw_spin = getattr(shot, 'spin', 'flat')
            normalized_spin = 'flat' if (not raw_spin or str(raw_spin).lower() in ['none', '']) else raw_spin
            
            shot_dict = {
                'shot_number': getattr(shot, 'shot_number', 0),
                'player': getattr(shot, 'player', 'unknown'),
                'shot_type': getattr(shot, 'shot_type', 'Unknown'),
                'speed': getattr(shot, 'speed', 0),
                'x': getattr(shot, 'x', 0),
                'y': getattr(shot, 'y', 0),
                'trajectory': getattr(shot, 'trajectory', 'Unknown'),
                'spin': normalized_spin,
            }
            rally_dict['shots'].append(shot_dict)
    
    # Add minimax_optimal if present (already formatted correctly in hierarchical_analysis.py)
    if hasattr(rally, 'minimax_optimal') and rally.minimax_optimal:
        optimal = rally.minimax_optimal
        
        # Copy existing minimax_optimal data (already has optimalShot wrapper with placement, etc.)
        if isinstance(optimal, dict):
            rally_dict['minimax_optimal'] = optimal.copy()
        else:
            # If it's not a dict (maybe a string), just pass it through
            rally_dict['minimax_optimal'] = optimal
    
    # Add butterfly_effect if present (for critical moments)
    if hasattr(rally, 'butterfly_effect') and rally.butterfly_effect:
        butterfly = rally.butterfly_effect
        
        # Copy butterfly effect data (has actualTimeline, optimalTimeline, context, etc.)
        if isinstance(butterfly, dict):
            rally_dict['butterfly_effect'] = butterfly.copy()
        else:
            rally_dict['butterfly_effect'] = butterfly
    
    return rally_dict

def enrich_pattern_with_narratives(pattern: DiscoveredPattern) -> Dict[str, Any]:
    """
    Enrich a discovered pattern with professional narratives, drills, and strategies.
    
    Converts raw pattern into frontend-ready format matching front_end_base.md spec.
    """
    is_strength = pattern.type == 'strength'
    
    # Generate description based on features
    description = generate_description(pattern)
    
    # Generate professional strategy
    professional_strategy = generate_professional_strategy(pattern)
    
    # Generate drills
    drills = generate_drills(pattern)
    
    # Generate pattern behavior explanation
    pattern_behavior = generate_pattern_behavior(pattern)
    
    # Determine severity
    if is_strength:
        severity = 'strength'
    else:
        significance_pct = pattern.significance_score / pattern.frequency if pattern.frequency > 0 else 0
        if significance_pct > 0.20:
            severity = 'high'
        elif significance_pct > 0.12:
            severity = 'medium'
        else:
            severity = 'low'
    
    # Filter critical moments to only include those with optimal shot data
    critical_moments_with_optimal = [
        r for r in pattern.critical_moments 
        if hasattr(r, 'minimax_optimal') and r.minimax_optimal
    ]
    
    # Build enriched pattern
    enriched = {
        'id': pattern.pattern_id,
        'name': clean_pattern_name(pattern.name),
        'type': pattern.type,
        'severity': severity,
        'frequency': pattern.frequency,
        'significance_score': pattern.significance_score,
        'description': description,
        'pattern_behavior': pattern_behavior,
        'professional_strategy': professional_strategy,
        'drills': drills,
        'supporting_rallies': [serialize_rally(r, pattern.features) for r in pattern.supporting_rallies],
        'critical_moments': [serialize_rally(r, pattern.features) for r in critical_moments_with_optimal],
    }
    
    # Add type-specific fields
    if is_strength:
        enriched['point_win_rate'] = pattern.point_win_rate
        enriched['leverage_potential'] = pattern.leverage_potential
        
        # Add strength-specific tactical strategy (camelCase for frontend)
        enriched['tacticalStrategy'] = generate_strength_tactics(pattern)
    else:
        enriched['point_loss_rate'] = pattern.point_loss_rate
        enriched['improvement_potential'] = pattern.improvement_potential
        
        # Add weakness-specific tactical fix (camelCase for frontend)
        enriched['tacticalFix'] = generate_weakness_tactics(pattern)
    
    return enriched


def clean_pattern_name(name: str) -> str:
    """Remove [Strong]/[Weak] tags from pattern name"""
    return name.replace(' [Strong]', '').replace(' [Weak]', '').strip()


def generate_description(pattern: DiscoveredPattern) -> str:
    """Generate natural language description of the pattern"""
    features = pattern.features
    is_strength = pattern.type == 'strength'
    
    # Build feature description
    parts = []
    if features.shot_type:
        parts.append(features.shot_type.lower())
    if features.direction:
        parts.append(features.direction)
    if features.depth:
        parts.append(features.depth.lower())
    if features.context:
        parts.append(f"during {features.context.lower()} points")
    
    feature_desc = " ".join(parts)
    
    win_rate = pattern.win_rate * 100
    freq = pattern.frequency
    
    if is_strength:
        return f"You excel with {feature_desc}, winning {win_rate:.0f}% of {freq} rallies featuring this shot."
    else:
        loss_rate = (1 - pattern.win_rate) * 100
        return f"You struggle with {feature_desc}, losing {loss_rate:.0f}% of {freq} rallies featuring this shot."


def generate_pattern_behavior(pattern: DiscoveredPattern) -> str:
    """Generate detailed behavioral explanation"""
    features = pattern.features
    is_strength = pattern.type == 'strength'
    
    if is_strength:
        behavior = f"When hitting {features.shot_type or 'this shot'}"
        if features.direction:
            behavior += f" {features.direction}"
        if features.depth:
            behavior += f" with {features.depth.lower()} placement"
        behavior += ", you consistently force weak returns and control the point."
        return behavior
    else:
        behavior = f"On {features.shot_type or 'this shot'}"
        if features.direction:
            behavior += f" {features.direction}"
        if features.depth:
            behavior += f" at {features.depth.lower()} depth"
        if features.context:
            behavior += f" during {features.context.lower()} situations"
        behavior += ", you show technical breakdown or strategic indecision, leading to unforced errors or weak positioning."
        return behavior


def generate_professional_strategy(pattern: DiscoveredPattern) -> Dict[str, Any]:
    """Generate professional tactical advice matching mock analysis structure"""
    features = pattern.features
    is_strength = pattern.type == 'strength'
    
    if is_strength:
        why_its_good = []
        what_to_do = []
        classic_pattern = "Build rallies → Create opportunity → Execute strength"
        
        # Build whyItsGood array
        if features.direction == 'Crosscourt':
            why_its_good = [
                "Longest diagonal on the court = maximum margin for error",
                "Creates wide angles that push opponent off the court",
                "Natural swing path for most players",
            ]
            classic_pattern = "Crosscourt → Crosscourt → Down the Line"
        elif features.direction == 'DTL':
            why_its_good = [
                "Changes direction and catches opponent moving wrong way",
                "Opens up crosscourt for next shot",
                "Tests opponent's ability to cover court width",
            ]
            classic_pattern = "Crosscourt → Down the Line → Approach"
        elif features.shot_type == 'Serve' and features.direction == 'T':
            why_its_good = [
                "Limits opponent's return angles",
                "Jams opponent's swing path",
                "Neutralizes opponent's strengths",
            ]
            classic_pattern = "T serve → Short return → Forehand attack"
        else:
            why_its_good = [
                f"{features.shot_type or 'Shot'} creates geometric advantage",
                "High margin for error with good net clearance",
                "Maintains optimal court positioning",
            ]
        
        # Build whatToDo array
        if features.shot_type == 'Serve' and features.direction == 'T':
            what_to_do = [
                "Use this serve 50% of the time on first serves",
                "Mix with wide serves to keep opponent guessing",
                "Follow up weak returns with aggressive forehands",
            ]
        elif features.direction == 'Crosscourt':
            what_to_do = [
                "Use this as your primary rally ball - 60-70% of neutral rallies",
                "Look for opportunities to set up this shot on returns",
                "When opponent is pushed wide, follow up with down-the-line attack",
            ]
        else:
            what_to_do = [
                "Actively seek opportunities to hit this shot",
                f"Set up rallies to create {features.direction or 'favorable'} angles",
                "Leverage this strength on big points",
            ]
        
        return {
            'why_its_good': why_its_good,
            'what_to_do': what_to_do,
            'classic_pattern': classic_pattern
        }
    else:
        why_its_bad = []
        what_to_do = []
        classic_pattern = "Build with safe shots → Wait for opportunity → Attack when ready"
        
        # Build whyItsBad array
        if features.direction == 'DTL':
            why_its_bad = [
                "DTL is the shortest distance = least margin for error",
                "Requires precise timing and technique",
                "Your current technique generates insufficient topspin for safety",
            ]
            what_to_do = [
                "Reduce DTL attempts by 50% - use only when opponent is way out of position",
                "Focus on crosscourt shots to build rallies",
                "When you must go DTL, aim 6 feet inside the line for safety margin",
            ]
            classic_pattern = "Build with crosscourt → Wait for short ball → DTL attack"
        elif features.direction == 'Crosscourt':
            why_its_bad = [
                "Insufficient depth allows opponent to step in and attack",
                "Lack of pace gives opponent time to recover position",
                "Predictable pattern that opponent can anticipate",
            ]
            what_to_do = [
                "Hit deeper crosscourt with more pace",
                "Aim for baseline depth with medium-heavy topspin",
                "Mix in occasional down-the-line to keep opponent honest",
            ]
        elif features.context == 'Pressure':
            why_its_bad = [
                "Defensive shot selection under pressure invites opponent attack",
                "Slower ball speed gives opponent easy setups",
                "Mental tension causes technical breakdown",
            ]
            what_to_do = [
                "Practice pressure simulation drills with point consequences",
                "Maintain normal ball speed even when nervous",
                "Focus on breathing and routine between points",
            ]
        else:
            why_its_bad = [
                f"{features.shot_type or 'Shot'} lacks margin-of-error",
                "Technical inconsistency leads to unforced errors",
                "Allows opponent to anticipate and attack",
            ]
            what_to_do = [
                f"Build confidence with {features.shot_type or 'groundstrokes'} through repetition",
                "Focus on consistent depth and spin quality",
                "Use this shot only in favorable situations until consistency improves",
            ]
        
        # Add margin calculations for DTL
        margin_calculations = None
        if features.direction == 'DTL':
            margin_calculations = {
                'your_way': "DTL - shortest diagonal, highest net at sideline",
                'optimal_way': "Crosscourt - longest diagonal, lowest net height"
            }
        
        result = {
            'why_its_bad': why_its_bad,
            'what_to_do': what_to_do,
            'classic_pattern': classic_pattern
        }
        
        if margin_calculations:
            result['margin_calculations'] = margin_calculations
        
        return result


def generate_drills(pattern: DiscoveredPattern) -> List[Dict[str, Any]]:
    """Generate pattern-specific drills matching mock analysis structure"""
    features = pattern.features
    is_strength = pattern.type == 'strength'
    
    drills = []
    
    if is_strength:
        # For strengths, create drills to leverage this weapon
        if features.direction == 'Crosscourt' and features.shot_type == 'Forehand':
            drill = {
                'name': "Crosscourt Forehand Rally",
                'description': "Build consistency and depth on crosscourt forehands",
                'reps': "3 sets of 20 balls",
                'metrics': [
                    "Net clearance: 2-3 feet minimum",
                    "Landing depth: Beyond service line",
                    "Topspin rotation: Visible heavy spin"
                ],
                'success_criteria': "15/20 balls land deep with good margin"
            }
        elif features.shot_type == 'Serve' and features.direction == 'T':
            drill = {
                'name': "T Serve Practice",
                'description': "Develop accuracy and pace on T serves",
                'reps': "2 sets of 10 serves per side",
                'metrics': [
                    "Target: Within 2 feet of center T",
                    "Speed: 95+ mph",
                    "First serve percentage: 60%+"
                ],
                'success_criteria': "6/10 serves hit the T target zone"
            }
        else:
            drill = {
                'name': f"{features.shot_type or 'Strength'} Consistency Drill",
                'description': f"Build consistency and effectiveness with {features.shot_type or 'this shot'}",
                'reps': "3 sets of 15-20 balls",
                'metrics': [
                    f"Consistent {features.direction or 'placement'}",
                    "Good depth and net clearance",
                    "Quality spin and pace"
                ],
                'success_criteria': "12/15 successful executions"
            }
        drills.append(drill)
    else:
        # For weaknesses, create corrective drills
        shot_name = features.shot_type or 'shot'
        direction = features.direction or ''
        
        if features.direction == 'DTL':
            drill = {
                'name': f"{shot_name} Down the Line Drill",
                'description': f"Improve consistency and margin on {shot_name.lower()} DTL shots",
                'reps': "4 sets of 15 balls",
                'metrics': [
                    "Net clearance: 3-4 feet minimum for safety",
                    "Landing depth: Beyond service line",
                    "Spin: Medium-heavy topspin",
                    "Aim 6 feet inside the line"
                ],
                'success_criteria': "10/15 balls land deep DTL with good margin"
            }
        elif features.context == 'Pressure':
            drill = {
                'name': "Pressure Point Simulation",
                'description': "Practice maintaining technique under pressure",
                'reps': "6 pressure point scenarios",
                'metrics': [
                    "Maintain normal ball speed",
                    "Avoid defensive high balls",
                    "Use aggressive shot selection"
                ],
                'success_criteria': "Win 4/6 pressure points with aggressive play"
            }
        elif features.direction == 'Crosscourt':
            drill = {
                'name': f"Deep {shot_name} Crosscourt",
                'description': f"Build depth and consistency on {shot_name.lower()} crosscourt",
                'reps': "4 sets of 20 balls",
                'metrics': [
                    "Landing depth: Baseline or deeper",
                    "Net clearance: 2-3 feet",
                    "Heavy topspin rotation"
                ],
                'success_criteria': "16/20 balls land deep crosscourt"
            }
        else:
            drill = {
                'name': f"{shot_name} {direction} Consistency".strip(),
                'description': f"Targeted practice to improve {shot_name.lower()} {direction.lower()}".strip(),
                'reps': "3 sets of 20 balls",
                'metrics': [
                    "Consistent depth and placement",
                    "Good net clearance and spin",
                    "Quality contact and follow-through"
                ],
                'success_criteria': "14/20 successful executions"
            }
        
        drills.append(drill)
    
    return drills


def generate_strength_tactics(pattern: DiscoveredPattern) -> Dict[str, Any]:
    """
    Generate tactical strategy for strength patterns.
    Returns: whenToDeploy, howToSetUp, professionalBenchmark, maximizeThisStrength
    """
    features = pattern.features
    shot_type = features.shot_type or 'shot'
    direction = features.direction or ''
    depth = features.depth or ''
    context = features.context or ''
    
    # When to Deploy This Weapon
    when_to_deploy = []
    if context and context.lower() == 'pressure':
        when_to_deploy = [
            "On big points (30-30, deuce, break points) - this is your clutch shot",
            "When you need to win the point quickly",
            "After holding serve to build momentum"
        ]
    elif 'serve' in shot_type.lower():
        when_to_deploy = [
            "Use this serve 50-60% of first serves",
            "On important points (15-30, 30-30, break points)",
            "To set up easy put-aways on next shot"
        ]
    elif direction.lower() == 'crosscourt':
        when_to_deploy = [
            "As your primary rally ball - use 60-70% of neutral rallies",
            "When you need time to recover position",
            "To build pressure before attacking down the line"
        ]
    elif direction.lower() == 'dtl':
        when_to_deploy = [
            "When opponent is pushed wide crosscourt",
            "To change direction and surprise opponent",
            "When you're inside the baseline and balanced"
        ]
    else:
        when_to_deploy = [
            f"On key points where you need your best {shot_type.lower()}",
            "When you've identified opponent's weakness",
            "To establish dominance early in games"
        ]
    
    # How to Set It Up
    how_to_set_up = []
    if direction.lower() == 'crosscourt':
        how_to_set_up = [
            "Build rally with crosscourt patterns",
            "Push opponent wide to create angles",
            "Use this shot to set up down-the-line finisher"
        ]
    elif direction.lower() == 'dtl':
        how_to_set_up = [
            "Pattern: Crosscourt → Crosscourt → Down the Line",
            "Wait for opponent to commit to crosscourt direction",
            "Attack when you're inside the baseline"
        ]
    elif 'serve' in shot_type.lower():
        how_to_set_up = [
            "Alternate with wide serves to keep opponent guessing",
            "Follow up weak returns aggressively",
            "Position yourself for forehand put-away after serve"
        ]
    else:
        how_to_set_up = [
            f"Create opportunities for your {shot_type.lower()}",
            "Recognize patterns where this shot succeeds",
            "Build confidence by using it in practice matches"
        ]
    
    # Professional Benchmark
    professional_benchmark = ""
    if 'forehand' in shot_type.lower():
        if direction.lower() == 'dtl':
            professional_benchmark = "Top players convert 75% of forehand DTL opportunities when opponent is wide. Your win rate on this shot matches professional standards."
        else:
            professional_benchmark = "Elite players win 70%+ of points when hitting heavy crosscourt forehands. You're executing at that level."
    elif 'backhand' in shot_type.lower():
        professional_benchmark = "Tour-level backhand crosscourts win 65% of rallies. Your execution is comparable to advanced players."
    elif 'serve' in shot_type.lower():
        professional_benchmark = "Professional first serve win rates average 70-75%. Your serve pattern is generating similar success."
    else:
        professional_benchmark = f"Your {shot_type.lower()} performance matches advanced competitive players in win rate and consistency."
    
    # Maximize This Strength
    maximize = []
    if pattern.point_win_rate > 0.75:
        maximize = [
            f"This is your WEAPON - use it aggressively on all important points",
            f"Practice this shot daily to maintain {int(pattern.point_win_rate * 100)}% success rate",
            "Build entire match strategy around creating opportunities for this shot"
        ]
    elif pattern.point_win_rate > 0.65:
        maximize = [
            f"Solid strength - look for chances to deploy this shot more often",
            "Practice variations to make this shot even more effective",
            "Use this shot to control tempo and momentum in matches"
        ]
    else:
        maximize = [
            f"Reliable shot - continue using it as foundation",
            "Small improvements can push this to elite level",
            "Trust this shot on important points"
        ]
    
    return {
        'whenToDeploy': when_to_deploy,
        'howToSetUp': how_to_set_up,
        'professionalBenchmark': professional_benchmark,
        'maximizeThisStrength': maximize
    }


def generate_weakness_tactics(pattern: DiscoveredPattern) -> Dict[str, Any]:
    """
    Generate tactical fix for weakness patterns.
    Returns: whyThisFails, professionalFix, situationalAdjustments, practiceFocus
    """
    features = pattern.features
    shot_type = features.shot_type or 'shot'
    direction = features.direction or ''
    depth = features.depth or ''
    context = features.context or ''
    
    # Why This Fails
    why_fails = []
    if direction.lower() == 'dtl':
        why_fails = [
            "Down the line is the shortest distance = least margin for error",
            "Net is higher at the sidelines (3ft vs 3.5ft)",
            "Requires precise timing and technique",
            "Your current technique generates insufficient topspin for safety"
        ]
    elif direction.lower() == 'crosscourt' and 'short' in depth.lower():
        why_fails = [
            "Short crosscourt balls give opponent easy attack opportunities",
            "Lack of depth allows opponent to step inside baseline",
            "Insufficient pace gives opponent time to set up winners",
            "You're hitting defensive shots in neutral situations"
        ]
    elif context and context.lower() == 'pressure':
        why_fails = [
            "Mental tension causes technical breakdown",
            "Defensive shot selection under pressure invites opponent attacks",
            "You're playing scared instead of trusting your game",
            "Slower ball speed gives opponent easy setups"
        ]
    elif 'serve' in shot_type.lower():
        why_fails = [
            "Predictable serve pattern allows opponent to anticipate",
            "Insufficient pace or placement lets opponent attack return",
            "Missing first serves creates pressure on second serve",
            "Not targeting opponent's weakness zones"
        ]
    else:
        why_fails = [
            f"{shot_type} lacks consistent margin-of-error",
            "Technical inconsistency leads to unforced errors",
            "Allows opponent to anticipate and attack",
            "You're attempting this shot in unfavorable situations"
        ]
    
    # Professional Fix
    professional_fix = []
    if direction.lower() == 'dtl':
        professional_fix = [
            "Reduce DTL attempts by 50% - use only when opponent is way out of position",
            "When you must go DTL, aim 6 feet inside the line for safety margin",
            "Build with crosscourt first (crosscourt → crosscourt → DTL)",
            "Practice DTL with 3-4 feet net clearance and heavy topspin"
        ]
    elif direction.lower() == 'crosscourt':
        professional_fix = [
            "Increase ball depth - aim for baseline or deeper",
            "Add pace with heavy topspin (2-3 feet net clearance)",
            "Pro pattern: Deep crosscourt → Deep crosscourt → Attack short ball",
            "Target beyond service line with every shot"
        ]
    elif context and context.lower() == 'pressure':
        professional_fix = [
            "Maintain your normal ball speed - avoid defensive pushing",
            "Trust your best shot patterns even when nervous",
            "Practice pressure simulation: play sets where games must be won twice",
            "Focus on process (feet, contact) not outcome (score)"
        ]
    else:
        professional_fix = [
            f"Build {shot_type.lower()} consistency with systematic practice",
            "Use this shot only in favorable situations until consistency improves",
            "Focus on margin-of-error - hit 5 feet inside lines until reliable",
            "Practice with consequences - losers do push-ups"
        ]
    
    # Situational Adjustments
    situational_adjustments = {}
    
    # When leading
    leading_adjustment = "Don't change your pattern - keep doing what's working. "
    if direction.lower() == 'dtl':
        leading_adjustment += "When ahead, avoid risky DTL shots. Build with safe crosscourt instead."
    else:
        leading_adjustment += f"Reduce {shot_type.lower()} usage by 30% and rely on safer shots."
    
    # When trailing
    trailing_adjustment = "Time to be more aggressive. "
    if direction.lower() == 'dtl':
        trailing_adjustment += "Still avoid DTL - but you can take calculated risks on other shots."
    elif context and context.lower() == 'pressure':
        trailing_adjustment += "Attack early in rallies - don't let points get to pressure situations."
    else:
        trailing_adjustment += f"Can't win playing scared - trust your {shot_type.lower()} and go for it."
    
    # When tired
    tired_adjustment = "Fatigue magnifies technical flaws. "
    if direction.lower() == 'dtl':
        tired_adjustment += "When tired, NEVER go DTL - use high-percentage crosscourt shots."
    else:
        tired_adjustment += f"Simplify game - avoid {shot_type.lower()} and focus on consistency."
    
    situational_adjustments = {
        'whenLeading': leading_adjustment,
        'whenTrailing': trailing_adjustment,
        'whenTired': tired_adjustment
    }
    
    # Practice Focus
    practice_focus = []
    loss_rate = (1 - pattern.win_rate) * 100
    
    if loss_rate > 70:
        practice_focus = [
            f"URGENT: This is costing you {int(loss_rate)}% of points - make it your #1 practice priority",
            "Dedicate 30-40% of practice time to fixing this specific pattern",
            f"Hire a coach if possible - this weakness is severely limiting your game",
            "Set measurable goal: Reduce error rate to under 50% within 4 weeks"
        ]
    elif loss_rate > 60:
        practice_focus = [
            f"High priority weakness - losing {int(loss_rate)}% of these points",
            "Dedicate 20-30 minutes every practice session to this shot",
            "Track progress weekly - aim for 10% improvement per month",
            "Consider video analysis to identify technical flaws"
        ]
    else:
        practice_focus = [
            "Moderate weakness - needs attention but not critical",
            "Include specific drills 2-3 times per week",
            "Focus on consistency before power",
            "Small technique adjustments can yield big improvements"
        ]
    
    return {
        'whyThisFails': why_fails,
        'professionalFix': professional_fix,
        'situationalAdjustments': situational_adjustments,
        'practiceFocus': practice_focus
    }
