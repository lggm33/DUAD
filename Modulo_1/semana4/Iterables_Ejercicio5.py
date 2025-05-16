user_numbers = []
top_number = 0
for i in range(10):
    user_input = int(input("Ingrese un número: "))
    user_numbers.append(user_input)
    if user_input > top_number:
        top_number = user_input
print("Los números ingresados son: ", user_numbers)
print("El número más grande es: ", top_number)