"""
Tennis Strategy Knowledge Base
Professional-level tactical understanding for shot selection analysis

Covers 6 active patterns:
WEAKNESSES:
1. Serve Predictability - Telegraphing serve direction/type
2. Pressure Conservatism - Playing safe under pressure
3. Missed Attacks - Not capitalizing on short balls

STRENGTHS:
4. Forehand DTL Aggression - Effective down-the-line forehands
5. Deep Crosscourt Control - Consistent deep crosscourts
6. Serve to T Dominance - Effective T serves
"""

from typing import Optional

FOREHAND_CROSSCOURT_STRATEGY = {
    "when_to_use": [
        "You're neutral or slightly behind in the rally",
        "You need to regain control of the rally",
        "You want to move opponent wide and open the court",
        "You're on the run or stretched",
        "You want to build pressure before attacking down the line"
    ],
    "why_effective": [
        "Largest margin for error (diagonal distance = longer court)",
        "Net is lowest at the middle of the court",
        "Keeps rally patterns predictable, letting you recover easily",
        "Sets up the next attacking shot (down-the-line or inside-out)"
    ],
    "when_to_avoid": [
        "If opponent has extremely strong forehand and loves crosscourt exchanges",
        "If they're waiting to counter with a sharp angle"
    ]
}

FOREHAND_DOWN_LINE_STRATEGY = {
    "when_to_use": [
        "You've gained control or time in the rally",
        "After a short or weak crosscourt ball from opponent",
        "You want to change direction and surprise opponent",
        "You've moved them wide first (crosscourt → crosscourt → down line)",
        "Their backhand is weaker - force them into defensive corner",
        "You're looking to finish or approach the net",
        "You're inside the baseline and balanced"
    ],
    "why_effective": [
        "Changes rhythm and direction - breaks opponent's pattern",
        "Opens the opposite side of the court for next shot",
        "Can pin their weaker side",
        "Well-placed down-the-line can be a finisher or setup shot"
    ],
    "when_to_avoid": [
        "When you're stretched or off-balance",
        "When the ball is deep and heavy from opponent",
        "When your down-the-line consistency is low (lower-margin shot)"
    ]
}

# ==============================================================================
# WEAKNESS PATTERN STRATEGIES
# ==============================================================================

SERVE_PREDICTABILITY_STRATEGY = {
    "problem": "Serving to same location/type reduces first-serve effectiveness by 25-35%",
    "why_bad": [
        "Opponents anticipate direction → faster reaction time → better returns",
        "Eliminates serve as tactical weapon (should win 70%+ of serve points)",
        "Allows opponent to stand wider/cheat on returns",
        "First serve % irrelevant if opponent is waiting for it"
    ],
    "what_to_do": [
        "Mix serve placement: 40% T, 35% Body, 25% Wide (pro distribution)",
        "Vary serve types: Flat, Slice (kick for second serve)",
        "Use patterns: T on deuce side → Body on ad side → Wide surprise",
        "Study opponent return position - if they're cheating, punish them",
        "On big points (30-30, break points): Go to your strength but vary spin"
    ],
    "geometry": {
        "t_serve": "Centerline = shortest angle for opponent, forces weak crosscourt return",
        "body_serve": "Jams opponent, prevents full swing, limits return angles",
        "wide_serve": "Opens court for next shot, but gives opponent angle to work with"
    },
    "drill_metrics": {
        "target_distribution": "40% T / 35% Body / 25% Wide",
        "success_criteria": "Opponent can't predict next serve location",
        "measurement": "Track last 4 serves - no more than 3 to same spot"
    }
}

PRESSURE_CONSERVATISM_STRATEGY = {
    "problem": "Playing conservatively under pressure = 15-20% lower point win rate",
    "why_bad": [
        "Gives opponent easy balls to attack when stakes are high",
        "Psychological: Shows fear, opponent gains confidence",
        "Tactical: Lose court positioning, get pushed behind baseline",
        "Statistical: Conservative play wins 35% vs aggressive 55% on break points"
    ],
    "what_to_do": [
        "Recognize pressure moments EARLY (30-30, break points, tiebreaks)",
        "Pre-plan first 3 shots before the point starts",
        "Use your strengths aggressively - this is when they matter most",
        "Don't change strategy just because it's pressure - trust your patterns",
        "Breathing: 2 deep breaths before serve on break points",
        "Tactical target: Go to opponent's weakness even more on big points"
    ],
    "mental_approach": {
        "mantra": "Big points = use my weapons, not defend",
        "visualization": "See yourself hitting aggressive first shot before point starts",
        "pattern_interrupt": "If you feel defensive urge, take extra second to commit to attack"
    },
    "drill_metrics": {
        "target_aggression": "Match your non-pressure shot speeds (within 5 mph)",
        "success_criteria": "50%+ first strikes on pressure points",
        "measurement": "Shot depth must match non-pressure situations"
    }
}

MISSED_ATTACK_STRATEGY = {
    "problem": "Missing short ball attacks = gifting 25-30 points per match",
    "why_bad": [
        "Short balls are GIFTS - opponent made a mistake, you must punish",
        "Playing safe lets opponent recover from defensive position",
        "Sends message: 'I won't hurt you even when you're vulnerable'",
        "Statistical: Converting 70% of short balls wins sets, 40% loses them"
    ],
    "what_to_do": [
        "Definition of short ball: Landing inside service line (less than 60ft deep)",
        "IMMEDIATE decision: Move forward + prepare to attack",
        "Target: Down the line to opponent's weakness OR crosscourt angle",
        "Speed minimum: 75+ mph (this is free speed - you have time)",
        "If near net: Approach shot deep + follow to net for volley finish",
        "Practice drill: 30 short balls per session, must hit 21+ winners (70%)"
    ],
    "geometry": {
        "short_ball_advantage": "You're 15-20 feet closer to net = 15-20% less court to cover",
        "angle_opportunity": "From inside baseline, crosscourt angle increases 45%",
        "approach_depth": "Approach shots must land within 10 feet of baseline to be effective"
    },
    "drill_metrics": {
        "attack_trigger": "Any ball landing inside service line = automatic attack",
        "target_speed": "75-85 mph minimum",
        "target_depth": "Approach: within 10ft of baseline, Winner: any depth",
        "success_criteria": "70% conversion rate (winners or opponent error)"
    }
}

# ==============================================================================
# STRENGTH PATTERN STRATEGIES
# ==============================================================================

FOREHAND_DTL_AGGRESSION_STRATEGY = {
    "strength": "Effective down-the-line forehands change rally direction and create winners",
    "why_good": [
        "Breaks opponent's crosscourt rhythm - they're moving wrong direction",
        "Opens court for next shot (if they get it back)",
        "Targets opponent's backhand (typically weaker side)",
        "Creates 15-20 degree angle opponent must reverse direction to cover"
    ],
    "when_to_leverage": [
        "After building with 2+ crosscourt shots (classic pattern)",
        "When opponent is leaning/moving to their forehand side",
        "When you receive a short or mid-court ball",
        "On balls where you're inside baseline and balanced",
        "To set up approach to net (DTL + approach)"
    ],
    "how_to_maximize": [
        "Drill: Crosscourt → Crosscourt → DTL pattern 100 times per week",
        "Target depth: Within 10 feet of baseline (deep DTL is key)",
        "Speed: 75+ mph to prevent opponent recovery",
        "Follow-up: If they return weak, attack open court crosscourt",
        "Court positioning: Take 2 steps forward after DTL to cut off angle"
    ],
    "geometry": {
        "dtl_distance": "78 feet baseline-to-baseline (vs 82 feet crosscourt diagonal)",
        "net_height": "3.5 feet at sideline (vs 3 feet at center)",
        "margin_difference": "Crosscourt ~5% longer distance, but DTL worth it to break rhythm when set up"
    }
}

DEEP_CROSSCOURT_CONTROL_STRATEGY = {
    "strength": "Consistent deep crosscourt shots = rally control + court positioning",
    "why_good": [
        "Largest margin for error: 82ft diagonal = longest court distance",
        "Lowest net height: 3ft at center vs 3.5ft at sidelines",
        "Maintains court positioning - you can recover to center",
        "Builds pressure gradually - opponent gets no angles to attack",
        "Sets up DTL attack when opponent is late or extended"
    ],
    "when_to_leverage": [
        "When neutral or slightly defensive in rally",
        "When opponent is attacking - reset rally with deep crosscourt",
        "When you need time to recover court position",
        "As first shot after serve return (establish pattern)",
        "To push opponent deep and behind baseline"
    ],
    "how_to_maximize": [
        "Drill: 100 deep crosscourt shots per session, 80%+ must land deep",
        "Target: Last 10 feet of court (beyond service line)",
        "Net clearance: 2-3 feet (topspin helps keep it in)",
        "Speed: 65-75 mph with heavy topspin for depth control",
        "Variation: Occasionally add DTL after 2-3 crosscourt exchanges"
    ],
    "geometry": {
        "crosscourt_diagonal": "82 feet (ad corner to deuce corner)",
        "net_clearance": "3 feet at center (lowest point)",
        "margin_advantage": "~5% more distance than DTL (82ft vs 78ft) PLUS lower net height (3ft vs 3.5ft)"
    }
}

SERVE_TO_T_DOMINANCE_STRATEGY = {
    "strength": "T serves = highest first serve win rate (65-75%)",
    "why_good": [
        "Shortest angle for opponent - limits return options",
        "Forces return crosscourt (predictable for you)",
        "On deuce side: Pulls returner out of position to open court",
        "On ad side: Jams right-hander's backhand return",
        "Centerline = least court for opponent to work with"
    ],
    "when_to_leverage": [
        "On big points (30-30, 40-30, break points) - use your strength",
        "When opponent is standing wide expecting wide serve",
        "When you need a reliable serve (pressure situations)",
        "On deuce side vs right-handers (pulls them wide)",
        "On ad side to jam backhand returns"
    ],
    "how_to_maximize": [
        "Don't abandon it - but mix to 40% T, 35% Body, 25% Wide",
        "Drill: Serve 50 T serves per session with targets",
        "Target zone: Within 2 feet of centerline",
        "Follow-up: Anticipate crosscourt return → hit forehand DTL",
        "Variation: Flat T on first serve, Kick T on second serve"
    ],
    "geometry": {
        "t_angle": "Centerline serve = opponent must cover 78ft diagonal to open court",
        "return_limitation": "T serve forces 80%+ crosscourt returns (predictable)",
        "positioning_advantage": "You can cheat 1-2 steps toward forehand side"
    },
    "drill_metrics": {
        "target_placement": "Within 2 feet of T",
        "target_speed": "105+ mph flat or 85+ mph kick",
        "success_criteria": "65%+ first serve points won to T",
        "follow_up": "Position for forehand on 80% of returns"
    }
}

TACTICAL_PATTERNS = {
    "crosscourt_crosscourt_dtl": {
        "name": "Crosscourt → Crosscourt → Down the Line",
        "description": "Build pressure with heavy crosscourt shots, then go down the line once they're late or out of position",
        "effectiveness": "high",
        "applies_to": ["Forehand DTL Aggression", "Deep Crosscourt Control"]
    },
    "dtl_open_court": {
        "name": "Down the Line → Open Court Crosscourt",
        "description": "Hit down the line to pull them wide, then finish into the open court",
        "effectiveness": "high",
        "applies_to": ["Forehand DTL Aggression"]
    },
    "inside_forehand": {
        "name": "Inside Forehand Pattern",
        "description": "Run around backhand, hit inside-out crosscourt, then use inside-in (down the line) for variety",
        "effectiveness": "medium-high",
        "applies_to": ["Forehand DTL Aggression", "Deep Crosscourt Control"]
    },
    "serve_t_followup": {
        "name": "T Serve → Forehand Down the Line",
        "description": "Serve to T forces crosscourt return, then attack down the line with forehand",
        "effectiveness": "high",
        "applies_to": ["Serve to T Dominance", "Forehand DTL Aggression"]
    },
    "short_ball_punish": {
        "name": "Short Ball → Aggressive Attack",
        "description": "Any ball inside service line = immediate attack down the line or crosscourt angle",
        "effectiveness": "high",
        "applies_to": ["Missed Attacks Fix"]
    }
}

def evaluate_shot_quality(shot: dict, rally_context: dict, opponent_position: Optional[dict] = None) -> dict:
    """
    Evaluate tactical quality of a shot based on professional tennis strategy
    
    Returns:
        dict with keys: quality (good/neutral/poor), reason, alternative
    """
    shot_type = shot.get('shot_type', '').lower()
    speed = shot.get('speed_mph', 0)
    depth = shot.get('depth', 'mid')
    player_x = shot.get('player_position', {}).get('x', 50)
    landing_x = shot.get('landing_zone', {}).get('x', 50)
    
    # Determine direction
    is_crosscourt = (player_x < 50 and landing_x < 50) or (player_x > 50 and landing_x > 50)
    is_down_line = (player_x < 50 and landing_x > 50) or (player_x > 50 and landing_x < 50)
    
    if 'forehand' in shot_type:
        # Deep heavy forehand crosscourt - generally good
        if is_crosscourt and depth == 'deep' and speed > 65:
            return {
                'quality': 'good',
                'reason': 'Deep heavy forehand crosscourt - largest margin, resets rally, builds pressure',
                'tactical_context': 'Neutral/defensive shot - maintaining control'
            }
        
        # Deep heavy forehand down the line - context-dependent
        if is_down_line and depth == 'deep' and speed > 65:
            # Could be good if you have control, risky if stretched
            return {
                'quality': 'neutral',
                'reason': 'Deep heavy forehand down the line - effective if balanced, risky if stretched',
                'tactical_context': 'Attacking shot - changing direction to break pattern',
                'warning': 'Lower margin shot - requires balance and control'
            }
        
        # Soft forehand to opponent's forehand side - poor
        if speed < 60 and depth in ['short', 'mid'] and landing_x > 50:
            return {
                'quality': 'poor',
                'reason': 'Soft forehand to opponent\'s forehand strength - should target backhand',
                'alternative': 'Hit deep heavy crosscourt to backhand (ad side) or wait for better opportunity'
            }
    
    if 'backhand' in shot_type:
        # Deep heavy backhand crosscourt - good
        if is_crosscourt and depth == 'deep' and speed > 60:
            return {
                'quality': 'good',
                'reason': 'Deep heavy backhand crosscourt - safe, high margin, maintains position',
                'tactical_context': 'Neutral/defensive shot'
            }
        
        # Soft backhand down the line - generally poor
        if is_down_line and speed < 65 and depth in ['short', 'mid']:
            return {
                'quality': 'poor',
                'reason': 'Soft backhand down the line feeds opponent\'s forehand strength',
                'alternative': 'Hit deep heavy crosscourt to their backhand instead'
            }
    
    return {
        'quality': 'neutral',
        'reason': 'Standard shot - context needed for deeper evaluation'
    }


def get_tactical_pattern_recommendation(rally_history: list) -> str:
    """
    Analyze rally history and recommend tactical pattern
    
    Args:
        rally_history: List of recent shots in rally
        
    Returns:
        String recommendation for next shot
    """
    if len(rally_history) < 2:
        return "Build pressure with deep heavy crosscourt shots"
    
    # Check if pattern is crosscourt → crosscourt
    recent_shots = rally_history[-2:]
    crosscourt_count = sum(1 for s in recent_shots if s.get('is_crosscourt'))
    
    if crosscourt_count >= 2:
        return "Classic pattern detected: After 2+ crosscourt shots, go down the line to break opponent's rhythm"
    
    return "Continue building pressure crosscourt, look for short ball to attack"


# ==============================================================================
# POSITION-AWARE TACTICS
# ==============================================================================

POSITION_BASED_TACTICS = {
    "deep_behind_baseline": {
        "position": "3+ feet behind baseline, defensive",
        "best_shots": [
            "Deep heavy crosscourt with topspin (65+ mph, 2-3ft net clearance)",
            "High looping topspin to push opponent back",
            "Defensive slice to change pace and buy time"
        ],
        "avoid": [
            "Down-the-line attacks (too risky when defensive)",
            "Flat aggressive shots (need margin when stretched)",
            "Short balls / drop shots (can't set them up from defense)"
        ],
        "reasoning": "You're defensive - prioritize recovery over attacking",
        "court_positioning": "Hit crosscourt to maintain center court position",
        "success_metrics": {
            "goal": "Reset rally to neutral, regain court position",
            "depth_target": "Last 10 feet of court (80%+ accuracy)",
            "net_clearance": "3-4 feet for safety margin"
        }
    },
    "baseline_neutral": {
        "position": "On or near baseline, neutral rally",
        "best_shots": [
            "Deep crosscourt to maintain position (65-75 mph)",
            "Heavy topspin to push opponent deep",
            "Occasional DTL to change rhythm (after 2-3 crosscourts)"
        ],
        "avoid": [
            "Forcing shots when no opening exists",
            "Going for winners from neutral position"
        ],
        "reasoning": "Build pressure, wait for opportunity to attack",
        "tactical_goal": "Control rally tempo, force opponent errors",
        "success_metrics": {
            "rally_control": "Keep opponent behind baseline 70%+ of time",
            "depth": "80%+ balls landing deep",
            "pattern": "2-3 crosscourts → then DTL when they're late"
        }
    },
    "inside_baseline": {
        "position": "1-3 feet inside baseline, offensive position",
        "best_shots": [
            "Down-the-line attack (75+ mph)",
            "Sharp crosscourt angle",
            "Approach shot deep DTL + move to net",
            "Inside-out forehand (if running around backhand)"
        ],
        "avoid": [
            "Soft rallying crosscourt (wasting offensive position)",
            "Playing it safe (you have control - use it)"
        ],
        "reasoning": "You have control - change direction or finish point",
        "tactical_mindset": "Attack mode - don't give opponent time",
        "success_metrics": {
            "attack_rate": "70%+ of inside baseline shots should be attacks",
            "speed_target": "75-85 mph minimum",
            "point_outcome": "Win 60%+ of points when inside baseline"
        }
    },
    "short_ball_zone": {
        "position": "Inside service line, ball landed short",
        "best_shots": [
            "Aggressive attack DTL (80+ mph)",
            "Sharp crosscourt angle for winner",
            "Approach shot deep + follow to net",
            "Drop shot if opponent is way back"
        ],
        "avoid": [
            "Soft rally shot back to opponent (NEVER - this is a gift)",
            "Playing it safe"
        ],
        "reasoning": "Short ball = FREE POINT - must punish 70%+ of time",
        "geometry_advantage": "You're 15-20 feet closer = 15-20% less court to cover",
        "success_metrics": {
            "conversion_rate": "70% minimum (21 out of 30 winners/forced errors)",
            "attack_speed": "80+ mph for putaways, 75+ mph for approaches",
            "approach_depth": "Within 10 feet of baseline"
        }
    },
    "at_net": {
        "position": "Inside service line, at net for volley",
        "best_shots": [
            "Volley to open court (sharp angle)",
            "Deep volley to opponent's weakness",
            "Drop volley if they're back",
            "Overhead smash on lobs"
        ],
        "avoid": [
            "Soft volleys that sit up",
            "Hitting back to center of court (gives them passing shot)",
            "Hesitating - commit to the finish"
        ],
        "reasoning": "At net = finish point within 1-2 shots",
        "tactical_mindset": "You're in control - put ball away or force error",
        "success_metrics": {
            "point_win_rate": "75%+ when at net",
            "volley_placement": "Aim for feet or sharp angles",
            "decisiveness": "No more than 2 volleys to finish point"
        }
    },
    "moving_forward": {
        "position": "Transitioning from baseline to net",
        "best_shots": [
            "Approach shot deep DTL",
            "Heavy topspin to feet",
            "Slice approach low and deep"
        ],
        "avoid": [
            "Short approach shots (opponent passes you easily)",
            "Soft approaches without moving forward"
        ],
        "reasoning": "Approach must be good enough to set up easy volley",
        "tactical_execution": "Hit approach → split step → close to net",
        "success_metrics": {
            "approach_depth": "Last 10 feet of court",
            "approach_speed": "70+ mph",
            "net_closure": "Get within 10 feet of net after approach"
        }
    },
    "moving_backward": {
        "position": "Retreating, defensive scramble",
        "best_shots": [
            "High defensive lob (buy time)",
            "Heavy topspin to push them back",
            "Slice to change pace"
        ],
        "avoid": [
            "Trying to hit winners (too risky when off-balance)",
            "Going down the line (lower margin)"
        ],
        "reasoning": "Get back into point - survival first, then counter",
        "tactical_goal": "Neutralize opponent's advantage",
        "success_metrics": {
            "survival_rate": "Stay in rally 60%+ of time",
            "recovery": "Get back to center court position"
        }
    }
}

# ==============================================================================
# OPPONENT STYLE ADAPTATION
# ==============================================================================

OPPONENT_STYLE_TACTICS = {
    "baseliner": {
        "characteristics": [
            "Prefers long rallies from baseline",
            "Solid groundstrokes, good consistency",
            "Uncomfortable at net",
            "Doesn't vary pace much"
        ],
        "exploit": [
            "Pull them forward with drop shots (5-8 per set)",
            "Attack the net yourself (they can't pass well)",
            "Change pace - mix slice with topspin",
            "Use angles to move them wide, then attack open court"
        ],
        "avoid": [
            "Long baseline rallies (their strength)",
            "Predictable rally patterns (they groove their shots)",
            "Giving them rhythm"
        ],
        "tactical_gameplan": "Disrupt their comfort zone - short balls, net approaches, pace changes",
        "key_stat": "Reduce rally length to 5-7 shots (vs 9+ they prefer)",
        "serve_strategy": {
            "placement": "Vary placement to prevent rhythm (40% T, 30% Body, 30% Wide)",
            "follow_up": "Attack their return + approach net on 40% of serves"
        },
        "return_strategy": {
            "positioning": "Neutralize their serve, then take over rally",
            "target": "Deep crosscourt to start, then attack with DTL"
        }
    },
    "serve_volleyer": {
        "characteristics": [
            "Big serve + immediate net approach",
            "Good volleys, comfortable at net",
            "Weaker groundstrokes from baseline",
            "Prefers short points"
        ],
        "exploit": [
            "Low returns at their feet (makes volley difficult)",
            "Topspin passing shots DTL",
            "Lob over their head when they crowd net",
            "Make them play from baseline (their weakness)"
        ],
        "avoid": [
            "Floating returns that set up easy volleys",
            "Trying to pass them every time (mix with lobs)",
            "Going for too much on return (they want quick errors)"
        ],
        "tactical_gameplan": "Force them to hit volleys from low position, use passing shots + lobs",
        "key_stat": "Return low (below net height) on 70%+ of returns",
        "serve_strategy": {
            "placement": "Mix it up - they'll attack net regardless",
            "follow_up": "Be ready for net rush, position for passing shot"
        },
        "return_strategy": {
            "positioning": "Stand 2-3 feet inside baseline for quicker returns",
            "target": "At their feet as they move forward (topspin or slice)",
            "variation": "70% low returns, 20% lobs, 10% passing shots"
        }
    },
    "counterpuncher": {
        "characteristics": [
            "Defensive style, retrieves everything",
            "Consistent but not powerful",
            "Waits for opponent errors",
            "Good court coverage, fitness"
        ],
        "exploit": [
            "Be patient, construct points carefully",
            "Use angles + drop shots to make them run",
            "Come to net (they struggle with passing shots under pressure)",
            "Vary pace and spin to prevent rhythm"
        ],
        "avoid": [
            "Going for low-percentage winners (they want you to miss)",
            "Getting frustrated by long rallies",
            "Falling into predictable patterns"
        ],
        "tactical_gameplan": "Patience + point construction - make them hit extra balls under pressure",
        "key_stat": "Win 65%+ of points lasting 9+ shots (their specialty)",
        "mental_approach": {
            "mindset": "This is a chess match - outthink, don't overpower",
            "rally_length": "Be willing to play 11-15 shot rallies",
            "finishing": "Build, build, build → then finish with approach + volley"
        },
        "serve_strategy": {
            "placement": "Kick serves to backhand (make them generate pace)",
            "follow_up": "Be prepared for neutral returns, build point"
        },
        "return_strategy": {
            "target": "Deep and consistent - they want you to miss",
            "approach": "Start neutral, probe for weakness, then attack"
        }
    },
    "big_hitter": {
        "characteristics": [
            "Powerful groundstrokes (80+ mph average)",
            "Goes for winners early in rally",
            "Can hit through opponent",
            "Higher error rate when forced to adjust"
        ],
        "exploit": [
            "Change pace - slice, angles, moon balls",
            "Move them around - don't give sitting balls",
            "Use their pace against them (block back)",
            "Wrong-foot them with direction changes"
        ],
        "avoid": [
            "Giving them sitting balls mid-court to crush",
            "Trading power with them (they're stronger)",
            "Predictable patterns (easy for them to tee off)"
        ],
        "tactical_gameplan": "Disrupt timing with pace changes, angles, and movement",
        "key_stat": "Reduce their average shot speed by 15% through pace variation",
        "serve_strategy": {
            "placement": "Vary heavily - don't give them groove",
            "spin": "Use kick serves to push them back (harder to attack)",
            "follow_up": "Change direction early to prevent setup"
        },
        "return_strategy": {
            "positioning": "Stand further back to handle big serves",
            "target": "Block low and slice (take pace off)",
            "variation": "Never give same return twice in a row"
        }
    },
    "all_court_player": {
        "characteristics": [
            "Comfortable anywhere on court",
            "Good variety in shots and tactics",
            "Adapts well to different styles",
            "No major weaknesses"
        ],
        "exploit": [
            "Test all areas to find micro-weaknesses",
            "Impose YOUR gameplan (don't let them dictate)",
            "Use your strengths more aggressively",
            "Out-execute them on big points"
        ],
        "avoid": [
            "Letting them control tempo and tactics",
            "Playing their game instead of yours",
            "Being too tentative on big points"
        ],
        "tactical_gameplan": "This is a pure execution battle - execute your patterns better",
        "key_stat": "Win 55%+ of break points (slight execution edge wins)",
        "serve_strategy": {
            "placement": "Go to your strength serve 50%+ on big points",
            "follow_up": "Execute serve+1 patterns aggressively"
        },
        "return_strategy": {
            "target": "Probe early, then attack their weaker wing",
            "aggression": "Be aggressive on second serves (they won't give gifts)"
        }
    }
}

# ==============================================================================
# SCORE-SITUATIONAL TACTICS
# ==============================================================================

SCORE_BASED_TACTICS = {
    "tiebreak": {
        "mental_approach": "Every point is a mini break point - max focus",
        "serve_strategy": {
            "first_serve_target": "75%+ to your strength serve (T, wide, or body)",
            "second_serve": "Be aggressive - don't give free points",
            "placement": "Don't experiment - stick to proven patterns"
        },
        "return_strategy": {
            "first_serve": "Neutralize - get it back deep",
            "second_serve": "Attack aggressively - this is your chance",
            "mental": "One break is huge - fight hard on their serves"
        },
        "point_construction": {
            "length": "Shorten points - attack on shot 2-3",
            "style": "Be aggressive but not reckless",
            "big_points": "At 3-3, 4-4, 5-5 use absolute best patterns"
        },
        "mini_break": "First to 3 points = psychological advantage, protect it",
        "changeover": "Use time to reset mentally between point clusters",
        "success_metrics": {
            "serve_hold": "Should win 70%+ of your serve points",
            "return_break": "Need to win 30%+ of their serve points",
            "first_to_5": "Reaching 5 points first = 65% win probability"
        }
    },
    "leading_5_2": {
        "mental_approach": "Close it out - don't let them back in",
        "serve_strategy": {
            "consistency": "Go to bread and butter serves - no experiments",
            "first_serve_pct": "Get 65%+ first serves in",
            "placement": "Use your highest win-rate serve location",
            "follow_up": "Execute your best serve+1 patterns"
        },
        "return_strategy": {
            "aggression": "Be measured - don't overhit",
            "target": "Deep and neutral, let them feel pressure"
        },
        "tactics": {
            "use_patterns": "Stick to what's working - this is NOT the time to try new things",
            "maintain_intensity": "Don't drop energy - finish strong",
            "avoid_giving_life": "Make them earn every point"
        },
        "mental_traps": {
            "overconfidence": "Don't assume it's over",
            "passive_play": "Don't play not to lose - keep using your weapons",
            "rushing": "Take full time between points"
        },
        "success_metrics": {
            "close_rate": "Should close out 85%+ of these situations",
            "unforced_errors": "Keep same error rate as earlier in match"
        }
    },
    "trailing_2_5": {
        "mental_approach": "Nothing to lose - take calculated risks",
        "serve_strategy": {
            "aggression": "Be more aggressive on second serves",
            "placement": "Go for broke on 20-30% of serves (surprise them)",
            "follow_up": "Attack immediately after serve"
        },
        "return_strategy": {
            "positioning": "Stand 1-2 feet closer for quicker returns",
            "aggression": "Attack their second serves aggressively",
            "target": "Go for their weakness - no safe returns"
        },
        "tactics": {
            "break_rhythm": "Try different patterns to disrupt them",
            "mix_it_up": "Slice, drop shots, come to net - variety",
            "momentum_shift": "One break gets you right back in it"
        },
        "mental_mindset": {
            "free_swinging": "Play loose - pressure is on them to close",
            "one_game": "Focus on winning THIS game, not the set",
            "belief": "Comebacks happen when you keep fighting"
        },
        "success_metrics": {
            "break_chance": "Need to convert 40%+ of break point chances",
            "risk_taking": "Increase winner attempts by 25%"
        }
    },
    "close_game_40_30": {
        "mental_approach": "One point from winning - be aggressive",
        "serve_strategy": {
            "placement": "Go to your best serve for this score",
            "first_serve": "Get it in - don't double fault",
            "follow_up": "Attack their return aggressively"
        },
        "return_strategy": {
            "aggression": "This is their pressure point - attack",
            "target": "Go to their weakness - they might crack"
        },
        "tactics": "Use your strengths - don't play it safe",
        "success_metrics": {
            "conversion": "Win 70%+ of these points when serving",
            "break": "Win 35%+ of these points when returning"
        }
    },
    "deuce_crucial": {
        "mental_approach": "Battle for advantage - every point matters",
        "serve_strategy": {
            "placement": "Vary to prevent opponent prediction",
            "consistency": "Avoid double faults at all costs",
            "follow_up": "Be ready for war - might be long point"
        },
        "return_strategy": {
            "neutralize": "Get it back, then construct point",
            "patience": "Don't go for too much too early"
        },
        "tactics": "This is mental strength test - who wants it more",
        "long_deuces": {
            "stamina": "May go to 5+ deuces - conserve energy",
            "mental": "Stay patient, wait for opportunity",
            "pattern": "Stick to reliable patterns, avoid experiments"
        }
    }
}

# ==============================================================================
# ADVANCED SHOT SEQUENCING
# ==============================================================================

ADVANCED_SEQUENCES = {
    "dropshot_setup": {
        "sequence": [
            "Shot 1: Deep heavy topspin crosscourt (push opponent back)",
            "Shot 2: Deep heavy topspin crosscourt (confirm they're deep)",
            "Shot 3: Drop shot to open court (they're 25+ feet from net)"
        ],
        "conditions": "After 2+ deep shots forcing opponent behind baseline",
        "success_rate": "65% if opponent is 20+ feet behind baseline",
        "execution_keys": [
            "First 2 shots must land deep (last 10ft of court)",
            "Opponent must be moving backward or stationary",
            "Drop shot must clear net by 6-12 inches (soft touch)",
            "Aim for opponent's backhand side (harder to retrieve)"
        ],
        "counter_if_fails": "If they get to it, lob over their head"
    },
    "inside_out_inside_in": {
        "sequence": [
            "Shot 1: Run around backhand to hit forehand",
            "Shot 2: Inside-out forehand crosscourt (pull them wide)",
            "Shot 3: Inside-in forehand DTL (wrong-foot them)"
        ],
        "conditions": "When you have time to run around backhand",
        "success_rate": "70% when opponent expects 3rd crosscourt",
        "execution_keys": [
            "Shot 1: Must recover to center after running around",
            "Shot 2: Heavy topspin to pull them 6+ feet wide",
            "Shot 3: Wait for them to commit to crosscourt defense",
            "Shot 3: Hit DTL with 75+ mph"
        ],
        "pro_pattern": "Nadal's signature - devastating when executed well"
    },
    "approach_volley_finish": {
        "sequence": [
            "Shot 1: Approach shot deep DTL (forces weak reply)",
            "Shot 2: Split step at service line",
            "Shot 3: Volley to open court for winner"
        ],
        "conditions": "On short balls inside service line",
        "success_rate": "75% if approach lands within 10ft of baseline",
        "execution_keys": [
            "Approach depth is critical - last 10 feet",
            "Approach speed minimum 70 mph",
            "Split step as they make contact",
            "Close to net quickly - get within 10 feet",
            "Volley placement: Aim for feet or sharp angles"
        ],
        "common_error": "Approaching with soft shot - opponent passes easily"
    },
    "serve_plus_one": {
        "sequence": [
            "Shot 1: Serve to T (forces crosscourt return 80% of time)",
            "Shot 2: Forehand DTL attack to open court"
        ],
        "conditions": "When serving on deuce or ad court",
        "success_rate": "65-70% when executed correctly",
        "execution_keys": [
            "Serve must be to T (not wide or body)",
            "Anticipate crosscourt return - cheat 1 step toward forehand",
            "Attack with 75+ mph DTL forehand",
            "If they go DTL on return, you're out of position - adjust"
        ],
        "variations": {
            "serve_wide": "Serve wide → expect DTL return → hit inside-out",
            "serve_body": "Serve body → expect weak middle return → attack anywhere"
        }
    },
    "change_pace_attack": {
        "sequence": [
            "Shot 1-2: Slice backhands (slow pace, low balls)",
            "Shot 3: Heavy topspin attack (sudden pace change)"
        ],
        "conditions": "When opponent is getting rhythm on your shots",
        "success_rate": "60% due to disrupted timing",
        "execution_keys": [
            "Slice must be low (below net height)",
            "Slice depth: Mid-court to pull them forward",
            "Shot 3: Sudden acceleration to 75+ mph",
            "Target their weakness with the attack"
        ],
        "tactical_reasoning": "Pace change disrupts timing - they're geared for slow ball"
    },
    "lob_overhead_finish": {
        "sequence": [
            "Shot 1: Defensive lob over opponent at net",
            "Shot 2: Recover to center court",
            "Shot 3: Overhead smash their defensive shot"
        ],
        "conditions": "When opponent is at net and crowding",
        "success_rate": "55% - difficult but effective",
        "execution_keys": [
            "Lob must clear their reach by 2+ feet",
            "Lob depth: Within 10 feet of baseline (not short)",
            "Recover quickly - they'll lob back",
            "Overhead: Hit to open court or at their feet"
        ]
    }
}

# ==============================================================================
# ENERGY MANAGEMENT
# ==============================================================================

ENERGY_MANAGEMENT = {
    "high_energy": {
        "set_timing": "Set 1, early Set 2",
        "physical_state": "Fresh, explosive movement available",
        "tactical_approach": {
            "court_coverage": "Cover full court - chase down everything",
            "rally_length": "Can afford 9-12 shot rallies",
            "short_balls": "Sprint for every short ball",
            "serve_strategy": "Aggressive first serves, kick second serves (requires legs)"
        },
        "shot_selection": {
            "defense": "Run down every ball - make them hit winners",
            "offense": "Attack short balls with full commitment",
            "movement": "Use full court - hit angles and make them run"
        },
        "serve_approach": {
            "first_serve": "Go for power - 85% effort",
            "second_serve": "Kick serves (require leg drive)",
            "serve_volley": "Can serve-and-volley 20-30% of time"
        },
        "return_approach": {
            "positioning": "Can stand inside baseline for aggressive returns",
            "movement": "Sprint for wide serves"
        }
    },
    "medium_energy": {
        "set_timing": "Mid Set 2, early Set 3",
        "physical_state": "Solid but need to manage output",
        "tactical_approach": {
            "rally_length": "Target 6-8 shot rallies (shorten from early match)",
            "point_shortening": "Attack earlier in rally (shot 3-4 vs shot 5-6)",
            "serve_strategy": "70% first serve in (don't waste energy on second serves)"
        },
        "shot_selection": {
            "smart_defense": "Pick which balls to chase - let some go",
            "offense": "Attack short balls but choose best opportunities",
            "drop_shots": "Use 3-5 per set to vary point length"
        },
        "serve_approach": {
            "first_serve": "Maintain quality, reduce max effort serves",
            "second_serve": "More slice, less kick (slice requires less energy)",
            "serve_volley": "Increase to 30% to shorten points"
        },
        "energy_conservation": {
            "between_points": "Use full 25 seconds",
            "changeovers": "Sit down, breathe deep, visualize next game",
            "hydration": "Drink on every changeover"
        }
    },
    "low_energy": {
        "set_timing": "Late Set 3, any Set 4-5",
        "physical_state": "Fatigued, must shorten points",
        "tactical_approach": {
            "rally_length": "Target 3-5 shots maximum",
            "point_shortening": "MUST attack by shot 2-3",
            "serve_strategy": "First serve = free points, attack immediately after"
        },
        "shot_selection": {
            "smart_not_hard": "Placement over power",
            "offense": "Attack earlier but with smarter placement",
            "conserve_movement": "Reduce court coverage - opponent must hit winners"
        },
        "serve_approach": {
            "first_serve": "Placement over power - conserve energy",
            "second_serve": "No kick serves (too taxing) - use slice only",
            "serve_volley": "Increase to 50%+ to avoid baseline rallies"
        },
        "mental_toughness": {
            "between_points": "Full 25 seconds - recover completely",
            "belief": "Who wants it more - mental game now",
            "pattern": "Use smart tactics to compensate for tired legs"
        },
        "high_percentage_tennis": {
            "reduce_errors": "Can't afford unforced errors",
            "serve_holds": "MUST hold serve (avoid long deuce games)",
            "break_points": "Go all-in on break point chances (might only get 1-2)"
        }
    },
    "point_shortening_tactics": {
        "serve_volley": "Finish points in 2-4 shots instead of 8-12",
        "approach_net": "Attack short balls + come to net (3-5 shot points)",
        "second_shot_attack": "Don't rally - attack on your 2nd or 3rd shot",
        "big_serves": "Use serve as weapon to get free points",
        "return_aggression": "Attack second serves immediately",
        "target_metrics": {
            "high_energy": "Average rally length 8-10 shots",
            "medium_energy": "Average rally length 6-8 shots",
            "low_energy": "Average rally length 4-5 shots"
        }
    }
}

# ==============================================================================
# BREAK POINT MASTERY
# ==============================================================================

BREAK_POINT_TACTICS = {
    "serving_break_point": {
        "mental_approach": {
            "mindset": "This is where champions are made - use your weapons",
            "avoid": "Playing it safe - that's how you lose",
            "mantra": "Go to my strength, trust my patterns"
        },
        "serve_strategy": {
            "placement": "Go to your highest win-rate serve (for most: T serve at 65-70%)",
            "first_serve": "Must get it in - but don't push (serve at 80-85% effort)",
            "second_serve": "Be aggressive - don't give free point",
            "stats_benchmark": "First serve % on BP should match your average (don't push or over-hit)"
        },
        "serve_patterns": {
            "deuce_court": "T serve → anticipate crosscourt return → forehand DTL",
            "ad_court": "Body serve → weak return → attack anywhere",
            "variation": "If they're cheating, go opposite direction"
        },
        "second_serve_approach": {
            "placement": "Kick to backhand or slice wide",
            "follow_up": "Attack their return immediately - don't rally",
            "mindset": "Even on second serve, be the aggressor"
        },
        "success_metrics": {
            "save_rate": "Should save 60-65% of break points",
            "first_serve_in": "65%+ (same as overall)",
            "pattern_execution": "Use your best serve+1 pattern"
        },
        "common_errors": {
            "double_fault": "Happens from over-thinking - trust your motion",
            "soft_second": "Giving them easy ball to attack",
            "no_follow_up": "Serving well but not attacking the return"
        }
    },
    "returning_break_point": {
        "mental_approach": {
            "mindset": "THIS IS YOUR OPPORTUNITY - be aggressive",
            "avoid": "Playing it safe and hoping for error",
            "belief": "I'm going to TAKE this break, not wait for it"
        },
        "return_strategy": {
            "positioning": "Stand 1-2 feet closer to baseline (show aggression)",
            "target": "Their weakness (usually backhand) deep or at feet",
            "goal": "Put pressure on them immediately - don't give neutral ball"
        },
        "first_serve_return": {
            "approach": "Neutralize with deep return",
            "target": "Crosscourt to their backhand, then construct point",
            "mindset": "Get it back deep, then attack on next shot"
        },
        "second_serve_return": {
            "approach": "ATTACK - this is your chance",
            "target": "DTL to their weakness or sharp crosscourt angle",
            "speed": "Return with 70+ mph - pressure them",
            "mindset": "Break their confidence with aggressive return"
        },
        "tactical_patterns": {
            "after_return": "If you get good return, attack on very next shot",
            "pressure": "They feel the pressure - make them hit one more ball",
            "patience": "Don't overhit - construct the point if needed"
        },
        "success_metrics": {
            "conversion_rate": "Should convert 25-35% of break points (pro benchmark)",
            "return_depth": "80%+ deep returns on break point",
            "aggression_level": "40%+ of BP returns should be attacks"
        },
        "common_errors": {
            "over_hitting": "Going for too much on return",
            "passive_return": "Giving soft ball back and hoping",
            "mental_letdown": "Not fighting hard enough for the opportunity"
        }
    },
    "break_point_conversion": {
        "psychology": {
            "first_bp": "May not convert - be ready for multiple chances",
            "multiple_bps": "If you get 3+ chances, MUST convert at least one",
            "momentum": "Converting BP = huge momentum swing"
        },
        "statistics": {
            "pro_average": "30-35% conversion rate",
            "elite": "40%+ conversion (Djokovic, Nadal level)",
            "recreational": "20-25% conversion",
            "target": "Improve by 5-10% through tactics and mindset"
        },
        "improvement_tactics": {
            "return_position": "Stand closer on second serves",
            "target_clarity": "Know exactly where you're returning before serve",
            "aggressive_mindset": "You're taking the break, not waiting for it",
            "pattern_execution": "Have specific BP return patterns practiced"
        }
    },
    "defending_break_points": {
        "psychology": {
            "one_point": "It's just one point - execute your best pattern",
            "pressure_on_them": "They have to make the return and win the point",
            "history": "Great players save 60-70% of break points"
        },
        "tactics": {
            "serve_selection": "Your #1 serve pattern - not the time to experiment",
            "aggressive_follow_up": "Attack their return immediately",
            "court_positioning": "Anticipate based on your serve placement"
        },
        "mental_keys": {
            "breathing": "2 deep breaths before serving",
            "visualization": "See yourself executing perfect serve before toss",
            "routine": "Same pre-serve routine as any other point",
            "confidence": "Trust your serve - it's won you points all match"
        }
    }
}
