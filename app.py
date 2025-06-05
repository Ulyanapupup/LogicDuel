import eventlet
eventlet.monkey_patch()

import os
import uuid
import random
import string
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room, emit

# Импортируем логику игры
from game_logic import mode_1_1
from game_logic.mode_1_2 import Game  # импорт класса Game из mode_1_2

from game_logic.mode_2_1 import Game2_1

app = Flask(__name__, static_folder='static')
app.secret_key = 'some_secret_key'  # для сессий
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}  # хранилище активных игр для режима 1.2: {game_id: Game}

room_roles = {}  # {room_code: {'guesser': session_id, 'creator': session_id}}

game_sessions = {}  # {'ROOM123': Game2_1()}

# Хранилище комнат для сетевой игры 2.1
rooms = {}

session_to_sid = {}  # сопоставление session_id -> socket.id


def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

@app.before_request
def make_session_permanent():
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()

# --- Маршруты ---

@app.route('/')
def index():
    return render_template('main.html')
    
@app.route('/mode_selection')
def mode_selection():
    return render_template('index1.html')

@app.route('/index')
def index_page():
    return render_template('index.html')

@app.route('/room_setup')
def room_setup():
    return render_template('room_setup.html')

@app.route('/game/<mode>')
def game_mode(mode):
    if mode == '1.1':
        return render_template('game_mode_1_1.html')
    elif mode == '1.2':
        return render_template('game_mode_1_2.html')
    elif mode == '2.1':
        return render_template('room_setup.html', mode=mode)
    else:
        return "Неизвестный режим", 404

@app.route('/game_mode_1_2')
def game_mode_1_2():
    return render_template('game_mode_1_2.html')
    
@app.route('/game/wordly/single')
def game_wordly_single():
    return render_template('wor1.html')

# Запуск игры 1.2 — создание новой игры
@app.route('/start_game_1_2', methods=['POST'])
def start_game_1_2():
    data = request.json
    secret = int(data.get('secret'))
    min_range = int(data.get('min_range'))
    max_range = int(data.get('max_range'))

    game_id = str(uuid.uuid4())
    games[game_id] = Game(secret, min_range, max_range)
    first_question = games[game_id].next_question()
    return jsonify({'game_id': game_id, 'question': first_question})

# Обработка ответа в игре 1.2
@app.route('/answer_1_2', methods=['POST'])
def answer_1_2():
    data = request.json
    game_id = data.get('game_id')
    answer = data.get('answer')

    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Игра не найдена'}), 404

    response = game.process_answer(answer)

    done = getattr(game, 'finished', False)

    return jsonify({'response': response, 'done': done})

# Обработка вопросов для режимов 1.1 и 1.2
@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get("question", "")
    mode = request.json.get("mode", "1.1")
    if mode == "1.1":
        # Передаем все необходимые параметры в process_question
        answer = mode_1_1.process_question(question)
    elif mode == "1.2":
        answer_yes = request.json.get("answer") == "да"
        game_id = request.json.get("game_id")
        game = games.get(game_id)
        if not game:
            return jsonify({"answer": "Игра не найдена"})
        game.filter_numbers(question, answer_yes)
        answer = ", ".join(map(str, game.get_possible_numbers()))
    else:
        answer = "Неподдерживаемый режим"

    return jsonify({"answer": answer})

# Новый роут /game для сетевой игры с комнатой
@app.route('/game')
def game():
    room = request.args.get('room', '').upper()
    if not room:
        return redirect(url_for('room_setup'))

    session_id = session['session_id']

    if room not in rooms:
        # Создаём новую комнату, первый игрок - создатель
        rooms[room] = {
            'players': set(),
            'roles': {},
            'creator': session_id,
            'mode': None
        }
    # Добавляем игрока в комнату, если его там нет
    rooms[room]['players'].add(session_id)

    player_count = len(rooms[room]['players'])
    is_creator = (session_id == rooms[room]['creator'])

    return render_template('game.html', room=room, player_count=player_count, is_creator=is_creator)


# WebSocket обработчики

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    session_id = data['session_id']

    # Проверяем есть ли комната, если нет — создаём с этим игроком как создателем
    if room not in rooms:
        rooms[room] = {
            'players': set(),
            'roles': {},
            'creator': session_id,
            'mode': None
        }

    players = rooms[room]['players']

    # Проверяем, если в комнате уже 2 игрока и текущий игрок не в списке — не пускаем
    if len(players) >= 2 and session_id not in players:
        emit('error', {'message': 'Комната заполнена, вход запрещен.'})
        return

    # Если всё ок, добавляем игрока в комнату и присоединяем socket.io к комнате
    join_room(room)
    players.add(session_id)

    # Отправляем обновление количества игроков всем в комнате
    emit('update_player_count', {'count': len(players)}, room=room)

    # Можно отправить подтверждение подключившемуся
    emit('joined', {'message': f'Вы подключились к комнате {room}.'})

@app.route('/game_mode_2_1')
def game_mode_2_1():
    room = request.args.get('room')
    # if not room or room not in rooms:
    #     return redirect(url_for('room_setup'))
    return render_template('game_mode_2_1.html', room=room)

@socketio.on('choose_mode')
def on_choose_mode(data):
    room = data['room']
    mode = data['mode']

    if room in rooms:
        rooms[room]['mode'] = mode
        if mode == '2.1':
            game_sessions[room] = Game2_1()
            emit('start_game', {'room': room, 'mode': mode}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    session_id = session.get('session_id')
    if not session_id:
        return

    for room, data in list(rooms.items()):
        if session_id in data['players']:
            data['players'].remove(session_id)
            leave_room(room)  # Игрок покидает комнату Socket.IO

            # Обновляем всех игроков в комнате о количестве
            emit('update_player_count', {'count': len(data['players'])}, room=room)

            # Если в комнате никого не осталось — удаляем её из словаря
            if len(data['players']) == 0:
                del rooms[room]
            break

# Простой WebSocket обработчик сообщений (можно убрать/настроить)
@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)
    
    
    
@socketio.on('join_game_room')
def handle_join_game_room(data):
    room = data['room']
    session_id = data['session_id']
    sid = request.sid

    join_room(room)
    session_to_sid[session_id] = sid  # сохраняем socket.id

    # Инициализация комнаты если её нет
    if room not in room_roles:
        room_roles[room] = {'guesser': None, 'creator': None}

    emit('roles_updated', {
        'roles': room_roles[room],
        'your_role': next((role for role, sid in room_roles[room].items() if sid == session_id), None)
    }, to=sid)


@socketio.on('select_role')
def handle_select_role(data):
    room = data['room']
    session_id = data['session_id']
    role = data['role']
    
    if room not in room_roles:
        emit('error', {'message': 'Комната не существует'}, to=session_id)
        return
    
    # Проверяем, что роль не занята другим игроком
    if room_roles[room][role] and room_roles[room][role] != session_id:
        emit('role_taken', {'role': role}, to=session_id)
        return
    
    # Удаляем игрока из других ролей (если он меняет выбор)
    for r in ['guesser', 'creator']:
        if room_roles[room][r] == session_id:
            room_roles[room][r] = None
    
    # Назначаем новую роль
    room_roles[room][role] = session_id
    
    # Отправляем обновление всем в комнате
    emit('roles_updated', {
        'roles': room_roles[room]
    }, room=room)
    
@socketio.on('choose_role')
def handle_choose_role(data):
    room = data['room']
    session_id = data['session_id']
    role = data['role']
    
    if room in rooms:
        rooms[room]['roles'][session_id] = role
        print(f"[SERVER] Игрок {session_id} выбрал роль {role} в комнате {room}")
        emit('role_chosen', {'session_id': session_id, 'role': role}, room=room)
        return
    
    # Инициализируем структуру roles если её нет
    if 'roles' not in rooms[room]:
        rooms[room]['roles'] = {}
    
    # Проверяем, что роль не занята другим игроком
    for existing_role, existing_id in rooms[room]['roles'].items():
        if existing_role == role and existing_id != session_id:
            emit('role_taken', {'role': role}, to=session_id)
            return
    
    # Сохраняем роль игрока
    rooms[room]['roles'][role] = session_id
    
    # Отправляем обновление ролей всем в комнате
    emit('roles_update', {'roles': rooms[room]['roles']}, room=room)

@socketio.on('leave_game')
def handle_leave_game(data):
    room = data['room']
    session_id = data['session_id']
    
    # Очищаем роли в rooms[room]['roles']
    if room in rooms:
        if 'players' in rooms[room] and session_id in rooms[room]['players']:
            rooms[room]['players'].remove(session_id)
        
        if 'roles' in rooms[room]:
            # Удаляем роль игрока из rooms[room]['roles']
            for role, sid in list(rooms[room]['roles'].items()):
                if sid == session_id:
                    del rooms[room]['roles'][role]
    
    # Очищаем роли в room_roles
    if room in room_roles:
        for role in ['guesser', 'creator']:
            if room_roles[room][role] == session_id:
                room_roles[room][role] = None
    
    # Уведомляем других игроков
    emit('player_left', {'session_id': session_id}, room=room)
    
    # Если комната пуста, удаляем её
    if room in rooms and 'players' in rooms[room] and not rooms[room]['players']:
        del rooms[room]
        if room in room_roles:
            del room_roles[room]
    
    # Перенаправляем всех игроков
    emit('force_leave', {}, room=room)

@socketio.on('start_game')
def handle_start_game(data):
    room = data['room']
    session_id = session.get('session_id')
    roles = room_roles.get(room, {})

    if not roles:
        return {'status': 'error', 'message': 'Комната не существует'}

    guesser_id = roles.get('guesser')
    creator_id = roles.get('creator')

    if guesser_id and creator_id and guesser_id != creator_id:
        # Получаем socket.id каждого игрока
        guesser_sid = session_to_sid.get(guesser_id)
        creator_sid = session_to_sid.get(creator_id)

        if not guesser_sid or not creator_sid:
            return {'status': 'error', 'message': 'Один из игроков отключён'}

        # Отправляем редирект каждому игроку
        print(f"Sending redirect to guesser: {roles['guesser']}")
        emit('redirect', {'url': f'/game2/guesser?room={room}'}, to=guesser_sid)
        emit('redirect', {'url': f'/game2/creator?room={room}'}, to=creator_sid)

        return {'status': 'ok'}
    else:
        return {'status': 'error', 'message': 'Оба игрока должны выбрать разные роли!'}

@socketio.on('chat_message')
def handle_chat_message(data):
    room = data.get('room')
    session_id = data.get('session_id')
    message = data.get('message')
    
    if not room or not session_id:
        return

    # Определяем роль отправителя
    sender_role = None
    if room in room_roles:
        if room_roles[room]['guesser'] == session_id:
            sender_role = 'guesser'
        elif room_roles[room]['creator'] == session_id:
            sender_role = 'creator'

    if sender_role:
        # Отправляем сообщение всем в комнате, включая отправителя
        emit('chat_message', {
            'sender': session_id,  # отправляем session_id для идентификации
            'message': message
        }, room=room)
        
@app.route('/game2/guesser')
def game_guesser():
    room = request.args.get('room')
    return render_template('game2/guesser.html', room=room, session=session)

@app.route('/game2/creator')
def game_creator():
    room = request.args.get('room')
    return render_template('game2/creator.html', room=room, session=session)
    
@app.route('/debug/templates')
def debug_templates():
    return str(os.listdir('templates/game2'))  # Должен показать ['guesser.html', 'creator.html']
    
@socketio.on('guess_logic')
def handle_guess_logic(data):
    room = data['room']
    session_id = data['session_id']
    message = data['message']
    
    # Проверяем, что отправитель действительно угадывающий
    if room_roles.get(room, {}).get('guesser') != session_id:
        return
    
    # Получаем или создаем игру для этой комнаты
    game = game_sessions.setdefault(room, Game2_1())
    game.handle_question(message)
    
    # Уведомляем создателя, что нужно ответить
    creator_sid = session_to_sid.get(room_roles[room]['creator'])
    if creator_sid:
        emit('need_answer', {'question': message}, to=creator_sid)


@socketio.on('reply_logic')
def handle_reply_logic(data):
    room = data['room']
    session_id = data['session_id']
    answer = data['answer']
    secret = data.get('secret')
    
    # Проверяем, что отправитель действительно создатель
    if room_roles.get(room, {}).get('creator') != session_id:
        return
    
    game = game_sessions.setdefault(room, Game2_1())
    if secret is not None:
        game.set_secret(secret)
    
    result = game.apply_answer(answer)
    
    # Отправляем результат угадывающему
    guesser_sid = session_to_sid.get(room_roles[room]['guesser'])
    if not guesser_sid:
        return
    
    if 'dim' in result:
        emit('filter_numbers', {'dim': result['dim']}, to=guesser_sid)
    elif 'guess' in result:
        emit('guess_result', {
            'correct': result['correct'],
            'value': result['guess']
        }, to=guesser_sid)
        
        
        
        
        

# В app.py добавим новый обработчик сокетов для Wordly

# Добавим маршрут для игры Wordly
@app.route('/game/wordly')
def game_wordly():
    return render_template('game_mode_wordly.html')
    
@socketio.on('create_wordly_room')
def handle_create_wordly_room(data):
    word_length = data.get('wordLength', 5)
    room_id = generate_wordly_room_id()
    rooms[room_id] = {
        'players': [request.sid],
        'words': {},
        'guesses': [],
        'currentTurn': 0,
        'gameOver': False,
        'type': 'wordly',
        'wordLength': word_length  # Сохраняем длину слова для комнаты
    }
    join_room(room_id)
    emit('wordly_room_created', {'roomId': room_id, 'wordLength': word_length})

@socketio.on('join_wordly_room')
def handle_join_wordly_room(data):
    room_id = data['roomId']
    room = rooms.get(room_id)
    
    if room and len(room['players']) == 1 and room.get('type') == 'wordly':
        room['players'].append(request.sid)
        join_room(room_id)
        emit('wordly_room_joined', {
            'roomId': room_id,
            'wordLength': room.get('wordLength', 5)  # Убедимся, что передаем длину слова
        }, room=room_id)
    else:
        emit('wordly_error', {'message': 'Room is full or does not exist.'})

@socketio.on('make_wordly_guess')
def handle_make_wordly_guess(data):
    room_id = data['roomId']
    guess = data['guess']
    room = rooms.get(room_id)

    if room and not room['gameOver'] and room.get('type') == 'wordly':
        if request.sid != room['players'][room['currentTurn']]:
            emit('wordly_error', {'message': 'Не ваш ход.'})
            return

        word_length = room.get('wordLength', 5)
        if len(guess) != word_length:
            emit('wordly_error', {'message': f'Догадка должна содержать {word_length} букв'})
            return

        opponent_id = next(pid for pid in room['players'] if pid != request.sid)
        guessed_word = guess.lower()

        if guessed_word == room['words'].get(opponent_id, ''):
            room['gameOver'] = True
            emit('wordly_game_over', {
                'winner': request.sid,
                'words': room['words']
            }, room=room_id)
            return

        room['guesses'].append({
            'player': request.sid,
            'opponent': opponent_id,
            'guess': guessed_word,
            'result': None
        })

        emit('wordly_opponent_guess', {'guess': guessed_word}, to=opponent_id)
        emit('wordly_guess_sent', room=request.sid)

@socketio.on('submit_wordly_word')
def handle_submit_wordly_word(data):
    room_id = data['roomId']
    word = data['word']
    room = rooms.get(room_id)

    if room and room.get('type') == 'wordly':
        word_length = room.get('wordLength', 5)
        if len(word) != word_length:
            emit('wordly_error', {'message': f'Слово должно содержать {word_length} букв'})
            return

        room['words'][request.sid] = word.lower()
        emit('wordly_update_words', room['words'], room=room_id)

        if len(room['words']) == 2:
            first_player = room['players'][room['currentTurn']]
            emit('wordly_start_game', {'firstPlayer': first_player}, room=room_id)
            emit('wordly_next_turn', {'playerId': first_player}, room=room_id)
            
@socketio.on('submit_wordly_evaluation')
def handle_submit_wordly_evaluation(data):
    room_id = data['roomId']
    evaluation = data['evaluation']
    room = rooms.get(room_id)

    if room and not room['gameOver'] and room.get('type') == 'wordly':
        # Находим последнюю догадку без оценки от соперника
        for guess_data in reversed(room['guesses']):
            if guess_data['opponent'] == request.sid and guess_data['result'] is None:
                guess_data['result'] = evaluation

                # Только отправителю догадки
                emit('wordly_guess_evaluated', {
                    'guess': guess_data['guess'],
                    'evaluation': evaluation
                }, to=guess_data['player'])

                # Передаём ход
                room['currentTurn'] = (room['currentTurn'] + 1) % 2
                emit('wordly_next_turn', {
                    'playerId': room['players'][room['currentTurn']]
                }, room=room_id)
                break

def generate_wordly_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
# Добавим новый обработчик сокетов
@socketio.on('leave_wordly_game')
def handle_leave_wordly_game(data):
    room_id = data['roomId']
    session_id = request.sid
    
    if room_id in rooms and rooms[room_id].get('type') == 'wordly':
        # Удаляем игрока из комнаты
        if 'players' in rooms[room_id] and session_id in rooms[room_id]['players']:
            rooms[room_id]['players'].remove(session_id)
            
            # Уведомляем другого игрока о выходе
            emit('wordly_force_leave', {}, room=room_id)
            
            # Если комната пуста, удаляем её
            if not rooms[room_id]['players']:
                del rooms[room_id]
        else:
            emit('wordly_error', {'message': 'Вы не в этой комнате'})
    
    







# В app.py добавим новый обработчик сокетов для Numbly

# Добавим маршрут для игры numbly
@app.route('/game/numbly')
def game_numbly():
    return render_template('game_mode_numbly.html')
    
@socketio.on('create_numbly_room')
def handle_create_numbly_room(data):
    numb_length = data.get('numbLength', 4)
    room_id = generate_numbly_room_id()
    rooms[room_id] = {
        'players': [request.sid],
        'numbs': {},
        'guesses': [],
        'currentTurn': 0,
        'gameOver': False,
        'type': 'numbly',
        'numbLength': numb_length  # Сохраняем длину слова для комнаты
    }
    join_room(room_id)
    emit('numbly_room_created', {'roomId': room_id, 'numbLength': numb_length})

@socketio.on('join_numbly_room')
@socketio.on('join_numbly_room')
def handle_join_numbly_room(data):
    room_id = data['roomId']
    room = rooms.get(room_id)
    
    if room and len(room['players']) == 1 and room.get('type') == 'numbly':
        room['players'].append(request.sid)
        join_room(room_id)
        emit('numbly_room_joined', {
            'roomId': room_id,
            'numbLength': room.get('numbLength', 5)  # Убедимся, что передаем длину слова
        }, room=room_id)
    else:
        emit('numbly_error', {'message': 'Room is full or does not exist.'})

@socketio.on('make_numbly_guess')
def handle_make_numbly_guess(data):
    room_id = data['roomId']
    guess = data['guess']
    room = rooms.get(room_id)

    if room and not room['gameOver'] and room.get('type') == 'numbly':
        if request.sid != room['players'][room['currentTurn']]:
            emit('numbly_error', {'message': 'Не ваш ход.'})
            return

        numb_length = room.get('numbLength', 5)
        if len(guess) != numb_length:
            emit('numbly_error', {'message': f'Догадка должна содержать {numb_length} букв'})
            return

        opponent_id = next(pid for pid in room['players'] if pid != request.sid)
        guessed_word = guess.lower()

        if guessed_word == room['numbs'].get(opponent_id, ''):
            room['gameOver'] = True
            emit('numbly_game_over', {
                'winner': request.sid,
                'numbs': room['numbs']
            }, room=room_id)
            return

        room['guesses'].append({
            'player': request.sid,
            'opponent': opponent_id,
            'guess': guessed_word,
            'result': None
        })

        emit('numbly_opponent_guess', {'guess': guessed_word}, to=opponent_id)
        emit('numbly_guess_sent', room=request.sid)

@socketio.on('submit_numbly_word')
def handle_submit_numbly_word(data):
    room_id = data['roomId']
    numb = data['numb']
    room = rooms.get(room_id)

    if room and room.get('type') == 'numbly':
        numb_length = room.get('numbLength', 5)
        if len(numb) != numb_length:
            emit('numbly_error', {'message': f'Слово должно содержать {numb_length} букв'})
            return

        room['numbs'][request.sid] = numb.lower()
        emit('numbly_update_numbs', room['numbs'], room=room_id)

        if len(room['numbs']) == 2:
            first_player = room['players'][room['currentTurn']]
            emit('numbly_start_game', {'firstPlayer': first_player}, room=room_id)
            emit('numbly_next_turn', {'playerId': first_player}, room=room_id)
            
@socketio.on('submit_numbly_evaluation')
def handle_submit_numbly_evaluation(data):
    room_id = data['roomId']
    evaluation = data['evaluation']
    room = rooms.get(room_id)

    if room and not room['gameOver'] and room.get('type') == 'numbly':
        # Находим последнюю догадку без оценки от соперника
        for guess_data in reversed(room['guesses']):
            if guess_data['opponent'] == request.sid and guess_data['result'] is None:
                guess_data['result'] = evaluation

                # Только отправителю догадки
                emit('numbly_guess_evaluated', {
                    'guess': guess_data['guess'],
                    'evaluation': evaluation
                }, to=guess_data['player'])

                # Передаём ход
                room['currentTurn'] = (room['currentTurn'] + 1) % 2
                emit('numbly_next_turn', {
                    'playerId': room['players'][room['currentTurn']]
                }, room=room_id)
                break

def generate_numbly_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
# Добавим новый обработчик сокетов
@socketio.on('leave_numbly_game')
def handle_leave_numbly_game(data):
    room_id = data['roomId']
    session_id = request.sid
    
    if room_id in rooms and rooms[room_id].get('type') == 'numbly':
        # Удаляем игрока из комнаты
        if 'players' in rooms[room_id] and session_id in rooms[room_id]['players']:
            rooms[room_id]['players'].remove(session_id)
            
            # Уведомляем другого игрока о выходе
            emit('numbly_force_leave', {}, room=room_id)
            
            # Если комната пуста, удаляем её
            if not rooms[room_id]['players']:
                del rooms[room_id]
        else:
            emit('numbly_error', {'message': 'Вы не в этой комнате'})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))