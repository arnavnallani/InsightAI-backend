"""
Advanced Pattern Discovery Engine for Tennis Matches

Uses sophisticated pattern recognition to discover:
- Shot sequence patterns (what you repeatedly do)
- Situational patterns (when you do it)
- Outcome correlations (how it affects points)
- Temporal patterns (early match vs late match)

Each pattern includes:
- 9-12 supporting moments showing the pattern (with Monte Carlo minimax optimal alternatives)
- 1-2 critical moments where it mattered most (with butterfly effect analysis)
- Specific improvement path
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
from .strategic_flow_models import (
    ShotType, ShotDirection, ShotDepth,
    MatchState, CourtPosition, OpponentTendencyProfile, BreakdownThreshold
)
from .minimax_core import MinimaxSimulationCore
from .tendency_learner import OpponentTendencyLearner
from .impact_models import ImpactModels
from .tennis_strategy_knowledge import (
    FOREHAND_CROSSCOURT_STRATEGY,
    FOREHAND_DOWN_LINE_STRATEGY,
    TACTICAL_PATTERNS,
    evaluate_shot_quality
)


class AdvancedPatternDiscoveryEngine:
    """
    State-of-the-art pattern discovery for tennis matches.
    
    Discovers patterns at multiple levels:
    - Shot patterns (what shots you hit)
    - Tactical patterns (how you construct points)
    - Strategic patterns (how you respond to pressure)
    - Mental patterns (when you make mistakes)
    """
    
    def __init__(self):
        self.min_pattern_instances = 6  # Adaptive threshold
        self.min_critical_instances = 1
        self.tendency_learner = OpponentTendencyLearner()
        self.impact_models = ImpactModels()
        self.opponent_profile = None  # Will be learned once per match
    
    def discover_match_patterns(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        player_name: str,
        opponent_name: str
    ) -> List[Dict[str, Any]]:
        """
        Discover all significant patterns in the match.
        
        Returns 3-4 patterns on average, each with:
        - 8-12 supporting moments (with Monte Carlo minimax optimal alternatives)
        - 1-2 critical moments (lost points + butterfly effects)
        """
        # Learn opponent tendencies once for all minimax simulations
        print(f"[Pattern Discovery] Learning {opponent_name}'s tendencies...", file=__import__('sys').stderr)
        self.opponent_profile = self.tendency_learner.learn_from_match(
            shots, rallies, player_name
        )
        
        all_patterns = []
        
        # Build rally index for efficient lookup
        rally_shots = self._build_rally_index(shots)
        
        # Pattern 1: Weakness exploitation (soft shots to opponent strength)
        weakness_pattern = self._discover_weakness_pattern(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if weakness_pattern:
            all_patterns.append(weakness_pattern)
        
        # Pattern 2: Missed attack opportunities
        missed_attack_pattern = self._discover_missed_attacks(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if missed_attack_pattern:
            all_patterns.append(missed_attack_pattern)
        
        # Pattern 3: Pressure point performance
        pressure_pattern = self._discover_pressure_response(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if pressure_pattern:
            all_patterns.append(pressure_pattern)
        
        # Pattern 4: Rally construction failures
        rally_construction_pattern = self._discover_rally_construction_issues(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if rally_construction_pattern:
            all_patterns.append(rally_construction_pattern)
        
        # Pattern 5: Serve placement predictability
        serve_pattern = self._discover_serve_pattern(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if serve_pattern:
            all_patterns.append(serve_pattern)
        
        # Pattern 6: Return position issues
        return_pattern = self._discover_return_pattern(
            shots, rallies, rally_shots, player_name, opponent_name
        )
        if return_pattern:
            all_patterns.append(return_pattern)
        
        # Enrich all patterns with Monte Carlo minimax analysis
        print(f"[Pattern Discovery] Enriching patterns with Monte Carlo minimax...", file=__import__('sys').stderr)
        enriched_patterns = []
        for pattern in all_patterns:
            enriched = self._enrich_pattern_with_minimax(
                pattern, rally_shots, player_name, rallies, shots
            )
            enriched_patterns.append(enriched)
        
        return enriched_patterns
    
    def _build_rally_index(self, shots: List[Dict]) -> Dict[int, List[Dict]]:
        """Build index mapping rally_id -> shots for efficient lookup"""
        rally_shots = defaultdict(list)
        for shot in shots:
            rally_id = shot.get('rally_id', shot.get('rally_number', 0))
            rally_shots[rally_id].append(shot)
        return rally_shots
    
    def _generate_rally_summary(
        self,
        rally_context: Dict,
        key_shot: Dict,
        player_name: str
    ) -> str:
        """Generate a concise narrative summary of what happened in this specific rally"""
        shots = rally_context.get('shots', [])
        winner = rally_context.get('winner', '')
        score = rally_context.get('point_score', rally_context.get('score', ''))
        
        if not shots:
            return "Rally details not available"
        
        # Build rally narrative
        shot_count = len(shots)
        outcome = "won point" if winner == player_name else "lost point"
        
        # Identify key moment (the problematic shot)
        key_shot_num = key_shot.get('shot_number', -1)
        key_shot_type = key_shot.get('shot_type', 'shot')
        key_shot_speed = key_shot.get('speed_mph', 0)
        key_shot_depth = key_shot.get('depth', '')
        
        # Find opponent's response
        opponent_response = None
        for shot in shots:
            if shot.get('shot_number', -1) == key_shot_num + 1:
                opponent_response = shot
                break
        
        if opponent_response:
            opp_shot_type = opponent_response.get('shot_type', 'shot')
            opp_speed = opponent_response.get('speed_mph', 0)
            is_winner = opponent_response.get('is_winner', False)
            
            if is_winner:
                return f"{shot_count}-shot rally. You hit {key_shot_type} ({key_shot_speed:.0f}mph, {key_shot_depth}), opponent attacked with {opp_shot_type} winner ({opp_speed:.0f}mph). {outcome.capitalize()} at {score}."
            else:
                return f"{shot_count}-shot rally. You hit {key_shot_type} ({key_shot_speed:.0f}mph, {key_shot_depth}), opponent countered with {opp_shot_type} ({opp_speed:.0f}mph). {outcome.capitalize()} at {score}."
        else:
            return f"{shot_count}-shot rally. You hit {key_shot_type} ({key_shot_speed:.0f}mph, {key_shot_depth}). {outcome.capitalize()} at {score}."
    
    def _enrich_pattern_with_minimax(
        self,
        pattern: Dict[str, Any],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        rallies: List[Dict],
        all_shots: List[Dict]
    ) -> Dict[str, Any]:
        """
        Enrich pattern with Monte Carlo minimax analysis.
        
        For each supporting rally:
        1. Run minimax to find optimal alternative shot
        2. Add to supporting_rallies with minimax recommendation
        
        From supporting rallies, identify 1-2 critical moments:
        1. Player lost the point
        2. Important score (break point, deuce, close game)
        3. Run full butterfly effect analysis
        """
        import time
        start_time = time.time()
        
        supporting_moments = pattern.get('supporting_rallies', [])
        enriched_supporting = []
        lost_point_candidates = []
        
        # Initialize TWO minimax cores for hybrid approach:
        # 1. Lighter analysis for supporting rallies (fast)
        # 2. Deeper analysis for critical moments (high quality)
        
        # Ensure opponent profile was learned
        if not self.opponent_profile:
            raise ValueError("Opponent profile must be learned before enriching patterns")
        
        minimax_supporting = MinimaxSimulationCore(
            opponent_profile=self.opponent_profile,
            num_rollouts=15,         # Balanced accuracy
            max_depth=2,             # Look 2 shots ahead
            branching_factor=4       # Consider all main shot types
        )
        
        minimax_critical = MinimaxSimulationCore(
            opponent_profile=self.opponent_profile,
            num_rollouts=30,         # High confidence
            max_depth=3,             # Look 3 shots ahead
            branching_factor=4       # Consider all main shot types
        )
        
        print(f"[Minimax] Processing {len(supporting_moments)} supporting moments for pattern: {pattern.get('title', 'Unknown')}", file=__import__('sys').stderr)
        
        # Process each supporting rally
        for idx, moment in enumerate(supporting_moments):
            # Extract rally information from moment structure
            rally_context = moment.get('rally', {})
            rally_id = rally_context.get('id', moment.get('rally_idx', idx))
            
            if not rally_context:
                # Keep original moment if we can't find rally context
                enriched_supporting.append(moment)
                continue
            
            # Get the problematic shot from this moment
            # Different patterns use different field names: 'shot', 'missed_shot', 'serve'
            key_shot = moment.get('shot') or moment.get('missed_shot') or moment.get('serve', {})
            
            if not key_shot:
                # No shot to analyze, keep original
                enriched_supporting.append(moment)
                continue
            
            # Build match state for minimax
            match_state = self._build_match_state_from_shot(
                key_shot, rally_context, all_shots, player_name
            )
            
            # Run minimax to find optimal alternative (using lighter parameters)
            optimal_decision_node = minimax_supporting.find_optimal_path(match_state)
            
            # Extract optimal shot from decision node
            optimal_shot = optimal_decision_node.decision if optimal_decision_node.decision else None
            
            # Generate rally summary for this specific rally
            rally_summary = self._generate_rally_summary(
                rally_context, key_shot, player_name
            )
            
            # Enrich moment with minimax recommendation
            enriched_moment = {
                **moment,
                'rally_summary': rally_summary,
                'minimax_analysis': {
                    'optimal_shot': {
                        'type': optimal_shot.shot_type.value if optimal_shot and optimal_shot.shot_type else 'GROUNDSTROKE',
                        'direction': optimal_shot.direction.value if optimal_shot and optimal_shot.direction else 'CROSSCOURT',
                        'depth': optimal_shot.depth.value if optimal_shot and optimal_shot.depth else 'DEEP',
                        'speed': optimal_shot.speed_mph if optimal_shot else 70.0
                    },
                    'expected_value': round(optimal_decision_node.value, 3),
                    'your_shot': {
                        'type': key_shot.get('shot_type', 'GROUNDSTROKE'),
                        'direction': key_shot.get('angle', 'CROSSCOURT'),
                        'depth': key_shot.get('depth', 'MID'),
                        'speed': key_shot.get('speed_mph', 0)
                    },
                    'rationale': optimal_decision_node.rationale if optimal_decision_node else 'Optimal path calculated'
                }
            }
            
            enriched_supporting.append(enriched_moment)
            
            # Track if this was a lost point for critical moment selection
            winner = rally_context.get('winner') or moment.get('outcome')
            if winner and winner != player_name:
                lost_point_candidates.append({
                    'moment': enriched_moment,
                    'rally': rally_context,
                    'score_importance': self._calculate_score_importance(rally_context)
                })
        
        # Select 1-2 critical moments (lost points + important score)
        # Use deeper minimax analysis for critical moments
        critical_moments = self._select_critical_moments(
            lost_point_candidates, minimax_critical, player_name, rallies
        )
        
        elapsed = time.time() - start_time
        print(f"[Minimax] Enriched pattern in {elapsed:.2f}s ({len(enriched_supporting)} supporting, {len(critical_moments)} critical)", file=__import__('sys').stderr)
        
        return {
            **pattern,
            'supporting_rallies': enriched_supporting,
            'critical_moments': critical_moments
        }
    
    def _build_match_state_from_shot(
        self,
        shot: Dict,
        rally_context: Dict,
        all_shots: List[Dict],
        player_name: str
    ) -> MatchState:
        """Build MatchState object from shot data for minimax simulation"""
        
        # Extract positions (normalize from 0-100 to 0-4 scale)
        player_pos = shot.get('player_position', {})
        opponent_pos = shot.get('opponent_position', {})
        
        player_position = CourtPosition(
            x=player_pos.get('x', 50.0) / 25.0,  # Normalize to 0-4
            y=player_pos.get('y', 50.0) / 25.0
        )
        
        opponent_position = CourtPosition(
            x=opponent_pos.get('x', 50.0) / 25.0,
            y=opponent_pos.get('y', 50.0) / 25.0
        )
        
        # Parse score
        score = rally_context.get('score', 'Set 1, 0-0, 0-0')
        set_num = rally_context.get('set_num', 1)
        game_score = rally_context.get('game_score', [0, 0])
        point_score = score.split(',')[-1].strip() if ',' in score else '0-0'
        
        # Energy based on rally length and fatigue
        rally_length = rally_context.get('shot_count', 3)
        player_energy = max(0.5, 1.0 - shot.get('fatigue_level', 0.0))
        opponent_energy = max(0.5, 1.0 - (rally_length / 30.0))
        
        # Build recent shots (empty for now - would need shot history)
        recent_shots = []
        
        # Default strengths/weaknesses (would ideally come from player profile)
        player_strengths = [ShotType.FOREHAND]
        player_weaknesses = [ShotType.BACKHAND]
        opponent_strengths = [ShotType.FOREHAND]
        opponent_weaknesses = [ShotType.BACKHAND]
        
        return MatchState(
            set_num=set_num,
            game_score=tuple(game_score) if isinstance(game_score, list) else (0, 0),
            point_score=point_score,
            player_energy=player_energy,
            opponent_energy=opponent_energy,
            player_momentum=0.0,  # Neutral momentum
            recent_shots=recent_shots,
            rally_length=rally_length,
            player_position=player_position,
            opponent_position=opponent_position,
            player_strengths=player_strengths,
            player_weaknesses=player_weaknesses,
            opponent_strengths=opponent_strengths,
            opponent_weaknesses=opponent_weaknesses
        )
    
    def _calculate_score_importance(self, rally_context: Dict) -> float:
        """
        Calculate how important a point was (0.0 to 1.0).
        
        ONLY truly critical moments qualify:
        - Break points (30-40, 40-Ad when opponent serving)
        - Deuce in crucial games (4-4, 5-5, 4-5, 5-4 game scores)
        
        Note: SwingVision data uses camelCase (pointScore, setNumber, gameNumber)
        """
        # Handle both camelCase (SwingVision) and snake_case (Python)
        point_score = rally_context.get('point_score', rally_context.get('pointScore', '0-0'))
        score = rally_context.get('score', point_score) # Full score string if available
        game_number = rally_context.get('game_number', rally_context.get('gameNumber', 1))
        is_deuce = rally_context.get('is_deuce', rally_context.get('isDeuce', False))
        
        # Normalize point score to uppercase for consistent matching
        point_score_upper = point_score.upper() if isinstance(point_score, str) else ''
        score_upper = score.upper() if isinstance(score, str) else ''
        
        # Break point - CRITICAL (30-40, 40-Ad, or BP marker)
        break_point_indicators = ['30-40', '40-AD', 'AD-OUT', 'BP']
        if any(indicator in score_upper or indicator in point_score_upper for indicator in break_point_indicators):
            return 1.0
        
        # Deuce in crucial games - CRITICAL
        # Game 9-10 in a set (like 4-4, 5-4, 4-5, 5-5) are crucial
        if is_deuce or 'DEUCE' in point_score_upper or '40-40' in point_score_upper:
            # Games 9-10+ are crucial (4-4, 5-4, 4-5, 5-5, etc.)
            if game_number >= 9:
                return 0.9
            # Also crucial if game 7-8 (3-3, 4-3, 3-4 game scores)
            if game_number >= 7:
                return 0.8
        
        # Not a critical moment - filter out
        return 0.0
    
    def _select_critical_moments(
        self,
        lost_point_candidates: List[Dict],
        minimax: MinimaxSimulationCore,
        player_name: str,
        rallies: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Select 1-2 critical moments from lost point candidates.
        
        Criteria:
        1. Player lost the point
        2. High score importance (must be > 0.5 to qualify as truly critical)
        3. Run butterfly effect analysis
        """
        if not lost_point_candidates:
            return []
        
        # Filter to only truly critical moments (importance > 0.5)
        # This filters out non-critical game situations
        truly_critical = [
            c for c in lost_point_candidates 
            if c['score_importance'] > 0.5
        ]
        
        if not truly_critical:
            return []
        
        # Sort by score importance
        sorted_candidates = sorted(
            truly_critical,
            key=lambda x: x['score_importance'],
            reverse=True
        )
        
        # Take top 1-2 most important
        num_critical = min(2, len(sorted_candidates))
        critical_moments = []
        
        for candidate in sorted_candidates[:num_critical]:
            moment = candidate['moment']
            rally = candidate['rally']
            
            # Add butterfly effect analysis
            butterfly_effect = self._calculate_butterfly_effect(
                rally, moment, player_name, rallies
            )
            
            critical_moment = {
                **moment,
                'is_critical': True,
                'score_importance': round(candidate['score_importance'], 2),
                'butterfly_effect': butterfly_effect
            }
            
            critical_moments.append(critical_moment)
        
        return critical_moments
    
    def _calculate_butterfly_effect(
        self,
        rally: Dict,
        moment: Dict,
        player_name: str,
        all_rallies: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate what losing this point led to, and what winning would have led to.
        
        Butterfly effect shows:
        - What actually happened (lost point → lost game → momentum shift)
        - What would have happened with optimal shot (won point → held serve → confidence)
        """
        game_number = rally.get('game_number', 1)
        score = rally.get('score', '0-0')
        
        # Find what happened after this point
        next_rallies = [r for r in all_rallies if r.get('game_number', 0) >= game_number]
        
        # What actually happened (lost the point)
        actual_outcome = {
            'immediate': f"Lost point at {score}",
            'game_impact': self._analyze_game_impact(rally, next_rallies, player_name, won=False),
            'momentum_impact': "Negative momentum shift"
        }
        
        # What would have happened (won with optimal shot)
        optimal_outcome = {
            'immediate': f"Would have won point at {score}",
            'game_impact': self._analyze_game_impact(rally, next_rallies, player_name, won=True),
            'momentum_impact': "Positive momentum shift"
        }
        
        return {
            'what_happened': actual_outcome,
            'what_would_have_happened': optimal_outcome
        }
    
    def _analyze_game_impact(
        self,
        rally: Dict,
        next_rallies: List[Dict],
        player_name: str,
        won: bool
    ) -> str:
        """Analyze what happened in the game after this point"""
        game_number = rally.get('game_number', 1)
        
        # Find the game outcome
        game_rallies = [r for r in next_rallies if r.get('game_number') == game_number]
        if game_rallies:
            last_rally_in_game = game_rallies[-1]
            game_winner = last_rally_in_game.get('game_winner', 'Unknown')
            
            if won:
                # If won the point
                if game_winner == player_name:
                    return "Would have held serve / won game"
                else:
                    return "Would have extended game, but still lost"
            else:
                # If lost the point
                if game_winner != player_name:
                    return "Lost game"
                else:
                    return "Still won game despite this point"
        
        return "Game outcome unknown"
    
    def _discover_weakness_pattern(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: Hitting soft/weak shots to opponent's strength zone.
        
        This is THE classic amateur mistake - hitting your weakness to their strength.
        Example: Soft backhand crosscourt → opponent's forehand
        """
        matching_rallies = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            # Look for player hitting soft shots
            player_shots = [s for s in shots_in_rally if s.get('player') == player_name]
            
            for shot in player_shots:
                shot_type = shot.get('shot_type', '').lower()
                speed = shot.get('speed_mph', 70)
                depth = shot.get('depth', 'mid')
                player_x = shot.get('player_position', {}).get('x', 50)
                landing_x = shot.get('landing_zone', {}).get('x', 50)
                
                # Determine court geometry:
                # X-axis: 0 (ad side/backhand) → 100 (deuce side/forehand)
                # For right-handed vs right-handed:
                # - Ad side (x < 50) = backhand side for both
                # - Deuce side (x > 50) = forehand side for both
                
                # Detect TACTICALLY WEAK shots to opponent's forehand strength:
                # 
                # Tennis Strategy Context:
                # ✅ Deep forehand crosscourt (deuce → deuce) is GOOD - maintains position
                # ✅ Deep backhand crosscourt (ad → ad) is GOOD - maintains position
                # ❌ Soft backhand down the line (ad → deuce) is BAD - feeds their forehand
                # ❌ Forehand down the line when out of position is RISKY - opens up court
                
                # Option 1: Soft backhand down the line (tactical mistake)
                # You're on ad side, hit soft/short to deuce side (opponent's forehand)
                is_weak_backhand_dtl = (
                    'backhand' in shot_type and
                    speed < 65 and
                    depth in ['short', 'mid'] and
                    player_x < 50 and  # You're on ad side (backhand)
                    landing_x > 50     # Hit to deuce side (opponent forehand)
                )
                
                # Option 2: Weak forehand that should have gone to backhand
                # Either soft crosscourt when you should attack, or down the line opening court
                is_weak_forehand = (
                    'forehand' in shot_type and
                    speed < 60 and
                    depth in ['short', 'mid'] and
                    player_x > 50 and  # You're on deuce side (forehand)
                    (
                        # Soft crosscourt to their forehand (should target backhand)
                        (landing_x > 50) or
                        # Soft down the line (opens up your backhand side)
                        (landing_x < 50)
                    )
                )
                
                is_weak_backhand = is_weak_backhand_dtl
                
                if is_weak_backhand or is_weak_forehand:
                    matching_rallies.append({
                        'rally_idx': rally_idx,
                        'rally': rally,
                        'shot': shot,
                        'shot_type': 'backhand' if is_weak_backhand else 'forehand',
                        'score': rally.get('score', 'Unknown'),
                        'outcome': rally.get('winner', 'unknown'),
                        'importance': self._calculate_importance(rally, rally_idx, len(rallies))
                    })
                    break  # One per rally
        
        if len(matching_rallies) < self.min_pattern_instances:
            return None
        
        # Sort by importance
        matching_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        # Adaptive: take 9-12 supporting rallies (or all if fewer)
        num_supporting = min(12, max(9, len(matching_rallies)))
        supporting_rallies = matching_rallies[:num_supporting]
        
        # Take top 1-2 as critical
        num_critical = min(2, len(matching_rallies))
        critical_rallies = matching_rallies[:num_critical]
        
        # Determine dominant shot type
        shot_types = [r['shot_type'] for r in matching_rallies]
        dominant_shot = Counter(shot_types).most_common(1)[0][0]
        
        # Determine the direction and strategic context using professional tennis knowledge
        if dominant_shot == "backhand":
            direction = "down the line"
            strategic_error = "Hitting soft backhands down the line feeds opponent's forehand strength instead of attacking their backhand"
            correct_pattern = "deep heavy backhand crosscourt"
            tactical_reasoning = "Crosscourt gives you largest margin (longest diagonal), lowest net height, and keeps you in neutral position while building pressure"
        else:
            direction = "to opponent's forehand"
            strategic_error = "Hitting soft forehands to opponent's forehand instead of targeting their weaker backhand side"
            correct_pattern = "deep heavy forehand crosscourt"
            tactical_reasoning = "When neutral/defensive, crosscourt forehands maintain control and set up the classic pattern: crosscourt → crosscourt → down the line attack"
        
        return {
            'pattern_name': f'{dominant_shot.title()} Tactical Error',
            'pattern_description': f'Hitting soft, short {dominant_shot}s {direction}',
            'pattern_behavior': f'Hit {len(supporting_rallies)} soft {dominant_shot}s to opponent\'s forehand side (should target backhand)',
            'why_bad': f'{strategic_error}. This allows opponent to step in and attack with their strongest shot.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': f'Use {correct_pattern} to opponent\'s backhand (ad side)',
            'alternative_description': f'{tactical_reasoning}. Force opponent to defend with their weaker wing, building pressure until they give a short ball to attack.',
            'expected_breakdown': f'After 5-7 consecutive {correct_pattern}s, opponent breaks down and gives short ball',
            'improvement_focus': f'Master {correct_pattern}: depth control (beyond service line), heavy topspin, crosscourt targeting',
            'practice_drill': f'{dominant_shot.title()} Crosscourt Pressure Drill: Hit 15 consecutive balls with heavy topspin, landing deep to backhand corner (ad side). Focus on: 1) Net clearance 2-3 feet, 2) Landing 3+ feet inside baseline, 3) Heavy topspin rotation',
            'expected_impact': 'High - This was a primary tactical weakness exploited by opponent',
            'pro_tip': f'Use the classic pattern: {correct_pattern} → {correct_pattern} → down the line to finish'
        }
    
    def _discover_missed_attacks(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: Missing opportunities to attack weak shots from opponent.
        
        When opponent gives you a short ball, you should attack. Not doing so is passive.
        """
        matching_rallies = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            # Build sequence
            for i in range(1, len(shots_in_rally)):
                prev_shot = shots_in_rally[i-1]
                curr_shot = shots_in_rally[i]
                
                # Check if opponent gave short ball, player didn't attack
                if (prev_shot.get('player') == opponent_name and
                    curr_shot.get('player') == player_name):
                    
                    opponent_depth = prev_shot.get('depth', 'deep')
                    opponent_speed = prev_shot.get('speed_mph', 80)
                    player_response_speed = curr_shot.get('speed_mph', 70)
                    player_response_depth = curr_shot.get('depth', 'mid')
                    
                    # Missed attack: opponent gave short/slow ball, player didn't attack
                    if (opponent_depth in ['short', 'mid'] and
                        opponent_speed < 70 and
                        player_response_speed < 75 and  # Didn't accelerate
                        player_response_depth != 'deep'):  # Didn't push opponent back
                        
                        matching_rallies.append({
                            'rally_idx': rally_idx,
                            'rally': rally,
                            'missed_shot': curr_shot,
                            'opponent_setup': prev_shot,
                            'score': rally.get('score', 'Unknown'),
                            'outcome': rally.get('winner', 'unknown'),
                            'importance': self._calculate_importance(rally, rally_idx, len(rallies))
                        })
                        break
        
        if len(matching_rallies) < self.min_pattern_instances:
            return None
        
        matching_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        num_supporting = min(12, max(9, len(matching_rallies)))
        supporting_rallies = matching_rallies[:num_supporting]
        critical_rallies = matching_rallies[:min(2, len(matching_rallies))]
        
        return {
            'pattern_name': 'Missed Attack Opportunities',
            'pattern_description': 'Not capitalizing when opponent gives short, slow balls',
            'pattern_behavior': f'Received {len(supporting_rallies)} attackable balls but played defensively',
            'why_bad': 'Allows opponent to recover position and continue controlling the point. You give them a second chance.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': 'Step inside the baseline and attack short balls aggressively',
            'alternative_description': 'Move forward quickly, take ball on the rise, hit deep to corners or approach net',
            'expected_breakdown': 'Forces opponent into defensive scramble, creates high-percentage winning opportunities',
            'improvement_focus': 'Court positioning awareness, recognizing attack opportunities faster, approach shot technique',
            'practice_drill': 'Short ball reaction drill: Partner feeds random short balls, practice stepping in and attacking within 1.5 seconds',
            'expected_impact': 'Medium-High - Converts defensive rallies into offensive control'
        }
    
    def _discover_pressure_response(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: How player responds to pressure points.
        
        Break points, set points, deuce points - these reveal mental patterns.
        """
        matching_rallies = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            point_score = str(rally.get('point_score', '')).lower()
            
            # Identify pressure points
            is_pressure = any([
                'break' in point_score,
                'deuce' in point_score,
                '40-30' in point_score,
                '30-40' in point_score,
                'ad' in point_score
            ])
            
            if not is_pressure:
                continue
            
            # Look for conservative/defensive play under pressure
            player_shots = [s for s in shots_in_rally if s.get('player') == player_name]
            
            if len(player_shots) < 2:
                continue
            
            # Calculate aggression level
            total_speed = sum(s.get('speed_mph', 70) for s in player_shots)
            avg_speed = total_speed / len(player_shots)
            
            short_shots = sum(1 for s in player_shots if s.get('depth') in ['short', 'mid'])
            conservative_pct = short_shots / len(player_shots)
            
            # Pattern: playing too conservative under pressure
            if avg_speed < 65 and conservative_pct > 0.6:
                matching_rallies.append({
                    'rally_idx': rally_idx,
                    'rally': rally,
                    'avg_speed': avg_speed,
                    'conservative_pct': conservative_pct,
                    'score': rally.get('score', 'Unknown'),
                    'point_score': point_score,
                    'outcome': rally.get('winner', 'unknown'),
                    'importance': self._calculate_importance(rally, rally_idx, len(rallies))
                })
        
        if len(matching_rallies) < self.min_pattern_instances:
            return None
        
        matching_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        num_supporting = min(12, max(9, len(matching_rallies)))
        supporting_rallies = matching_rallies[:num_supporting]
        critical_rallies = matching_rallies[:min(2, len(matching_rallies))]
        
        # Calculate how conservative player gets
        avg_conservative_pct = sum(r['conservative_pct'] for r in matching_rallies) / len(matching_rallies)
        
        return {
            'pattern_name': 'Pressure Point Conservatism',
            'pattern_description': f'Playing {avg_conservative_pct*100:.0f}% more conservative on break points and deuce',
            'pattern_behavior': f'On {len(supporting_rallies)} pressure points, reverted to slow, short shots',
            'why_bad': 'Predictability under pressure allows opponent to anticipate and attack. Fear-based play creates errors.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': 'Maintain normal aggressive baseline game even under pressure',
            'alternative_description': 'Trust your patterns, play your game, don\'t give opponent free control',
            'expected_breakdown': 'More first-strike winners, opponent forced to defend even on pressure points',
            'improvement_focus': 'Mental toughness under pressure, maintaining shot quality on big points',
            'practice_drill': 'Pressure point simulation: Play practice points where every point is "break point", maintain normal aggression',
            'expected_impact': 'High - Break point conversion is often the difference between winning and losing'
        }
    
    def _discover_rally_construction_issues(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: Poor rally construction (not setting up points properly).
        
        Good players construct points: defense → neutral → attack. Bad players hit aimlessly.
        """
        matching_rallies = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            player_shots = [s for s in shots_in_rally if s.get('player') == player_name]
            
            if len(player_shots) < 4:  # Need enough shots to see pattern
                continue
            
            # Analyze shot sequence quality
            # Good construction: defensive → neutral → attack
            # Bad construction: all similar shots (no progression)
            
            speeds = [s.get('speed_mph', 70) for s in player_shots]
            depths = [s.get('depth', 'mid') for s in player_shots]
            
            # Check for progression
            speed_variance = max(speeds) - min(speeds) if speeds else 0
            depth_changes = sum(1 for i in range(1, len(depths)) if depths[i] != depths[i-1])
            
            # Pattern: no tactical progression (all shots similar)
            if speed_variance < 15 and depth_changes < 2:
                matching_rallies.append({
                    'rally_idx': rally_idx,
                    'rally': rally,
                    'speed_variance': speed_variance,
                    'depth_changes': depth_changes,
                    'score': rally.get('score', 'Unknown'),
                    'outcome': rally.get('winner', 'unknown'),
                    'importance': self._calculate_importance(rally, rally_idx, len(rallies))
                })
        
        if len(matching_rallies) < self.min_pattern_instances:
            return None
        
        matching_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        num_supporting = min(12, max(9, len(matching_rallies)))
        supporting_rallies = matching_rallies[:num_supporting]
        critical_rallies = matching_rallies[:min(2, len(matching_rallies))]
        
        return {
            'pattern_name': 'Poor Rally Construction',
            'pattern_description': 'Hitting same-paced shots without tactical progression',
            'pattern_behavior': f'In {len(supporting_rallies)} rallies, failed to build points strategically',
            'why_bad': 'Without pace/depth variation, opponent can predict and time your shots. No setup = no payoff.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': 'Use 3-ball tactic: 1) Deep defensive shot, 2) Neutral positioning shot, 3) Aggressive put-away',
            'alternative_description': 'Construct points with purpose: push opponent back, take court position, finish',
            'expected_breakdown': 'Creates forced errors from opponent, generates better attack opportunities',
            'improvement_focus': 'Tactical awareness, shot selection based on court position, tempo variation',
            'practice_drill': '3-ball drill: Must hit deep, then neutral, then attack in sequence. Repeat 20 times.',
            'expected_impact': 'Medium - Transforms aimless rallying into purposeful point construction'
        }
    
    def _discover_serve_pattern(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: Predictable serve placement.
        
        Serving to the same spot repeatedly allows opponent to anticipate.
        """
        matching_rallies = []
        serve_placements = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            # Find player's serve
            player_serves = [s for s in shots_in_rally 
                            if s.get('player') == player_name and 'serve' in s.get('shot_type', '').lower()]
            
            if not player_serves:
                continue
            
            serve = player_serves[0]
            landing_x = serve.get('landing_zone', {}).get('x', 50)
            
            # Categorize placement: wide (<40), body (40-60), T (>60)
            if landing_x < 40:
                placement = 'wide'
            elif landing_x > 60:
                placement = 'T'
            else:
                placement = 'body'
            
            serve_placements.append(placement)
            
            matching_rallies.append({
                'rally_idx': rally_idx,
                'rally': rally,
                'serve': serve,
                'placement': placement,
                'score': rally.get('score', 'Unknown'),
                'outcome': rally.get('winner', 'unknown'),
                'importance': self._calculate_importance(rally, rally_idx, len(rallies))
            })
        
        if len(serve_placements) < 10:
            return None
        
        # Check for predictability (>55% to same spot is predictable)
        placement_counts = Counter(serve_placements)
        most_common_placement, most_common_count = placement_counts.most_common(1)[0]
        predictability = most_common_count / len(serve_placements)
        
        if predictability < 0.55:  # Not predictable enough
            return None
        
        # Get rallies with most common placement
        predictable_rallies = [r for r in matching_rallies if r['placement'] == most_common_placement]
        predictable_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        num_supporting = min(12, max(9, len(predictable_rallies)))
        supporting_rallies = predictable_rallies[:num_supporting]
        critical_rallies = predictable_rallies[:min(2, len(predictable_rallies))]
        
        return {
            'pattern_name': 'Predictable Serve Placement',
            'pattern_description': f'Serving {predictability*100:.0f}% to {most_common_placement}',
            'pattern_behavior': f'Served to {most_common_placement} {most_common_count} out of {len(serve_placements)} times ({predictability*100:.0f}%)',
            'why_bad': 'Opponent anticipates and cheats on returns, neutralizing your serve advantage. Free points become rallies.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': f'Mix serve placement: 40% {most_common_placement}, 30% each to other zones',
            'alternative_description': 'Keep opponent guessing on every serve, prevent them from leaning/anticipating',
            'expected_breakdown': 'Lower return quality, more aces and service winners, easier service holds',
            'improvement_focus': 'Practice all three serve placements with equal confidence and power',
            'practice_drill': 'Serve placement variety: 10 serves each to wide/body/T, track success rate for each',
            'expected_impact': 'Medium - Improves first serve effectiveness and hold percentage'
        }
    
    def _discover_return_pattern(
        self,
        shots: List[Dict],
        rallies: List[Dict],
        rally_shots: Dict[int, List[Dict]],
        player_name: str,
        opponent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Discover pattern: Return of serve positioning or shot selection issues.
        
        Standing too far back, returning passively, or poor shot selection.
        """
        matching_rallies = []
        
        for rally_idx, rally in enumerate(rallies):
            rally_id = rally.get('id', rally_idx)
            shots_in_rally = rally_shots.get(rally_id, [])
            
            if len(shots_in_rally) < 2:
                continue
            
            # Find opponent serve and player return
            opponent_serves = [s for s in shots_in_rally 
                              if s.get('player') == opponent_name and 'serve' in s.get('shot_type', '').lower()]
            
            if not opponent_serves:
                continue
            
            serve = opponent_serves[0]
            
            # Find player's return (shot after serve)
            serve_idx = shots_in_rally.index(serve)
            if serve_idx + 1 >= len(shots_in_rally):
                continue
            
            return_shot = shots_in_rally[serve_idx + 1]
            
            if return_shot.get('player') != player_name:
                continue
            
            # Analyze return quality
            return_speed = return_shot.get('speed_mph', 60)
            return_depth = return_shot.get('depth', 'mid')
            serve_speed = serve.get('speed_mph', 100)
            
            # Pattern: passive returns (too slow, too short)
            if return_speed < 55 and return_depth in ['short', 'mid']:
                matching_rallies.append({
                    'rally_idx': rally_idx,
                    'rally': rally,
                    'serve': serve,
                    'return': return_shot,
                    'return_speed': return_speed,
                    'serve_speed': serve_speed,
                    'score': rally.get('score', 'Unknown'),
                    'outcome': rally.get('winner', 'unknown'),
                    'importance': self._calculate_importance(rally, rally_idx, len(rallies))
                })
        
        if len(matching_rallies) < self.min_pattern_instances:
            return None
        
        matching_rallies.sort(key=lambda x: x['importance'], reverse=True)
        
        num_supporting = min(12, max(9, len(matching_rallies)))
        supporting_rallies = matching_rallies[:num_supporting]
        critical_rallies = matching_rallies[:min(2, len(matching_rallies))]
        
        avg_return_speed = sum(r['return_speed'] for r in matching_rallies) / len(matching_rallies)
        
        return {
            'pattern_name': 'Passive Return of Serve',
            'pattern_description': f'Averaging {avg_return_speed:.0f} mph on returns, frequently short',
            'pattern_behavior': f'Hit {len(supporting_rallies)} passive returns, giving opponent easy transition shots',
            'why_bad': 'Allows opponent to immediately take control after serve. You start every rally on defense.',
            'supporting_rallies': supporting_rallies,
            'critical_rallies': critical_rallies,
            'alternative_strategy': 'Step inside baseline, block returns deep with pace',
            'alternative_description': 'Take returns earlier, push them back with depth, neutralize their serve advantage',
            'expected_breakdown': 'Forces opponent to hit from baseline instead of approaching, creates rally parity',
            'improvement_focus': 'Return position (step in), contact point (take ball rising), target depth over net',
            'practice_drill': 'Return depth drill: Partner serves, must land 8/10 returns past service line',
            'expected_impact': 'Medium-High - Better returns create break point opportunities'
        }
    
    def _calculate_importance(self, rally: Dict, rally_idx: int, total_rallies: int) -> float:
        """
        Calculate rally importance (0-1 scale).
        
        Factors:
        - Score situation (break point, set point, deuce)
        - Game score (close games more important)
        - Match progression (later matters more)
        - Rally length (longer rallies more meaningful)
        """
        importance = 0.0
        
        point_score = str(rally.get('point_score', '')).lower()
        game_score = rally.get('game_score', (0, 0))
        
        # Critical points
        if any(x in point_score for x in ['break', 'set point', 'match point']):
            importance += 0.5
        elif 'deuce' in point_score or '40-40' in point_score:
            importance += 0.3
        elif '40-30' in point_score or '30-40' in point_score:
            importance += 0.2
        
        # Close games
        if isinstance(game_score, (list, tuple)) and len(game_score) == 2:
            game_diff = abs(game_score[0] - game_score[1])
            if game_diff <= 1:
                importance += 0.2
            elif game_diff == 2:
                importance += 0.1
        
        # Match progression (later = more important)
        progress = rally_idx / max(total_rallies, 1)
        if progress > 0.75:
            importance += 0.25
        elif progress > 0.5:
            importance += 0.15
        elif progress > 0.25:
            importance += 0.05
        
        # Rally length (longer = more important)
        rally_length = rally.get('length', 0)
        if rally_length > 12:
            importance += 0.15
        elif rally_length > 8:
            importance += 0.1
        elif rally_length > 5:
            importance += 0.05
        
        return min(1.0, importance)


# Alias for backward compatibility
PatternNarrativeEngine = AdvancedPatternDiscoveryEngine
