"""
Tactical Playbook Generator
Generates situation-specific strategic playbooks from pattern analysis

Creates ready-to-render playbooks for:
- Leading situations (5-2, closing out)
- Trailing situations (2-5, comeback mode)  
- Tiebreaks (every point matters)
- Break points (serving and returning)
- Opponent-style specific tactics
"""

from typing import Dict, Any, List
from tennis_strategy_knowledge import (
    SCORE_BASED_TACTICS,
    OPPONENT_STYLE_TACTICS,
    ENERGY_MANAGEMENT,
    BREAK_POINT_TACTICS
)


class TacticalPlaybookGenerator:
    """
    Generates situation-specific playbooks from patterns and match data
    """
    
    def generate_complete_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict,
        opponent_style: str = "baseliner"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive tactical playbook
        
        Args:
            patterns: Discovered patterns (strengths + weaknesses)
            match_stats: Match statistics and context
            opponent_style: Opponent player type
            
        Returns:
            Complete playbook with situation-specific strategies
        """
        return {
            'tiebreak_strategy': self._generate_tiebreak_playbook(patterns, match_stats),
            'leading_strategy': self._generate_leading_playbook(patterns, match_stats),
            'trailing_strategy': self._generate_trailing_playbook(patterns, match_stats),
            'break_point_strategy': self._generate_break_point_playbook(patterns, match_stats),
            'opponent_adaptation': self._generate_opponent_playbook(opponent_style, patterns),
            'energy_management': self._generate_energy_playbook(patterns, match_stats)
        }
    
    def _generate_tiebreak_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict
    ) -> Dict[str, Any]:
        """Generate tiebreak-specific strategy"""
        # Get tiebreak tactics from knowledge base
        tiebreak_tactics = SCORE_BASED_TACTICS.get('tiebreak', {})
        
        # Find your best serve pattern
        serve_patterns = [p for p in patterns if 'serve' in getattr(p, 'name', '').lower() and getattr(p, 'type', '') == 'strength']
        best_serve = serve_patterns[0] if serve_patterns else None
        
        # Find patterns that work under pressure
        pressure_patterns = []
        for p in patterns:
            if getattr(p, 'type', '') == 'strength':
                win_rate = getattr(p, 'point_win_rate', 0) or getattr(p, 'pointWinRate', 0) or 0
                if win_rate > 0.60:  # 60%+ win rate
                    pressure_patterns.append(p)
        
        return {
            'mental_approach': tiebreak_tactics.get('mental_approach', 'Max focus - every point critical'),
            'serve_strategy': {
                'recommendation': f"Use your {getattr(best_serve, 'name', 'best')} serve 75%+ of time" if best_serve else "Go to your most reliable serve",
                'first_serve_target': '75%+ to your strength',
                'second_serve': 'Be aggressive - no free points',
                'your_best_serve': getattr(best_serve, 'name', 'T serve') if best_serve else 'T serve'
            },
            'return_strategy': tiebreak_tactics.get('return_strategy', {}),
            'point_construction': {
                'target_length': '3-5 shots (shorten points)',
                'style': 'Aggressive but not reckless',
                'use_patterns': [getattr(p, 'name', '') for p in pressure_patterns[:3]]
            },
            'key_moments': {
                'mini_break': 'First to 3 points = psychological edge',
                'stay_composed': 'Use changeovers to reset mentally'
            }
        }
    
    def _generate_leading_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict
    ) -> Dict[str, Any]:
        """Generate strategy when leading (e.g., 5-2)"""
        leading_tactics = SCORE_BASED_TACTICS.get('leading_5_2', {})
        
        # Find most reliable patterns (lowest error rate)
        reliable_patterns = []
        for p in patterns:
            if getattr(p, 'type', '') == 'strength':
                frequency = getattr(p, 'frequency', 0)
                if frequency > 10:  # Used frequently = reliable
                    reliable_patterns.append(p)
        
        return {
            'mental_approach': 'Close it out - maintain intensity, don\'t let them back in',
            'serve_strategy': {
                'consistency': 'Get 65%+ first serves in',
                'placement': 'Use your highest win-rate serves',
                'your_bread_and_butter': [getattr(p, 'name', '') for p in reliable_patterns[:2]],
                'avoid': 'No experiments - stick to what works'
            },
            'tactics': {
                'maintain_patterns': 'Keep using what got you the lead',
                'intensity': 'Don\'t drop energy level',
                'avoid_passive_play': 'Don\'t play not to lose - keep using weapons'
            },
            'mental_traps': leading_tactics.get('mental_traps', {}),
            'close_out_rate': '85%+ of these situations should close'
        }
    
    def _generate_trailing_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict
    ) -> Dict[str, Any]:
        """Generate comeback strategy when trailing (e.g., 2-5)"""
        trailing_tactics = SCORE_BASED_TACTICS.get('trailing_2_5', {})
        
        # Find opponent's weaknesses (your discovered patterns show what works)
        attack_patterns = []
        for p in patterns:
            if getattr(p, 'type', '') == 'strength':
                attack_patterns.append(p)
        
        return {
            'mental_approach': 'Nothing to lose - take calculated risks',
            'serve_strategy': {
                'aggression': 'Be more aggressive on 20-30% of serves',
                'second_serve': 'Attack more - don\'t give free points',
                'variation': 'Mix it up to surprise them'
            },
            'return_strategy': {
                'positioning': 'Stand 1-2 feet closer',
                'aggression': 'Attack second serves aggressively',
                'target': 'Go for their weakness - no safe returns'
            },
            'tactics': {
                'break_rhythm': 'Try different patterns to disrupt',
                'variety': 'Slice, drop shots, net approaches',
                'momentum_shift': 'One break gets you right back'
            },
            'your_weapons': [getattr(p, 'name', '') for p in attack_patterns[:3]],
            'mindset': 'Play loose - pressure is on them to close'
        }
    
    def _generate_break_point_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict
    ) -> Dict[str, Any]:
        """Generate break point strategy (serving and returning)"""
        serving_bp = BREAK_POINT_TACTICS.get('serving_break_point', {})
        returning_bp = BREAK_POINT_TACTICS.get('returning_break_point', {})
        
        # Find best serve pattern for pressure
        best_serve_pattern = None
        for p in patterns:
            if 'serve' in getattr(p, 'name', '').lower() and getattr(p, 'type', '') == 'strength':
                best_serve_pattern = p
                break
        
        # Get break point stats
        bp_saved = match_stats.get('break_points_saved', 0)
        bp_faced = match_stats.get('break_points_faced', 1)
        bp_save_rate = bp_saved / bp_faced if bp_faced > 0 else 0.60
        
        bp_converted = match_stats.get('break_points_converted', 0)
        bp_chances = match_stats.get('break_point_chances', 1)
        bp_conversion_rate = bp_converted / bp_chances if bp_chances > 0 else 0.30
        
        return {
            'serving_break_point': {
                'mental_approach': serving_bp.get('mental_approach', {}),
                'your_best_serve': getattr(best_serve_pattern, 'name', 'T serve') if best_serve_pattern else 'T serve',
                'serve_strategy': serving_bp.get('serve_strategy', {}),
                'current_save_rate': f"{bp_save_rate * 100:.0f}%",
                'target_save_rate': '60-65%',
                'improvement': 'good' if bp_save_rate >= 0.60 else 'needs_work'
            },
            'returning_break_point': {
                'mental_approach': returning_bp.get('mental_approach', {}),
                'return_strategy': returning_bp.get('return_strategy', {}),
                'current_conversion': f"{bp_conversion_rate * 100:.0f}%",
                'target_conversion': '25-35%',
                'improvement': 'good' if bp_conversion_rate >= 0.25 else 'needs_work'
            },
            'key_insight': self._get_break_point_insight(bp_save_rate, bp_conversion_rate, patterns)
        }
    
    def _get_break_point_insight(
        self,
        save_rate: float,
        conversion_rate: float,
        patterns: List[Dict]
    ) -> str:
        """Generate personalized break point insight"""
        if save_rate < 0.55 and conversion_rate < 0.25:
            return "You're struggling on BOTH sides of break points. Focus on being more aggressive - use your strengths, don't play it safe."
        elif save_rate < 0.55:
            weakness_patterns = [p for p in patterns if getattr(p, 'type', '') == 'weakness']
            if weakness_patterns:
                return f"You're vulnerable on your serve at break point. Your {getattr(weakness_patterns[0], 'name', 'weakness')} pattern shows up - fix this to improve save rate."
        elif conversion_rate < 0.25:
            return "You're not converting enough break point chances. Stand closer on returns and attack their second serves aggressively."
        else:
            return "Your break point performance is solid. Keep using your current approach on big points."
    
    def _generate_opponent_playbook(
        self,
        opponent_style: str,
        patterns: List[Dict]
    ) -> Dict[str, Any]:
        """Generate opponent-specific adaptation strategy"""
        opponent_tactics = OPPONENT_STYLE_TACTICS.get(opponent_style, {})
        
        if not opponent_tactics:
            # Default to baseliner
            opponent_style = "baseliner"
            opponent_tactics = OPPONENT_STYLE_TACTICS.get('baseliner', {})
        
        # Find patterns that match exploiting this opponent type
        relevant_strengths = []
        for p in patterns:
            if getattr(p, 'type', '') == 'strength':
                # Net approaches good vs baseliners
                if opponent_style == "baseliner" and ('net' in getattr(p, 'name', '').lower() or 'approach' in getattr(p, 'name', '').lower()):
                    relevant_strengths.append(p)
                # Passing shots good vs serve-volleyers
                elif opponent_style == "serve_volleyer" and 'passing' in getattr(p, 'name', '').lower():
                    relevant_strengths.append(p)
                else:
                    relevant_strengths.append(p)
        
        return {
            'opponent_type': opponent_style,
            'characteristics': opponent_tactics.get('characteristics', []),
            'how_to_exploit': opponent_tactics.get('exploit', []),
            'what_to_avoid': opponent_tactics.get('avoid', []),
            'tactical_gameplan': opponent_tactics.get('tactical_gameplan', ''),
            'key_stat_target': opponent_tactics.get('key_stat', ''),
            'your_weapons_vs_this_style': [getattr(p, 'name', '') for p in relevant_strengths[:3]],
            'serve_strategy': opponent_tactics.get('serve_strategy', {}),
            'return_strategy': opponent_tactics.get('return_strategy', {})
        }
    
    def _generate_energy_playbook(
        self,
        patterns: List[Dict],
        match_stats: Dict
    ) -> Dict[str, Any]:
        """Generate energy management strategy"""
        high_energy = ENERGY_MANAGEMENT.get('high_energy', {})
        medium_energy = ENERGY_MANAGEMENT.get('medium_energy', {})
        low_energy = ENERGY_MANAGEMENT.get('low_energy', {})
        
        # Analyze rally length patterns
        avg_rally_length = match_stats.get('average_rally_length', 7.0)
        set_3_rally_length = match_stats.get('set_3_rally_length', avg_rally_length)
        
        rally_increase = set_3_rally_length - avg_rally_length
        
        return {
            'high_energy': {
                'when': 'Set 1, early Set 2',
                'approach': high_energy.get('tactical_approach', {}),
                'rally_target': '9-12 shots OK',
                'serve_approach': 'Aggressive first serves, kick second serves'
            },
            'medium_energy': {
                'when': 'Mid Set 2, early Set 3',
                'approach': medium_energy.get('tactical_approach', {}),
                'rally_target': '6-8 shots',
                'serve_approach': '70% first serve in, more slice on second'
            },
            'low_energy': {
                'when': 'Late Set 3, any Set 4-5',
                'approach': low_energy.get('tactical_approach', {}),
                'rally_target': '3-5 shots MAXIMUM',
                'serve_approach': 'Placement over power, serve-volley 50%+'
            },
            'your_pattern': {
                'average_rally_length': f"{avg_rally_length:.1f} shots",
                'set_3_rally_length': f"{set_3_rally_length:.1f} shots",
                'analysis': self._analyze_energy_pattern(rally_increase),
                'improvement': 'Point shortening tactics needed' if rally_increase > 2.0 else 'Good energy management'
            }
        }
    
    def _analyze_energy_pattern(self, rally_increase: float) -> str:
        """Analyze energy management pattern"""
        if rally_increase > 2.5:
            return f"Rally length increased by {rally_increase:.1f} shots in late sets - you're grinding when tired. Shorten points!"
        elif rally_increase > 1.5:
            return f"Rally length up {rally_increase:.1f} shots late - consider attacking earlier to conserve energy"
        elif rally_increase < -1.0:
            return f"Good! Rally length down {abs(rally_increase):.1f} shots late - you're shortening points when tired"
        else:
            return "Rally length consistent throughout match - maintaining energy well"
