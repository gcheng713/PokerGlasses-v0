from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
from poker_game import PokerGame, Player
from hand_evaluator import HandEvaluator
import json
import threading
from collections import deque
import time
from ultralytics import YOLO
import os

app = Flask(__name__)

class PokerVisionSystem:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        model_path = os.path.abspath('../final_models/yolov8m_tuned.pt')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model not found at {model_path}")
        print(f"Loading YOLO model from {model_path}")
        self.model = YOLO(model_path)
        self.poker_game = None
        self.hand_evaluator = HandEvaluator()
        self.detected_cards = {
            'player_cards': [],
            'community_cards': [],
            'last_detection_time': 0,
            'detection_buffer': deque(maxlen=3),
            'waiting_for_community': True,
            'street_complete': False,
            'seen_cards': set(),
            'current_bet': 0  # Track current bet amount
        }
        self.lock = threading.Lock()
        self.opponent_actions = []
        self.pot_size = 0
        self.current_bet = 0  # Track the current bet amount
        self.opponents = []
        self.current_street = 0
        print("PokerVisionSystem initialized")

    def initialize_game(self, num_opponents, stacks):
        """Initialize or reset the game with given number of opponents and their stacks"""
        player_names = ['Player'] + [f'Opponent{i+1}' for i in range(num_opponents)]
        self.opponents = [{
            'name': f'Opponent{i+1}',
            'stack': stacks[i],
            'style': 'Unknown',
            'position': i + 1,
            'stats': {'vpip': 0, 'pfr': 0, 'aggression': 0}
        } for i in range(num_opponents)]
        
        self.poker_game = PokerGame(player_names, stacks[0])
        return {'status': 'success', 'message': f'Game initialized with {num_opponents} opponents'}

    def detect_cards(self, frame):
        """Detect cards in the frame using YOLO model"""
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.model(frame_rgb, conf=0.4)  # Lower confidence threshold
            detected = []
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    confidence = float(box.conf[0])
                    cls = int(box.cls[0])
                    card_name = self.model.names[cls]
                    
                    # Extract coordinates for both corners
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Check both top-left and bottom-right corners
                    top_left = frame[y1:y1+30, x1:x1+30]
                    bottom_right = frame[y2-30:y2, x2-30:x2]
                    
                    # Additional validation based on card corners
                    if self.validate_card_corners(top_left) or self.validate_card_corners(bottom_right):
                        confidence += 0.1  # Boost confidence if corners look valid
                    
                    if confidence > 0.45:  # Adjusted threshold
                        detected.append(card_name)
                        # Draw detection info
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{card_name} ({confidence:.2f})"
                        cv2.putText(frame, label, (x1, y1-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        if card_name not in self.detected_cards['seen_cards']:
                            self.add_new_card(card_name)
            
            return frame, detected
        except Exception as e:
            print(f"Error in detect_cards: {e}")
            return frame, []

    def validate_card_corners(self, corner_img):
        """Validate card corners using basic image processing"""
        try:
            if corner_img.size == 0:
                return False
            
            # Convert to grayscale
            gray = cv2.cvtColor(corner_img, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # Check for strong edges
            edges = cv2.Canny(thresh, 100, 200)
            return np.count_nonzero(edges) > 10
        except Exception:
            return False

    def add_new_card(self, card_name):
        """Add a newly detected card to the appropriate list"""
        with self.lock:
            if card_name not in self.detected_cards['seen_cards']:
                print(f"Adding new card: {card_name}")
                self.detected_cards['seen_cards'].add(card_name)
                
                if self.detected_cards['waiting_for_community']:
                    current_community = len(self.detected_cards['community_cards'])
                    
                    if self.current_street == 0 and current_community < 3:
                        self.detected_cards['community_cards'].append(card_name)
                        print(f"Added to flop: {card_name}")
                    elif self.current_street in [1, 2] and current_community < 5:
                        self.detected_cards['community_cards'].append(card_name)
                        print(f"Added to turn/river: {card_name}")
                    
                    if self.poker_game:
                        self.poker_game.community_cards = self.detected_cards['community_cards']
                        print(f"Current community cards: {self.detected_cards['community_cards']}")

    def update_poker_state(self, detected_cards):
        """Update poker game state based on detected cards"""
        with self.lock:
            current_time = time.time()
            self.detected_cards['detection_buffer'].append(detected_cards)
            
            if len(set(tuple(d) for d in self.detected_cards['detection_buffer'])) == 1 and detected_cards:
                if self.detected_cards['waiting_for_community']:
                    new_cards = []
                    for card in detected_cards:
                        if (card not in self.detected_cards['player_cards'] and 
                            card not in self.detected_cards['community_cards']):
                            new_cards.append(card)
                    
                    if new_cards:
                        if self.current_street == 0 and len(self.detected_cards['community_cards']) == 0:
                            new_cards = new_cards[:3]
                        elif self.current_street in [1, 2]:
                            new_cards = new_cards[:1]
                        
                        self.detected_cards['community_cards'].extend(new_cards)
                        if self.poker_game:
                            self.poker_game.community_cards = self.detected_cards['community_cards']
                        
                        self.detected_cards['waiting_for_community'] = False
                        self.detected_cards['street_complete'] = False
                        
                self.detected_cards['last_detection_time'] = current_time

    def end_action_round(self):
        """End the current action round and prepare for next street"""
        with self.lock:
            if self.current_street < 3:  
                self.current_street += 1
                self.detected_cards['waiting_for_community'] = True
                self.detected_cards['street_complete'] = True
                return {
                    'status': 'success',
                    'message': 'Ready for next street',
                    'current_street': self.current_street,
                    'expected_cards': 3 if self.current_street == 1 else 1
                }
            else:
                return {
                    'status': 'complete',
                    'message': 'Hand is complete'
                }

    def reset_hand(self):
        """Reset the game state for a new hand"""
        with self.lock:
            self.detected_cards['player_cards'] = []
            self.detected_cards['community_cards'] = []
            self.detected_cards['waiting_for_community'] = True
            self.detected_cards['street_complete'] = False
            self.detected_cards['seen_cards'] = set()
            self.current_street = 0
            if self.poker_game:
                self.poker_game.community_cards = []
                for player in self.poker_game.players:
                    player.reset()
            return {'status': 'success', 'message': 'Hand reset'}

    def analyze_action(self, opponent_idx, action, amount):
        """Analyze opponent action and update statistics"""
        try:
            print(f"Recording action for opponent {opponent_idx}: {action} {amount}")
            with self.lock:
                if opponent_idx >= len(self.opponents):
                    return {'error': 'Invalid opponent index'}
                
                opponent = self.opponents[opponent_idx]
                
                # Validate action and amount
                if action in ['call', 'raise']:
                    if amount <= 0:
                        return {'error': 'Amount must be positive for call or raise'}
                    if amount > opponent['stack']:
                        return {'error': 'Insufficient funds'}
                    
                    if action == 'call':
                        if amount != self.current_bet:
                            return {'error': f'Call amount must match current bet: ${self.current_bet}'}
                    else:  # raise
                        if amount <= self.current_bet:
                            return {'error': f'Raise amount must be greater than current bet: ${self.current_bet}'}
                
                # Update opponent stats and stack
                if action == 'raise':
                    opponent['stats']['aggression'] = (opponent['stats']['aggression'] * 9 + 1) / 10
                    if self.current_street == 0:
                        opponent['stats']['pfr'] = (opponent['stats']['pfr'] * 9 + 1) / 10
                    self.current_bet = amount
                elif action == 'call':
                    opponent['stats']['vpip'] = (opponent['stats']['vpip'] * 9 + 1) / 10
                
                if action in ['call', 'raise']:
                    opponent['stack'] -= amount
                    self.pot_size += amount
                
                # Record action
                self.opponent_actions.append({
                    'opponent': opponent_idx,
                    'action': action,
                    'amount': amount,
                    'time': time.time()
                })
                
                print(f"Action recorded. New stack: {opponent['stack']}, Pot: {self.pot_size}, Current bet: {self.current_bet}")
                
                return self.get_recommendation(opponent, action, amount)
        except Exception as e:
            print(f"Error in analyze_action: {e}")
            return {'error': str(e)}

    def get_recommendation(self, opponent, action, amount):
        """Get detailed recommendation based on opponent style and action"""
        if not self.detected_cards['player_cards']:
            return {'recommendation': 'Wait for hole cards to be detected'}
            
        hand_strength = self.hand_evaluator.evaluate_hand_strength(
            self.detected_cards['player_cards'],
            self.detected_cards['community_cards']
        )
        
        if opponent['stats']['vpip'] > 0.7:
            opponent['style'] = 'Loose'
        elif opponent['stats']['vpip'] < 0.3:
            opponent['style'] = 'Tight'
        
        if opponent['stats']['aggression'] > 0.6:
            opponent['style'] += '-Aggressive'
        else:
            opponent['style'] += '-Passive'
        
        pot_odds = None
        if action in ['raise', 'call'] and amount > 0:
            pot_odds = self.pot_size / (self.pot_size + amount)
        
        recommendation = {
            'hand_strength': hand_strength,
            'pot_odds': pot_odds,
            'opponent_style': opponent['style'],
            'opponent_stack': opponent['stack'],
            'pot_size': self.pot_size
        }
        
        if action == 'raise':
            if hand_strength > 0.8:
                recommendation['action'] = 'Consider re-raising'
                recommendation['reasoning'] = 'Strong hand against a raise'
            elif hand_strength > 0.6 and pot_odds and pot_odds > 0.3:
                recommendation['action'] = 'Consider calling'
                recommendation['reasoning'] = 'Decent hand with good pot odds'
            else:
                recommendation['action'] = 'Consider folding'
                recommendation['reasoning'] = 'Weak hand against a raise'
        elif action == 'check':
            if hand_strength > 0.7:
                recommendation['action'] = 'Consider betting'
                recommendation['reasoning'] = 'Strong hand, bet for value'
            else:
                recommendation['action'] = 'Consider checking back'
                recommendation['reasoning'] = 'Weak hand, avoid betting'
        
        return recommendation

    def get_game_analysis(self):
        """Get current game state analysis"""
        with self.lock:
            return {
                'player_cards': self.detected_cards['player_cards'],
                'community_cards': self.detected_cards['community_cards'],
                'current_street': self.current_street,
                'pot_size': self.pot_size,
                'opponents': self.opponents,
                'waiting_for_cards': self.detected_cards['waiting_for_community']
            }

    def set_player_cards(self, cards):
        """Manually set the player's hole cards"""
        with self.lock:
            self.detected_cards['player_cards'] = cards
            self.detected_cards['seen_cards'].update(cards)
            if self.poker_game:
                self.poker_game.players[0].cards = cards
            return {'status': 'success', 'message': 'Player cards set'}

    def edit_community_cards(self, action, card_index=None, new_card=None):
        """Edit community cards"""
        with self.lock:
            if action == 'remove' and card_index is not None:
                if 0 <= card_index < len(self.detected_cards['community_cards']):
                    removed_card = self.detected_cards['community_cards'].pop(card_index)
                    self.detected_cards['seen_cards'].remove(removed_card)
                    if self.poker_game:
                        self.poker_game.community_cards = self.detected_cards['community_cards']
                    return {'status': 'success', 'message': f'Removed card {removed_card}'}
            
            elif action == 'add' and new_card:
                if new_card not in self.detected_cards['seen_cards']:
                    self.detected_cards['community_cards'].append(new_card)
                    self.detected_cards['seen_cards'].add(new_card)
                    if self.poker_game:
                        self.poker_game.community_cards = self.detected_cards['community_cards']
                    return {'status': 'success', 'message': f'Added card {new_card}'}
            
            return {'status': 'error', 'message': 'Invalid edit action'}

    def generate_frames(self):
        """Generate frames with card detection"""
        while True:
            success, frame = self.camera.read()
            if not success:
                break
                
            frame, detected_cards = self.detect_cards(frame)
            
            if detected_cards:
                self.update_poker_state(detected_cards)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def __del__(self):
        self.camera.release()

poker_vision = PokerVisionSystem()

@app.route('/')
def index():
    return render_template('poker_vision.html')

@app.route('/video_feed')
def video_feed():
    return Response(poker_vision.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_analysis')
def get_analysis():
    analysis = poker_vision.get_game_analysis()
    return jsonify(analysis if analysis else {})

@app.route('/initialize_game', methods=['POST'])
def initialize_game():
    data = request.json
    num_opponents = data.get('numOpponents', 2)
    stacks = data.get('stacks', [1000] * (num_opponents + 1))
    result = poker_vision.initialize_game(num_opponents, stacks)
    return jsonify(result)

@app.route('/record_action', methods=['POST'])
def record_action():
    data = request.json
    opponent_idx = data.get('opponent', 0)
    action = data.get('action', '')
    amount = data.get('amount', 0)
    
    if not poker_vision.poker_game:
        return jsonify({'error': 'Game not initialized'})
    
    analysis = poker_vision.analyze_action(opponent_idx, action, amount)
    return jsonify(analysis)

@app.route('/end_action', methods=['POST'])
def end_action():
    result = poker_vision.end_action_round()
    return jsonify(result)

@app.route('/reset_hand', methods=['POST'])
def reset_hand():
    result = poker_vision.reset_hand()
    return jsonify(result)

@app.route('/set_player_cards', methods=['POST'])
def set_player_cards():
    data = request.json
    cards = data.get('cards', [])
    result = poker_vision.set_player_cards(cards)
    return jsonify(result)

@app.route('/edit_community_cards', methods=['POST'])
def edit_community_cards():
    """Edit community cards (add/remove)"""
    data = request.json
    action = data.get('action')
    card_index = data.get('card_index')
    new_card = data.get('new_card')
    result = poker_vision.edit_community_cards(action, card_index, new_card)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
