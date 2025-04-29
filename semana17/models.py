from data_manager import export_transactions_csv_file

def add_transaction(transactions, new_transaction):
    """Add a new transaction to the list and save to file"""
    if not new_transaction:
        return transactions
    
    transactions.append(new_transaction)
    export_transactions_csv_file(transactions)
    return transactions 