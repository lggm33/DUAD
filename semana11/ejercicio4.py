class Head:
    def __init__(self):
        self.description = "Head"
    
    def __str__(self):
        return self.description

class Hand:
    def __init__(self, side):
        self.side = side
        self.description = f"{self.side} Hand"
    
    def __str__(self):
        return self.description

class Feet:
    def __init__(self, side):
        self.side = side
        self.description = f"{self.side} Foot"
    
    def __str__(self):
        return self.description

class Arm:
    def __init__(self, hand, side):
        self.hand = hand
        self.side = side
        self.description = f"{self.side} Arm"
    
    def __str__(self):
        return f"{self.description} connected to {self.hand}"

class Leg:
    def __init__(self, feet, side):
        self.feet = feet
        self.side = side
        self.description = f"{self.side} Leg"
    
    def __str__(self):
        return f"{self.description} connected to {self.feet}"

class Torso:
    def __init__(self, head, right_arm, left_arm, right_leg, left_leg):
        self.head = head
        self.right_arm = right_arm
        self.left_arm = left_arm
        self.right_leg = right_leg
        self.left_leg = left_leg
        self.description = "Torso"
    
    def __str__(self):
        return self.description

class Human:
    def __init__(self):
        # Create all body parts
        head = Head()
        
        right_hand = Hand("Right")
        left_hand = Hand("Left")
        
        right_feet = Feet("Right")
        left_feet = Feet("Left")
        
        right_arm = Arm(right_hand, "Right")
        left_arm = Arm(left_hand, "Left")
        
        right_leg = Leg(right_feet, "Right")
        left_leg = Leg(left_feet, "Left")
        
        # Connect all parts through the torso
        self.torso = Torso(head, right_arm, left_arm, right_leg, left_leg)
    
    def __str__(self):
        description = "Human body description:\n"
        description += f"- {self.torso}\n"
        description += f"  - {self.torso.head}\n"
        description += f"  - {self.torso.right_arm}\n"
        description += f"  - {self.torso.left_arm}\n"
        description += f"  - {self.torso.right_leg}\n"
        description += f"  - {self.torso.left_leg}\n"
        return description

# Example of use
if __name__ == "__main__":
    human = Human()
    print(human)
