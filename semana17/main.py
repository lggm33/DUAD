import FreeSimpleGUI as sg
import datetime

# Import modules
from data_manager import init_process, export_transactions_csv_file, export_categories_file, ask_add_transactions_examples
from gui_windows import create_category_window, create_transaction_window
from models import add_transaction

def main():
    transactions, categories = init_process()

    ask_add_examples_transaction_column = sg.Column([
        [sg.Text("Not previous data found")],
        [sg.Text("Do you want to add data example?")],
        [sg.Button("Yes"), sg.Button("No")],
    ], key="-ASK-ADD-EXAMPLES-TRANSACTION-COLUMN-", visible=False)

    # Define elements
    layout = [
        [sg.Text("Welcome to the Personal Finance Manager System", font=("Helvetica", 16), justification="center", expand_x=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("Transactions Table", font=("Helvetica", 12))],
        [ask_add_examples_transaction_column],
        [sg.Table(values=[], headings=["Date", "Description", "Amount", "Category", "Type"], 
                 key="-TABLE-", 
                 auto_size_columns=True,
                 col_widths=[12, 20, 10, 15, 10],
                 justification="center", 
                 num_rows=10, 
                 expand_x=True,
                 expand_y=True,
                 visible=False)],
        [sg.Button("Add Expense", key="-ADD-EXPENSE-", visible=False), 
         sg.Button("Add Income", key="-ADD-INCOME-", visible=False),
         sg.Button("Add Category", key="-ADD-CATEGORY-", visible=False)],
        [sg.Push(), sg.Text("© 2024 Personal Finance Manager", font=("Helvetica", 8)), sg.Push()]
    ]

    # Determine window size
    window_width, window_height = 700, 400

    window = sg.Window("Personal Finance Manager System", 
                      layout, 
                      finalize=True,
                      resizable=True,
                      size=(window_width, window_height),
                      element_justification='center',
                      relative_location=(0.5, 0.5))
    
    first_time = True
    print(transactions)
    print(f"Available categories: {categories}")

    # Show question column if it's the first time and there are no transactions
    if first_time and len(transactions) == 0:
        window["-ASK-ADD-EXAMPLES-TRANSACTION-COLUMN-"].update(visible=True)
    else:
        window["-TABLE-"].update(visible=True)
        window["-ADD-CATEGORY-"].update(visible=True)
        window["-ADD-EXPENSE-"].update(visible=True)
        window["-ADD-INCOME-"].update(visible=True)
        # Show existing transactions in the table
        if transactions:
            table_data = [[t["date"], t["description"], t["amount"], t["category"], t["type"]] for t in transactions]
            window["-TABLE-"].update(values=table_data)

    while True:
        event, values = window.read()
        print("running")

        if event == sg.WIN_CLOSED:
            break

        if first_time and len(transactions) == 0:
            if event == "Yes":
                print("Yes")
                transactions, categories = ask_add_transactions_examples()
                first_time = False
                window["-ASK-ADD-EXAMPLES-TRANSACTION-COLUMN-"].update(visible=False)
                window["-TABLE-"].update(visible=True)
                window["-ADD-CATEGORY-"].update(visible=True)
                window["-ADD-EXPENSE-"].update(visible=True)
                window["-ADD-INCOME-"].update(visible=True)
                # Update the table with added transactions
                table_data = [[t["date"], t["description"], t["amount"], t["category"], t["type"]] for t in transactions]
                window["-TABLE-"].update(values=table_data)
            elif event == "No":
                print("No")
                # Create empty files for transactions and categories
                export_transactions_csv_file([])
                export_categories_file([])
                first_time = False
                window["-ASK-ADD-EXAMPLES-TRANSACTION-COLUMN-"].update(visible=False)
                window["-TABLE-"].update(visible=True)
                window["-ADD-CATEGORY-"].update(visible=True)
                window["-ADD-EXPENSE-"].update(visible=True)
                window["-ADD-INCOME-"].update(visible=True)
                
        if event == "-ADD-CATEGORY-":
            categories = create_category_window(categories)
            print(f"Updated categories: {categories}")
            
        if event == "-ADD-EXPENSE-" or event == "-ADD-INCOME-":
            # Check if there are categories before allowing to add transactions
            if not categories:
                sg.popup_ok("You need to add at least one category before adding transactions.", 
                           title="No Categories Available")
                categories = create_category_window(categories)
                # If user still didn't add categories, don't proceed
                if not categories:
                    continue
            
            # Now proceed with adding the transaction
            transaction_type = "expense" if event == "-ADD-EXPENSE-" else "income"
            new_transaction = create_transaction_window(transaction_type, categories)
            if new_transaction:
                transactions = add_transaction(transactions, new_transaction)
                table_data = [[t["date"], t["description"], t["amount"], t["category"], t["type"]] for t in transactions]
                window["-TABLE-"].update(values=table_data)

    window.close()

if __name__ == "__main__":
    main()