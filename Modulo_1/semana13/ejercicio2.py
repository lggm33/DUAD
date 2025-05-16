class BankAccount:
    """
    Represents a bank account with balance and bank name information.
    Includes functionality to validate and sum deposits.
    """
    def __init__(self, balance=0, bank_name="Bank of America"):
        # Initialize account with default balance and bank name
        self.balance = balance
        self.bank_name = bank_name

    def validate_numbers(func):
        """
        Decorator that validates all arguments passed to the decorated function are numeric.
        Raises ValueError if any non-numeric argument is found.
        """
        def wrapper(self, *deposits):
            # Check each deposit to ensure it's a valid number
            for deposit in deposits:
                if not isinstance(deposit, (int, float)):
                    raise ValueError("All deposits must be numbers")
            # Call the original function if validation passes
            return func(self, *deposits)
        return wrapper

    
    @validate_numbers
    def sum_total_deposits(self, *deposits):
        """
        Sums all numeric deposits after validation.
        Takes variable number of arguments representing deposit amounts.
        """
        return sum(deposits)

myBankAccount = BankAccount()
print(myBankAccount.sum_total_deposits(100, 200, 300))
print(myBankAccount.sum_total_deposits(100, 200, "300"))