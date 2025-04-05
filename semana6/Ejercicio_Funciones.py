# Ejercicio 1

def first_function():
    print("First function")
    print("Calling second function")
    second_function()

def second_function():
    print("Second function")

first_function()

# Ejercicio 2

global_variable = 10

def test_scopte():
    local_variable = 5
    print(local_variable)
    print(global_variable)

test_scopte()
# print(local_variable) # NameError: name 'local_variable' is not defined

# Ejercicio 3

list_numbers = [1, 2, 3, 4, 5]

def sum_all_numbers(list_numbers):
    total = 0
    for number in list_numbers:
        total += number
    return total

sum_all_numbers(list_numbers)

# Ejercicio 4

def print_string_backwards(string):
    for i in range(len(string) - 1, -1, -1):
        print(string[i])

print_string_backwards("Hola mundo adios")

# Ejercicio 5

def count_lowercase_letters(string):
    count = 0
    for letter in string:
        if letter.islower():
            count += 1
    return count

def count_uppercase_letters(string):
    count = 0
    for letter in string:
        if letter.isupper():
            count += 1
    return count

text = "I love Nación Sushi"

lower_letters = count_lowercase_letters(text)
upper_letters = count_uppercase_letters(text)

print(f"There's {lower_letters} lowercase letters and {upper_letters} uppercase letters in the text")

# Ejercicio 6

def order_alphabetically(text):
    words = text.split("-")
    words.sort()
    return "-".join(words)

text = "python-variable-funcion-computadora-monitor"

print(order_alphabetically(text))

# Ejercicio 7

is_prime_list =[]
number_list = [1, 4, 6, 7, 13, 9, 67]

def is_prime(number):
    if number <= 1:
        return False  # Los números menores o iguales a 1 no son primos
    for i in range(2, int(number ** 0.5) + 1):  # Verificar divisores hasta la raíz cuadrada del número
        if number % i == 0:
            return False  # Si es divisible por 'i', no es primo
    return True  # Si no tiene divisores, es primo

def prime_filter(numbers):
    for number in numbers:
        if is_prime(number):
            is_prime_list.append(number)
    return is_prime_list

print(prime_filter(number_list))
