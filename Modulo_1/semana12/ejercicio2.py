from abc import ABC, abstractmethod
from math import pi

class Shape(ABC):
    @abstractmethod
    def calculate_area(self):
        pass
    @abstractmethod
    def calculate_perimeter(self):
        pass
        
class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius
        
    def calculate_area(self):
        return 3.14 * self.radius ** 2
    
    def calculate_perimeter(self):
        return 2 * pi * self.radius
    
class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def calculate_area(self):
        return self.width * self.height
    
    def calculate_perimeter(self):
        return 2 * (self.width + self.height)
    
    
class Square(Shape):
    def __init__(self, side):
        self.side = side
        
    def calculate_area(self):
        return self.side ** 2
        
    def calculate_perimeter(self):
        return 4 * self.side

myCircle = Circle(10)
myRectangle = Rectangle(10, 20)
mySquare = Square(10)

print(myCircle.calculate_area())
print(myCircle.calculate_perimeter())
