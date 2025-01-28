from treys import Card, Evaluator
import numpy as np
from enum import Enum
from itertools import combinations
import random

class HandStrength(Enum):
    PREMIUM = "premium"         # AA, KK, QQ, AKs
    STRONG = "strong"          # JJ, TT, AQs, AJs, KQs
    MEDIUM = "medium"          # 99-77, ATs-A8s, KJs-KTs, QJs
    SPECULATIVE = "speculative"# Small pairs, suited connectors
    WEAK = "weak"             # Everything else

class HandEvaluator:
    def __init__(self):
        self.evaluator = Evaluator()
        self.premium_hands = {
            'pairs': {'AA', 'KK', 'QQ'},
            'suited': {'AKs'},
            'offsuit': {'AKo'}
        }
        self.strong_hands = {
            'pairs': {'JJ', 'TT'},
            'suited': {'AQs', 'AJs', 'KQs'},
            'offsuit': {'AQo'}
        }
        self.medium_hands = {
            'pairs': {'99', '88', '77'},
            'suited': {'ATs', 'A9s', 'A8s', 'KJs', 'KTs', 'QJs'},
            'offsuit': {'AJo', 'KQo'}
        }
        self.speculative_hands = {
            'pairs': {'66', '55', '44', '33', '22'},
            'suited': {'76s', '65s', '54s', '43s', 'T9s', '98s', '87s'},
            'offsuit': {}
        }

    def _hand_to_str(self, cards):
        """Convert hand cards to string representation"""
        ranks = '23456789TJQKA'
        suits = 'hdcs'
        
        if len(cards) != 2:
            return ''
            
        card1, card2 = sorted([
            (ranks.index(c[0]), suits.index(c[1])) for c in cards
        ], reverse=True)
        
        rank1, suit1 = card1
        rank2, suit2 = card2
        
        if rank1 == rank2:  # Pair
            return ranks[rank1] * 2
        else:
            suffix = 's' if suit1 == suit2 else 'o'
            return f"{ranks[rank1]}{ranks[rank2]}{suffix}"

    def get_hand_strength_category(self, hole_cards):
        """Categorize starting hand strength"""
        hand_str = self._hand_to_str(hole_cards)
        
        if any(hand_str in hands for hands in self.premium_hands.values()):
            return HandStrength.PREMIUM
        elif any(hand_str in hands for hands in self.strong_hands.values()):
            return HandStrength.STRONG
        elif any(hand_str in hands for hands in self.medium_hands.values()):
            return HandStrength.MEDIUM
        elif any(hand_str in hands for hands in self.speculative_hands.values()):
            return HandStrength.SPECULATIVE
        else:
            return HandStrength.WEAK

    def evaluate_hand_strength(self, hole_cards, community_cards=[]):
        """
        Evaluate the absolute strength of a hand (0-1 scale)
        0 = worst possible hand
        1 = best possible hand
        """
        if not community_cards:
            # Preflop hand strength
            strength_map = {
                HandStrength.PREMIUM: 0.9,
                HandStrength.STRONG: 0.7,
                HandStrength.MEDIUM: 0.5,
                HandStrength.SPECULATIVE: 0.3,
                HandStrength.WEAK: 0.1
            }
            return strength_map[self.get_hand_strength_category(hole_cards)]
        
        # Convert string cards to Card objects
        board = [Card.new(card) for card in community_cards]
        hand = [Card.new(card) for card in hole_cards]
        
        # Get hand rank (lower is better in treys)
        rank = self.evaluator.evaluate(hand, board)
        
        # Convert rank to percentile (0-1 scale)
        return 1 - (rank / 7462)  # 7462 is the total number of distinct hands

    def calculate_pot_equity(self, hole_cards, community_cards, num_opponents, num_simulations=1000):
        """
        Calculate pot equity through Monte Carlo simulation
        Returns: (equity, win_probability, tie_probability)
        """
        wins = 0
        ties = 0
        
        # Convert known cards to Card objects
        my_hand = [Card.new(card) for card in hole_cards]
        board = [Card.new(card) for card in community_cards]
        
        # Create deck excluding known cards
        deck = []
        for rank in 'AKQJT98765432':
            for suit in 'hdcs':
                card = f"{rank}{suit}"
                if card not in hole_cards and card not in community_cards:
                    deck.append(Card.new(card))
        
        for _ in range(num_simulations):
            # Deal random cards to opponents
            simulation_deck = deck.copy()
            random.shuffle(simulation_deck)
            
            opponent_hands = []
            for _ in range(num_opponents):
                opponent_hands.append(simulation_deck[:2])
                simulation_deck = simulation_deck[2:]
            
            # Complete the board if needed
            remaining_board = simulation_deck[:5-len(community_cards)]
            simulation_board = board + remaining_board
            
            # Evaluate all hands
            my_rank = self.evaluator.evaluate(my_hand, simulation_board)
            opponent_ranks = [self.evaluator.evaluate(hand, simulation_board) 
                            for hand in opponent_hands]
            
            # Count wins and ties
            if my_rank < min(opponent_ranks):  # Remember: lower rank is better
                wins += 1
            elif my_rank == min(opponent_ranks):
                ties += 1
        
        equity = (wins + ties/2) / num_simulations
        return equity, wins/num_simulations, ties/num_simulations

    def get_betting_recommendation(self, hole_cards, community_cards, pot_size, 
                                 to_call, stack_size, num_opponents, position):
        """
        Get betting recommendation based on hand strength and pot equity
        Returns: (action, bet_size, confidence)
        """
        hand_strength = self.evaluate_hand_strength(hole_cards, community_cards)
        equity, win_prob, _ = self.calculate_pot_equity(
            hole_cards, community_cards, num_opponents
        )
        
        # Calculate pot odds if facing a bet
        pot_odds = to_call / (pot_size + to_call) if to_call > 0 else 0
        
        # Base recommendation on pot odds and equity
        if equity > pot_odds + 0.1:  # Significant edge
            if hand_strength > 0.8:
                return 'raise', pot_size * 0.75, 0.9
            elif equity > 0.7:
                return 'raise', pot_size * 0.5, 0.8
            elif equity > pot_odds + 0.2:
                return 'raise', pot_size * 0.33, 0.7
            else:
                return 'call', to_call, 0.6
        elif equity > pot_odds:  # Small edge
            if position == 'late' and num_opponents <= 2:
                return 'call', to_call, 0.6
            else:
                return 'call', to_call, 0.5
        else:  # No edge
            if to_call == 0 and position == 'late':
                return 'check', 0, 0.7
            else:
                return 'fold', 0, 0.8

    def get_postflop_hand_type(self, hole_cards, community_cards):
        """Classify the type of hand made with the community cards"""
        board = [Card.new(card) for card in community_cards]
        hand = [Card.new(card) for card in hole_cards]
        
        rank = self.evaluator.evaluate(hand, board)
        hand_class = self.evaluator.get_rank_class(rank)
        
        return self.evaluator.class_to_string(hand_class)

    def calculate_draw_outs(self, hole_cards, community_cards):
        """Calculate number of outs for potential draws"""
        if len(community_cards) < 3:
            return {}
            
        outs = {
            'flush_draw': 0,
            'straight_draw': 0,
            'two_pair_draw': 0,
            'set_draw': 0
        }
        
        # Current hand strength
        current_strength = self.evaluate_hand_strength(hole_cards, community_cards)
        
        # Check each possible card
        for rank in 'AKQJT98765432':
            for suit in 'hdcs':
                card = f"{rank}{suit}"
                if card not in hole_cards and card not in community_cards:
                    # Calculate strength with this card
                    new_board = community_cards + [card]
                    new_strength = self.evaluate_hand_strength(hole_cards, new_board)
                    
                    if new_strength > current_strength + 0.2:  # Significant improvement
                        if self.get_postflop_hand_type(hole_cards, new_board) == "Flush":
                            outs['flush_draw'] += 1
                        elif self.get_postflop_hand_type(hole_cards, new_board) == "Straight":
                            outs['straight_draw'] += 1
                        elif self.get_postflop_hand_type(hole_cards, new_board) == "Two Pair":
                            outs['two_pair_draw'] += 1
                        elif self.get_postflop_hand_type(hole_cards, new_board) == "Three of a Kind":
                            outs['set_draw'] += 1
        
        return outs
