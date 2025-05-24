class Person: 
    
    def __init__(self, name, age):
        self.name = name
        self.age = age

class Bus:
    
    def __init__(self, max_passengers):
        self.max_passengers = max_passengers
        self.current_passengers = []

    def add_passenger(self, person):
        if len(self.current_passengers) < self.max_passengers:
            self.current_passengers.append(person)
            print(f"Passenger {person.name} added to the bus")
        else:
            print("The bus is full")
            

person1 = Person("John", 20)
person2 = Person("Jane", 21)
person3 = Person("Jim", 22)
person4 = Person("Jill", 23)

bus = Bus(3)
bus.add_passenger(person1)
bus.add_passenger(person2)
bus.add_passenger(person3)
bus.add_passenger(person4)