import FreeSimpleGUI as sg
import datetime
from data_manager import export_categories_file

def create_category_window(categories):
    """Create a new window for adding categories"""
    
    layout = [
        [sg.Text("Current Categories:", font=("Helvetica", 12))],
        [sg.Listbox(values=categories, size=(30, 10), key="-CATEGORIES-LIST-")],
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
            new_category = values["-NEW-CATEGORY-"].strip()
            if new_category and new_category not in categories:
                categories.append(new_category)
                window["-CATEGORIES-LIST-"].update(categories)
                window["-NEW-CATEGORY-"].update("")
                # Save categories to file
                export_categories_file(categories)
                window["-STATUS-"].update(f"Category '{new_category}' added successfully!", text_color="#008080", background_color="#f0f0f0")
            elif not new_category:
                window["-STATUS-"].update("Please enter a category name!", text_color="red")
            else:
                window["-STATUS-"].update("Category already exists!", text_color="red")
    
    window.close()
    return categories

def create_transaction_window(transaction_type, categories):
    """Create a new window for adding a transaction"""
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    layout = [
        [sg.Text(f"Add {transaction_type.capitalize()}", font=("Helvetica", 14))],
        [sg.Text("Title:"), sg.InputText(key="-TITLE-")],
        [sg.Text("Amount:"), sg.InputText(key="-AMOUNT-")],
        [sg.Text("Category:"), sg.Combo(categories, key="-CATEGORY-", size=(20, 1))],
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
            category = values["-CATEGORY-"]
            date = values["-DATE-"].strip()
            
            # Validation checks
            errors = []
            
            if not title:
                errors.append("Title is required")
            
            # Validate amount is a number
            try:
                amount = float(amount_str)
                if amount <= 0:
                    errors.append("Amount must be greater than zero")
            except ValueError:
                errors.append("Amount must be a valid number")
            
            # Validate category
            if not category or category not in categories:
                errors.append("Please select a valid category")
            
            # Validate date format
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                errors.append("Date must be in format YYYY-MM-DD")
            
            if errors:
                window["-STATUS-"].update('\n'.join(errors), text_color="red")
            else:
                # Create transaction object
                transaction = {
                    "date": date,
                    "description": title,
                    "amount": amount,
                    "category": category,
                    "type": transaction_type
                }
                window.close()
                return transaction
    
    return None 