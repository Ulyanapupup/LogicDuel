let playersInRoom = 0; // Глобальная переменная

const socket = io();

const roomCode = window.roomCode;
const isCreator = window.isCreator;
const sessionId = window.sessionId;

socket.emit('join_room', { room: roomCode, session_id: sessionId });

socket.on('joined', (data) => {
  console.log(data.message);
  document.getElementById('status').innerText = data.message;
});

socket.on('update_player_count', (data) => {
  console.log(`Игроков в комнате: ${data.count}`);
  playersInRoom = data.count;
  document.getElementById('playerCount').innerText = data.count;
  updateUI(); // Добавьте этот вызов
});

socket.on('start_game', (data) => {
  if (data.room === roomCode) {
    // Переносим в нужный игровой режим для обоих игроков
    if (data.mode === '2.1') {
      window.location.href = `/game_mode_2_1?room=${roomCode}`;
    } else if (data.mode === '2.2') {
      window.location.href = `/game_mode_2_2?room=${roomCode}`;
    }
  }
});

socket.on('start_game_2_2', (data) => {
  if (data.room === roomCode) {
    window.location.href = `/game_mode_2_2?room=${roomCode}`;
  }
});

socket.on('error', (data) => {
  alert(data.message);
  window.location.href = '/';
});

function chooseMode(mode) {
  if (!isCreator) {
    alert("Только создатель комнаты может выбрать режим.");
    return;
  }

  if (playersInRoom < 2) {
    alert("Нельзя начать игру: в комнате должен быть хотя бы один соперник.");
    return;
  }

  socket.emit('choose_mode', { room: roomCode, mode: mode });
}

// Добавьте вызов updateUI при загрузке
document.addEventListener('DOMContentLoaded', function() {
  updateUI();
});

function updateModeButtons() {
  const buttons = document.querySelectorAll('.mode-button');
  const shouldEnable = isCreator && playersInRoom >= 2;

  buttons.forEach(button => {
    button.disabled = !shouldEnable;
  });
}

function updateUI() {
  const modeSelection = document.getElementById('modeSelection');
  const waitingMsg = document.getElementById('waitingForPlayers');
  
  if (isCreator) {
    if (playersInRoom >= 2) {
      if (modeSelection) modeSelection.style.display = 'block';
      if (waitingMsg) waitingMsg.style.display = 'none';
    } else {
      if (modeSelection) modeSelection.style.display = 'none';
      if (waitingMsg) waitingMsg.style.display = 'block';
    }
  }
}