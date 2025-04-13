# Mixins como componentes reutilizables
class SerializableMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)
    
    def to_xml(self):
        # Implementación básica
        return f"<{self.__class__.__name__}>{self.__dict__}</{self.__class__.__name__}>"

class LoggableMixin:
    def log(self, message):
        print(f"[LOG] {message}")

# Clase base
class Vehicle:
    def __init__(self, model, year):
        self.model = model
        self.year = year
    
    def display_info(self):
        return f"{self.year} {self.model}"

# Herencia múltiple
class Car(Vehicle, SerializableMixin, LoggableMixin):
    def __init__(self, model, year, color):
        super().__init__(model, year)
        self.color = color
        self.log(f"Created a new {color} {model}")
    
    def start_engine(self):
        self.log("Engine started")
        return "Vroom!"
    
myCar = Car("Toyota", 2020, "Red")
print(myCar.display_info())
print(myCar.to_json())
print(myCar.to_xml())
print(myCar.start_engine())
