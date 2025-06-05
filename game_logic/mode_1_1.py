import json, re, string
import os
import math
from flask import request

# Путь к JSON
json_path = os.path.join('game_logic', 'questions_1_1.json')

with open(json_path, 'r', encoding='utf-8') as f:
    question_map = json.load(f)

def is_greater(x, secret_number): 
    return secret_number > x

def is_less(x, secret_number): 
    return secret_number < x

def is_equal(x, secret_number): 
    return secret_number == x

def is_prime(x, secret_number):
    n = abs(secret_number)
    if n < 2: return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0: return False
    return True

def is_positive(x, secret_number): 
    return secret_number > 0

def is_negative(x, secret_number): 
    return secret_number < 0

def is_divisible(x, secret_number): 
    return x != 0 and secret_number % x == 0

def is_even(x, secret_number): 
    return secret_number % 2 == 0

def is_single_digit(x, secret_number): 
    return -10 < secret_number < 10

def is_double_digit(x, secret_number): 
    return (-100 < secret_number <= -10) or (10 <= secret_number < 100)

def is_power(x, secret_number):
    n = abs(secret_number)
    if n in (0, 1):
        return True
    for base in range(2, int(n ** 0.5) + 2):
        exp = 1
        power = base
        while power < n:
            exp += 1
            power *= base
        if power == n:
            return True
    return False

def sum_of_digits_greater(x, secret_number):
    n = abs(secret_number)
    sum_digits = sum(int(d) for d in str(n))
    return sum_digits > x

def sum_of_digits_less(x, secret_number):
    n = abs(secret_number)
    sum_digits = sum(int(d) for d in str(n))
    return sum_digits < x

# Карта функций
question_functions = {
    "is_greater": is_greater,
    "is_less": is_less,
    "is_equal": is_equal,
    "is_prime": is_prime,
    "is_positive": is_positive,
    "is_negative": is_negative,
    "is_divisible": is_divisible,
    "is_even": is_even,
    "is_single_digit": is_single_digit,
    "is_double_digit": is_double_digit,
    "is_power": is_power,
    "sum_of_digits_greater": sum_of_digits_greater,
    "sum_of_digits_less": sum_of_digits_less
}

def process_question(q):
    q = q.lower().translate(str.maketrans('', '', string.punctuation))
    
    secret_number = int(request.json.get("secret_number", 17))
    min_range = -100
    max_range = 100

    # Специальный случай: сумма цифр
    if "сумма цифр" in q:
        nums = re.findall(r'-?\d+', q)
        if not nums:
            return "Пожалуйста, укажите число"
        x = int(nums[0])
        if "больше" in q:
            return "Да" if sum_of_digits_greater(x, secret_number) else "Нет"
        elif "меньше" in q:
            return "Да" if sum_of_digits_less(x, secret_number) else "Нет"
        else:
            return "Уточните, сумма цифр больше или меньше указанного числа"

    for keyword, func_name in question_map.items():
        if keyword in q:
            func = question_functions[func_name]

            # Вопрос без аргумента
            if func_name in ["is_prime", "is_positive", "is_negative", "is_even", 
                             "is_single_digit", "is_double_digit", "is_power"]:
                return "Да" if func(None, secret_number) else "Нет"

            # Вопрос с числом
            nums = re.findall(r'-?\d+', q)
            if not nums:
                return "Пожалуйста, укажите число"
            x = int(nums[0])
            if x < min_range or x > max_range:
                return f"Число должно быть в диапазоне от {min_range} до {max_range}"

            # Специальная логика сравнения для отрицательных чисел
            if func_name in ["is_greater", "is_less"] and secret_number < 0:
                # Инвертируем знак и результат
                adjusted_secret = abs(secret_number)
                result = func(x, adjusted_secret)
                return "Нет" if result else "Да"

            return "Да" if func(x, secret_number) else "Нет"

    return "Неизвестный вопрос"

