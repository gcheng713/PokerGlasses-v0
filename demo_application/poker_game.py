from treys import Card, Evaluator
from enum import Enum
import random
from gto_strategy import GTOStrategy
from player_analysis import PlayerAnalyzer, PlayerStyle
from hand_evaluator import HandEvaluator, HandStrength

class PlayerAction(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all-in"

class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.cards = []
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False
        self.is_ai = False
        self.hand_history = {
            'participated': False,
            'vpip': False,
            'pfr': False,
            'aggressive_actions': 0,
            'passive_actions': 0,
            'average_bet_size': 0,
            'total_bet': 0,
            'num_bets': 0,
            'went_to_showdown': False,
            'won_at_showdown': False,
            'won': False
        }

    def reset(self):
        self.cards = []
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False

class PokerGame:
    def __init__(self, players, starting_chips, small_blind=1):
        self.players = [Player(name, starting_chips) for name in players]
        self.dealer_idx = len(self.players) - 1
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.deck = []
        self.gto_strategy = GTOStrategy(len(players))
        self.player_analyzer = PlayerAnalyzer()
        self.hand_evaluator = HandEvaluator()
        self.initialize_deck()

    def initialize_deck(self):
        """Initialize a standard deck of 52 cards."""
        suits = ['h', 'd', 'c', 's']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
        random.shuffle(self.deck)

    def deal_cards(self):
        """Deal two cards to each player."""
        for _ in range(2):
            for player in self.players:
                if self.deck:
                    player.cards.append(self.deck.pop())

    def deal_community_cards(self, count):
        """Deal specified number of community cards."""
        for _ in range(count):
            if self.deck:
                self.community_cards.append(self.deck.pop())

    def post_blinds(self):
        """Post small and big blinds."""
        sb_idx = (self.dealer_idx + 1) % len(self.players)
        bb_idx = (self.dealer_idx + 2) % len(self.players)
        
        # Post small blind
        sb_amount = min(self.small_blind, self.players[sb_idx].chips)
        self.players[sb_idx].chips -= sb_amount
        self.players[sb_idx].current_bet = sb_amount
        self.pot += sb_amount
        
        # Post big blind
        bb_amount = min(self.big_blind, self.players[bb_idx].chips)
        self.players[bb_idx].chips -= bb_amount
        self.players[bb_idx].current_bet = bb_amount
        self.pot += bb_amount
        
        self.current_bet = bb_amount

    def get_next_player(self, current_idx):
        """Get the next active player after current_idx, moving left (clockwise)."""
        next_idx = (current_idx + 1) % len(self.players)
        while next_idx != current_idx:
            if not self.players[next_idx].folded and not self.players[next_idx].is_all_in:
                return next_idx
            next_idx = (next_idx + 1) % len(self.players)
        return None

    def is_round_complete(self):
        """Check if betting round is complete."""
        active_players = [p for p in self.players if not p.folded and not p.is_all_in]
        
        # If only one player remains, round is complete
        if len(active_players) <= 1:
            return True
        
        # Check if all active players have matched the current bet
        return all(p.current_bet == self.current_bet for p in active_players)

    def process_action(self, player, action, amount=0):
        """Process a player's action."""
        if action == PlayerAction.FOLD:
            player.folded = True
            # Reset their current bet since they folded
            player.current_bet = 0
        elif action == PlayerAction.CHECK:
            pass  # No action needed for check
        elif action == PlayerAction.CALL:
            call_amount = self.current_bet - player.current_bet
            player.chips -= call_amount
            player.current_bet = self.current_bet
            self.pot += call_amount
        elif action == PlayerAction.RAISE:
            # Amount is the total bet (including the call amount)
            raise_amount = amount - player.current_bet
            player.chips -= raise_amount
            player.current_bet = amount
            self.current_bet = amount
            self.pot += raise_amount
        elif action == PlayerAction.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            player.current_bet += all_in_amount
            self.pot += all_in_amount
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
            player.is_all_in = True

        self.update_hand_history(player, action, amount)

    def update_hand_history(self, player, action, bet_amount=0):
        """Update player's hand history based on their action"""
        history = player.hand_history
        history['participated'] = True
        
        if action in [PlayerAction.RAISE, PlayerAction.ALL_IN]:
            history['aggressive_actions'] += 1
            if len(self.community_cards) == 0:  # Pre-flop
                history['pfr'] = True
        elif action in [PlayerAction.CALL, PlayerAction.CHECK]:
            history['passive_actions'] += 1
            
        if action != PlayerAction.CHECK and action != PlayerAction.FOLD:
            history['vpip'] = True
            history['total_bet'] += bet_amount
            history['num_bets'] += 1
            if history['num_bets'] > 0:
                history['average_bet_size'] = history['total_bet'] / history['num_bets']

    def reset_bets(self):
        """Reset all players' current bets to 0."""
        for player in self.players:
            player.current_bet = 0
        self.current_bet = 0

    def move_dealer_button(self):
        """Move the dealer button one position to the left."""
        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        
        # Reset dealer, SB, BB flags
        for player in self.players:
            player.is_dealer = False
            player.is_small_blind = False
            player.is_big_blind = False
            
        # Set new positions
        self.players[self.dealer_idx].is_dealer = True
        sb_idx = (self.dealer_idx + 1) % len(self.players)
        bb_idx = (self.dealer_idx + 2) % len(self.players)
        self.players[sb_idx].is_small_blind = True
        self.players[bb_idx].is_big_blind = True

    def reset_round(self):
        """Reset the game state for a new hand."""
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.initialize_deck()
        for player in self.players:
            player.reset()

    def get_winners(self):
        """Determine the winner(s) of the hand."""
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            return [active_players[0]]
            
        # Use treys for hand evaluation
        evaluator = Evaluator()
        board = [Card.new(card) for card in self.community_cards]
        
        best_score = float('inf')
        winners = []
        
        for player in active_players:
            hole_cards = [Card.new(card) for card in player.cards]
            score = evaluator.evaluate(board, hole_cards)
            
            if score < best_score:
                best_score = score
                winners = [player]
            elif score == best_score:
                winners.append(player)
                
        return winners

    def get_valid_actions(self, player):
        """Get list of valid actions for the current player."""
        valid_actions = []
        
        # Can always fold unless checking is free
        if self.current_bet > player.current_bet:
            valid_actions.append(PlayerAction.FOLD)
            
        # Can check if no bet to call
        if self.current_bet == player.current_bet:
            valid_actions.append(PlayerAction.CHECK)
        else:
            # Can call if player has enough chips
            if player.chips >= (self.current_bet - player.current_bet):
                valid_actions.append(PlayerAction.CALL)
                
        # Can raise if player has enough chips for current bet plus minimum raise
        min_raise = self.current_bet + self.big_blind
        if player.chips >= (min_raise - player.current_bet):
            valid_actions.append(PlayerAction.RAISE)
            
        # Can go all-in if player has chips
        if player.chips > 0:
            valid_actions.append(PlayerAction.ALL_IN)
            
        return valid_actions

    def get_ai_action(self, player_idx):
        """Get the next action for an AI player using enhanced strategy"""
        player = self.players[player_idx]
        valid_actions = self.get_valid_actions(player)
        
        # Get opponent styles
        opponent_styles = {}
        for i, opp in enumerate(self.players):
            if i != player_idx:
                opponent_styles[i] = self.player_analyzer.get_player_style(i)
        
        # Calculate position
        position = 'early' if player_idx < len(self.players) // 3 else 'late'
        
        # Calculate hand strength and pot equity
        hand_strength = self.hand_evaluator.evaluate_hand_strength(
            player.cards, self.community_cards
        )
        
        equity, win_prob, tie_prob = self.hand_evaluator.calculate_pot_equity(
            player.cards,
            self.community_cards,
            sum(1 for p in self.players if not p.folded) - 1  # number of active opponents
        )
        
        # Get betting recommendation
        action, bet_size, confidence = self.hand_evaluator.get_betting_recommendation(
            player.cards,
            self.community_cards,
            self.pot,
            self.current_bet - player.current_bet,  # amount to call
            player.chips,
            sum(1 for p in self.players if not p.folded) - 1,
            position
        )
        
        # Get draw outs if on flop or turn
        draw_outs = {}
        if len(self.community_cards) in [3, 4]:
            draw_outs = self.hand_evaluator.calculate_draw_outs(
                player.cards, self.community_cards
            )
        
        # Create game state for player analyzer
        game_state = {
            'player_cards': player.cards,
            'community_cards': self.community_cards,
            'pot': self.pot,
            'current_bet': self.current_bet,
            'to_call': self.current_bet - player.current_bet,
            'player_chips': player.chips,
            'player_position': player_idx,
            'position': position,
            'board_texture': self._analyze_board_texture(),
            'previous_action': self._get_previous_action(),
            'num_active_players': sum(1 for p in self.players if not p.folded),
            'hand_strength': hand_strength,
            'pot_equity': equity,
            'win_probability': win_prob,
            'draw_outs': draw_outs
        }
        
        # Get final recommendation combining both strategies
        recommendation = self.player_analyzer.get_action_recommendation(
            player_idx, game_state, opponent_styles
        )
        
        # Combine recommendations based on confidence
        if confidence > recommendation['confidence']:
            final_action = action
            final_bet = bet_size
        else:
            final_action = recommendation['action']
            final_bet = recommendation['raise_amount']
        
        # Convert to valid action
        if final_action == 'raise' and PlayerAction.RAISE in valid_actions:
            action = PlayerAction.RAISE
            self._last_raise_amount = min(final_bet, player.chips)
        elif final_action == 'call' and PlayerAction.CALL in valid_actions:
            action = PlayerAction.CALL
        else:
            action = PlayerAction.FOLD if PlayerAction.FOLD in valid_actions else PlayerAction.CHECK
            
        return action

    def get_hand_analysis(self, player_idx):
        """Get detailed analysis of current hand for a player"""
        player = self.players[player_idx]
        
        # Basic hand strength and categorization
        hand_strength = self.hand_evaluator.evaluate_hand_strength(
            player.cards, self.community_cards
        )
        hand_category = self.hand_evaluator.get_hand_strength_category(player.cards)
        
        # Pot equity and win probability
        equity, win_prob, tie_prob = self.hand_evaluator.calculate_pot_equity(
            player.cards,
            self.community_cards,
            sum(1 for p in self.players if not p.folded) - 1
        )
        
        # Draw analysis
        draw_outs = {}
        if len(self.community_cards) in [3, 4]:
            draw_outs = self.hand_evaluator.calculate_draw_outs(
                player.cards, self.community_cards
            )
        
        # Pot odds if facing a bet
        pot_odds = 0
        if self.current_bet > player.current_bet:
            to_call = self.current_bet - player.current_bet
            pot_odds = to_call / (self.pot + to_call)
        
        return {
            'hand_strength': hand_strength,
            'hand_category': hand_category.value,
            'pot_equity': equity,
            'win_probability': win_prob,
            'tie_probability': tie_prob,
            'pot_odds': pot_odds,
            'draw_outs': draw_outs,
            'made_hand': self.hand_evaluator.get_postflop_hand_type(
                player.cards, self.community_cards
            ) if self.community_cards else None
        }

    def _analyze_board_texture(self):
        """Analyze the texture of the community cards"""
        if len(self.community_cards) < 3:
            return 'none'
            
        # Simple analysis - can be expanded
        suits = [card[-1] for card in self.community_cards]
        ranks = [card[0] for card in self.community_cards]
        
        if len(set(suits)) <= 2:
            return 'wet'  # Flush possible
        elif len(set(ranks)) == len(ranks):
            return 'dry'  # No pairs
        else:
            return 'semi-wet'

    def _get_previous_action(self):
        """Get the previous player's action"""
        # Implement logic to track previous action
        return 'unknown'

    def end_hand(self, winners):
        """End the current hand and update player statistics"""
        for player in self.players:
            # Update showdown information
            if not player.folded:
                player.hand_history['went_to_showdown'] = True
                player.hand_history['won_at_showdown'] = player in winners
            
            # Update win information
            player.hand_history['won'] = player in winners
            
            # Update player analyzer
            self.player_analyzer.update_player_stats(
                self.players.index(player),
                player.hand_history
            )
            
            # Reset hand history for next hand
            player.hand_history = {
                'participated': False,
                'vpip': False,
                'pfr': False,
                'aggressive_actions': 0,
                'passive_actions': 0,
                'average_bet_size': 0,
                'total_bet': 0,
                'num_bets': 0,
                'went_to_showdown': False,
                'won_at_showdown': False,
                'won': False
            }
