from poker_game import PokerGame, PlayerAction
import sys

def print_game_state(game, show_all_cards=False):
    """Print the current state of the game."""
    print("\n" + "="*50)
    print(f"Pot: ${game.pot}")
    print(f"Current bet: ${game.current_bet}")
    if game.community_cards:
        print("\nCommunity cards:")
        print("  " + " ".join(game.community_cards))
    print("\nPlayers:")
    for i, player in enumerate(game.players):
        position = []
        if player.is_dealer:
            position.append("Dealer")
        if player.is_small_blind:
            position.append("SB")
        if player.is_big_blind:
            position.append("BB")
        position = " ".join(position)
        
        status = "Folded" if player.folded else "All-in" if player.is_all_in else "Active"
        # Show cards if it's a showdown, or if player is active and it's their cards
        if show_all_cards or (not player.folded and i == game.dealer_idx):
            cards = ' '.join(player.cards) if player.cards else "Unknown"
        else:
            cards = ' '.join(player.cards) if len(player.cards) == 2 and not player.folded else "?? ??"
        print(f"Player {i+1} ({position}): ${player.chips} - Bet: ${player.current_bet} - Cards: {cards} - {status}")

def get_player_action(game, player_idx):
    """Get action from a player."""
    player = game.players[player_idx]
    print(f"\nPlayer {player_idx + 1}'s turn")
    print(f"Your cards: {' '.join(player.cards)}")
    print(f"Your chips: ${player.chips}")
    print(f"Current bet: ${game.current_bet}")
    print(f"Your current bet: ${player.current_bet}")
    
    valid_actions = []
    
    # Check if player can check
    can_check = game.current_bet <= player.current_bet
    if can_check:
        valid_actions.append(PlayerAction.CHECK)
    
    # Can always fold
    valid_actions.append(PlayerAction.FOLD)
    
    # Can call if there's a bet to call and player has enough chips
    call_amount = game.current_bet - player.current_bet
    if call_amount > 0 and call_amount <= player.chips:
        valid_actions.append(PlayerAction.CALL)
    
    # Can raise if player has enough chips
    if player.chips > call_amount:
        valid_actions.append(PlayerAction.RAISE)
    
    # Can always go all-in if they have chips
    if player.chips > 0:
        valid_actions.append(PlayerAction.ALL_IN)
    
    print("\nValid actions:")
    for i, action in enumerate(valid_actions):
        print(f"{i+1}. {action.value}")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (number): ")) - 1
            if 0 <= choice < len(valid_actions):
                action = valid_actions[choice]
                if action == PlayerAction.RAISE:
                    min_raise = game.current_bet + game.big_blind
                    max_raise = player.chips + player.current_bet
                    while True:
                        try:
                            amount = int(input(f"Enter raise amount (${min_raise}-${max_raise}): "))
                            if min_raise <= amount <= max_raise:
                                return action, amount
                            print("Invalid amount!")
                        except ValueError:
                            print("Please enter a valid number!")
                return action, 0
            print("Invalid choice!")
        except ValueError:
            print("Please enter a valid number!")

def run_betting_round(game, start_idx, round_name):
    """Run a betting round starting from start_idx."""
    print(f"\n{round_name} betting round")
    print_game_state(game)
    
    current_idx = start_idx
    first_to_act = True
    last_raiser = None
    bb_idx = (game.dealer_idx + 2) % len(game.players)  # Big blind position
    bb_has_option = round_name == "Pre-flop"  # Track if BB needs option to raise
    
    while True:
        # Get next player
        if not first_to_act:
            current_idx = game.get_next_player(current_idx)
            if current_idx is None:
                break
        first_to_act = False
        
        player = game.players[current_idx]
        
        # Pre-flop, if we've gone around to BB and they haven't had option to raise
        if bb_has_option and current_idx == bb_idx and game.current_bet == game.big_blind:
            print("\nBig blind has option to raise")
            bb_has_option = False
        
        action, amount = get_player_action(game, current_idx)
        game.process_action(player, action, amount)
        
        if action == PlayerAction.RAISE:
            last_raiser = current_idx
            if current_idx == bb_idx:
                bb_has_option = False
        
        print_game_state(game)
        
        # Check if betting round is complete
        if game.is_round_complete():
            # Pre-flop, BB still needs option and hasn't folded
            if bb_has_option and not game.players[bb_idx].folded:
                continue
            break

def wait_for_enter():
    """Wait for user to press Enter to continue."""
    input("\nPress Enter to continue...")

def play_poker():
    """Start and run a poker game."""
    # Get game setup from user
    while True:
        try:
            num_players = int(input("Enter number of players (2-9): "))
            if 2 <= num_players <= 9:
                break
            print("Number of players must be between 2 and 9!")
        except ValueError:
            print("Please enter a valid number!")
    
    while True:
        try:
            starting_stack = int(input("Enter starting stack for each player: "))
            if starting_stack >= 10:
                break
            print("Starting stack must be at least 10!")
        except ValueError:
            print("Please enter a valid number!")
    
    # Initialize game
    player_names = [f"Player {i+1}" for i in range(num_players)]
    game = PokerGame(player_names, starting_stack)
    
    # Main game loop
    while True:
        # Start new hand
        game.reset_round()
        game.move_dealer_button()
        game.post_blinds()
        game.deal_cards()
        
        print("\nNew hand starting!")
        print_game_state(game)
        wait_for_enter()
        
        # Pre-flop betting (starts after big blind)
        start_idx = (game.dealer_idx + 3) % len(game.players)  # Start with UTG
        run_betting_round(game, start_idx, "Pre-flop")
        
        # Check if only one player remains
        active_players = [p for p in game.players if not p.folded]
        if len(active_players) == 1:
            print(f"\n{active_players[0].name} wins ${game.pot}!")
            active_players[0].chips += game.pot
        else:
            # Flop
            print("\nReady to deal the flop...")
            wait_for_enter()
            game.deal_community_cards(3)
            game.reset_bets()  # Reset bets for new street
            print_game_state(game)
            
            # Post-flop betting (starts left of dealer)
            while True:
                start_idx = (game.dealer_idx + 1) % len(game.players)
                run_betting_round(game, start_idx, "Flop")
                
                # Ask if players want to continue betting
                if input("\nContinue betting on flop? (y/n): ").lower() != 'y':
                    break
                game.reset_bets()
            
            active_players = [p for p in game.players if not p.folded]
            if len(active_players) > 1:
                # Turn
                print("\nReady to deal the turn...")
                wait_for_enter()
                game.deal_community_cards(1)
                game.reset_bets()
                print_game_state(game)
                
                # Post-turn betting (starts left of dealer)
                while True:
                    start_idx = (game.dealer_idx + 1) % len(game.players)
                    run_betting_round(game, start_idx, "Turn")
                    
                    # Ask if players want to continue betting
                    if input("\nContinue betting on turn? (y/n): ").lower() != 'y':
                        break
                    game.reset_bets()
                
                active_players = [p for p in game.players if not p.folded]
                if len(active_players) > 1:
                    # River
                    print("\nReady to deal the river...")
                    wait_for_enter()
                    game.deal_community_cards(1)
                    game.reset_bets()
                    print_game_state(game)
                    
                    # Post-river betting (starts left of dealer)
                    while True:
                        start_idx = (game.dealer_idx + 1) % len(game.players)
                        run_betting_round(game, start_idx, "River")
                        
                        # Ask if players want to continue betting
                        if input("\nContinue betting on river? (y/n): ").lower() != 'y':
                            break
                        game.reset_bets()
                    
                    # Showdown
                    active_players = [p for p in game.players if not p.folded]
                    if len(active_players) > 1:
                        print("\nShowdown!")
                        print_game_state(game, show_all_cards=True)
                        winners = game.get_winners()
                        if winners:
                            win_amount = game.pot // len(winners)
                            for winner in winners:
                                print(f"{winner.name} wins ${win_amount} with cards: {' '.join(winner.cards)}")
                                winner.chips += win_amount
                        wait_for_enter()
        
        # Ask to continue
        if input("\nPlay another hand? (y/n): ").lower() != 'y':
            break
        
        # Check if enough players have chips to continue
        players_with_chips = sum(1 for p in game.players if p.chips >= game.big_blind)
        if players_with_chips < 2:
            print("Not enough players with chips to continue!")
            break

if __name__ == "__main__":
    play_poker()
