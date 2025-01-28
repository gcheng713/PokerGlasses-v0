import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
from enum import Enum

class PlayerStyle(Enum):
    TIGHT_PASSIVE = "tight_passive"    # Plays few hands, rarely raises
    TIGHT_AGGRESSIVE = "tight_aggressive"  # Plays few hands, raises often
    LOOSE_PASSIVE = "loose_passive"    # Plays many hands, rarely raises
    LOOSE_AGGRESSIVE = "loose_aggressive"  # Plays many hands, raises often
    UNKNOWN = "unknown"  # Not enough data

class PlayerAnalyzer:
    def __init__(self):
        self.player_stats = defaultdict(lambda: {
            'hands_played': 0,
            'hands_won': 0,
            'total_hands': 0,
            'vpip_hands': 0,  # Voluntarily Put money In Pot
            'pfr_hands': 0,   # Pre-Flop Raise
            'aggression_frequency': [],  # List of 1 for aggressive actions (raise/bet), 0 for passive
            'average_bet_size': [],
            'bluff_frequency': [],  # Estimated from betting pattern vs hand strength
            'fold_to_3bet': [],    # Folding to 3-bets
            'showdown_wins': 0,
            'showdown_total': 0
        })
        self.kmeans = KMeans(n_clusters=4)
        self.style_thresholds = {
            'vpip': {'tight': 0.25, 'loose': 0.4},
            'pfr': {'passive': 0.15, 'aggressive': 0.25},
            'aggression': {'passive': 0.3, 'aggressive': 0.5}
        }

    def update_player_stats(self, player_id, hand_result):
        """Update player statistics after each hand"""
        stats = self.player_stats[player_id]
        stats['total_hands'] += 1
        
        if hand_result['participated']:
            stats['hands_played'] += 1
            if hand_result['won']:
                stats['hands_won'] += 1
            
            if hand_result['vpip']:
                stats['vpip_hands'] += 1
            if hand_result['pfr']:
                stats['pfr_hands'] += 1
            
            stats['aggression_frequency'].append(1 if hand_result['aggressive_actions'] > hand_result['passive_actions'] else 0)
            stats['average_bet_size'].append(hand_result['average_bet_size'])
            
            if hand_result['went_to_showdown']:
                stats['showdown_total'] += 1
                if hand_result['won_at_showdown']:
                    stats['showdown_wins'] += 1

    def get_player_style(self, player_id):
        """Determine player's playing style based on collected statistics"""
        stats = self.player_stats[player_id]
        
        if stats['total_hands'] < 20:  # Need minimum hands for reliable classification
            return PlayerStyle.UNKNOWN
            
        vpip_rate = stats['vpip_hands'] / stats['total_hands']
        pfr_rate = stats['pfr_hands'] / stats['total_hands']
        aggression_rate = np.mean(stats['aggression_frequency'][-20:])  # Last 20 hands
        
        # Classify based on VPIP and Aggression
        is_loose = vpip_rate > self.style_thresholds['vpip']['loose']
        is_tight = vpip_rate < self.style_thresholds['vpip']['tight']
        is_aggressive = aggression_rate > self.style_thresholds['aggression']['aggressive']
        is_passive = aggression_rate < self.style_thresholds['aggression']['passive']
        
        if is_tight and is_aggressive:
            return PlayerStyle.TIGHT_AGGRESSIVE
        elif is_tight and is_passive:
            return PlayerStyle.TIGHT_PASSIVE
        elif is_loose and is_aggressive:
            return PlayerStyle.LOOSE_AGGRESSIVE
        else:
            return PlayerStyle.LOOSE_PASSIVE

    def get_action_recommendation(self, player_id, game_state, opponent_styles):
        """Get recommended action based on player styles and game state"""
        pot_odds = game_state['to_call'] / (game_state['pot'] + game_state['to_call'])
        hand_strength = self._evaluate_hand_strength(game_state)
        
        recommendations = {
            'action': None,
            'raise_amount': 0,
            'confidence': 0.0,
            'reasoning': []
        }
        
        # Analyze opponent tendencies
        aggressive_opponents = sum(1 for style in opponent_styles.values() 
                                if style in [PlayerStyle.TIGHT_AGGRESSIVE, PlayerStyle.LOOSE_AGGRESSIVE])
        
        # Basic strategy matrix
        if hand_strength > 0.8:  # Very strong hand
            recommendations['action'] = 'raise'
            recommendations['raise_amount'] = game_state['pot'] * 0.75
            recommendations['reasoning'].append("Strong hand strength")
            recommendations['confidence'] = 0.9
            
        elif hand_strength > 0.6:  # Strong hand
            if aggressive_opponents >= 2:
                recommendations['action'] = 'call'
                recommendations['reasoning'].append("Strong hand but multiple aggressive opponents")
                recommendations['confidence'] = 0.7
            else:
                recommendations['action'] = 'raise'
                recommendations['raise_amount'] = game_state['pot'] * 0.5
                recommendations['reasoning'].append("Strong hand against passive opponents")
                recommendations['confidence'] = 0.8
                
        elif hand_strength > 0.4:  # Medium hand
            if pot_odds < hand_strength:
                recommendations['action'] = 'call'
                recommendations['reasoning'].append("Decent hand with good pot odds")
                recommendations['confidence'] = 0.6
            else:
                recommendations['action'] = 'fold'
                recommendations['reasoning'].append("Medium hand with poor pot odds")
                recommendations['confidence'] = 0.65
                
        else:  # Weak hand
            bluff_opportunity = self._evaluate_bluff_opportunity(game_state, opponent_styles)
            if bluff_opportunity > 0.7:
                recommendations['action'] = 'raise'
                recommendations['raise_amount'] = game_state['pot'] * 0.3
                recommendations['reasoning'].append("Bluff opportunity identified")
                recommendations['confidence'] = 0.5
            else:
                recommendations['action'] = 'fold'
                recommendations['reasoning'].append("Weak hand and no good bluff opportunity")
                recommendations['confidence'] = 0.8
        
        return recommendations

    def _evaluate_hand_strength(self, game_state):
        """Evaluate the strength of the current hand"""
        # Implement hand strength evaluation using treys or other poker hand evaluator
        # This is a placeholder returning random strength for demonstration
        return np.random.random()

    def _evaluate_bluff_opportunity(self, game_state, opponent_styles):
        """Evaluate if current situation is good for bluffing"""
        bluff_score = 0.0
        
        # Count tight players who are likely to fold
        tight_players = sum(1 for style in opponent_styles.values() 
                          if style in [PlayerStyle.TIGHT_PASSIVE, PlayerStyle.TIGHT_AGGRESSIVE])
        bluff_score += tight_players * 0.2
        
        # Consider position
        if game_state['position'] == 'late':
            bluff_score += 0.3
        
        # Consider board texture
        if game_state['board_texture'] == 'dry':
            bluff_score += 0.2
        
        # Consider previous action
        if game_state['previous_action'] == 'check':
            bluff_score += 0.2
            
        return min(bluff_score, 1.0)  # Normalize to [0,1]
