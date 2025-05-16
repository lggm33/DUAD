list_a = ['first_name', 'last_name', 'role']
list_b = ['Alek', 'Castillo', 'Software Engineer']
dictionary = {}

for i in range(len(list_a)):
    dictionary[list_a[i]] = list_b[i]

print(dictionary)