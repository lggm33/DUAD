# Ejericio 1

hotel = {
  "name": "Hotel",
  "number_of_start": 5,
  "habitaciones": [
    {
      "number": 101,
      "floor": 1,
      "price_per_night": 100,
    }
  ]
}

# ejercicio 2

list_a = ['first_name', 'last_name', 'role']
list_b = ['Alek', 'Castillo', 'Software Engineer']
dictionary = {}

for i in range(len(list_a)):
    dictionary[list_a[i]] = list_b[i]

print(dictionary)

# Ejercicio 3

list_of_keys = ['access_level', 'age']
employee = {'name': 'John', 'email': 'john@ecorp.com', 'access_level': 5, 'age': 28}

for key in list_of_keys:
    employee.pop(key)

print(employee)

# Ejercicio Extra 1
sales = [
	{
		'date': '27/02/23',
		'customer_email': 'joe@gmail.com',
		'items': [
			{
				'name': 'Lava Lamp',
				'upc': 'ITEM-453',
				'unit_price': 65.76,
			},
			{
				'name': 'Iron',
				'upc': 'ITEM-324',
				'unit_price': 32.45,
			},
			{
				'name': 'Basketball',
				'upc': 'ITEM-432',
				'unit_price': 12.54,
			},
		],
	},
	{
		'date': '27/02/23',
		'customer_email': 'david@gmail.com',
		'items': [
			{
				'name': 'Lava Lamp',
				'upc': 'ITEM-453',
				'unit_price': 65.76,
			},
			{
				'name': 'Key Holder',
				'upc': 'ITEM-23',
				'unit_price': 5.42,
			},
		],
	},
	{
		'date': '26/02/23',
		'customer_email': 'amanda@gmail.com',
		'items': [
			{
				'name': 'Key Holder',
				'upc': 'ITEM-23',
				'unit_price': 3.42,
			},
			{
				'name': 'Basketball',
				'upc': 'ITEM-432',
				'unit_price': 17.54,
			},
		],
	},
]

# result = {
# 	'ITEM-453': 131.52,
# 	'ITEM-324': 32.45,
# 	'ITEM-432': 30.08,
# 	'ITEM-23': 8.84,
# }

result = {}

for sale in sales:
    for item in sale['items']:
        if item['upc'] in result:
            result[item['upc']] += item['unit_price']
        else:
            result[item['upc']] = item['unit_price']

print(result)