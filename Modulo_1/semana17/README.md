# Personal Finance Manager

A simple yet powerful personal finance management system built with Python and FreeSimpleGUI. This application helps users track their income and expenses, categorize transactions, and manage their personal finances effectively.

## Features

- Track income and expense transactions
- Categorize transactions for better organization
- Simple and intuitive user interface
- Data persistence using CSV and text files
- Add, view, and manage categories
- Validation for data integrity

## Architecture

The application is structured in a modular way for better organization, maintainability, and scalability:

### Modules

1. **main.py**
   - Entry point of the application
   - Handles the main GUI window and event loop
   - Coordinates interactions between other modules

2. **data_manager.py**
   - Handles data persistence operations
   - Implements file I/O operations for transactions and categories
   - Performs data validation and error handling for file operations
   - Contains initialization process and example data generation

3. **gui_windows.py**
   - Implements all secondary GUI windows
   - Contains form validation logic
   - Handles user interaction in modal windows
   - Creates consistent UI experience

4. **models.py**
   - Contains business logic for data operations
   - Implements transaction management
   - Separates data manipulation from presentation logic

## How to Use

### Initial Setup

1. Run the program by executing `main.py`
2. On first run, you'll be asked if you want to add example data
   - If you choose "Yes", the system will populate with sample transactions and categories
   - If you choose "No", you'll start with empty data files

### Adding Transactions

1. Click "Add Income" or "Add Expense" buttons
2. Fill in the required fields:
   - Title: Description of the transaction
   - Amount: The monetary value (must be a positive number)
   - Category: Select from available categories
   - Date: Transaction date in YYYY-MM-DD format
3. Click "Save" to store the transaction

### Managing Categories

1. Click "Add Category" button
2. Enter a new category name
3. Click "Add" to save the category
4. The category will immediately be available for use in transactions

## Data Storage

- Transactions are stored in a CSV file (`transactions.csv`)
- Categories are stored in a text file (`categories.txt`)
- Both files are automatically created and maintained by the application

## Requirements

- Python 3.6 or higher
- FreeSimpleGUI library

## Dependencies and Installation

Before running the application, make sure to install all required dependencies:

```bash
# Install the FreeSimpleGUI library
pip install FreeSimpleGUI
```

If you encounter any issues with the GUI, you might need to install additional packages depending on your operating system:

### Windows
```bash
# Usually no additional packages required
```

### Linux
```bash
# On Debian/Ubuntu
sudo apt-get install python3-tk
```

### macOS
```bash
# Using Homebrew
brew install python-tk
```

## Running the Application

After installing the dependencies, you can run the application using:

```bash
python main.py
```

## Notes

- The application will validate all inputs to ensure data integrity
- If you try to add a transaction without any categories, you'll be prompted to create a category first
- File format errors are handled with options to recover corrupted data files