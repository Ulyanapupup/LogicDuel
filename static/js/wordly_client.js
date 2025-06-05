const socket = io();

// UI Elements
const lobby = document.getElementById('lobby');
const game = document.getElementById('game');
const createRoomBtn = document.getElementById('createRoom');
const joinRoomBtn = document.getElementById('joinRoom');
const roomIdInput = document.getElementById('roomIdInput');
const submitWordBtn = document.getElementById('submitWord');
const secretWordInput = document.getElementById('secretWord');
const guessSection = document.getElementById('guessSection');
const guessInput = document.getElementById('guessInput');
const submitGuessBtn = document.getElementById('submitGuess');
const gameStatus = document.getElementById('gameStatus');
const evaluationSection = document.getElementById('evaluationSection');
const opponentGuess = document.getElementById('opponentGuess');
const submitEvaluationBtn = document.getElementById('submitEvaluation');
const guessHistory = document.getElementById('guessHistory');

const myWordDisplay = document.getElementById('myWord');
const opponentWordDisplay = document.getElementById('opponentWord');
const gameInfo = document.getElementById('gameInfo');

const leaveLobbyBtn = document.getElementById('leaveLobby');
const leaveGameBtn = document.getElementById('leaveGame');

let roomId = null;
let playerId = null;
let currentEvaluation = [];
let opponentLetters = [];

let wordLength = 5;

createRoomBtn.addEventListener('click', () => {
  wordLength = parseInt(document.getElementById('wordLength').value);
  socket.emit('create_wordly_room', { wordLength });
});

joinRoomBtn.addEventListener('click', () => {
  const id = roomIdInput.value.trim();
  if (id) {
    socket.emit('join_wordly_room', { roomId: id });
  }
});

submitWordBtn.addEventListener('click', () => {
  const word = secretWordInput.value.trim();
  if (word.length === wordLength) {
    socket.emit('submit_wordly_word', { 
      roomId, 
      word 
    });
    document.getElementById('wordSubmission').style.display = 'none';
    myWordDisplay.textContent = word;
    gameInfo.classList.remove('hidden');
    gameStatus.textContent = 'Дождитесь соперника...';
  } else {
    gameStatus.textContent = `Слово должно содержать ${wordLength} букв`;
  }
});

submitGuessBtn.addEventListener('click', () => {
  const guess = guessInput.value.trim();
  if (guess.length === wordLength) {
    socket.emit('make_wordly_guess', { 
      roomId, 
      guess 
    });
    addGuessToHistory(guess, 'pending');
    guessInput.value = '';
    guessInput.disabled = true;
    submitGuessBtn.disabled = true;
  } else {
    gameStatus.textContent = `Догадка должна содержать ${wordLength} букв`;
  }
});

// Сервер присылает результат оценки слова
socket.on('wordly_guess_evaluated', (data) => {
  addGuessToHistory(data.guess, data.evaluation);

  // Разблокируем ввод
  guessInput.disabled = false;
  submitGuessBtn.disabled = false;
});

leaveLobbyBtn.addEventListener('click', () => {
  window.location.href = '/mode_selection';
});

leaveGameBtn.addEventListener('click', () => {
  if (roomId) {
    socket.emit('leave_wordly_game', { roomId });
  }
  window.location.href = '/mode_selection';
});

submitEvaluationBtn.addEventListener('click', () => {
  socket.emit('submit_wordly_evaluation', { 
    roomId, 
    evaluation: currentEvaluation 
  });
  evaluationSection.classList.add('hidden');
  guessSection.classList.remove('hidden');
  gameStatus.textContent = 'Дождитесь соперника...';
});

// Функция фильтрации ввода: только русские буквы (А-Я, Ё, ё)
function allowOnlyRussianLetters(input) {
	input.addEventListener("input", function () {
		this.value = this.value.replace(/[^а-яё]/gi, "").toLowerCase();
	});
}

// Применить к нужным полям после загрузки страницы
document.addEventListener("DOMContentLoaded", () => {
	const guessInput = document.getElementById("guessInput");
	const secretWord = document.getElementById("secretWord");
	
	if (guessInput) allowOnlyRussianLetters(guessInput);
	if (secretWord) allowOnlyRussianLetters(secretWord);
});

function updateInputFields(length) {
  // Обновляем атрибуты полей ввода
  secretWordInput.maxLength = length;
  secretWordInput.pattern = `[А-Яа-яЁё]{${length}}`;
  secretWordInput.placeholder = `Введите слово из ${length} букв`;
  secretWordInput.title = `Слово должно содержать ${length} букв`;
  
  guessInput.maxLength = length;
  guessInput.pattern = `[А-Яа-яЁё]{${length}}`;
  guessInput.placeholder = `Введите догадку из ${length} букв`;
  guessInput.title = `Догадка должна содержать ${length} букв`;
  
  // Обновляем размеры букв в истории
  document.querySelectorAll('.guess-row .letter').forEach(letter => {
    letter.style.width = `${40 - (wordLength - 5) * 3}px`;
    letter.style.height = `${40 - (wordLength - 5) * 3}px`;
  });
}

function createLetterElement(letter, index) {
  const letterElement = document.createElement('div');
  letterElement.className = 'letter';
  letterElement.textContent = letter;
  letterElement.dataset.index = index;
  letterElement.dataset.state = 'none';
  
  letterElement.style.width = `${40 - (wordLength - 5) * 2}px`;
  letterElement.style.height = `${40 - (wordLength - 5) * 2}px`;
  
  letterElement.addEventListener('click', () => {
    const states = ['none', 'green', 'yellow'];
    const currentState = letterElement.dataset.state;
    const currentIndex = states.indexOf(currentState);
    const nextState = states[(currentIndex + 1) % states.length];
    
    letterElement.dataset.state = nextState;
    letterElement.className = 'letter ' + nextState;
    
    currentEvaluation[index] = nextState === 'none' ? null : nextState;
  });
  
  return letterElement;
}

function setupEvaluation(guess) {
  opponentGuess.innerHTML = '';
  currentEvaluation = new Array(wordLength).fill(null); // Используем wordLength вместо фиксированного 5
  opponentLetters = guess.split('');
  
  opponentLetters.forEach((letter, index) => {
    opponentGuess.appendChild(createLetterElement(letter, index));
  });
}

function addGuessToHistory(guess, result) {
  if (result === 'pending') return;

  const guessElement = document.createElement('div');
  guessElement.className = 'guess-row';

  for (let i = 0; i < wordLength; i++) {
    const letterBox = document.createElement('div');
    letterBox.className = 'letter';
    letterBox.textContent = guess[i];
    letterBox.style.width = `${40 - (wordLength - 5) * 2}px`;
    letterBox.style.height = `${40 - (wordLength - 5) * 2}px`;

    const state = result[i];
    letterBox.classList.add(state);
    guessElement.appendChild(letterBox);
  }

  guessHistory.appendChild(guessElement);
}

// Socket events
socket.on('wordly_room_created', (data) => {
  roomId = data.roomId;
  playerId = socket.id;
  wordLength = data.wordLength;
  updateInputFields(wordLength);
  lobby.classList.add('hidden');
  game.classList.remove('hidden');
  gameStatus.textContent = `Комната создана. Поделитесь этим кодом с другом: ${roomId}`;
  leaveLobbyBtn.classList.remove('hidden');
  document.getElementById('roomCode').textContent = roomId;
});

socket.on('wordly_room_joined', (data) => {
  roomId = data.roomId;
  playerId = socket.id;
  wordLength = data.wordLength; // Получаем длину слова из данных комнаты
  updateInputFields(wordLength);
  
  lobby.classList.add('hidden');
  game.classList.remove('hidden');
  gameStatus.textContent = `Вы присоединились к комнате. Введите слово из ${wordLength} букв`;
  leaveLobbyBtn.classList.remove('hidden');
  document.getElementById('roomCode').textContent = roomId;
  
  // Обновляем подсказки в полях ввода
  secretWordInput.placeholder = `Введите слово из ${wordLength} букв`;
  secretWordInput.pattern = `[А-Яа-яЁё]{${wordLength}}`;
  guessInput.placeholder = `Введите догадку из ${wordLength} букв`;
  guessInput.pattern = `[А-Яа-яЁё]{${wordLength}}`;
});

socket.on('wordly_start_game', (data) => {
  const resultsSection = document.getElementById('resultsSection');
  resultsSection.classList.add('hidden');
  guessHistory.parentElement.classList.remove('hidden');
  gameInfo.classList.remove('hidden');
  guessSection.classList.remove('hidden');
  evaluationSection.classList.add('hidden');
  
  if (data.firstPlayer === playerId) {
    gameStatus.textContent = 'Игра началась! Ваш ход';
    guessSection.classList.remove('hidden');
  } else {
    gameStatus.textContent = 'Игра началась! Ждём ход соперника...';
  }
  leaveLobbyBtn.classList.add('hidden');
  leaveGameBtn.classList.remove('hidden');
});

socket.on('wordly_force_leave', () => {
  window.location.href = '/mode_selection';
});

socket.on('wordly_opponent_guess', (data) => {
  gameStatus.textContent = 'Оцените предположение соперника';
  guessSection.classList.add('hidden');
  evaluationSection.classList.remove('hidden');
  setupEvaluation(data.guess);
});

socket.on('wordly_game_over', (data) => {
  // Скрыть все игровые секции
  document.querySelectorAll('.game-section').forEach(section => {
	  section.classList.add('hidden');
  });
  document.querySelector('.room-code-display').classList.add('hidden');
  guessSection.classList.add('hidden');
  evaluationSection.classList.add('hidden');
  gameInfo.classList.add('hidden');
  guessHistory.parentElement.classList.add('hidden');

  // Показать итоги
  const resultsSection = document.getElementById('resultsSection');
  resultsSection.classList.remove('hidden');

  const myWord = data.words[playerId];
  const opponentId = Object.keys(data.words).find(id => id !== playerId);
  const opponentWord = data.words[opponentId];

  document.getElementById('resultMyWord').textContent = myWord;
  document.getElementById('resultOpponentWord').textContent = opponentWord;

  const resultStatus = document.getElementById('resultStatus');
  if (data.winner === playerId) {
    resultStatus.textContent = 'Поздравляем! Вы выиграли!';
    resultStatus.style.color = '#d59336';
  } else {
    resultStatus.textContent = 'К сожалению, вы проиграли.';
    resultStatus.style.color = '#d59336';
  }

  gameStatus.textContent = '';
});

socket.on('wordly_player_disconnected', () => {
  gameStatus.textContent = 'Соперник отключился. Игра окончена';
  guessSection.classList.add('hidden');
  evaluationSection.classList.add('hidden');
});

socket.on('wordly_guess_made', (data) => {
  const guessElement = document.createElement('div');
  guessElement.className = 'guess-row';
  
  data.guess.split('').forEach((letter, index) => {
    const letterElement = document.createElement('div');
    letterElement.className = `letter ${data.result[index] || ''}`;
    letterElement.textContent = letter;
    guessElement.appendChild(letterElement);
  });
  
  guessHistory.appendChild(guessElement);
});

socket.on('wordly_next_turn', (data) => {
  const isMyTurn = data.playerId === socket.id;
  gameStatus.textContent = isMyTurn 
    ? 'Ваш ход: угадайте слово соперника' 
    : 'Ход соперника: ожидайте...';

  // отключить ввод для игрока, если не его ход
  guessInput.disabled = !isMyTurn;
  submitGuessBtn.disabled = !isMyTurn;
});

socket.on('wordly_update_words', (words) => {
  if (words[playerId]) {
    myWordDisplay.textContent = words[playerId];
  }
  const opponentId = Object.keys(words).find(id => id !== playerId);
  if (opponentId && words[opponentId]) {
    opponentWordDisplay.textContent = words[opponentId];
  }
});

socket.on('wordly_error', (data) => {
  gameStatus.textContent = `Ошибка: ${data.message}`;
});