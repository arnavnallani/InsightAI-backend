"""
Minimax Simulation Core

Implements the minimax decision tree algorithm with alpha-beta pruning
to find optimal shot sequences in tennis matches.
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from strategic_flow_models import (
    MatchState, DecisionNode, ShotState, ShotType, ShotDirection,
    ShotDepth, ShotIntent, CourtPosition, OpponentTendencyProfile
)


class MinimaxSimulationCore:
    """
    Core minimax algorithm for finding optimal decision paths.
    
    Uses depth-limited search with alpha-beta pruning and Monte Carlo rollouts
    for opponent responses.
    """
    
    def __init__(
        self,
        opponent_profile: OpponentTendencyProfile,
        max_depth: int = 6,
        branching_factor: int = 5,
        num_rollouts: int = 100
    ):
        """
        Initialize the minimax core.
        
        Args:
            opponent_profile: Learned tendencies of opponent
            max_depth: Maximum search depth (number of shots ahead)
            branching_factor: Number of alternative shots to consider per decision
            num_rollouts: Number of Monte Carlo simulations per leaf node
        """
        self.opponent_profile = opponent_profile
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.num_rollouts = num_rollouts
        
        # Evaluation weights (used for rollout shot quality, not final evaluation)
        self.weights = {
            'point_equity': 0.40,      # Probability of winning the point
            'momentum': 0.25,          # Momentum impact
            'fatigue': 0.15,           # Fatigue differential
            'strength_exploitation': 0.20  # Using strengths / exploiting weaknesses
        }
    
    def find_optimal_shot(self, initial_state: MatchState) -> Dict:
        """
        Find the optimal shot from the given state.
        
        Args:
            initial_state: Current match state
            
        Returns:
            Dictionary with optimal shot details wrapped in expected structure
        """
        # Find optimal path using minimax
        root = self.find_optimal_path(initial_state)
        
        # Extract the best first move (optimal shot)
        optimal_shot_data = {}
        expected_value = 0.5
        
        if root.children:
            # Get best child (highest value for maximizing player)
            best_child = max(root.children, key=lambda c: c.value if c.value is not None else float('-inf'))
            optimal_shot = best_child.decision
            expected_value = best_child.value if best_child.value is not None else 0.5
            
            if optimal_shot:
                # Convert ShotState to dictionary with placement coordinates
                optimal_shot_data = {
                    'shot_type': optimal_shot.shot_type.value if hasattr(optimal_shot.shot_type, 'value') else str(optimal_shot.shot_type),
                    'direction': optimal_shot.direction.value if hasattr(optimal_shot.direction, 'value') else str(optimal_shot.direction),
                    'depth': optimal_shot.depth.value if hasattr(optimal_shot.depth, 'value') else str(optimal_shot.depth),
                    'spin': 'topspin',  # Default to topspin
                    'speed': 75,  # Default speed
                    'placement': {
                        'x': optimal_shot.position.x * 25,  # Convert 0-4 scale to 0-100
                        'y': 100 - (optimal_shot.position.y * 25)   # Convert AND FLIP: minimax y=0 (player baseline) → diagram Y=100, minimax y=4 (net/opponent) → diagram Y=0
                    }
                }
        
        # Fallback if no children
        if not optimal_shot_data:
            optimal_shot_data = {
                'shot_type': 'Forehand',
                'direction': 'crosscourt',
                'depth': 'deep',
                'spin': 'topspin',
                'speed': 70,
                'placement': {'x': 25, 'y': 15}
            }
        
        # Return in expected structure matching stub implementation
        return {
            'optimal_shot': optimal_shot_data,
            'expected_value': expected_value
        }
    
    def find_optimal_path(self, initial_state: MatchState) -> DecisionNode:
        """
        Find the optimal decision path from the given state.
        
        Args:
            initial_state: Current match state
            
        Returns:
            Root decision node with evaluated tree
        """
        root = DecisionNode(
            state=initial_state,
            depth=0,
            alpha=float('-inf'),
            beta=float('inf')
        )
        
        # Run minimax with alpha-beta pruning
        self._minimax(root, 0, float('-inf'), float('inf'), True)
        
        return root
    
    def _minimax(
        self,
        node: DecisionNode,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool
    ) -> float:
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            node: Current decision node
            depth: Current depth in tree
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing: True if this is player's turn (max node)
            
        Returns:
            Evaluated value of this node
        """
        # Terminal conditions
        if depth >= self.max_depth or self._is_terminal_state(node.state):
            node.value = self._evaluate_state(node.state)
            return node.value
        
        if is_maximizing:
            # Player's turn - find best move
            max_value = float('-inf')
            
            # Generate possible shots
            possible_shots = self._generate_player_shots(node.state)
            
            for shot in possible_shots:
                # Create child node
                child_state = self._simulate_shot_outcome(node.state, shot, is_player=True)
                child = DecisionNode(
                    state=child_state,
                    depth=depth + 1,
                    decision=shot,
                    parent=node
                )
                node.children.append(child)
                
                # Recursively evaluate
                value = self._minimax(child, depth + 1, alpha, beta, False)
                max_value = max(max_value, value)
                alpha = max(alpha, value)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
            
            node.value = max_value
            node.alpha = alpha
            return max_value
        
        else:
            # Opponent's turn - use Monte Carlo sampling
            min_value = float('inf')
            
            # Generate opponent responses based on tendencies
            possible_responses = self._generate_opponent_shots(node.state)
            
            for shot in possible_responses:
                # Create child node
                child_state = self._simulate_shot_outcome(node.state, shot, is_player=False)
                child = DecisionNode(
                    state=child_state,
                    depth=depth + 1,
                    decision=shot,
                    parent=node
                )
                node.children.append(child)
                
                # Recursively evaluate
                value = self._minimax(child, depth + 1, alpha, beta, True)
                min_value = min(min_value, value)
                beta = min(beta, value)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
            
            node.value = min_value
            node.beta = beta
            return min_value
    
    def _is_terminal_state(self, state: MatchState) -> bool:
        """Check if state is terminal (point over)"""
        # Point is over if rally is very long or someone won
        return state.rally_length > 20 or state.player_energy < 0.1 or state.opponent_energy < 0.1
    
    def _evaluate_state(self, state: MatchState) -> float:
        """
        Evaluate a state using Monte Carlo rollouts.
        
        Runs multiple simulations from this state to completion and
        returns the win probability based on actual outcomes.
        """
        # Run Monte Carlo simulations
        wins = 0
        for _ in range(self.num_rollouts):
            if self._simulate_rally_to_completion(state):
                wins += 1
        
        # Return win probability (-1 to 1 scale for minimax)
        win_rate = wins / self.num_rollouts
        # Convert 0-1 to -1 to 1 scale
        return (win_rate - 0.5) * 2
    
    def _simulate_rally_to_completion(self, state: MatchState) -> bool:
        """
        Simulate a rally from given state to completion.
        
        Returns True if player wins, False if opponent wins.
        Uses probabilistic shot outcomes based on position, energy, quality.
        """
        import copy
        current_state = copy.deepcopy(state)
        is_player_turn = len(current_state.recent_shots) % 2 == 0
        
        # Maximum 30 shots in simulated rally
        for _ in range(30):
            # Generate shot for current player
            if is_player_turn:
                shot = self._generate_rollout_shot(current_state, is_player=True)
            else:
                shot = self._generate_rollout_shot(current_state, is_player=False)
            
            # Determine shot outcome
            outcome = self._determine_shot_outcome(shot, current_state, is_player_turn)
            
            if outcome == 'winner':
                # Shot was a winner
                return is_player_turn
            elif outcome == 'error':
                # Shot was an error
                return not is_player_turn
            elif outcome == 'continue':
                # Rally continues - update state
                current_state = self._simulate_shot_outcome(current_state, shot, is_player_turn)
                is_player_turn = not is_player_turn
            
            # Check if someone ran out of energy
            if current_state.player_energy < 0.05:
                return False  # Player loses from exhaustion
            if current_state.opponent_energy < 0.05:
                return True  # Opponent loses from exhaustion
        
        # Rally went too long - use position to determine winner
        return current_state.player_position.y > current_state.opponent_position.y
    
    def _determine_shot_outcome(
        self,
        shot: ShotState,
        state: MatchState,
        is_player: bool
    ) -> str:
        """
        Determine if shot is winner, error, or continues rally.
        
        Returns: 'winner', 'error', or 'continue'
        """
        # Base error probability depends on shot quality and difficulty
        error_prob = 0.05  # Base 5% error rate
        winner_prob = 0.02  # Base 2% winner rate
        
        # Adjust based on shot quality
        if shot.quality < 0.4:
            error_prob += 0.15  # Poor quality = 20% total error
        elif shot.quality > 0.8:
            error_prob -= 0.03  # High quality = 2% error
            winner_prob += 0.08  # High quality = 10% winner
        
        # Adjust based on shot intent
        if shot.intent == ShotIntent.ATTACK:
            error_prob += 0.05  # Aggressive = more errors
            winner_prob += 0.10  # Aggressive = more winners
        elif shot.intent == ShotIntent.DEFEND:
            error_prob -= 0.02  # Defensive = fewer errors
            winner_prob -= 0.02  # Defensive = fewer winners
        
        # Adjust based on position
        if is_player:
            if state.player_position.y >= 3:
                # At net - easier to hit winners
                winner_prob += 0.15
                error_prob += 0.03
        else:
            if state.opponent_position.y >= 3:
                winner_prob += 0.15
                error_prob += 0.03
        
        # Adjust based on energy (fatigue increases errors)
        energy = state.player_energy if is_player else state.opponent_energy
        if energy < 0.3:
            error_prob += 0.10  # Tired = more errors
        
        # Determine outcome
        roll = random.random()
        if roll < error_prob:
            return 'error'
        elif roll < error_prob + winner_prob:
            return 'winner'
        else:
            return 'continue'
    
    def _generate_rollout_shot(self, state: MatchState, is_player: bool) -> ShotState:
        """Generate a random but reasonable shot for Monte Carlo rollout"""
        if is_player:
            # Player shot - consider strengths/weaknesses
            viable_types = [ShotType.FOREHAND, ShotType.BACKHAND]
            if state.player_position.y >= 3:
                viable_types.extend([ShotType.FOREHAND_VOLLEY, ShotType.BACKHAND_VOLLEY])
            
            # Prefer strengths
            shot_type = random.choice(viable_types)
            if state.player_strengths and random.random() < 0.6:
                strengths_viable = [st for st in state.player_strengths if st in viable_types]
                if strengths_viable:
                    shot_type = random.choice(strengths_viable)
            
            quality_base = 0.65
        else:
            # Opponent shot
            shot_type = random.choice([ShotType.FOREHAND, ShotType.BACKHAND])
            quality_base = 0.60
        
        return ShotState(
            shot_type=shot_type,
            direction=random.choice([ShotDirection.CROSSCOURT, ShotDirection.DOWN_THE_LINE, ShotDirection.CENTER]),
            depth=random.choice([ShotDepth.DEEP, ShotDepth.MID, ShotDepth.SHORT]),
            speed_mph=60.0 + random.random() * 25,
            spin_rpm=1500 + int(random.random() * 1500),
            position=state.player_position if is_player else state.opponent_position,
            intent=random.choice([ShotIntent.ATTACK, ShotIntent.NEUTRALIZE, ShotIntent.DEFEND]),
            quality=quality_base + random.random() * 0.3
        )
    
    def _calculate_point_equity(self, state: MatchState) -> float:
        """Calculate probability of winning the point from this state"""
        # Base probability from position
        position_advantage = 0.0
        
        # Player near net is advantageous
        if state.player_position.y >= 3:
            position_advantage += 0.2
        elif state.player_position.y <= 1:
            position_advantage -= 0.1
        
        # Opponent pushed back is advantageous
        if state.opponent_position.y <= 1:
            position_advantage += 0.2
        elif state.opponent_position.y >= 3:
            position_advantage -= 0.1
        
        # Energy differential
        energy_advantage = (state.player_energy - state.opponent_energy) * 0.3
        
        # Momentum factor
        momentum_boost = state.player_momentum * 0.2
        
        # Base + advantages
        equity = 0.5 + position_advantage + energy_advantage + momentum_boost
        
        return max(0.0, min(1.0, equity))
    
    def _calculate_strength_exploitation(self, state: MatchState) -> float:
        """Calculate how well state uses player strengths and exploits opponent weaknesses"""
        score = 0.0
        
        if not state.recent_shots:
            return 0.0
        
        last_shot = state.recent_shots[-1]
        
        # Bonus for using player strengths
        if last_shot.shot_type in state.player_strengths:
            score += 0.3
        
        # Penalty for using player weaknesses
        if last_shot.shot_type in state.player_weaknesses:
            score -= 0.3
        
        # Big bonus for targeting opponent weaknesses
        # (determined by shot direction and opponent position)
        if len(state.recent_shots) >= 2:
            # If we're forcing them to hit their weakness
            prev_shot = state.recent_shots[-2]
            if self._shot_targets_weakness(prev_shot, state.opponent_weaknesses):
                score += 0.4
        
        return score
    
    def _shot_targets_weakness(self, shot: ShotState, opponent_weaknesses: List[ShotType]) -> bool:
        """Check if shot forces opponent to use their weakness"""
        # Simplified: assume crosscourt forehand forces opponent backhand
        if shot.shot_type == ShotType.FOREHAND and shot.direction == ShotDirection.CROSSCOURT:
            return ShotType.BACKHAND in opponent_weaknesses
        if shot.shot_type == ShotType.BACKHAND and shot.direction == ShotDirection.CROSSCOURT:
            return ShotType.FOREHAND in opponent_weaknesses
        return False
    
    def _calculate_landing_position(self, player_pos: CourtPosition, direction: ShotDirection, depth: ShotDepth) -> CourtPosition:
        """
        Calculate where the ball should land based on shot direction and depth.
        Uses ABSOLUTE court coordinates to ensure variation.
        
        Coordinate system: x: 0=Ad side, 4=Deuce side; y: 0=Player baseline, 4=Opponent baseline (net area)
        """
        # Create deterministic seed from direction/depth/position
        # Use simple integer mapping to ensure same inputs always give same outputs
        direction_map = {'crosscourt': 100, 'down_the_line': 200, 'center': 300, 'inside_out': 400, 'inside_in': 500}
        depth_map = {'deep': 10, 'mid': 20, 'short': 30}
        
        position_seed = (
            direction_map.get(direction.value, 0) +
            depth_map.get(depth.value, 0) +
            int(player_pos.x * 10) * 7 +  # Multiply by prime to spread values
            int(player_pos.y * 10) * 13   # Different prime for y
        ) % 1000
        
        # Calculate target X position based on direction using ABSOLUTE coordinates
        if direction == ShotDirection.CROSSCOURT:
            # Crosscourt: opposite side from where player is
            if player_pos.x < 2:  # Player on Ad side
                # Land on Deuce side - absolute coordinates
                target_x = 2.8 + (position_seed % 10) * 0.12  # Range: 2.8-3.88
            else:  # Player on Deuce side
                # Land on Ad side - absolute coordinates
                target_x = 0.12 + (position_seed % 10) * 0.12  # Range: 0.12-1.2
        elif direction == ShotDirection.DOWN_THE_LINE:
            # Down-the-line: same side as player
            if player_pos.x < 2:  # Player on Ad side
                # Stay on Ad side - absolute coordinates
                target_x = 0.15 + (position_seed % 8) * 0.15  # Range: 0.15-1.35
            else:  # Player on Deuce side
                # Stay on Deuce side - absolute coordinates
                target_x = 2.65 + (position_seed % 8) * 0.15  # Range: 2.65-3.85
        else:  # CENTER
            # Center of court - absolute coordinates
            target_x = 1.6 + (position_seed % 6) * 0.13  # Range: 1.6-2.38
        
        # Calculate target Y position based on depth using ABSOLUTE coordinates
        # Higher Y = closer to opponent baseline (better optimal shot)
        if depth == ShotDepth.DEEP:
            # Deep: near opponent baseline (optimal shots should land here)
            # Y range: 3.0-3.7 in minimax coords
            target_y = 3.0 + ((position_seed // 10) % 8) * 0.0875  # Range: 3.0-3.7
        elif depth == ShotDepth.MID:
            # Mid: mid-court area
            # Y range: 2.2-2.9 in minimax coords
            target_y = 2.2 + ((position_seed // 10) % 8) * 0.0875  # Range: 2.2-2.9
        else:  # SHORT
            # Short: near service line (drop shots, angles)
            # Y range: 1.4-2.0 in minimax coords
            target_y = 1.4 + ((position_seed // 10) % 7) * 0.0857  # Range: 1.4-2.0
        
        return CourtPosition(x=target_x, y=target_y)
    
    def _generate_player_shots(self, state: MatchState) -> List[ShotState]:
        """
        Generate viable shot options for player based on state.
        
        Filters to most promising shot families using player strengths.
        """
        shots = []
        
        # Determine viable shot types based on position
        if state.player_position.y >= 3:
            # Near net - volleys and overheads
            viable_types = [ShotType.FOREHAND_VOLLEY, ShotType.BACKHAND_VOLLEY, ShotType.OVERHEAD]
        elif state.player_position.y >= 2:
            # Mid court - approach shots
            viable_types = [ShotType.FOREHAND, ShotType.BACKHAND]
        else:
            # Baseline - groundstrokes
            viable_types = [ShotType.FOREHAND, ShotType.BACKHAND]
        
        # Prioritize player strengths
        prioritized_types = []
        for st in state.player_strengths:
            if st in viable_types:
                prioritized_types.append(st)
        for st in viable_types:
            if st not in prioritized_types:
                prioritized_types.append(st)
        
        # Generate shots with different strategies
        for shot_type in prioritized_types[:self.branching_factor]:
            # Try different directions
            for direction in [ShotDirection.CROSSCOURT, ShotDirection.DOWN_THE_LINE, ShotDirection.CENTER]:
                # Try different depths
                for depth in [ShotDepth.DEEP, ShotDepth.MID]:
                    # CALCULATE THE LANDING POSITION based on direction and depth
                    landing_pos = self._calculate_landing_position(state.player_position, direction, depth)
                    
                    shot = ShotState(
                        shot_type=shot_type,
                        direction=direction,
                        depth=depth,
                        speed_mph=70.0 + random.random() * 20,
                        spin_rpm=2000 + int(random.random() * 1000),
                        position=landing_pos,  # USE CALCULATED LANDING POSITION, not player position!
                        intent=ShotIntent.ATTACK if depth == ShotDepth.DEEP else ShotIntent.NEUTRALIZE,
                        quality=0.7 + random.random() * 0.3
                    )
                    shots.append(shot)
                    
                    if len(shots) >= self.branching_factor:
                        return shots
        
        return shots[:self.branching_factor]
    
    def _generate_opponent_shots(self, state: MatchState) -> List[ShotState]:
        """
        Generate opponent responses using learned tendencies.
        
        Uses Monte Carlo sampling from tendency profile.
        """
        # For now, simplified - generate likely responses
        shots = []
        
        # Check if opponent is breaking under pressure
        if self._is_opponent_breaking(state):
            # Generate weaker shots
            for _ in range(min(3, self.branching_factor)):
                shot = self._generate_weak_opponent_shot(state)
                shots.append(shot)
        else:
            # Generate normal responses
            for _ in range(self.branching_factor):
                shot = self._generate_normal_opponent_shot(state)
                shots.append(shot)
        
        return shots
    
    def _is_opponent_breaking(self, state: MatchState) -> bool:
        """Check if opponent is likely to break under current pressure"""
        # Check breakdown thresholds
        if not state.recent_shots:
            return False
        
        # Count consecutive shots to opponent weakness
        consecutive_to_weakness = 0
        for shot in reversed(state.recent_shots[-10:]):
            if shot.shot_type in state.player_strengths and \
               self._shot_targets_weakness(shot, state.opponent_weaknesses):
                consecutive_to_weakness += 1
            else:
                break
        
        # Check if threshold reached
        for threshold in self.opponent_profile.breakdown_thresholds:
            if consecutive_to_weakness >= threshold.avg_shots_to_break:
                return True
        
        # Also check energy and rally length
        if state.opponent_energy < 0.4 and state.rally_length > 8:
            return True
        
        return False
    
    def _generate_weak_opponent_shot(self, state: MatchState) -> ShotState:
        """Generate a weak shot when opponent is breaking"""
        # Short, slower, to player's strength
        return ShotState(
            shot_type=random.choice([ShotType.FOREHAND, ShotType.BACKHAND]),
            direction=ShotDirection.CENTER,
            depth=ShotDepth.SHORT,
            speed_mph=50.0 + random.random() * 15,
            spin_rpm=1000 + int(random.random() * 500),
            position=state.opponent_position,
            intent=ShotIntent.DEFEND,
            quality=0.3 + random.random() * 0.3
        )
    
    def _generate_normal_opponent_shot(self, state: MatchState) -> ShotState:
        """Generate normal opponent shot"""
        return ShotState(
            shot_type=random.choice([ShotType.FOREHAND, ShotType.BACKHAND]),
            direction=random.choice([ShotDirection.CROSSCOURT, ShotDirection.DOWN_THE_LINE, ShotDirection.CENTER]),
            depth=random.choice([ShotDepth.DEEP, ShotDepth.MID]),
            speed_mph=65.0 + random.random() * 20,
            spin_rpm=1800 + int(random.random() * 1000),
            position=state.opponent_position,
            intent=ShotIntent.NEUTRALIZE,
            quality=0.6 + random.random() * 0.3
        )
    
    def _simulate_shot_outcome(self, state: MatchState, shot: ShotState, is_player: bool) -> MatchState:
        """
        Simulate the outcome of a shot and return new state.
        
        Updates positions, energy, momentum, etc.
        """
        import copy
        new_state = copy.deepcopy(state)
        
        # Update rally length
        new_state.rally_length += 1
        
        # Update positions based on shot
        if is_player:
            # Player shot - update opponent position
            new_state.opponent_position = self._predict_opponent_position(shot)
            # Player position changes slightly
            new_state.player_position.y = min(4, state.player_position.y + 0.2 if shot.depth == ShotDepth.SHORT else state.player_position.y - 0.1)
        else:
            # Opponent shot - update player position
            new_state.player_position = self._predict_player_position(shot)
            # Opponent position changes
            new_state.opponent_position.y = min(4, state.opponent_position.y + 0.2 if shot.depth == ShotDepth.SHORT else state.opponent_position.y - 0.1)
        
        # Update energy
        energy_cost = 0.02 * (1 + state.rally_length * 0.01)
        if is_player:
            new_state.player_energy = max(0, state.player_energy - energy_cost)
        else:
            new_state.opponent_energy = max(0, state.opponent_energy - energy_cost)
        
        # Update momentum
        if is_player and shot.shot_type in state.player_strengths:
            new_state.player_momentum = min(1, state.player_momentum + 0.05)
        elif is_player and shot.quality < 0.5:
            new_state.player_momentum = max(-1, state.player_momentum - 0.05)
        
        # Add shot to recent shots
        new_state.recent_shots = state.recent_shots[-9:] + [shot]
        
        return new_state
    
    def _predict_opponent_position(self, player_shot: ShotState) -> CourtPosition:
        """Predict where opponent will be after player's shot"""
        # Simplified prediction based on shot direction and depth
        x = 2.0  # Center by default
        if player_shot.direction == ShotDirection.CROSSCOURT:
            x = player_shot.position.x
        elif player_shot.direction == ShotDirection.DOWN_THE_LINE:
            x = 4 - player_shot.position.x
        
        y = 0.5 if player_shot.depth == ShotDepth.DEEP else 1.5
        
        return CourtPosition(x=x, y=y)
    
    def _predict_player_position(self, opponent_shot: ShotState) -> CourtPosition:
        """Predict where player will be after opponent's shot"""
        # Similar to opponent prediction
        x = 2.0
        if opponent_shot.direction == ShotDirection.CROSSCOURT:
            x = opponent_shot.position.x
        elif opponent_shot.direction == ShotDirection.DOWN_THE_LINE:
            x = 4 - opponent_shot.position.x
        
        y = 0.5 if opponent_shot.depth == ShotDepth.DEEP else 1.5
        
        return CourtPosition(x=x, y=y)
    
    def get_best_path(self, root: DecisionNode) -> List[DecisionNode]:
        """Extract the best path from the evaluated tree"""
        path = [root]
        current = root
        
        # Follow the best child at each level
        while current.children:
            # Find child with best value
            if current.is_max_node():
                best_child = max(current.children, key=lambda c: c.value)
            else:
                best_child = min(current.children, key=lambda c: c.value)
            
            path.append(best_child)
            current = best_child
        
        return path
