import platform
import os
from operator import itemgetter, attrgetter
from utils import clear_console
from models import Student

def add_student(students_list):
    """Add a new student to the system"""
    clear_console()
    print("===== ADD NEW STUDENTS =====")
    try:
        n = int(input("Enter the number of students to add: "))
        if n <= 0:
            print("Please enter a positive number.")
            return students_list
    except ValueError:
        print("Invalid input! Please enter a valid number.")
        return students_list
    
    for i in range(n):
        print(f"\nEntering data for student #{i+1}")
        # Get full name
        name = input("Enter full name: ")
        while not name.strip():
            print("Name cannot be empty!")
            name = input("Enter full name: ")
        
        # Get section
        section = input("Enter section (e.g. 11B): ")
        while not section.strip():
            print("Section cannot be empty!")
            section = input("Enter section (e.g. 11B): ")
        
        # Get grades
        spanish_grade = get_valid_grade("Spanish")
        english_grade = get_valid_grade("English")
        social_grade = get_valid_grade("Social Studies")
        science_grade = get_valid_grade("Science")
        
        # Create student record
        student = Student(name, section)
        student.add_subject('Spanish', spanish_grade)
        student.add_subject('English', english_grade)
        student.add_subject('Social Studies', social_grade)
        student.add_subject('Science', science_grade)
        student.calculate_average()
        
        students_list.append(student)
        print(f"Student {name} added successfully!")
    
    return students_list

def get_valid_grade(subject):
    """Helper function to get and validate a grade between 0 and 100"""
    while True:
        try:
            grade = float(input(f"Enter {subject} grade (0-100): "))
            if 0 <= grade <= 100:
                return grade
            else:
                print(f"Grade must be between 0 and 100")
        except ValueError:
            print("Invalid grade! Please enter a number.")

def view_all_students(students_list):
    """Display all students in the database"""
    clear_console()
    print("===== VIEW ALL STUDENTS =====")
    if not students_list:
        print("No students found in the system!")
        print("Please add some students first.")
        return
    
    print("\n--- All Students ---")
    for i, student in enumerate(students_list, 1):
        print(f"{i}. {student.name} - Section: {student.section}")
        print(f"   Spanish: {student.subjects_grades['Spanish']} | English: {student.subjects_grades['English']} | "
              f"Social Studies: {student.subjects_grades['Social Studies']} | Science: {student.subjects_grades['Science']}")
    print("-------------------\n")

def view_top_students(students_list):
    """Display top 3 students based on grade"""
    clear_console()
    print("===== TOP 3 STUDENTS =====")
    if not students_list:
        print("No students found in the system!")
        print("Please add some students first.")
        return
    
    # Sort students by average grade in descending order (internal calculation)
    sorted_students = sorted(students_list, key=attrgetter('average_grade'), reverse=True)
    
    # Get top 3 or fewer if there are less than 3 students
    top_students = sorted_students[:3]
    
    print("\n--- Top 3 Students ---")
    for i, student in enumerate(top_students, 1):
        # Calculate total of all grades to display
        total = student.subjects_grades['Spanish'] + student.subjects_grades['English'] + student.subjects_grades['Social Studies'] + student.subjects_grades['Science']
        print(f"{i}. {student.name} - Section: {student.section} - Total Points: {total}")
    print("---------------------\n")

def view_average_grade(students_list):
    """Calculate and display the average grade of all students"""
    clear_console()
    print("===== AVERAGE GRADE =====")
    if not students_list:
        print("No students found in the system!")
        print("Please add some students first.")
        return
    
    # Still show the class average since this function is specifically for that
    total_average = sum(student.average_grade for student in students_list)
    class_average = total_average / len(students_list)
    
    print(f"\nClass average grade: {class_average:.2f}\n")
