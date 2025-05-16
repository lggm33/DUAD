import FreeSimpleGUI as sg
import datetime
from typing import List, Optional
from models import Transaction, Category, save_categories

def create_category_window(categories: List[Category]) -> List[Category]:
    """Create a new window for adding categories"""
    
    # Get category names for display
    category_names = [c.name for c in categories]
    
    layout = [
        [sg.Text("Current Categories:", font=("Helvetica", 12))],
        [sg.Listbox(values=category_names, size=(30, 10), key="-CATEGORIES-LIST-")],
        [sg.Text("New Category:")],
        [sg.InputText(key="-NEW-CATEGORY-")],
        [sg.Text("", size=(40, 1), key="-STATUS-", text_color="red")],
        [sg.Button("Add"), sg.Button("Close")]
    ]
    
    window = sg.Window("Manage Categories", layout, modal=True, finalize=True)
    
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == "Close":
            break
        
        if event == "Add":
            new_category_name = values["-NEW-CATEGORY-"].strip()
            if new_category_name and new_category_name not in category_names:
                # Create new Category object
                new_category = Category(new_category_name)
                if new_category.is_valid():
                    categories.append(new_category)
                    category_names = [c.name for c in categories]
                    window["-CATEGORIES-LIST-"].update(category_names)
                    window["-NEW-CATEGORY-"].update("")
                    # Save categories to file
                    save_categories(categories)
                    window["-STATUS-"].update(f"Category '{new_category_name}' added successfully!", text_color="#008080", background_color="#f0f0f0")
                else:
                    window["-STATUS-"].update("Invalid category name!", text_color="red")
            elif not new_category_name:
                window["-STATUS-"].update("Please enter a category name!", text_color="red")
            else:
                window["-STATUS-"].update("Category already exists!", text_color="red")
    
    window.close()
    return categories

def create_transaction_window(transaction_type: str, categories: List[Category]) -> Optional[Transaction]:
    """Create a new window for adding a transaction"""
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    # Get category names for display
    category_names = [c.name for c in categories]
    
    layout = [
        [sg.Text(f"Add {transaction_type.capitalize()}", font=("Helvetica", 14))],
        [sg.Text("Title:"), sg.InputText(key="-TITLE-")],
        [sg.Text("Amount:"), sg.InputText(key="-AMOUNT-")],
        [sg.Text("Category:"), sg.Combo(category_names, key="-CATEGORY-", size=(20, 1))],
        [sg.Text("Date (YYYY-MM-DD):"), sg.InputText(today, key="-DATE-")],
        [sg.Text("", size=(40, 1), key="-STATUS-", text_color="red")],
        [sg.Button("Save"), sg.Button("Cancel")]
    ]
    
    window = sg.Window(f"Add {transaction_type.capitalize()}", layout, modal=True, finalize=True)
    
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == "Cancel":
            window.close()
            return None
        
        if event == "Save":
            # Validate inputs
            title = values["-TITLE-"].strip()
            amount_str = values["-AMOUNT-"].strip()
            category_name = values["-CATEGORY-"]
            date = values["-DATE-"].strip()
            
            # Create Transaction object for validation
            try:
                amount = float(amount_str)
                # Create transaction object
                transaction = Transaction(
                    date=date,
                    description=title,
                    amount=amount,
                    category=category_name,
                    type_=transaction_type
                )
                
                # Validate transaction
                if transaction.is_valid():
                    window.close()
                    return transaction
                else:
                    window["-STATUS-"].update("Invalid transaction data. Please check all fields.", text_color="red")
            except ValueError:
                window["-STATUS-"].update("Amount must be a valid number", text_color="red")
    
    return None 