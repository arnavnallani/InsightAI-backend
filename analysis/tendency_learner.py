"""
Opponent Tendency Learner

Learns opponent patterns, breakdown thresholds, and response tendencies
using Bayesian updating from match data.
"""

from collections import defaultdict
from typing import List, Dict, Tuple
import math
from .strategic_flow_models import (
    OpponentTendencyProfile, ShotContext, ShotResponse, BreakdownThreshold,
    ShotType, ShotDirection, ShotDepth, CourtPosition
)


class OpponentTendencyLearner:
    """
    Learns opponent tendencies from match data using Bayesian updating.
    
    Discovers:
    - Response patterns given shot contexts
    - Breakdown thresholds (when they give weak shots)
    - Strong/weak zones on court
    - Pressure handling characteristics
    """
    
    def __init__(self, smoothing_alpha: float = 0.1):
        """
        Initialize the learner.
        
        Args:
            smoothing_alpha: Laplace smoothing parameter for probability estimation
        """
        self.smoothing_alpha = smoothing_alpha
    
    def learn_from_match(self, shots: List[Dict], rallies: List[Dict], player_name: str) -> OpponentTendencyProfile:
        """
        Learn opponent tendencies from match data.
        
        Args:
            shots: List of shot dictionaries from match
            rallies: List of rally dictionaries from match
            player_name: Name of the player (to identify opponent shots)
            
        Returns:
            Learned opponent tendency profile
        """
        profile = OpponentTendencyProfile()
        
        # Identify opponent shots
        opponent_shots = [s for s in shots if s.get('player') != player_name]
        player_shots = [s for s in shots if s.get('player') == player_name]
        
        # Learn response probabilities
        profile.response_probabilities = self._learn_response_probabilities(
            player_shots, opponent_shots
        )
        
        # Detect breakdown thresholds
        profile.breakdown_thresholds = self._detect_breakdown_thresholds(
            player_shots, opponent_shots, rallies
        )
        
        # Identify strong/weak zones
        profile.strong_zones, profile.weak_zones = self._identify_zone_tendencies(
            opponent_shots
        )
        
        # Learn fatigue response degradation
        profile.fatigue_response_degradation = self._learn_fatigue_patterns(
            opponent_shots, rallies
        )
        
        # Learn pressure error rates
        profile.pressure_error_rate = self._learn_pressure_handling(
            opponent_shots, rallies
        )
        
        return profile
    
    def _learn_response_probabilities(
        self,
        player_shots: List[Dict],
        opponent_shots: List[Dict]
    ) -> Dict[ShotContext, Dict[ShotResponse, float]]:
        """
        Learn P(opponent response | player shot context) using Bayesian updating.
        """
        # Build context -> response count mappings
        context_response_counts = defaultdict(lambda: defaultdict(int))
        context_totals = defaultdict(int)
        
        # Process shot sequences
        for i in range(len(player_shots) - 1):
            player_shot = player_shots[i]
            
            # Find corresponding opponent response
            if i < len(opponent_shots):
                opponent_shot = opponent_shots[i]
                
                # Build context
                context = self._build_shot_context(player_shot, i, player_shots)
                
                # Build response
                response = self._build_shot_response(opponent_shot)
                
                # Update counts
                context_response_counts[context][response] += 1
                context_totals[context] += 1
        
        # Convert counts to probabilities with Laplace smoothing
        response_probs = {}
        for context, responses in context_response_counts.items():
            total = context_totals[context]
            vocab_size = len(responses) + 1  # +1 for unseen responses
            
            response_probs[context] = {}
            for response, count in responses.items():
                # Laplace smoothing
                prob = (count + self.smoothing_alpha) / (total + self.smoothing_alpha * vocab_size)
                response_probs[context][response] = prob
        
        return response_probs
    
    def _detect_breakdown_thresholds(
        self,
        player_shots: List[Dict],
        opponent_shots: List[Dict],
        rallies: List[Dict]
    ) -> List[BreakdownThreshold]:
        """
        Detect when opponent breaks under repeated pressure.
        
        Looks for patterns like:
        - "After 5 consecutive backhands to their backhand, they give a short ball"
        - "After 3 deep heavy forehands, they hit a weak slice"
        """
        thresholds = []
        
        # Group shots by rally
        rally_shot_sequences = defaultdict(list)
        for shot in player_shots:
            rally_id = shot.get('rally_id', 0)
            rally_shot_sequences[rally_id].append(shot)
        
        # Analyze each rally for breakdown patterns
        breakdown_sequences = []
        
        for rally_id, rally_shots in rally_shot_sequences.items():
            # Look for consecutive shots to same target
            for start_idx in range(len(rally_shots) - 2):
                sequence = []
                shot_types = []
                
                # Build sequence
                for offset in range(min(10, len(rally_shots) - start_idx)):
                    shot = rally_shots[start_idx + offset]
                    shot_type = shot.get('shot_type', 'forehand')
                    shot_types.append(shot_type)
                    sequence.append(shot)
                    
                    # Check if next opponent shot is weak (if available)
                    if start_idx + offset < len(opponent_shots):
                        opponent_response = opponent_shots[start_idx + offset]
                        if self._is_weak_shot(opponent_response):
                            # Found a breakdown!
                            breakdown_sequences.append({
                                'sequence': shot_types,
                                'length': len(shot_types),
                                'breakdown_type': opponent_response.get('shot_type', 'unknown')
                            })
                            break
        
        # Cluster similar breakdown sequences
        sequence_clusters = self._cluster_breakdown_sequences(breakdown_sequences)
        
        # Convert to breakdown thresholds
        for cluster in sequence_clusters:
            if len(cluster) >= 3:  # Need at least 3 occurrences to be confident
                avg_length = sum(b['length'] for b in cluster) / len(cluster)
                breakdown_types = defaultdict(int)
                for b in cluster:
                    breakdown_types[b['breakdown_type']] += 1
                
                # Create threshold
                threshold = BreakdownThreshold(
                    shot_sequence=[ShotType(s) if s in [e.value for e in ShotType] else ShotType.FOREHAND 
                                  for s in cluster[0]['sequence']],
                    avg_shots_to_break=avg_length,
                    breakdown_shot_types={
                        ShotType(k): v/len(cluster) 
                        for k, v in breakdown_types.items()
                        if k in [e.value for e in ShotType]
                    },
                    confidence=min(1.0, len(cluster) / 10.0)
                )
                thresholds.append(threshold)
        
        return thresholds
    
    def _identify_zone_tendencies(
        self,
        opponent_shots: List[Dict]
    ) -> Tuple[List[str], List[str]]:
        """
        Identify court zones where opponent is strong vs weak.
        
        Returns:
            (strong_zones, weak_zones)
        """
        zone_stats = defaultdict(lambda: {'total': 0, 'winners': 0, 'errors': 0})
        
        for shot in opponent_shots:
            zone = self._get_zone_name(shot.get('land_x', 2.0), shot.get('land_y', 2.0))
            zone_stats[zone]['total'] += 1
            
            if shot.get('is_winner'):
                zone_stats[zone]['winners'] += 1
            if shot.get('is_error'):
                zone_stats[zone]['errors'] += 1
        
        # Calculate success rates
        zone_success_rates = {}
        for zone, stats in zone_stats.items():
            if stats['total'] > 5:  # Need enough data
                success_rate = (stats['winners'] - stats['errors']) / stats['total']
                zone_success_rates[zone] = success_rate
        
        # Identify strong (top 30%) and weak (bottom 30%) zones
        sorted_zones = sorted(zone_success_rates.items(), key=lambda x: x[1], reverse=True)
        
        num_strong = max(1, len(sorted_zones) // 3)
        num_weak = max(1, len(sorted_zones) // 3)
        
        strong_zones = [z[0] for z in sorted_zones[:num_strong]]
        weak_zones = [z[0] for z in sorted_zones[-num_weak:]]
        
        return strong_zones, weak_zones
    
    def _learn_fatigue_patterns(
        self,
        opponent_shots: List[Dict],
        rallies: List[Dict]
    ) -> Dict[str, float]:
        """
        Learn how opponent shot quality degrades with fatigue.
        
        Returns dict mapping quarter -> quality_degradation_factor
        """
        # Group shots by match quarter
        total_rallies = len(rallies)
        quarter_shots = {
            'Q1': [],
            'Q2': [],
            'Q3': [],
            'Q4': []
        }
        
        for shot in opponent_shots:
            rally_num = shot.get('rally_id', 0)
            if rally_num < total_rallies * 0.25:
                quarter = 'Q1'
            elif rally_num < total_rallies * 0.5:
                quarter = 'Q2'
            elif rally_num < total_rallies * 0.75:
                quarter = 'Q3'
            else:
                quarter = 'Q4'
            
            quarter_shots[quarter].append(shot)
        
        # Calculate average quality per quarter
        quarter_quality = {}
        baseline_quality = None
        
        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            shots = quarter_shots[quarter]
            if shots:
                avg_quality = sum(s.get('quality', 0.7) for s in shots) / len(shots)
                quarter_quality[quarter] = avg_quality
                
                if quarter == 'Q1':
                    baseline_quality = avg_quality
        
        # Calculate degradation relative to Q1
        degradation = {}
        if baseline_quality:
            for quarter, quality in quarter_quality.items():
                degradation[quarter] = baseline_quality - quality
        
        return degradation
    
    def _learn_pressure_handling(
        self,
        opponent_shots: List[Dict],
        rallies: List[Dict]
    ) -> Dict[str, float]:
        """
        Learn error rates at different pressure levels.
        
        Returns dict mapping pressure_level -> error_rate
        """
        pressure_errors = defaultdict(lambda: {'total': 0, 'errors': 0})
        
        for shot in opponent_shots:
            # Determine pressure level
            rally = next((r for r in rallies if r.get('id') == shot.get('rally_id')), None)
            if not rally:
                continue
            
            pressure = self._calculate_pressure_level(rally)
            
            pressure_errors[pressure]['total'] += 1
            if shot.get('is_error'):
                pressure_errors[pressure]['errors'] += 1
        
        # Calculate error rates
        error_rates = {}
        for pressure, stats in pressure_errors.items():
            if stats['total'] > 0:
                error_rates[pressure] = stats['errors'] / stats['total']
        
        return error_rates
    
    def _build_shot_context(self, shot: Dict, shot_idx: int, all_shots: List[Dict]) -> ShotContext:
        """Build shot context for tendency learning"""
        shot_type = ShotType(shot.get('shot_type', 'forehand'))
        direction = ShotDirection(shot.get('direction', 'crosscourt'))
        depth = ShotDepth(shot.get('depth', 'deep'))
        
        # Determine pressure (simplified)
        pressure = "high" if shot_idx > len(all_shots) * 0.7 else "medium" if shot_idx > len(all_shots) * 0.3 else "low"
        
        # Get zone
        court_zone = self._get_zone_name(shot.get('land_x', 2.0), shot.get('land_y', 2.0))
        
        # Rally length bin
        rally_length = shot.get('rally_length', 5)
        rally_bin = "long" if rally_length > 10 else "medium" if rally_length > 5 else "short"
        
        return ShotContext(
            shot_type=shot_type,
            direction=direction,
            depth=depth,
            pressure_level=pressure,
            court_zone=court_zone,
            rally_length_bin=rally_bin
        )
    
    def _build_shot_response(self, shot: Dict) -> ShotResponse:
        """Build shot response for tendency learning"""
        return ShotResponse(
            shot_type=ShotType(shot.get('shot_type', 'forehand')),
            direction=ShotDirection(shot.get('direction', 'crosscourt')),
            depth=ShotDepth(shot.get('depth', 'deep')),
            quality=shot.get('quality', 0.7),
            is_error=shot.get('is_error', False),
            is_winner=shot.get('is_winner', False)
        )
    
    def _is_weak_shot(self, shot: Dict) -> bool:
        """Check if shot is weak (short, slow, or error)"""
        return (
            shot.get('depth') == 'short' or
            shot.get('speed_mph', 70) < 55 or
            shot.get('quality', 0.7) < 0.4 or
            shot.get('is_error', False)
        )
    
    def _get_zone_name(self, x: float, y: float) -> str:
        """Get zone name from coordinates"""
        y_zone = "Net" if y >= 3 else "Volley" if y >= 2 else "Mid" if y >= 1 else "Baseline"
        x_zone = "Ad Side" if x < 1.5 else "Center" if x < 2.5 else "Deuce Side"
        return f"{x_zone} {y_zone}"
    
    def _cluster_breakdown_sequences(self, sequences: List[Dict]) -> List[List[Dict]]:
        """Cluster similar breakdown sequences together"""
        if not sequences:
            return []
        
        clusters = []
        
        for seq in sequences:
            # Find matching cluster
            matched = False
            for cluster in clusters:
                # Check if similar to cluster representative
                if self._sequences_similar(seq['sequence'], cluster[0]['sequence']):
                    cluster.append(seq)
                    matched = True
                    break
            
            if not matched:
                clusters.append([seq])
        
        return clusters
    
    def _sequences_similar(self, seq1: List[str], seq2: List[str]) -> bool:
        """Check if two sequences are similar"""
        if abs(len(seq1) - len(seq2)) > 2:
            return False
        
        # Check if majority of shots match
        min_len = min(len(seq1), len(seq2))
        matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])
        
        return matches / min_len >= 0.7
    
    def _calculate_pressure_level(self, rally: Dict) -> str:
        """Calculate pressure level for a rally"""
        # Simplified: based on score and rally length
        point_score = rally.get('point_score', '0-0')
        rally_length = rally.get('length', 5)
        
        # High pressure at deuce, break points, etc.
        if 'deuce' in point_score.lower() or '40-30' in point_score or '30-40' in point_score:
            return "high"
        elif rally_length > 8:
            return "high"
        elif rally_length > 4:
            return "medium"
        else:
            return "low"
