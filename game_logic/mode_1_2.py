# mode_1_2.py
import math
import random

question_pool = [
    {"text": "Число чётное", "fn": "is_even"},
    {"text": "Число простое", "fn": "is_prime"},
    {"text": "Число делится на 3", "fn": "is_div_3"},
    {"text": "Число делится на 5", "fn": "is_div_5"},
    {"text": "Число делится на 7", "fn": "is_div_7"},
    {"text": "Число положительное", "fn": "is_positive", "condition": lambda n: n < 0},
    {"text": "Число является квадратом", "fn": "is_square", "condition": lambda n: n >= 0},
    {"text": "Число является кубом", "fn": "is_cube", "condition": lambda n: n >= 0},
    {"text": "Модуль числа является квадратом", "fn": "abs_is_square", "condition": lambda n: n < 0},
    {"text": "Модуль числа является кубом", "fn": "abs_is_cube", "condition": lambda n: n < 0},
    {"text": "Число однозначное", "fn": "is_single_digit", "group": "digitSize"},
    {"text": "Число двузначное", "fn": "is_two_digit", "group": "digitSize"},
    {"text": "Число трехзначное", "fn": "is_three_digit", "group": "digitSize"},
    {"text": "Сумма цифр числа — чётная", "fn": "sum_digits_even"}
]

unique_functions = {
    "is_even": lambda n: n % 2 == 0,
    "is_prime": lambda n: n >= 2 and all(n % d != 0 for d in range(2, int(n ** 0.5) + 1)),
    "is_div_3": lambda n: n % 3 == 0,
    "is_div_5": lambda n: n % 5 == 0,
    "is_div_7": lambda n: n % 7 == 0,
    "is_square": lambda n: n >= 0 and math.isqrt(n) ** 2 == n,
    "is_cube": lambda n: round(abs(n) ** (1 / 3)) ** 3 == abs(n),
    "abs_is_square": lambda n: math.isqrt(abs(n)) ** 2 == abs(n),
    "abs_is_cube": lambda n: round(abs(n) ** (1 / 3)) ** 3 == abs(n),
    "is_positive": lambda n: n > 0,
    "is_single_digit": lambda n: abs(n) < 10,
    "is_two_digit": lambda n: 10 <= abs(n) < 100,
    "is_three_digit": lambda n: 100 <= abs(n) < 1000,
    "sum_digits_even": lambda n: sum(int(d) for d in str(abs(n))) % 2 == 0
}

class Game:
    def __init__(self, secret, min_range, max_range):
        self.finished = False
        self.final_guess = None  # Последнее число, если система уверена
        self.awaiting_final_confirmation = False
        self.secret = secret
        self.min_range = min_range
        self.max_range = max_range
        self.min = min_range
        self.max = max_range
        self.possible_numbers = list(range(min_range, max_range + 1))
        self.asked_questions = set()
        self.asked_range_questions = []
        self.asked_digit_group = False
        self.range_guessing_mode = False
        self.current_question = None
        self.remaining_questions = self._init_questions(secret)

    def _init_questions(self, secret):
        q_filtered = [q for q in question_pool if 'condition' not in q or q['condition'](secret)]
        random.shuffle(q_filtered)
        return q_filtered

    def next_question(self):
        if not self.range_guessing_mode:
            while self.remaining_questions:
                q = self.remaining_questions.pop(0)
                if q.get("group") == "digitSize" and self.asked_digit_group:
                    continue
                self.current_question = q
                return q["text"]

            self.range_guessing_mode = True

        # бинарный поиск
        if len(self.possible_numbers) <= 1:
            guess = self.possible_numbers[0] if self.possible_numbers else 'не найдено'
            self.final_guess = guess
            self.awaiting_final_confirmation = True
            return f"Я знаю! Это число {guess}?"


        mid = (self.min + self.max) // 2
        while mid in self.asked_range_questions:
            if mid == self.min:
                mid = self.max
            elif mid == self.max:
                mid = self.min
            else:
                return "Вы меня запутали 🙃"

        self.asked_range_questions.append(mid)
        self.current_question = {"type": "range", "value": mid, "text": f"Число больше {mid}"}
        return self.current_question["text"]

    def process_answer(self, answer):
        yes = answer.lower().strip() == "да"
        
        # Обработка финального ответа
        if self.awaiting_final_confirmation:
            self.finished = True
            self.awaiting_final_confirmation = False
            if yes:
                return "Ура! Я угадала!"
            else:
                return "О нет, я ошиблась"
  
        if not self.current_question:
            return "Нет текущего вопроса."

        if self.current_question.get("type") == "range":
            mid = self.current_question["value"]
            if yes:
                self.min = max(self.min, mid + 1)
            else:
                self.max = min(self.max, mid)
            self.possible_numbers = [n for n in self.possible_numbers if self.min <= n <= self.max]

        else:
            fn = self.current_question.get("fn")
            if yes and self.current_question.get("group") == "digitSize":
                self.asked_digit_group = True
                self.remaining_questions = [q for q in self.remaining_questions if q.get("group") != "digitSize"]

            if fn in unique_functions:
                self.possible_numbers = [n for n in self.possible_numbers if unique_functions[fn](n) == yes]

            if self.possible_numbers:
                self.min = min(self.possible_numbers)
                self.max = max(self.possible_numbers)

        if len(self.possible_numbers) == 0:
            return "Вы меня запутали 🙃"
        elif len(self.possible_numbers) == 1:
            self.awaiting_final_confirmation = True
            return f"Я знаю! Это число {self.possible_numbers[0]}"
        else:
            return self.next_question()
