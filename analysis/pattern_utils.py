"""
PATTERN ANALYSIS UTILITIES
===========================
Shared statistical and analytical utilities used by all pattern detectors.

Prevents code duplication by centralizing:
- Baseline statistics computation
- Shot clustering and classification
- Pressure situation tagging
- Opportunity recognition
- Win rate calculations
- Statistical comparisons
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import statistics


# ============================================================================
# DATA STRUCTURES (matching SwingVision output)
# ============================================================================

class Shot:
    """Single shot from SwingVision output"""
    def __init__(self, data: Dict[str, Any]):
        self.shot_number = data.get('shot_number', data.get('shotNumber', 0))
        self.player = data.get('player', 'you')
        self.shot_type = data.get('shot_type', data.get('shotType', 'Forehand'))
        self.speed = data.get('speed', 0)
        
        # Handle both placement object and separate x/y fields (where ball landed)
        if 'placement' in data:
            self.placement = data['placement']
        elif 'landing_zone' in data:
            self.placement = data['landing_zone']
        else:
            self.placement = {'x': data.get('x', 50), 'y': data.get('y', 50)}
        
        # Extract player position (where player was when hitting the shot)
        if 'player_position' in data:
            self.player_position = data['player_position']
        elif 'playerPosition' in data:
            self.player_position = data['playerPosition']
        else:
            self.player_position = {'x': 50, 'y': 85}  # default baseline center
        
        self.trajectory = data.get('trajectory', 'medium')
        self.spin = data.get('spin', 'topspin')
        self.depth = data.get('depth', 'mid')
        self.direction = data.get('direction', 'unknown')  # Extract direction field!
        self.shot_result = data.get('shot_result', data.get('shotResult', 'in-play'))
        
    @property
    def is_error(self) -> bool:
        return self.shot_result == 'error'
    
    @property
    def is_winner(self) -> bool:
        return self.shot_result == 'winner'
    
    @property
    def x(self) -> float:
        return self.placement.get('x', 50)
    
    @property
    def y(self) -> float:
        return self.placement.get('y', 50)


class Rally:
    """Single point from SwingVision"""
    def __init__(self, data: Dict[str, Any]):
        self.rally_number = data.get('rally_number', data.get('rallyNumber', 0))
        self.set_number = data.get('set_number', data.get('setNumber', 1))
        self.game_score = data.get('game_score', data.get('gameScore', '0-0'))
        self.point_score = data.get('point_score', data.get('pointScore', '0-0'))
        self.server = data.get('server', 'you')
        self.is_break_point = data.get('is_break_point', data.get('isBreakPoint', False))
        self.is_game_point = data.get('is_game_point', data.get('isGamePoint', False))
        self.is_deuce = data.get('is_deuce', data.get('isDeuce', False))
        self.point_winner = data.get('point_winner', data.get('pointWinner', 'opponent'))
        self.opponent_handedness = data.get('opponent_handedness', data.get('opponentHandedness', 'right'))
        
        # Convert shots
        shot_data = data.get('shots', [])
        self.shots = [Shot(s) for s in shot_data]
        
        # Pattern-specific metadata (set during pattern discovery)
        self.pattern_shot_index = None  # Index of the shot that represents the pattern
        
    @property
    def outcome(self) -> str:
        return 'won' if self.point_winner == 'you' else 'lost'
    
    @property
    def serving(self) -> bool:
        return self.server == 'you'
    
    @property
    def is_pressure(self) -> bool:
        """Returns True if this is a high-pressure point"""
        return self.is_break_point or self.is_game_point or self.is_deuce


# ============================================================================
# BASELINE STATISTICS
# ============================================================================

def compute_baseline_statistics(rallies: List[Rally]) -> Dict[str, Any]:
    """
    Compute baseline player statistics from all rallies.
    
    Returns:
        Dictionary with player's normal behavior metrics:
        - Total counts and win rates
        - Average shot speeds by type
        - Typical shot placements
        - Standard trajectory patterns
        - Pressure vs normal performance
    """
    if not rallies:
        return {}
    
    stats = {
        'total_rallies': len(rallies),
        'total_points_won': sum(1 for r in rallies if r.outcome == 'won'),
        'total_points_lost': sum(1 for r in rallies if r.outcome == 'lost'),
        'overall_win_rate': 0.0,
    }
    
    stats['overall_win_rate'] = round(stats['total_points_won'] / len(rallies), 2)
    
    # Shot statistics by type
    shot_stats = defaultdict(lambda: {
        'speeds': [], 
        'placements_x': [], 
        'placements_y': [],
        'trajectories': defaultdict(int),
        'spins': defaultdict(int),
        'depths': defaultdict(int)
    })
    
    for rally in rallies:
        for shot in rally.shots:
            if shot.player == 'you':
                shot_type = shot.shot_type
                shot_stats[shot_type]['speeds'].append(shot.speed)
                shot_stats[shot_type]['placements_x'].append(shot.x)
                shot_stats[shot_type]['placements_y'].append(shot.y)
                shot_stats[shot_type]['trajectories'][shot.trajectory] += 1
                shot_stats[shot_type]['spins'][shot.spin] += 1
                if shot.depth:
                    shot_stats[shot_type]['depths'][shot.depth] += 1
    
    # Calculate averages (round to 2 decimal places)
    for shot_type, data in shot_stats.items():
        key_prefix = f'avg_{shot_type.lower()}'
        stats[f'{key_prefix}_speed'] = round(statistics.mean(data['speeds']), 2) if data['speeds'] else 0
        stats[f'{key_prefix}_placement_x'] = round(statistics.mean(data['placements_x']), 2) if data['placements_x'] else 50.0
        stats[f'{key_prefix}_placement_y'] = round(statistics.mean(data['placements_y']), 2) if data['placements_y'] else 50.0
    
    # Pressure vs normal statistics (round to 2 decimal places)
    pressure_rallies = [r for r in rallies if r.is_pressure]
    normal_rallies = [r for r in rallies if not r.is_pressure]
    
    if pressure_rallies:
        stats['pressure_win_rate'] = round(sum(1 for r in pressure_rallies if r.outcome == 'won') / len(pressure_rallies), 2)
        stats['pressure_count'] = len(pressure_rallies)
    else:
        stats['pressure_win_rate'] = 0.0
        stats['pressure_count'] = 0
    
    if normal_rallies:
        stats['normal_win_rate'] = round(sum(1 for r in normal_rallies if r.outcome == 'won') / len(normal_rallies), 2)
    else:
        stats['normal_win_rate'] = 0.0
    
    # Store baseline win rate for other functions
    stats['baseline_win_rate'] = stats['overall_win_rate']
    
    return stats


# ============================================================================
# SHOT CLUSTERING & CLASSIFICATION
# ============================================================================

def classify_shot_direction(shot: Shot, player_handedness: str = 'right') -> str:
    """
    Classify shot direction as crosscourt, down-the-line, or middle.
    
    Args:
        shot: Shot object
        player_handedness: 'right' or 'left'
        
    Returns:
        'crosscourt', 'down-the-line', or 'middle'
    """
    x = shot.x
    
    # For right-handed player
    if player_handedness == 'right':
        if shot.shot_type == 'Forehand':
            # Forehand from deuce side
            if x < 20:  # DTL to ad side
                return 'down-the-line'
            elif 20 <= x <= 45:  # CC to ad side
                return 'crosscourt'
            else:  # Middle
                return 'middle'
        elif shot.shot_type == 'Backhand':
            # Backhand from ad side
            if x > 80:  # DTL to deuce side
                return 'down-the-line'
            elif 55 <= x <= 80:  # CC to deuce side
                return 'crosscourt'
            elif 20 <= x <= 55:  # CC to center
                return 'crosscourt'
            else:
                return 'down-the-line'
    
    return 'middle'


def classify_shot_depth(shot: Shot) -> str:
    """
    Classify shot depth as short, mid, or deep.
    
    Court geometry: y=0 (net), y=100 (far baseline)
    - Short: y < 55 (inside service line)
    - Mid: 55 <= y < 75 (between service line and baseline)
    - Deep: y >= 75 (deep in court, pushing opponent back)
    """
    if shot.depth:
        return shot.depth
    
    y = shot.y
    if y < 55:
        return 'short'
    elif y < 75:
        return 'mid'
    else:
        return 'deep'


def is_attacking_shot(shot: Shot) -> bool:
    """
    Determine if shot is aggressive/attacking.
    
    Criteria:
    - High speed (>75mph for groundstrokes, >100mph for serves)
    - Low trajectory (aggressive shot)
    - OR winner
    """
    if shot.is_winner:
        return True
    
    if shot.shot_type in ['Forehand', 'Backhand']:
        return shot.speed > 75 and shot.trajectory == 'low'
    elif shot.shot_type == 'Serve':
        return shot.speed > 100
    elif shot.shot_type in ['Volley', 'Overhead']:
        return True
    
    return False


def is_defensive_shot(shot: Shot) -> bool:
    """
    Determine if shot is defensive/conservative.
    
    Criteria:
    - Low speed
    - High trajectory (moonball)
    - Deep placement (pushing opponent back)
    """
    if shot.shot_type in ['Forehand', 'Backhand']:
        return shot.speed < 60 or shot.trajectory == 'high'
    
    return False


# ============================================================================
# PRESSURE SITUATION TAGGING
# ============================================================================

def tag_pressure_rallies(rallies: List[Rally]) -> Tuple[List[Rally], List[Rally]]:
    """
    Separate rallies into pressure and normal groups.
    
    Returns:
        (pressure_rallies, normal_rallies)
    """
    pressure = []
    normal = []
    
    for rally in rallies:
        if rally.is_pressure:
            pressure.append(rally)
        else:
            normal.append(rally)
    
    return pressure, normal


def calculate_leverage_score(rally: Rally) -> int:
    """
    Calculate leverage/importance score (0-10) for a rally.
    
    Factors:
    - Break point: +4
    - Game point: +3
    - Deuce: +2
    - Late in set: +1 to +3
    """
    score = 0
    
    if rally.is_break_point:
        score += 4
    if rally.is_game_point:
        score += 3
    if rally.is_deuce:
        score += 2
    
    # Parse game score for set criticality
    try:
        your_games, opp_games = map(int, rally.game_score.split('-'))
        total_games = your_games + opp_games
        
        # Late in set
        if total_games >= 8:
            score += 3
        elif total_games >= 6:
            score += 2
        elif total_games >= 4:
            score += 1
    except:
        pass
    
    return min(score, 10)


# ============================================================================
# OPPORTUNITY RECOGNITION
# ============================================================================

def find_short_balls(rallies: List[Rally]) -> List[Tuple[Rally, Shot]]:
    """
    Find all short balls that could have been attacked.
    
    Returns:
        List of (rally, opponent_short_shot) tuples
    """
    opportunities = []
    
    for rally in rallies:
        for i, shot in enumerate(rally.shots):
            # Opponent hit a short ball
            if shot.player == 'opponent' and classify_shot_depth(shot) == 'short':
                # Check if there's a next shot by you
                if i + 1 < len(rally.shots) and rally.shots[i + 1].player == 'you':
                    opportunities.append((rally, shot))
                    break  # One opportunity per rally
    
    return opportunities


def find_serve_opportunities(rallies: List[Rally], serving: bool = True) -> List[Rally]:
    """
    Find all rallies where you served (or received).
    
    Args:
        serving: If True, find rallies where you served. If False, where opponent served.
    """
    return [r for r in rallies if r.serving == serving]


# ============================================================================
# WIN RATE CALCULATIONS
# ============================================================================

def calculate_win_rate(rallies: List[Rally]) -> float:
    """Calculate win rate for a list of rallies"""
    if not rallies:
        return 0.0
    won = sum(1 for r in rallies if r.outcome == 'won')
    return won / len(rallies)


def calculate_comparative_stats(
    group_a: List[Rally], 
    group_b: List[Rally]
) -> Dict[str, Any]:
    """
    Compare statistics between two rally groups.
    
    Returns:
        Dictionary with comparative metrics:
        - Win rates for both groups
        - Difference in win rates
        - Statistical significance (sample sizes)
    """
    stats = {
        'group_a_count': len(group_a),
        'group_b_count': len(group_b),
        'group_a_win_rate': calculate_win_rate(group_a),
        'group_b_win_rate': calculate_win_rate(group_b),
    }
    
    stats['win_rate_difference'] = stats['group_a_win_rate'] - stats['group_b_win_rate']
    stats['group_a_loss_rate'] = 1 - stats['group_a_win_rate']
    stats['group_b_loss_rate'] = 1 - stats['group_b_win_rate']
    
    return stats


# ============================================================================
# SHOT SPEED ANALYSIS
# ============================================================================

def calculate_speed_stats(rallies: List[Rally], shot_type: str = None) -> Dict[str, float]:
    """
    Calculate speed statistics for shots in rallies.
    
    Args:
        rallies: List of rallies
        shot_type: Optional filter by shot type (e.g., 'Forehand', 'Backhand')
        
    Returns:
        Dictionary with speed metrics
    """
    speeds = []
    
    for rally in rallies:
        for shot in rally.shots:
            if shot.player == 'you':
                if shot_type is None or shot.shot_type == shot_type:
                    speeds.append(shot.speed)
    
    if not speeds:
        return {'avg_speed': 0, 'min_speed': 0, 'max_speed': 0}
    
    return {
        'avg_speed': statistics.mean(speeds),
        'min_speed': min(speeds),
        'max_speed': max(speeds),
        'median_speed': statistics.median(speeds),
        'count': len(speeds)
    }


def compare_shot_speeds(
    group_a: List[Rally], 
    group_b: List[Rally],
    shot_type: str = None
) -> Dict[str, Any]:
    """
    Compare shot speeds between two rally groups.
    
    Useful for comparing:
    - Pressure vs normal rallies
    - Different tactical situations
    - Different shot selections
    """
    stats_a = calculate_speed_stats(group_a, shot_type)
    stats_b = calculate_speed_stats(group_b, shot_type)
    
    speed_diff = stats_a['avg_speed'] - stats_b['avg_speed']
    speed_diff_pct = (speed_diff / stats_b['avg_speed'] * 100) if stats_b['avg_speed'] > 0 else 0
    
    return {
        'group_a_avg': stats_a['avg_speed'],
        'group_b_avg': stats_b['avg_speed'],
        'speed_difference': speed_diff,
        'speed_difference_percent': speed_diff_pct,
        'group_a_stats': stats_a,
        'group_b_stats': stats_b
    }


# ============================================================================
# TRAJECTORY ANALYSIS
# ============================================================================

def calculate_trajectory_distribution(rallies: List[Rally], shot_type: str = None) -> Dict[str, float]:
    """
    Calculate distribution of trajectories (low/medium/high) in rallies.
    
    Returns:
        Dictionary with rates: {'low_rate': 0.2, 'medium_rate': 0.5, 'high_rate': 0.3}
    """
    counts = defaultdict(int)
    total = 0
    
    for rally in rallies:
        for shot in rally.shots:
            if shot.player == 'you':
                if shot_type is None or shot.shot_type == shot_type:
                    counts[shot.trajectory] += 1
                    total += 1
    
    if total == 0:
        return {'low_rate': 0, 'medium_rate': 0, 'high_rate': 0}
    
    return {
        'low_rate': counts['low'] / total,
        'medium_rate': counts['medium'] / total,
        'high_rate': counts['high'] / total
    }


# ============================================================================
# SERVE ANALYSIS
# ============================================================================

def analyze_serve_placement(rallies: List[Rally]) -> Dict[str, Any]:
    """
    Analyze serve placement patterns.
    
    Returns distribution of serves to T, Wide, and Body
    """
    serves_t = []  # x near 50 (centerline)
    serves_wide = []  # x < 25 or x > 75
    serves_body = []  # x 30-70
    
    for rally in rallies:
        if rally.serving and rally.shots:
            first_shot = rally.shots[0]
            if first_shot.shot_type == 'Serve' and first_shot.player == 'you':
                x = first_shot.x
                if 45 <= x <= 55:
                    serves_t.append(rally)
                elif x < 25 or x > 75:
                    serves_wide.append(rally)
                elif 30 <= x < 45 or 55 < x <= 70:
                    serves_body.append(rally)
    
    total = len(serves_t) + len(serves_wide) + len(serves_body)
    
    if total == 0:
        return {
            't_count': 0,
            'wide_count': 0,
            'body_count': 0,
            't_rate': 0,
            'wide_rate': 0,
            'body_rate': 0,
            't_win_rate': 0,
            'wide_win_rate': 0,
            'body_win_rate': 0,
            'serves_t': [],
            'serves_wide': [],
            'serves_body': []
        }
    
    return {
        't_count': len(serves_t),
        'wide_count': len(serves_wide),
        'body_count': len(serves_body),
        't_rate': len(serves_t) / total,
        'wide_rate': len(serves_wide) / total,
        'body_rate': len(serves_body) / total,
        't_win_rate': calculate_win_rate(serves_t),
        'wide_win_rate': calculate_win_rate(serves_wide),
        'body_win_rate': calculate_win_rate(serves_body),
        'serves_t': serves_t,
        'serves_wide': serves_wide,
        'serves_body': serves_body
    }


# ============================================================================
# PATTERN DETECTION HELPERS
# ============================================================================

def meets_minimum_sample_size(rallies: List[Rally], minimum: int = 5) -> bool:
    """Check if rally list meets minimum sample size for reliable detection"""
    return len(rallies) >= minimum


def calculate_significance_score(
    frequency: int,
    impact_rate: float,
    leverage_avg: float = 5.0
) -> float:
    """
    Calculate pattern significance score (0-100).
    
    Factors:
    - Frequency: How often pattern occurs
    - Impact: Win/loss rate associated with pattern
    - Leverage: Average importance of situations where pattern occurs
    
    Returns:
        Score from 0-100 indicating pattern significance
    """
    # Frequency component (0-40 points)
    freq_score = min(frequency / 50 * 40, 40)
    
    # Impact component (0-40 points)  
    impact_score = abs(impact_rate - 0.5) * 2 * 40
    
    # Leverage component (0-20 points)
    leverage_score = min(leverage_avg / 10 * 20, 20)
    
    return freq_score + impact_score + leverage_score
