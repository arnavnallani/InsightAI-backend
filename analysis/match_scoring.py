"""
Match scoring system that handles various formats
"""

from models import Match, Set, Game, Rally, MatchConfig
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class MatchScorer:
    """Handles match scoring based on configuration"""
    
    def __init__(self, config: MatchConfig):
        self.config = config
        
    def get_point_score_name(self, points: int, is_tiebreak: bool = False) -> str:
        """Convert point count to score name"""
        if is_tiebreak:
            return str(points)
        
        score_map = {0: '0', 1: '15', 2: '30', 3: '40'}
        return score_map.get(points, '40')
    
    def is_deuce(self, p1_points: int, p2_points: int) -> bool:
        """Check if it's deuce"""
        if self.config.use_no_ad:
            return False  # No deuce in no-ad scoring
        return p1_points >= 3 and p2_points >= 3 and p1_points == p2_points
    
    def is_advantage(self, p1_points: int, p2_points: int) -> Tuple[bool, int]:
        """Check if someone has advantage"""
        if self.config.use_no_ad:
            return False, 0
        
        if p1_points >= 3 and p2_points >= 3:
            if p1_points > p2_points:
                return True, 1
            elif p2_points > p1_points:
                return True, 2
        return False, 0
    
    def check_game_won(self, p1_points: int, p2_points: int, is_tiebreak: bool = False) -> int:
        """
        Check if game/tiebreak is won
        Returns: 0 (ongoing), 1 (player 1 won), 2 (player 2 won)
        """
        if is_tiebreak:
            # Tiebreak scoring
            min_points = self.config.tiebreak_points if not is_match_tiebreak else self.config.match_tiebreak_points
            
            if p1_points >= min_points and p1_points - p2_points >= 2:
                return 1
            elif p2_points >= min_points and p2_points - p1_points >= 2:
                return 2
            return 0
        else:
            # Regular game scoring
            if self.config.use_no_ad:
                # No-ad scoring: first to 4 points wins
                if p1_points >= 4:
                    return 1
                elif p2_points >= 4:
                    return 2
                return 0
            else:
                # Traditional scoring with deuce/advantage
                if p1_points >= 4 and p1_points - p2_points >= 2:
                    return 1
                elif p2_points >= 4 and p2_points - p1_points >= 2:
                    return 2
                return 0
    
    def check_set_won(self, p1_games: int, p2_games: int) -> int:
        """
        Check if set is won
        Returns: 0 (ongoing), 1 (player 1 won), 2 (player 2 won)
        """
        target_games = self.config.games_per_set
        tiebreak_at = self.config.tiebreak_at
        
        # Won by reaching target games with 2+ game lead
        if p1_games >= target_games and p1_games - p2_games >= 2:
            return 1
        elif p2_games >= target_games and p2_games - p1_games >= 2:
            return 2
        
        # Check if tiebreak should be played
        if p1_games == tiebreak_at and p2_games == tiebreak_at:
            # Tiebreak will be played
            return 0
        
        return 0
    
    def needs_tiebreak(self, p1_games: int, p2_games: int) -> bool:
        """Check if tiebreak should be played"""
        return p1_games == self.config.tiebreak_at and p2_games == self.config.tiebreak_at
    
    def check_match_won(self, p1_sets: int, p2_sets: int) -> int:
        """
        Check if match is won
        Returns: 0 (ongoing), 1 (player 1 won), 2 (player 2 won)
        """
        if self.config.set_format == 'single_set':
            # Single set match - already won if there's a set winner
            return 1 if p1_sets > 0 else (2 if p2_sets > 0 else 0)
        elif self.config.set_format == 'best_of_3':
            if p1_sets >= 2:
                return 1
            elif p2_sets >= 2:
                return 2
        elif self.config.set_format == 'best_of_5':
            if p1_sets >= 3:
                return 1
            elif p2_sets >= 3:
                return 2
        
        return 0
    
    def is_deciding_set(self, set_number: int, p1_sets: int, p2_sets: int) -> bool:
        """Check if this is the deciding set"""
        if self.config.set_format == 'best_of_3':
            return set_number == 3 and p1_sets == 1 and p2_sets == 1
        elif self.config.set_format == 'best_of_5':
            return set_number == 5 and p1_sets == 2 and p2_sets == 2
        return False
    
    def format_score(self, match: Match) -> str:
        """Format the full match score"""
        if not match.sets:
            return "0-0"
        
        set_scores = []
        for set_data in match.sets:
            p1_games = set_data.score.get(1, 0)
            p2_games = set_data.score.get(2, 0)
            
            set_score = f"{p1_games}-{p2_games}"
            
            # Add tiebreak score if applicable
            if set_data.tiebreak_score:
                p1_tb = set_data.tiebreak_score.get(1, 0)
                p2_tb = set_data.tiebreak_score.get(2, 0)
                set_score += f"({p1_tb}-{p2_tb})"
            
            set_scores.append(set_score)
        
        return " ".join(set_scores)
