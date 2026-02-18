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
    inclusive_counts = Counter()
    
    for _ in range(iterations):
        drawn = random.sample(remaining_deck, cards_to_draw)
        parsed_drawn = [parse_card(c) for c in drawn]
        
        # Best hand for exclusive stats
        rank = evaluate_hand(parsed_drawn)
        results[rank] += 1
        
        # All hands for inclusive stats
        all_ranks = evaluate_all_hands(parsed_drawn)
        for r in all_ranks:
            inclusive_counts[r] += 1
        
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

    # Build final structure
    # We Map hand names to constants to easy looping
    HAND_NAMES = {
        ROYAL_FLUSH: "Royal Flush",
        STRAIGHT_FLUSH: "Straight Flush",
        FOUR_OF_A_KIND: "Four of a Kind",
        FULL_HOUSE: "Full House",
        FLUSH: "Flush",
        STRAIGHT: "Straight",
        THREE_OF_A_KIND: "Three of a Kind",
        TWO_PAIR: "Two Pair",
        PAIR: "Pair",
        HIGH_CARD: "High Card"
    }

    probabilities = {}
    for hand_val, hand_name in HAND_NAMES.items():
        best_prob = results_with_min(results[hand_val], iterations, hand_val)
        inclusive_prob = results_with_min(inclusive_counts[hand_val], iterations, hand_val)
        
        probabilities[hand_name] = {
            "best": best_prob,
            "inclusive": inclusive_prob
        }
    
    return probabilities

def evaluate_all_hands(cards):
    """
    Evaluates all possible hands formed by the cards.
    Returns a set of hand values (integers) that are present.
    Includes logic for wild cards (Red Joker).
    """
    # Filter active cards
    active_cards = [c for c in cards if c["value"] != 0] # 0 is J-BLK
    red_jokers = [c for c in active_cards if c["value"] == 15] # 15 is J-RED
    normal_cards = [c for c in active_cards if c["value"] != 15]
    
    # If we have Red Jokers, we iterate replacements to find ALL valid hands
    # Note: "Best Hand" logic maximizes score. "All Hands" logic checks existence.
    # To be efficient:
    # 1. If 0 jokers -> check strictly.
    # 2. If Jokers -> Try all substitutions and union the results.
    
    found_hands = set()
    
    deck_cards = [f"{s}-{r}" for s in SUITS for r in RANKS]
    normal_card_strs = {f"{c['suit']}-{c['rank']}" for c in normal_cards}
    available_replacements = []
    
    if red_jokers:
        for dc in deck_cards:
            if dc not in normal_card_strs:
                available_replacements.append(parse_card(dc))
        
        # Iterate all joker substitutions
        for substitution in itertools.combinations_with_replacement(available_replacements, len(red_jokers)):
            current_hand = normal_cards + list(substitution)
            hands_in_this_combo = _check_all_standard_hands(current_hand)
            found_hands.update(hands_in_this_combo)
    else:
        found_hands = _check_all_standard_hands(normal_cards)
        
    return found_hands

def _check_all_standard_hands(cards):
    # Checks which standard poker hands are present in the cards.
    # Returns a set of hand constants.
    
    found = set()
    n = len(cards)
    if n == 0: return found
    
    # Sort
    cards.sort(key=lambda x: x["value"], reverse=True)
    rank_counts = Counter(c["value"] for c in cards)
    suit_counts = Counter(c["suit"] for c in cards)
    
    # High Card (Always true if n > 0)
    found.add(HIGH_CARD)
    
    # Pair (2+)
    if n >= 2 and any(c >= 2 for c in rank_counts.values()):
        found.add(PAIR)
        
    # Two Pair (4+)
    if n >= 4 and list(rank_counts.values()).count(2) >= 2:
        found.add(TWO_PAIR)
        
    # Three of a Kind (3+)
    if n >= 3 and any(c >= 3 for c in rank_counts.values()):
        found.add(THREE_OF_A_KIND)
        
    # Straight (5+)
    has_straight_val = _has_straight(cards)
    if has_straight_val:
        found.add(STRAIGHT)
        
    # Flush (5+)
    has_flush_val = False
    flush_suit = None
    if n >= 5:
        for s, count in suit_counts.items():
            if count >= 5:
                found.add(FLUSH)
                has_flush_val = True
                flush_suit = s
                break
                
    # Full House (5+)
    # 3 of X and 2 of Y.
    if n >= 5:
        has_3 = any(c >= 3 for c in rank_counts.values())
        has_2 = any(c >= 2 for c in rank_counts.values())
        # To be strict count 3 and count 2 must be different ranks?
        # AAAA K -> 4 kind. Is it full house? No.
        # AAA KK -> Full House.
        # Count 3 >= 1 and Count 2 >= 1 (if strict 2 pairs)
        # Actually simplest check: 
        # Check if we have a set of 3, and a set of 2 (distinct)
        threes = [r for r, c in rank_counts.items() if c >= 3]
        twos = [r for r, c in rank_counts.items() if c >= 2]
        
        # If we have two threes (AAA BBB), we have FH.
        # If we have one three and one two (AAA BB), we have FH.
        if len(threes) >= 2:
            found.add(FULL_HOUSE)
        elif len(threes) == 1:
            # Check if there is a pair that is NOT the three
            # But the 'twos' list will include the 'threes' rank too since 3>=2
            # So if len(twos) >= 2 means we have at least 2 ranks with >=2 cards.
            # Since one of them is >=3, we have a FH.
             if len(twos) >= 2:
                 found.add(FULL_HOUSE)
                 
    # Four of a Kind (4+)
    if n >= 4 and any(c >= 4 for c in rank_counts.values()):
        found.add(FOUR_OF_A_KIND)
        
    # Straight Flush (5+)
    if has_flush_val and has_straight_val: # Opt: only check if both exist
        # Check if the flush cards form a straight
        flush_cards = [c for c in cards if c["suit"] == flush_suit]
        if _has_straight(flush_cards):
            found.add(STRAIGHT_FLUSH)
            # Royal Flush check
            values = {c["value"] for c in flush_cards}
            if {14,13,12,11,10}.issubset(values):
                found.add(ROYAL_FLUSH)
                
    # Implications logic (as requested by user "Flush + High Card")
    # "Four of a kind" implies "Three of a Kind", "Pair", "High Card"
    # My logic above checks them independently based on card counts, so it should be covered.
    # Ex: AAAA -> counts[A]=4. 
    # -> PAIR check (any >=2): True (A)
    # -> 3-KIND check (any >=3): True (A)
    # -> 4-KIND check (any >=4): True (A)
    # So AAAA gives {PAIR, 3-KIND, 4-KIND, HIGH_CARD}
    
    # Ex: Straight Flush
    # -> Flush check: True
    # -> Straight check: True
    # -> SF Check: True
    # -> High Card: True
    # So SF gives {SF, Flush, Straight, High Card}
    
    return found
