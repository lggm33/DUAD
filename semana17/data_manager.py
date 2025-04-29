import csv
import os
import FreeSimpleGUI as sg

def import_transactions_csv_file():
    """Import transactions from a CSV file"""
    
    if not os.path.exists("transactions.csv"):
        print("File not found")
        return []
    
    try:
        imported_transactions = []
        with open("transactions.csv", "r") as file:
            reader = csv.DictReader(file)
            # Verificar que el archivo tenga las columnas correctas
            expected_fields = ["date", "description", "amount", "category", "type"]
            if not all(field in reader.fieldnames for field in expected_fields):
                missing_fields = [field for field in expected_fields if field not in reader.fieldnames]
                error_msg = f"The transactions.csv file has an incorrect format. Missing fields: {', '.join(missing_fields)}"
                print(error_msg)
                if sg.popup_yes_no("File format error", 
                                   error_msg + "\nDo you want to delete the corrupted file and create a new one?",
                                   title="Format Error"):
                    os.remove("transactions.csv")
                return []
            
            for row in reader:
                imported_transactions.append(row)
        return imported_transactions
    except Exception as e:
        error_msg = f"Error importing transactions: {e}"
        print(error_msg)
        if sg.popup_yes_no("Error reading file", 
                           error_msg + "\nDo you want to delete the corrupted file and create a new one?",
                           title="File Error"):
            try:
                os.remove("transactions.csv")
            except Exception as e:
                print(f"Could not delete the file: {e}")
        return []

def export_transactions_csv_file(transactions):
    """Export transactions to a CSV file"""
    if not transactions:
        print("No transactions to export")
        return
    
    filename = "transactions.csv"
    
    try:
        with open("transactions.csv", "w", newline="") as file:
           fieldnames = ["date", "description", "amount", "category", "type"]
           writer = csv.DictWriter(file, fieldnames=fieldnames)
           writer.writeheader()
           print(transactions)
           for transaction in transactions:
               print(transaction)
               writer.writerow(transaction)
    except Exception as e:
        print(f"Error exporting transactions: {e}")

def import_categories_file():
    """Import categories from a text file"""
    
    categories = []
    if not os.path.exists("categories.txt"):
        # Create empty file if it doesn't exist
        export_categories_file([])
        return categories
    
    try:
        with open("categories.txt", "r") as file:
            for line in file:
                category = line.strip()
                if category:  # Only add non-empty lines
                    categories.append(category)
        return categories
    except Exception as e:
        error_msg = f"Error importing categories: {e}"
        print(error_msg)
        if sg.popup_yes_no("Error reading categories file", 
                           error_msg + "\nDo you want to delete the corrupted file and create a new one?",
                           title="File Error"):
            try:
                os.remove("categories.txt")
                export_categories_file([])
            except Exception as e:
                print(f"Could not delete the file: {e}")
        return []

def export_categories_file(categories):
    """Export categories to a text file"""
    
    try:
        with open("categories.txt", "w") as file:
            for category in categories:
                file.write(f"{category}\n")
    except Exception as e:
        print(f"Error exporting categories: {e}")

def init_process():
    """Initialize the process"""

    transactions = import_transactions_csv_file()
    categories = import_categories_file()

    if len(transactions) == 0:
        print("First time running the program")
        export_transactions_csv_file(transactions)
        return transactions, categories
    
    else:
        print("Transactions already exist")
        return transactions, categories

def ask_add_transactions_examples():
    """Add transactions examples to the transactions list and default categories"""

    transactions = [
        {"date": "2024-01-01", "description": "Salary", "amount": 5000, "category": "Income", "type": "income"},
        {"date": "2024-01-02", "description": "Rent", "amount": 1500, "category": "Expense", "type": "expense"},
        {"date": "2024-01-03", "description": "Groceries", "amount": 200, "category": "Expense", "type": "expense"},
        {"date": "2024-01-04", "description": "Gasoline", "amount": 100, "category": "Expense", "type": "expense"},
        {"date": "2024-01-05", "description": "Entertainment", "amount": 50, "category": "Expense", "type": "expense"},
    ]

    # Add default categories
    default_categories = ["Income", "Expense", "Food", "Transportation", "Entertainment", "Utilities", "Rent", "Savings", "Other"]
    export_categories_file(default_categories)

    # Export example transactions
    export_transactions_csv_file(transactions)
    return transactions, default_categories 