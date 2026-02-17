const SUITS = [
    { name: 'Spades', symbol: '♠', color: 'black', id: 'S' },
    { name: 'Hearts', symbol: '♥', color: 'red', id: 'H' },
    { name: 'Clubs', symbol: '♣', color: 'black', id: 'C' },
    { name: 'Diamonds', symbol: '♦', color: 'red', id: 'D' }
];

const VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

// Special Cards
const JOKERS = [
    { name: 'Red Joker', symbol: 'JOKER', color: 'red', id: 'J-RED' },
    { name: 'Black Joker', symbol: 'JOKER', color: 'black', id: 'J-BLK' }
];

const container = document.getElementById('deck-container');
let markedCards = new Set();

async function init() {
    await loadState();
    renderDeck();
}

async function loadState() {
    try {
        const response = await fetch('cards.json', { cache: 'no-store' });
        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data)) {
                markedCards = new Set(data);
            }
        }
    } catch (error) {
        console.log('No existing state found or error loading:', error);
    }
}

function renderDeck() {
    container.innerHTML = '';

    SUITS.forEach(suit => {
        const row = document.createElement('div');
        row.className = 'suit-row';

        VALUES.forEach(value => {
            const cardId = `${suit.id}-${value}`;
            createCardElement(cardId, value + suit.symbol, suit.color, row);
        });

        container.appendChild(row);
    });

    // Joker Row
    const jokerRow = document.createElement('div');
    jokerRow.className = 'suit-row joker-row';
    JOKERS.forEach(joker => {
        createCardElement(joker.id, joker.symbol, joker.color, jokerRow);
    });
    container.appendChild(jokerRow);
}

function createCardElement(id, text, color, parent) {
    const card = document.createElement('div');
    card.className = `card ${color} ${markedCards.has(id) ? 'marked' : ''}`;
    card.textContent = text;
    card.dataset.id = id;

    card.addEventListener('click', () => toggleCard(id, card));
    parent.appendChild(card);
}

async function toggleCard(id, element) {
    if (markedCards.has(id)) {
        markedCards.delete(id);
        element.classList.remove('marked');
    } else {
        markedCards.add(id);
        element.classList.add('marked');
    }

    await saveState();
}

async function saveState() {
    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(Array.from(markedCards))
        });

        if (!response.ok) {
            console.error('Failed to save state');
        }
    } catch (error) {
        console.error('Error saving state:', error);
    }
}

// Calculator Logic
async function calculateProbabilities() {
    const input = document.getElementById('cards-to-pull');
    const resultDiv = document.getElementById('calc-results');
    const numCards = parseInt(input.value);

    if (!numCards || numCards < 1) {
        alert("Please enter a valid number of cards to pull.");
        return;
    }

    resultDiv.innerHTML = 'Calculating...';

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                marked_cards: Array.from(markedCards),
                cards_to_draw: numCards
            })
        });

        if (response.ok) {
            const probs = await response.json();
            if (probs.error) {
                resultDiv.innerHTML = `<div style="padding: 10px; color: #ff5252; background: #330000; border-radius: 4px; margin-top: 10px;">Error: ${probs.error}</div>`;
            } else {
                displayResults(probs);
            }
        } else {
            resultDiv.innerHTML = 'Error calculating.';
        }
    } catch (e) {
        console.error(e);
        resultDiv.innerHTML = 'Error: ' + e.message;
    }
}

function displayResults(probs) {
    const resultDiv = document.getElementById('calc-results');
    let html = '<table class="result-table"><tr><th>Hand</th><th>Probability</th></tr>';

    for (const [hand, prob] of Object.entries(probs)) {
        // Highlight likely hands
        const style = prob > 0 ? 'color: #fff;' : 'color: #555;';
        html += `<tr style="${style}"><td>${hand}</td><td>${prob.toFixed(2)}%</td></tr>`;
    }
    html += '</table>';
    resultDiv.innerHTML = html;
}

async function resetDeck() {
    if (!confirm('Are you sure you want to reset the deck? All marks will be cleared.')) {
        return;
    }

    markedCards.clear();
    const markedElements = document.querySelectorAll('.card.marked');
    markedElements.forEach(el => el.classList.remove('marked'));

    await saveState();
}

// Start the app
init();
