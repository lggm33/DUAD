class BankAccount:
    """
    Represents a bank account with balance and bank name information.
    """
    def __init__(self, balance=0, bank_name="Bank of America"):
        # Initialize account with default balance of 0 and default bank name
        self.balance = balance
        self.bank_name = bank_name
        
    def show_deatils_before_deposit(func):
        """
        Decorator that shows parameters before executing the deposit function
        and displays the return value after execution.
        """
        def wrapper(self, amount, from_bank_name):
            # Display parameters before executing the function
            print(f"Parameters: amount={amount}, from_bank_name={from_bank_name}")
            # Call the original function
            result = func(self, amount, from_bank_name)
            # Display the return value
            print(f"Return value: {result}")
            return result
        return wrapper


    @show_deatils_before_deposit
    def deposit(self, amount, from_bank_name):
        """
        Deposits the specified amount if from_bank_name matches this account's bank.
        Returns the current balance after the operation.
        """
        # Check if the deposit is from the same bank
        if from_bank_name != self.bank_name:
            print("Error: Cannot deposit from a different bank")
            return self.balance
        # Add amount to balance if banks match
        self.balance += amount
        return self.balance

# Example usage
myBankAccount = BankAccount()
# Successful deposit from the matching bank
print(myBankAccount.deposit(100, "Bank of America"))
# Failed deposit from a different bank
print(myBankAccount.deposit(100, "Bank of Mexico"))