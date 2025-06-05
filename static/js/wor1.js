const setupDiv = document.getElementById('setup');
const gameDiv = document.getElementById('game');
const startBtn = document.getElementById('startBtn');
const wordLengthInput = document.getElementById('wordLength');
const guessInput = document.getElementById('guessInput');
const guessBtn = document.getElementById('guessBtn');
const guessesDiv = document.getElementById('guesses');
const messageDiv = document.getElementById('message');

let secretWord = '';
let wordLength = 5;
let attempts = 0;
let dictionary = [];

// Загрузка словаря из words.json
fetch('/static/wor.json')
    .then(response => response.json())
    .then(data => {
        dictionary = data;
    })
    .catch(error => {
        console.error('Ошибка при загрузке словаря:', error);
    });

// Фильтруем словарь по длине
function getWordsByLength(len) {
    return dictionary.filter(w => w.length >= 5 && w.length <= 7 && w.length === len);
}

function isAlpha(str) {
    return /^[а-яА-Яa-zA-Z]+$/.test(str);
}

startBtn.addEventListener('click', () => {
    wordLength = parseInt(wordLengthInput.value);
    if (isNaN(wordLength) || wordLength < 5 || wordLength > 7) {
        alert('Длина слова должна быть от 5 до 7.');
        return;
    }

    const words = getWordsByLength(wordLength);
    if (words.length === 0) {
        alert('Нет слов с такой длиной в словаре.');
        return;
    }

    // Случайный выбор слова
    secretWord = words[Math.floor(Math.random() * words.length)].toLowerCase();

    attempts = 0;
    guessesDiv.innerHTML = '';
    messageDiv.textContent = '';
    guessInput.value = '';
    guessInput.maxLength = wordLength;
    guessInput.focus();

    setupDiv.classList.add('hidden');
    gameDiv.classList.remove('hidden');
    guessBtn.disabled = false;
    guessInput.disabled = false;

    console.log('Загаданное слово (для отладки):', secretWord);
});

guessBtn.addEventListener('click', () => {
    let guess = guessInput.value.trim().toLowerCase();

    if (guess.length !== wordLength) {
        alert(`Введите слово ровно из ${wordLength} букв.`);
        return;
    }
    if (!isAlpha(guess)) {
        alert('Введите только буквы.');
        return;
    }
    // Проверка, что слово присутствует в словаре
    if (!dictionary.includes(guess)) {
        alert('Слово не найдено в словаре.');
        return;
    }

    attempts++;

    const secretLetters = secretWord.split('');
    const guessLetters = guess.split('');

    const result = new Array(wordLength).fill('absent');
    const secretUsed = new Array(wordLength).fill(false);

    // Помечаем правильные буквы на своих местах
    for (let i = 0; i < wordLength; i++) {
        if (guessLetters[i] === secretLetters[i]) {
            result[i] = 'correct';
            secretUsed[i] = true;
        }
    }

    // Помечаем буквы, которые есть в слове, но на других позициях
    for (let i = 0; i < wordLength; i++) {
        if (result[i] === 'correct') continue;
        for (let j = 0; j < wordLength; j++) {
            if (!secretUsed[j] && guessLetters[i] === secretLetters[j]) {
                result[i] = 'present';
                secretUsed[j] = true;
                break;
            }
        }
    }

    const row = document.createElement('div');
    row.className = 'guess-row';
    for (let i = 0; i < wordLength; i++) {
        const box = document.createElement('div');
        box.className = 'letter-box ' + result[i];
        box.textContent = guessLetters[i].toUpperCase();
        row.appendChild(box);
    }
    guessesDiv.appendChild(row);

    guessInput.value = '';
    guessInput.focus();

    if (guess === secretWord) {
        messageDiv.textContent = `Поздравляем! Вы угадали слово за ${attempts} попыток! 🎉`;
        guessBtn.disabled = true;
        guessInput.disabled = true;
    } else {
        messageDiv.textContent = '';
    }
});
document.getElementById("restartBtn").addEventListener("click", () => {
  location.reload();
});