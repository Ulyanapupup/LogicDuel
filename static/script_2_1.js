const socket = io();
const room = window.room;
const sessionId = window.session_id;

let myRole = null;
let currentRoles = { guesser: null, creator: null };

// Подключение к комнате
socket.emit('join_game_room', { room, session_id: sessionId });

socket.on('redirect', (data) => {
    console.log('Redirecting to:', data.url);
	console.log("=== DEBUG REDIRECT ===", data.url);
    window.location.href = data.url;
});

socket.on('redirect_guesser', (data) => {
	console.log('Redirecting guesser to:', data.url);
	window.location.href = data.url;
});

socket.on('redirect_creator', (data) => {
	console.log('Redirecting creator to:', data.url);
	window.location.href = data.url;
});

// Обработчики событий
socket.on('roles_updated', (data) => {
    console.log('Получены обновленные роли:', data);
    
    // Обновляем текущие роли
    currentRoles = data.roles || { guesser: null, creator: null };
    
    // Определяем свою роль
    myRole = null;
    for (const [role, sid] of Object.entries(currentRoles)) {
        if (sid === sessionId) {
            myRole = role;
            break;
        }
    }
    
    updateUI();
});

socket.on('role_taken', (data) => {
    alert(`Роль "${getRoleName(data.role)}" уже занята другим игроком!`);
});

socket.on('game_started', () => {
    if (myRole === 'creator') {
        window.location.href = `/game_creator?room=${room}`;
    } else {
        window.location.href = `/game_guesser?room=${room}`;
    }
});

socket.on('player_left', () => {
    alert('Другой игрок покинул игру. Вы будете перенаправлены в комнату.');
    window.location.href = `/game?room=${room}`;
});

// Вспомогательные функции
function getRoleName(role) {
    return role === 'guesser' ? 'Угадывающий' : 'Загадывающий';
}

function chooseRole(role) {
    if (myRole === role) return;
    
    socket.emit('select_role', { 
        room: room, 
        session_id: sessionId, 
        role: role 
    });
}

function canStartGame() {
    return currentRoles.guesser && 
           currentRoles.creator && 
           currentRoles.guesser !== currentRoles.creator;
}

function updateUI() {
    const guesserBtn = document.getElementById('role-guesser');
    const creatorBtn = document.getElementById('role-creator');
    const startBtn = document.getElementById('start-game');
    
    // Обновляем кнопки ролей
    guesserBtn.classList.toggle('selected', myRole === 'guesser');
    creatorBtn.classList.toggle('selected', myRole === 'creator');
    
    // Блокируем занятые роли
    guesserBtn.disabled = !!currentRoles.guesser && currentRoles.guesser !== sessionId;
    creatorBtn.disabled = !!currentRoles.creator && currentRoles.creator !== sessionId;
    
    // Обновляем статус
    let statusMessage = myRole ? `Ваша роль: ${getRoleName(myRole)}` : 'Выберите роль';
    if (currentRoles.guesser && currentRoles.guesser !== sessionId) {
        statusMessage += ` | Угадывающий: другой игрок`;
    }
    if (currentRoles.creator && currentRoles.creator !== sessionId) {
        statusMessage += ` | Загадывающий: другой игрок`;
    }
    document.getElementById('status-message').textContent = statusMessage;
    
    // Активируем кнопку старта
    startBtn.disabled = !canStartGame();
}

function startGame() {
    if (canStartGame()) {
        console.log('Attempting to start game in room:', room);
        
        socket.emit('start_game', { room }, (response) => {
            if (response && response.status === 'ok') {
                console.log('Game started successfully');
            } else {
                console.error('Start error:', response?.message || 'Unknown error');
                alert(response?.message || 'Ошибка запуска игры');
            }
        });
    } else {
        alert('Необходимо чтобы один игрок был Угадывающим, а другой - Загадывающим!');
    }
}

function leaveGame() {
    if (confirm('Вы уверены, что хотите покинуть игру?')) {
        socket.emit('leave_game', { room, session_id: sessionId });
        window.location.href = `/game?room=${room}`;
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('role-guesser').addEventListener('click', () => chooseRole('guesser'));
    document.getElementById('role-creator').addEventListener('click', () => chooseRole('creator'));
    document.getElementById('start-game').addEventListener('click', startGame);
    document.getElementById('leave-game').addEventListener('click', leaveGame);
});