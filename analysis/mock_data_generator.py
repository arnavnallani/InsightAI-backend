"""
Comprehensive Mock Data Generator for Revolutionary AI Tennis Analytics
Generates realistic tennis match statistics for all analytics modules
"""

import sys
import random
import math
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .player_profile import PlayerBehavioralProfile, OpponentProfile


class ComprehensiveMockDataGenerator:
    """Generates realistic mock tennis match data with all statistics"""
    
    def __init__(self, player_name: str = "Alex Johnson", opponent_name: str = "Chris Martinez"):
        self.player_name = player_name
        self.opponent_name = opponent_name
        
        # Player behavioral profiles (creates realistic tendencies in shot data)
        self.player_profile = PlayerBehavioralProfile(skill_level='intermediate')
        self.opponent_profile = OpponentProfile()
    
    def _format_tennis_score(self, player_sets: int, opponent_sets: int, 
                             player_games: int, opponent_games: int,
                             player_points: int, opponent_points: int) -> str:
        """Format tennis score as 'Sets, Games, Points' (e.g., '1-0, 3-2, 15-40')"""
        # Convert point numbers to tennis scoring
        point_map = {0: '0', 1: '15', 2: '30', 3: '40'}
        
        # Handle deuce and advantage
        if player_points >= 3 and opponent_points >= 3:
            if player_points == opponent_points:
                points_str = 'Deuce'
            elif player_points > opponent_points:
                points_str = 'Adv-P'
            else:
                points_str = 'Adv-O'
        else:
            player_pts = point_map.get(player_points, '40')
            opponent_pts = point_map.get(opponent_points, '40')
            points_str = f'{player_pts}-{opponent_pts}'
        
        return f'{player_sets}-{opponent_sets}, {player_games}-{opponent_games}, {points_str}'
        
    def generate_complete_match(self) -> Dict[str, Any]:
        """Generate a complete match with all comprehensive statistics"""
        
        # Match metadata - 2-hour match with 6-4, 6-3 score
        match_duration = 7200  # Exactly 120 minutes (2 hours)
        
        # Generate target score: 6-4, 6-3 (player wins)
        # Set 1: 6-4 = 10 games, Set 2: 6-3 = 9 games, Total: 19 games
        # Average ~6-7 points per game (including deuces) = ~120-130 rallies
        total_rallies = 128  # Realistic for a 6-4, 6-3 match with some deuces
        
        # Generate all shots across the match
        shots = self._generate_all_shots(total_rallies)
        
        # Build rallies from shots
        rallies = self._build_rallies(shots)
        
        # Pure organic shot data - NO pattern injection
        # Pattern discovery engine will analyze these raw statistics
        
        # Calculate match summary
        match_summary = self._calculate_match_summary(rallies, match_duration)
        
        # Generate serve statistics
        serve_stats = self._generate_serve_stats(shots)
        
        # Generate return statistics
        return_stats = self._generate_return_stats(shots)
        
        # Generate efficiency metrics
        efficiency = self._calculate_efficiency_metrics(shots, rallies)
        
        return {
            'match_summary': match_summary,
            'shots': shots,
            'rallies': rallies,
            'serve_stats': serve_stats,
            'return_stats': return_stats,
            'efficiency_metrics': efficiency,
            'player_name': self.player_name,
            'opponent_name': self.opponent_name
        }
    
    def _generate_all_shots(self, num_rallies: int) -> List[Dict[str, Any]]:
        """Generate all shots across the match with predetermined 6-4, 6-3 score"""
        shots = []
        current_time = 0.0
        fatigue_factor = 0.0  # Increases over time
        
        # Tennis score tracking (sets, games, points)
        player_sets = 0
        opponent_sets = 0
        player_games = 0
        opponent_games = 0
        player_points = 0  # 0, 1, 2, 3 (0, 15, 30, 40)
        opponent_points = 0
        
        # Target match: Player wins 6-4, 6-3
        # Set 1: P-O-P-O-P-O-P-O-P-P (Player wins 6, Opponent wins 4) = 10 games total
        # Set 2: P-O-P-O-P-P-O-P-P (Player wins 6, Opponent wins 3) = 9 games total
        set1_games = ['P', 'O', 'P', 'O', 'P', 'O', 'P', 'O', 'P', 'P']  # 6-4
        set2_games = ['P', 'O', 'P', 'O', 'P', 'P', 'O', 'P', 'P']  # 6-3 (P wins: 1,3,5,6,8,9 = 6; O wins: 2,4,7 = 3)
        game_winners = set1_games + set2_games
        
        # Calculate rallies per game (distribute 108 rallies across 19 games)
        rallies_per_game = [num_rallies // len(game_winners)] * len(game_winners)
        for i in range(num_rallies % len(game_winners)):
            rallies_per_game[i] += 1
        
        current_game_idx = 0
        rallies_in_current_game = 0
        current_game_winner = game_winners[current_game_idx]
        
        for rally_num in range(num_rallies):
            rally_length = random.randint(2, 25)
            
            # Determine rally winner based on game plan
            # Check if this rally will win the game for someone
            will_win_game_for_player = (player_points >= 3 and player_points >= opponent_points + 1)
            will_win_game_for_opponent = (opponent_points >= 3 and opponent_points >= player_points + 1)
            
            if will_win_game_for_player or will_win_game_for_opponent:
                # Game point - force the intended winner to win
                if current_game_winner == 'P':
                    rally_winner = 'player'
                else:
                    rally_winner = 'opponent'
            elif player_points >= 3 and opponent_points >= 3:
                # Deuce or advantage situation - bias toward intended winner
                if current_game_winner == 'P':
                    rally_winner = 'player' if random.random() < 0.70 else 'opponent'
                else:
                    rally_winner = 'opponent' if random.random() < 0.70 else 'player'
            else:
                # Normal play - add variety but still favor intended winner
                if current_game_winner == 'P':
                    rally_winner = 'player' if random.random() < 0.65 else 'opponent'
                else:
                    rally_winner = 'opponent' if random.random() < 0.65 else 'player'
            
            # Update tennis scores based on rally winner
            if rally_winner == 'player':
                player_points += 1
            else:
                opponent_points += 1
            
            # Track rallies in current game
            rallies_in_current_game += 1
            
            # Handle game scoring
            game_won = False
            if player_points >= 4 and player_points >= opponent_points + 2:
                # Player wins game
                player_games += 1
                player_points = 0
                opponent_points = 0
                game_won = True
            elif opponent_points >= 4 and opponent_points >= player_points + 2:
                # Opponent wins game
                opponent_games += 1
                player_points = 0
                opponent_points = 0
                game_won = True
            
            # Move to next game if current game is complete
            if game_won and current_game_idx < len(game_winners) - 1:
                current_game_idx += 1
                current_game_winner = game_winners[current_game_idx]
                rallies_in_current_game = 0
            
            # Handle set scoring
            if player_games >= 6 and player_games >= opponent_games + 2:
                # Player wins set
                player_sets += 1
                player_games = 0
                opponent_games = 0
            elif opponent_games >= 6 and opponent_games >= player_games + 2:
                # Opponent wins set
                opponent_sets += 1
                player_games = 0
                opponent_games = 0
            # Tiebreak at 6-6
            elif player_games == 7 and opponent_games == 6:
                player_sets += 1
                player_games = 0
                opponent_games = 0
            elif opponent_games == 7 and player_games == 6:
                opponent_sets += 1
                player_games = 0
                opponent_games = 0
            
            # Match ends when one player wins 2 sets (best of 3)
            if player_sets == 2 or opponent_sets == 2:
                # Match is complete - stop generating rallies
                break
            
            # Calculate fatigue (increases over time)
            fatigue_factor = min(rally_num / num_rallies, 1.0)
            
            # Format the current tennis score
            tennis_score = self._format_tennis_score(
                player_sets, opponent_sets,
                player_games, opponent_games,
                player_points, opponent_points
            )
            
            # Current set number (1-indexed)
            current_set_num = player_sets + opponent_sets + 1
            
            for shot_num in range(rally_length):
                is_player_shot = (shot_num % 2 == 0)
                
                if is_player_shot:
                    shot = self._generate_single_shot(
                        shot_num=shot_num,
                        rally_num=rally_num,
                        rally_length=rally_length,
                        rally_winner=rally_winner,
                        fatigue_factor=fatigue_factor,
                        current_time=current_time,
                        tennis_score=tennis_score,
                        is_player=True,
                        set_num=current_set_num,
                        game_score=(player_games, opponent_games)
                    )
                    shots.append(shot)
                else:
                    # Generate opponent shot
                    shot = self._generate_single_shot(
                        shot_num=shot_num,
                        rally_num=rally_num,
                        rally_length=rally_length,
                        rally_winner=rally_winner,
                        fatigue_factor=fatigue_factor,
                        current_time=current_time,
                        tennis_score=tennis_score,
                        is_player=False,
                        set_num=current_set_num,
                        game_score=(opponent_games, player_games)  # Swapped for opponent perspective
                    )
                    shots.append(shot)
                
                current_time += random.uniform(1.5, 4.0)
            
            # Add gap between rallies
            current_time += random.uniform(15, 30)
        
        return shots
    
    def _generate_single_shot(
        self, 
        shot_num: int, 
        rally_num: int, 
        rally_length: int,
        rally_winner: str,
        fatigue_factor: float,
        current_time: float,
        tennis_score: str,
        is_player: bool,
        set_num: int,
        game_score: tuple
    ) -> Dict[str, Any]:
        """Generate a single shot with all statistics - uses player profiles for realistic tendencies"""
        
        # Shot type classification
        if shot_num == 0:
            shot_type = 'serve'
            is_first_serve = random.random() < 0.65
        else:
            shot_type = random.choices(
                ['forehand', 'backhand', 'forehand_volley', 'backhand_volley', 'overhead', 'drop_shot', 'lob'],
                weights=[35, 30, 8, 7, 3, 2, 1]
            )[0]
            is_first_serve = False
        
        # Detect pressure point (deuce, ad, break point, game point)
        is_pressure_point = 'deuce' in tennis_score.lower() or 'ad' in tennis_score.lower() or '40-30' in tennis_score or '30-40' in tennis_score
        
        # Base speed with fatigue effect
        base_speed = self._get_base_speed(shot_type)
        speed_mph = base_speed * (1 - fatigue_factor * 0.15)
        speed_mph += random.uniform(-5, 5)
        
        # APPLY PLAYER PROFILE TENDENCIES
        is_conservative_shot = False  # Track if this shot was played conservatively
        
        if is_player:
            # Weaker backhand for player (natural tendency shows in stats)
            if shot_type == 'backhand':
                speed_mph = self.player_profile.backhand_speed_avg + random.uniform(-8, 8)
            
            # Conservative play under pressure (natural tendency)
            # This creates detectable pattern in shot statistics
            if is_pressure_point and random.random() < self.player_profile.pressure_conservative_probability:
                speed_mph -= self.player_profile.pressure_speed_reduction
                is_conservative_shot = True
        else:
            # Opponent has stronger, more consistent shots
            if shot_type == 'backhand':
                speed_mph = self.opponent_profile.backhand_speed_avg + random.uniform(-7, 7)
        
        # Spin type
        spin = random.choices(
            ['topspin', 'slice', 'flat'],
            weights=[50, 30, 20]
        )[0]
        
        # Landing depth - use profile distributions for realistic tendencies
        if shot_type in ['serve', 'lob', 'overhead']:
            depth = 'deep'
        elif is_player and shot_type == 'backhand':
            # Player's backhand depth distribution (tends to be shorter)
            depth = random.choices(
                ['deep', 'mid', 'short'],
                weights=[
                    self.player_profile.backhand_depth_distribution['deep'],
                    self.player_profile.backhand_depth_distribution['mid'],
                    self.player_profile.backhand_depth_distribution['short']
                ]
            )[0]
        elif is_conservative_shot:
            # Under pressure: play shorter, safer shots (detectable pattern)
            depth = random.choices(['mid', 'short'], weights=[60, 40])[0]
        else:
            depth = random.choices(
                ['deep', 'mid', 'short'],
                weights=[45, 35, 20]
            )[0]
        
        # Landing zone (court coordinates 0-100)
        # Court layout: Y=0 (top baseline), Y=50 (net), Y=100 (bottom baseline)
        # Player is at bottom (Y=70-95), opponent at top (Y=5-30)
        # Shots go FROM player side (Y>50) TO opponent side (Y<50)
        if is_player and shot_type == 'serve':
            # Player's predictable serve placement (tends to go to T)
            if random.uniform(0, 1) < self.player_profile.serve_placement_distribution['T']:
                landing_x = random.uniform(55, 75)  # T zone
            elif random.uniform(0, 1) < 0.5:
                landing_x = random.uniform(15, 35)  # Wide
            else:
                landing_x = random.uniform(35, 55)  # Body
        else:
            landing_x = random.uniform(0, 100)
        
        # Landing Y coordinate: Ball lands on OPPONENT side (Y < 50)
        # Deep shots land near opponent baseline (Y=5-20)
        # Mid shots land in mid-court (Y=25-40)
        # Short shots land just past net (Y=35-48)
        if depth == 'deep':
            landing_y = random.uniform(5, 20)  # Deep in opponent's court
        elif depth == 'mid':
            landing_y = random.uniform(25, 40)  # Mid-court opponent side
        else:  # short
            landing_y = random.uniform(35, 48)  # Short, just past net
        
        # Shot angle
        if shot_type in ['forehand', 'backhand']:
            if is_player and shot_type == 'backhand':
                # Player's backhand crosscourt bias (predictable pattern)
                if random.uniform(0, 1) < self.player_profile.backhand_crosscourt_bias:
                    angle = 'cross_court'
                else:
                    angle = random.choice(['down_line', 'inside_out'])
            else:
                angle = random.choices(
                    ['cross_court', 'down_line', 'inside_out', 'inside_in'],
                    weights=[50, 30, 12, 8]
                )[0]
        else:
            angle = 'straight'
        
        # Player position (court coordinates)
        # Player is on THEIR side of court (Y > 50)
        # Deep position = at baseline (Y=75-95)
        # Forward position = inside baseline (Y=55-75)
        position_x = random.uniform(20, 80)
        if is_player:
            # Player on bottom side (Y > 50)
            position_y = random.uniform(75, 95)  # At or behind baseline
        else:
            # Opponent on top side (Y < 50)
            position_y = random.uniform(5, 25)  # At or behind their baseline
        
        # SwingVision does NOT track movement metrics, time to ball, or rushed status
        # Only tracks: speed, spin, depth, placement, positioning
        
        # Outcome
        is_last_shot = (shot_num == rally_length - 1)
        if is_last_shot:
            if rally_winner == 'player':
                outcome = random.choice(['winner', 'forced_error'])
            else:
                outcome = random.choice(['unforced_error', 'out', 'net'])
        else:
            outcome = 'in_play'
        
        # Trajectory height at net
        net_height = random.uniform(0.2, 2.5)
        
        # Point importance (based on rally number to mark key moments)
        is_important = (rally_num % 10 == 0 or rally_num % 15 == 0)
        
        return {
            'shot_number': shot_num,
            'rally_number': rally_num,
            'timestamp': current_time,
            'player': self.player_name if is_player else self.opponent_name,
            
            # Shot classification
            'shot_type': shot_type,
            'is_first_serve': is_first_serve,
            'is_second_serve': shot_type == 'serve' and not is_first_serve,
            
            # Shot metrics
            'speed_mph': round(speed_mph, 1),
            'spin_type': spin,
            'net_height_ft': round(net_height, 2),
            'depth': depth,
            'landing_zone': {'x': round(landing_x, 1), 'y': round(landing_y, 1)},
            'angle': angle,
            
            # Player context (only what SwingVision actually provides)
            'player_position': {'x': round(position_x, 1), 'y': round(position_y, 1)},
            
            # Rally context
            'rally_length': rally_length,
            'rally_winner': rally_winner,
            'point_score': tennis_score,  # Formatted as "Sets, Games, Points" (e.g., "1-0, 3-2, 15-40")
            'score': f"Set {set_num}, {tennis_score}",  # Full formatted score with set number
            'set_num': set_num,
            'game_score': game_score,
            'is_important_point': is_important,
            
            # Outcome
            'outcome': outcome,
            'is_winner': outcome == 'winner',
            'is_error': outcome in ['unforced_error', 'out', 'net'],
            'is_forced_error': outcome == 'forced_error',
            
            # Fatigue indicator
            'fatigue_level': round(fatigue_factor, 2)
        }
    
    def _get_base_speed(self, shot_type: str) -> float:
        """Get base speed for shot type"""
        speeds = {
            'serve': 105,
            'forehand': 72,
            'backhand': 68,
            'forehand_volley': 58,
            'backhand_volley': 55,
            'overhead': 85,
            'drop_shot': 35,
            'lob': 45
        }
        return speeds.get(shot_type, 65)
    
    def _build_rallies(self, shots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build rally structures from shots"""
        rallies = []
        current_rally = []
        current_rally_num = 0
        
        for shot in shots:
            if shot['rally_number'] != current_rally_num:
                if current_rally:
                    # Get score info from first shot of rally
                    first_shot = current_rally[0]
                    rallies.append({
                        'id': current_rally_num,
                        'rally_number': current_rally_num,
                        'shots': current_rally,
                        'length': len(current_rally),
                        'winner': first_shot.get('rally_winner', 'opponent'),
                        'duration': current_rally[-1]['timestamp'] - first_shot['timestamp'],
                        'score': first_shot.get('score', 'Unknown'),
                        'point_score': first_shot.get('point_score', '0-0'),
                        'game_score': first_shot.get('game_score', (0, 0)),
                        'set_num': first_shot.get('set_num', 1)
                    })
                current_rally = [shot]
                current_rally_num = shot['rally_number']
            else:
                current_rally.append(shot)
        
        # Add last rally
        if current_rally:
            first_shot = current_rally[0]
            rallies.append({
                'id': current_rally_num,
                'rally_number': current_rally_num,
                'shots': current_rally,
                'length': len(current_rally),
                'winner': first_shot.get('rally_winner', 'opponent'),
                'duration': current_rally[-1]['timestamp'] - first_shot['timestamp'],
                'score': first_shot.get('score', 'Unknown'),
                'point_score': first_shot.get('point_score', '0-0'),
                'game_score': first_shot.get('game_score', (0, 0)),
                'set_num': first_shot.get('set_num', 1)
            })
        
        return rallies
    
    def _calculate_match_summary(self, rallies: List[Dict[str, Any]], duration: int) -> Dict[str, Any]:
        """Calculate match summary statistics"""
        total_shots = sum(rally['length'] for rally in rallies)
        player_points = sum(1 for r in rallies if r['winner'] == 'player')
        opponent_points = sum(1 for r in rallies if r['winner'] == 'opponent')
        
        return {
            'total_rallies': len(rallies),
            'total_shots': total_shots,
            'total_points': len(rallies),
            'player_points_won': player_points,
            'opponent_points_won': opponent_points,
            'final_score': f"{player_points}-{opponent_points}",
            'duration_minutes': duration // 60,
            'average_rally_length': round(total_shots / len(rallies), 1) if rallies else 0
        }
    
    def _generate_serve_stats(self, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate serve statistics"""
        serves = [s for s in shots if s['shot_type'] == 'serve']
        first_serves = [s for s in serves if s['is_first_serve']]
        second_serves = [s for s in serves if s['is_second_serve']]
        
        first_in = sum(1 for s in first_serves if s['outcome'] != 'out')
        first_won = sum(1 for s in first_serves if s['rally_winner'] == 'player')
        
        return {
            'total_serves': len(serves),
            'first_serve_pct': round(len(first_serves) / len(serves) * 100, 1) if serves else 0,
            'first_serve_in_pct': round(first_in / len(first_serves) * 100, 1) if first_serves else 0,
            'first_serve_won_pct': round(first_won / first_in * 100, 1) if first_in > 0 else 0,
            'aces': sum(1 for s in serves if s['outcome'] == 'winner'),
            'double_faults': sum(1 for s in second_serves if s['outcome'] in ['out', 'net']),
            'avg_first_serve_speed': round(sum(s['speed_mph'] for s in first_serves) / len(first_serves), 1) if first_serves else 0,
            'avg_second_serve_speed': round(sum(s['speed_mph'] for s in second_serves) / len(second_serves), 1) if second_serves else 0
        }
    
    def _generate_return_stats(self, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate return statistics"""
        # Returns are shots that come right after opponent serves
        returns = [s for s in shots if s['shot_number'] == 1]  # Simplified
        
        deep_returns = sum(1 for r in returns if r['depth'] == 'deep')
        aggressive_returns = sum(1 for r in returns if r['outcome'] == 'winner')
        
        return {
            'total_returns': len(returns),
            'return_depth_deep_pct': round(deep_returns / len(returns) * 100, 1) if returns else 0,
            'aggressive_return_pct': round(aggressive_returns / len(returns) * 100, 1) if returns else 0,
            'return_winners': aggressive_returns
        }
    
    def _calculate_efficiency_metrics(
        self, 
        shots: List[Dict[str, Any]], 
        rallies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate efficiency metrics"""
        player_shots = [s for s in shots if s['player'] == self.player_name]
        winners = sum(1 for s in player_shots if s['is_winner'])
        unforced_errors = sum(1 for s in player_shots if s['outcome'] == 'unforced_error')
        points_won = sum(1 for r in rallies if r['winner'] == 'player')
        
        return {
            'points_won_per_shot': round(points_won / len(player_shots), 3) if player_shots else 0,
            'winner_to_error_ratio': round(winners / unforced_errors, 2) if unforced_errors > 0 else winners,
            'winners': winners,
            'unforced_errors': unforced_errors,
            'forced_errors': sum(1 for s in player_shots if s['is_forced_error'])
        }
