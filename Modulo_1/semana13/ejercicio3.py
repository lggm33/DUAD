from datetime import datetime

class User:
    def __init__(self, date_of_birth):
        self.date_of_birth = date_of_birth
    
    @property
    def age(self):
        today = datetime.now()
        age = today.year - self.date_of_birth.year
        
        # Adjust age if birthday hasn't occurred yet this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
            
        return age
    
    @classmethod
    def check_adult(cls, func):
        """
        Decorator that checks if a user is an adult (18 years or older).
        Raises an exception if the user is underage.
        """
        def wrapper(user, *args, **kwargs):
            if user.age < 18:
                raise Exception("User is underage")
            return func(user, *args, **kwargs)
        return wrapper


if __name__ == "__main__":
    # Create an adult user (over 18 years old)
    adult_user = User(datetime(1990, 1, 1))
    
    # Create an underage user
    underage_user = User(datetime(2010, 1, 1))
    
    @User.check_adult
    def secure_function(user):
        print(f"Function executed successfully for user of {user.age} years old")
    
    # Test with adult user
    try:
        secure_function(adult_user)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with underage user
    try:
        secure_function(underage_user)
    except Exception as e:
        print(f"Error: {e}")
