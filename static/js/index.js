const lengthInput = document.getElementById('lengthInput');
const startBtn = document.getElementById('start');
const gameArea = document.getElementById('gameArea');
const guessInput = document.getElementById('guessInput');
const submitBtn = document.getElementById('submitGuess');
const historyList = document.getElementById('historyList');
const guessDisplay = document.getElementById('guessDisplay');

let secretNumber = '';
let numberLength = 4;

startBtn.addEventListener('click', () => {
  numberLength = parseInt(lengthInput.value, 10);

  if (isNaN(numberLength) || numberLength < 4 || numberLength > 7) {
    alert('Пожалуйста, выберите длину от 4 до 7.');
    return;
  }
  
  lengthInput.disabled = true;

  secretNumber = generateSecretNumber(numberLength);
  console.log('Загаданное число:', secretNumber); // для отладки, можно убрать

  document.getElementById('guessDisplayTable').innerHTML = '';
  guessInput.value = '';
  guessInput.maxLength = numberLength;
  guessInput.placeholder = `Введите ${numberLength}-значное число`;
  gameArea.classList.remove('hidden');
  document.getElementById('guessSection').classList.remove('hidden');
});

submitBtn.addEventListener('click', () => {
  const guess = guessInput.value.trim();

  if (guess.length !== numberLength) {
    alert(`Введите число ровно из ${numberLength} цифр.`);
    return;
  }

  if (!/^\d+$/.test(guess)) {
    alert('Введите только цифры.');
    return;
  }

  // Отобразить введённое число в ячейках с подсветкой совпадений
  displayGuess(guess);

  // Добавить в историю
  addGuessToHistory(guess);

  guessInput.value = '';
  guessInput.focus();
});

function generateSecretNumber(length) {
  let result = '';
  for (let i = 0; i < length; i++) {
    // Можно разрешить ведущие нули, если хотите
    result += Math.floor(Math.random() * 10);
  }
  return result;
}

function displayGuess(guess) {
  const table = document.getElementById('guessDisplayTable');
  const row = document.createElement('div');
  row.className = 'guess-history-row';

  const secretArr = secretNumber.split('');
  const guessArr = guess.split('');
  const usedInSecret = new Array(secretArr.length).fill(false);
  const correctPositions = new Array(secretArr.length).fill(false);

  // Сначала отметим правильные позиции (зелёные)
  for (let i = 0; i < guessArr.length; i++) {
    if (guessArr[i] === secretArr[i]) {
      correctPositions[i] = true;
      usedInSecret[i] = true;
    }
  }

  for (let i = 0; i < guessArr.length; i++) {
    const cell = document.createElement('div');
    cell.className = 'guess-history-cell';

    if (correctPositions[i]) {
      cell.classList.add('correct');
    } else {
      // Проверяем, есть ли цифра в secretNumber на другой позиции
      for (let j = 0; j < secretArr.length; j++) {
        if (!usedInSecret[j] && guessArr[i] === secretArr[j]) {
          cell.classList.add('yellow');
          usedInSecret[j] = true;
          break;
        }
      }
    }

    cell.textContent = guessArr[i];
    row.appendChild(cell);
  }

  table.appendChild(row);
}

function addGuessToHistory(guess) {
  const li = document.createElement('li');
  // Формируем HTML с подсветкой совпадающих цифр
  let html = '';
  for (let i = 0; i < guess.length; i++) {
    if (guess[i] === secretNumber[i]) {
      html += `<span class="correct-history">${guess[i]}</span>`;
    } else {
      html += guess[i];
    }
  }
  if (guess === secretNumber) {
    alert('Поздравляем! Вы угадали число! 🎉');
    // Здесь можно добавить сброс игры или другие действия, если нужно
  }
  li.innerHTML = html;
  historyList.appendChild(li);
}
function addGuessToHistory(guess) {
  const li = document.createElement('li');
  const secretArr = secretNumber.split('');
  const guessArr = guess.split('');
  const correctPositions = new Array(secretArr.length).fill(false);
  const usedInSecret = new Array(secretArr.length).fill(false);

  // Сначала отметим правильные позиции (зелёные)
  for (let i = 0; i < guessArr.length; i++) {
    if (guessArr[i] === secretArr[i]) {
      correctPositions[i] = true;
      usedInSecret[i] = true;
    }
  }

  let html = '';
  for (let i = 0; i < guessArr.length; i++) {
    let className = '';

    if (correctPositions[i]) {
      // Правильная цифра на правильной позиции — зелёная подсветка
      className = 'correct';
    } else {
      // Проверяем, есть ли цифра в secretNumber на другой позиции и не использована ли она уже
      for (let j = 0; j < secretArr.length; j++) {
        if (!usedInSecret[j] && guessArr[i] === secretArr[j]) {
          className = 'yellow'; // Добавляем желтую подсветку
          usedInSecret[j] = true; // Помечаем цифру как использованную
          break;
        }
      }
    }

    if (className) {
      html += `<span class="number-cell ${className}">${guessArr[i]}</span>`;
    } else {
      html += `<span class="number-cell">${guessArr[i]}</span>`;
    }
  }

  if (guess === secretNumber) {
    alert('Поздравляем! Вы угадали число! 🎉');
    // Здесь можно добавить сброс игры или другие действия, если нужно
  }

  li.innerHTML = html;
  historyList.appendChild(li);
}