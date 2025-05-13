# Ejerecio 1
first_list = ["Hay", "en", "que", "iteracion", "indices", "muy"]
second_list = ["casos", "los", "la", "por", "es", "util"]

for i in range(len(first_list)):
    print(first_list[i], second_list[i])

# Ejercicio 2
my_string = "Pizza con piña"

for i in range(len(my_string) - 1, -1, -1):
    print(my_string[i])

# Ejercicio 3

my_list = [4, 3, 6, 1, 7]
first_element = my_list[0]
last_element = my_list[-1]
my_list[0] = last_element
my_list[-1] = first_element
print(my_list)

# Ejercicio 4

my_list2 = [1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]
even_numbers = []

for number in my_list2: 
    if number % 2 == 0:  
        even_numbers.append(number)  

print("even numbers: ",even_numbers)

# Ejercicio 5

user_numbers = []
top_number = 0
for i in range(10):
    user_input = int(input("Ingrese un número: "))
    user_numbers.append(user_input)
    if user_input > top_number:
        top_number = user_input
print("Los números ingresados son: ", user_numbers)
print("El número más grande es: ", top_number)

