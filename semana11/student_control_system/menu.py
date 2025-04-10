import os
import platform

from actions import (
    add_student,
    view_all_students,
    view_top_students,
    view_average_grade
)

from data import (
    export_to_csv,
    import_from_csv
)

from utils import clear_console

def display_menu():
    """Display the main menu options"""
    clear_console()
    print("\n===== STUDENT MANAGEMENT SYSTEM =====")
    print("1. Add Student")
    print("2. View All Students")
    print("3. View Top 3 Students")
    print("4. View Average Grade")
    print("5. Export Data to CSV")
    print("6. Import Data from CSV")
    print("0. Exit")
    print("====================================")

def main_loop():
    """Main program loop"""
    # Initialize the students list here to maintain state across function calls
    students = []
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            students = add_student(students)
        elif choice == '2':
            view_all_students(students)
        elif choice == '3':
            view_top_students(students)
        elif choice == '4':
            view_average_grade(students)
        elif choice == '5':
            export_to_csv(students)
        elif choice == '6':
            students = import_from_csv(students)
        elif choice == '0':
            clear_console()
            print("Thank you for using the Student Management System. Goodbye!")
            break
        else:
            clear_console()
            print("Invalid choice! Please enter a number between 0 and 6.")
            input("Press Enter to continue...")
            continue
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_loop()