import random
from collections import Counter
import itertools

# Card definitions
SUITS = ['S', 'H', 'C', 'D']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}
RANK_VALUES['A'] = 14

# Hand Rankings
ROYAL_FLUSH = 10
STRAIGHT_FLUSH = 9
FOUR_OF_A_KIND = 8
FULL_HOUSE = 7
FLUSH = 6
STRAIGHT = 5
THREE_OF_A_KIND = 4
TWO_PAIR = 3
PAIR = 2
HIGH_CARD = 1

def get_deck():
    deck = [f"{s}-{r}" for s in SUITS for r in RANKS]
    deck.append("J-RED")
    deck.append("J-BLK")
    return deck

def parse_card(card_str):
    if card_str == "J-RED":
        return {"suit": "WILD", "rank": "WILD", "value": 15}
    if card_str == "J-BLK":
        return {"suit": "NONE", "rank": "NONE", "value": 0}
    
    parts = card_str.split('-')
    suit = parts[0]
    rank = parts[1]
    return {"suit": suit, "rank": rank, "value": RANK_VALUES[rank]}

def evaluate_hand(cards):
    # cards is a list of card objects (from parse_card)
    # Filter out Black Jokers (they reduce hand size effectively, but assume they are already handled or just ignored)
    # Actually, if we draw N cards, and one is Black Joker, we have N-1 functional cards.
    # The prompt implies Black Joker is "-1". So if I draw 5 and get Block Joker, I evaluate the best hand from the other 4.
    
    active_cards = [c for c in cards if c["value"] != 0] # 0 is J-BLK
    red_jokers = [c for c in active_cards if c["value"] == 15] # 15 is J-RED
    normal_cards = [c for c in active_cards if c["value"] != 15]
    
    # If we have Red Jokers, we need to try all possibilities.
    # To optimize, we can just iterate standard 52 cards for each joker.
    # But that's 52^N complexity. 
    # Optimization: A wild card is useful to complete a standard hand.
    # We can use a brute force approach if num red jokers is small (usually 1).
    # If 1 Red Joker: Try substituting it with every card in the deck (that isn't already in hand).
    # Take the max score.
    
    if not red_jokers:
        return _evaluate_best_standard_hand(normal_cards)
    
    # Handle Wilds
    best_rank = 0
    
    # Generate all possible replacements for wilds
    # We only need to check cards that improve the hand.
    # Brute force: Try replacing each Wild with every card in the standard deck that isn't in 'normal_cards'.
    
    deck_cards = [f"{s}-{r}" for s in SUITS for r in RANKS]
    # Filter out cards already holding
    available_replacements = []
    normal_card_strs = {f"{c['suit']}-{c['rank']}" for c in normal_cards}
    
    for dc in deck_cards:
        if dc not in normal_card_strs:
            available_replacements.append(parse_card(dc))
            
    # If we have 1 joker, loop available. 2 jokers, combinations of 2.
    import itertools
    
    best_score = -1
    
    # Limit combinations if too many to prevent slow down (usually max 1 joker in deck)
    # But user logic says "red joker is a wild card".
    
    for substitution in itertools.combinations_with_replacement(available_replacements, len(red_jokers)):
        current_hand = normal_cards + list(substitution)
        score = _evaluate_best_standard_hand(current_hand)
        if score > best_score:
            best_score = score
            if best_score == ROYAL_FLUSH: # Max possible
                return best_score
                
    return best_score

def _evaluate_best_standard_hand(cards):
    # Evaluates best poker hand from a list of cards (standard 52).
    # Can be less than 5 cards.
    
    if not cards:
        return 0
        
    # Valid Poker Hands require at least:
    # High Card: 1
    # Pair: 2
    # Two Pair: 4
    # 3 Kind: 3
    # Straight: 5 (Standard rules? User said "minimal cards being a factor... 2 cards flush")
    # WAIT. User said: 
    # "so 2 cards CANT form a flush, a straight, or 3 of a kind, just 2 a pair or a high card"
    # "Other hands: all poker hands are included, and follow rule 1"
    # This contradicts "if the informed cards is 2, you can form a flush" from the prompt?
    # NO. User correction: "1. correcting... so 2 cards CANT form a flush... just 2 a pair or a high card"
    # So Standard Rules apply for minimum cards!
    # Flush needs 5? Or just "standard poker rules"?
    # Standard poker Flush = 5 cards.
    # Standard Straight = 5 cards.
    # Pair = 2.
    # 3 Kind = 3.
    # 4 Kind = 4.
    # Full House = 5.
    
    # So if I have 4 cards, I can't have a Flush or Straight.
    
    n = len(cards)
    
    # Sort by value
    cards.sort(key=lambda x: x["value"], reverse=True)
    
    # Check Flush (5+)
    if n >= 5:
        suits = Counter(c["suit"] for c in cards)
        for suit, count in suits.items():
            if count >= 5:
                # Check Straight Flush
                flush_cards = [c for c in cards if c["suit"] == suit]
                if _has_straight(flush_cards):
                    # Check Royal
                    if flush_cards[0]["value"] == 14 and flush_cards[4]["value"] == 10: # Rough check
                        # Real royal check: A,K,Q,J,10
                        values = {c["value"] for c in flush_cards}
                        if {14,13,12,11,10}.issubset(values):
                            return ROYAL_FLUSH
                    return STRAIGHT_FLUSH
                return FLUSH
                
    # Check 4 Kind (4+)
    counts = Counter(c["value"] for c in cards)
    if n >= 4:
        if 4 in counts.values():
            return FOUR_OF_A_KIND
            
    # Check Full House (5+)
    if n >= 5:
        if 3 in counts.values() and 2 in counts.values():
            return FULL_HOUSE
        if list(counts.values()).count(3) >= 2: # Two 3-kinds make a full house
            return FULL_HOUSE
            
    # Check Straight (5+)
    if n >= 5:
        if _has_straight(cards):
            return STRAIGHT
            
    # Check 3 Kind (3+)
    if n >= 3:
        if 3 in counts.values():
            return THREE_OF_A_KIND
            
    # Check Two Pair (4+)
    if n >= 4:
        if list(counts.values()).count(2) >= 2:
            return TWO_PAIR
            
    # Check Pair (2+)
    if n >= 2:
        if 2 in counts.values():
            return PAIR
            
    return HIGH_CARD

def _has_straight(cards):
    # cards sorted desc
    values = sorted(list({c["value"] for c in cards}), reverse=True)
    if len(values) < 5:
        return False
        
    # Check A-5-4-3-2
    if 14 in values and {2,3,4,5}.issubset(set(values)):
        return True
        
    for i in range(len(values) - 4):
        if values[i] - values[i+4] == 4:
            return True
    return False

def calculate_probabilities(marked_cards_ids, cards_to_draw, iterations=1000):
    full_deck = get_deck()
    remaining_deck = [c for c in full_deck if c not in marked_cards_ids]
    
    if cards_to_draw > len(remaining_deck):
        return {"error": "Not enough cards"}
        
    results = Counter()
    
    for _ in range(iterations):
        drawn = random.sample(remaining_deck, cards_to_draw)
        parsed_drawn = [parse_card(c) for c in drawn]
        rank = evaluate_hand(parsed_drawn)
        results[rank] += 1
        
    # Pre-calculate deck stats for possibility checks
    active_deck_strs = [c for c in remaining_deck if c != "J-BLK"]
    active_deck = [parse_card(c) for c in active_deck_strs]
    wild_count = sum(1 for c in active_deck if c["value"] == 15)
    normal_cards = [c for c in active_deck if c["value"] != 15]
    
    max_hand_size = min(cards_to_draw, len(active_deck))
    
    rank_counts = Counter(c["value"] for c in normal_cards)
    suit_counts = Counter(c["suit"] for c in normal_cards)
    present_ranks = set(c["value"] for c in normal_cards)

    def is_possible(hand_val):
        if hand_val == ROYAL_FLUSH:
            # Check per suit for {10,J,Q,K,A}
            if max_hand_size < 5: return False
            for s in SUITS:
                suit_cards = {c["value"] for c in normal_cards if c["suit"] == s}
                needed = 0
                for r in [10, 11, 12, 13, 14]:
                    if r not in suit_cards: needed += 1
                if wild_count >= needed: return True
            return False

        if hand_val == STRAIGHT_FLUSH:
            if max_hand_size < 5: return False
            for s in SUITS:
                suit_vals = {c["value"] for c in normal_cards if c["suit"] == s}
                # Check normal range 2-6 to 10-14
                for start in range(2, 11):
                    window = set(range(start, start+5))
                    needed = len(window) - len(window.intersection(suit_vals))
                    if wild_count >= needed: return True
                # Check A-low: A,2,3,4,5 -> {14,2,3,4,5}
                window = {14, 2, 3, 4, 5}
                needed = len(window) - len(window.intersection(suit_vals))
                if wild_count >= needed: return True
            return False

        if hand_val == FOUR_OF_A_KIND:
            if max_hand_size < 4: return False
            for r in range(2, 15):
                if rank_counts[r] + wild_count >= 4: return True
            return False

        if hand_val == FULL_HOUSE:
            if max_hand_size < 5: return False
            for r1 in range(2, 15):
                for r2 in range(2, 15):
                    if r1 == r2: continue
                    needed = max(0, 3 - rank_counts[r1]) + max(0, 2 - rank_counts[r2])
                    if wild_count >= needed: return True
            return False

        if hand_val == FLUSH:
            if max_hand_size < 5: return False
            for s in SUITS:
                if suit_counts[s] + wild_count >= 5: return True
            return False

        if hand_val == STRAIGHT:
            if max_hand_size < 5: return False
            for start in range(2, 11):
                window = set(range(start, start+5))
                needed = len(window) - len(window.intersection(present_ranks))
                if wild_count >= needed: return True
            # A-low
            window = {14, 2, 3, 4, 5}
            needed = len(window) - len(window.intersection(present_ranks))
            if wild_count >= needed: return True
            return False

        if hand_val == THREE_OF_A_KIND:
            if max_hand_size < 3: return False
            for r in range(2, 15):
                if rank_counts[r] + wild_count >= 3: return True
            return False

        if hand_val == TWO_PAIR:
            if max_hand_size < 4: return False
            for r1 in range(2, 15):
                for r2 in range(2, 15):
                    if r1 >= r2: continue
                    needed = max(0, 2 - rank_counts[r1]) + max(0, 2 - rank_counts[r2])
                    if wild_count >= needed: return True
            return False

        if hand_val == PAIR:
            if max_hand_size < 2: return False
            for r in range(2, 15):
                if rank_counts[r] + wild_count >= 2: return True
            return False

        if hand_val == HIGH_CARD:
            return max_hand_size >= 1
            
        return False

    def results_with_min(count, iterations, hand_type):
        percentage = count / iterations * 100
        if percentage == 0:
            if is_possible(hand_type):
                return 0.01
        return percentage

    probabilities = {
        "Royal Flush": results_with_min(results[ROYAL_FLUSH], iterations, ROYAL_FLUSH),
        "Straight Flush": results_with_min(results[STRAIGHT_FLUSH], iterations, STRAIGHT_FLUSH),
        "Four of a Kind": results_with_min(results[FOUR_OF_A_KIND], iterations, FOUR_OF_A_KIND),
        "Full House": results_with_min(results[FULL_HOUSE], iterations, FULL_HOUSE),
        "Flush": results_with_min(results[FLUSH], iterations, FLUSH),
        "Straight": results_with_min(results[STRAIGHT], iterations, STRAIGHT),
        "Three of a Kind": results_with_min(results[THREE_OF_A_KIND], iterations, THREE_OF_A_KIND),
        "Two Pair": results_with_min(results[TWO_PAIR], iterations, TWO_PAIR),
        "Pair": results_with_min(results[PAIR], iterations, PAIR),
        "High Card": results_with_min(results[HIGH_CARD], iterations, HIGH_CARD)
    }
    
    return probabilities
