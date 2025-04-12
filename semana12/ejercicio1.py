class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance
        
    def withdraw(self, amount):
        if amount > self.balance:
            print("Insufficient funds")
            return self.balance
        self.balance -= amount
        return self.balance
        
class SavingsAccount(BankAccount):
    def __init__(self, balance=0, min_balance=0):
        super().__init__(balance)
        self.min_balance = min_balance
        
    def withdraw(self, amount):
        if self.balance - amount < self.min_balance:
            print("Error: Cannot withdraw. Balance would fall below minimum balance.")
            return self.balance
        return super().withdraw(amount)
    
myBankAccount = BankAccount(100)
mySavingsAccount = SavingsAccount(100, 10)

print(myBankAccount.withdraw(50))
print(mySavingsAccount.withdraw(50))
        