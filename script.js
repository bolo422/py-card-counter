const SUITS = [
    { name: 'Spades', symbol: '♠', color: 'black', id: 'S' },
    { name: 'Hearts', symbol: '♥', color: 'red', id: 'H' },
    { name: 'Clubs', symbol: '♣', color: 'black', id: 'C' },
    { name: 'Diamonds', symbol: '♦', color: 'red', id: 'D' }
];

const VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

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
            const card = document.createElement('div');
            card.className = `card ${suit.color} ${markedCards.has(cardId) ? 'marked' : ''}`;
            card.textContent = `${value}${suit.symbol}`;
            card.dataset.id = cardId;

            card.addEventListener('click', () => toggleCard(cardId, card));

            row.appendChild(card);
        });

        container.appendChild(row);
    });
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

// Start the app
init();
