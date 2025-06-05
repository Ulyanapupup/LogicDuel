# game_logic/mode_2_1.py

class Game2_1:
    def __init__(self):
        self.pending_check = None  # {'type': '>', 'value': 50}
        self.last_guess = None     # {'guess': 42}
        self.secret = None

    def set_secret(self, number):
        self.secret = number

    def handle_question(self, message):
        import re
        msg = message.lower()
        self.pending_check = None
        self.last_guess = None

        # Улучшенное распознавание вопросов
        if m := re.search(r"(число\s*)?больше\s*(-?\d+)", msg):
            self.pending_check = {'type': '>', 'value': int(m.group(2))}
        elif m := re.search(r"(число\s*)?меньше\s*(-?\d+)", msg):
            self.pending_check = {'type': '<', 'value': int(m.group(2))}
        elif m := re.search(r"(это\s*число\s*|число\s*это\s*|равно\s*)?(-?\d+)", msg):
            self.last_guess = int(m.group(2))


    def apply_answer(self, answer):
        answer = answer.lower()
        if self.pending_check:
            t = self.pending_check['type']
            v = self.pending_check['value']
            if t == '>' and answer == 'да':
                return {'dim': list(range(-1000, v + 1))}
            elif t == '>' and answer == 'нет':
                return {'dim': list(range(v + 1, 1001))}
            elif t == '<' and answer == 'да':
                return {'dim': list(range(v, 1001))}
            elif t == '<' and answer == 'нет':
                return {'dim': list(range(-1000, v))}
        elif self.last_guess is not None:
            correct = self.last_guess == self.secret
            return {'guess': self.last_guess, 'correct': correct}
        return {}
