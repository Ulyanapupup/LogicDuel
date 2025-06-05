let questionPool = [
  { text: "Число чётное", fn: "is_even" },
  { text: "Число простое", fn: "is_prime" },
  { text: "Число делится на 3", fn: "is_div_3" },
  { text: "Число делится на 5", fn: "is_div_5" },
  { text: "Число делится на 7", fn: "is_div_7" },
  { text: "Число положительное", fn: "is_positive", condition: n => n < 0 },
  { text: "Число является квадратом", fn: "is_square", condition: n => n >= 0 },
  { text: "Число является кубом", fn: "is_cube", condition: n => n >= 0 },
  { text: "Модуль числа является квадратом", fn: "abs_is_square", condition: n => n < 0 },
  { text: "Модуль числа является кубом", fn: "abs_is_cube", condition: n => n < 0 },
  { text: "Число однозначное", fn: "is_single_digit", group: "digitSize" },
  { text: "Число двузначное", fn: "is_two_digit", group: "digitSize" },
  { text: "Число трехзначное", fn: "is_three_digit", group: "digitSize" },
  { text: "Сумма цифр числа — чётная", fn: "sum_digits_even" }
];
