import datetime
from typing import List, Dict, Any, Optional
from data_manager import export_transactions_csv_file, export_categories_file

class Category:
    def __init__(self, name: str):
        self.name = name.strip()
    
    def is_valid(self) -> bool:
        """Check if the category is valid"""
        return bool(self.name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the category to a dictionary"""
        return {"name": self.name}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """Create a category from a dictionary"""
        return cls(data["name"])
    
    @classmethod
    def from_str(cls, name: str) -> 'Category':
        """Create a category from a string"""
        return cls(name)
    
    def __str__(self) -> str:
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Category):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False

class Transaction:
    def __init__(self, date: str, description: str, amount: float, 
                 category: str, type_: str):
        self.date = date
        self.description = description
        self.amount = float(amount)
        self.category = category
        self.type_ = type_
    
    def is_valid(self) -> bool:
        """Check if the transaction is valid"""
        try:
            # Validate date format
            datetime.datetime.strptime(self.date, '%Y-%m-%d')
            
            # Validate other fields
            if not self.description:
                return False
            
            if self.amount <= 0:
                return False
                
            if not self.category:
                return False
                
            if self.type_ not in ["income", "expense"]:
                return False
                
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transaction to a dictionary"""
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "type": self.type_
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create a transaction from a dictionary"""
        return cls(
            date=data["date"],
            description=data["description"],
            amount=float(data["amount"]),
            category=data["category"],
            type_=data["type"]
        )

def add_transaction(transactions: List[Transaction], new_transaction: Optional[Transaction]) -> List[Transaction]:
    """Add a new transaction to the list and save to file"""
    if not new_transaction:
        return transactions
    
    transactions.append(new_transaction)
    # Convert transaction objects to dictionaries before exporting
    transactions_dict = [t.to_dict() for t in transactions]
    export_transactions_csv_file(transactions_dict)
    return transactions

def save_categories(categories: List[Category]) -> None:
    """Save categories to file"""
    category_names = [c.name for c in categories]
    export_categories_file(category_names) 