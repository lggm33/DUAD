import csv
import os
from utils import clear_console
from models import Student

def export_to_csv(students_list):
    """Export student data to a CSV file"""
    clear_console()
    print("===== EXPORT DATA TO CSV =====")
    if not students_list:
        print("No students to export!")
        print("Please add some students first.")
        return
    
    filename = input("Enter filename to export (default: students.csv): ") or "students.csv"
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            # Define fieldnames for the CSV
            fieldnames = ['name', 'section', 'spanish_grade', 'english_grade', 
                          'social_grade', 'science_grade']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for student in students_list:
                # Create a dictionary with student data
                student_data = {
                    'name': student.name,
                    'section': student.section,
                    'spanish_grade': student.subjects_grades.get('Spanish', 0),
                    'english_grade': student.subjects_grades.get('English', 0),
                    'social_grade': student.subjects_grades.get('Social Studies', 0),
                    'science_grade': student.subjects_grades.get('Science', 0)
                }
                writer.writerow(student_data)
        
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")

def import_from_csv(students_list):
    """Import student data from a CSV file"""
    clear_console()
    print("===== IMPORT DATA FROM CSV =====")
    filename = input("Enter filename to import (default: students.csv): ") or "students.csv"
    
    if not os.path.exists(filename):
        print(f"File {filename} not found!")
        return students_list
    
    try:
        imported_students = []
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract name and section
                name = row['name']
                section = row['section']
                
                # Convert grades to float
                spanish_grade = float(row['spanish_grade'])
                english_grade = float(row['english_grade'])
                social_grade = float(row['social_grade'])
                science_grade = float(row['science_grade'])
                
                # Create Student instance
                student = Student(name, section)
                student.add_subject('Spanish', spanish_grade)
                student.add_subject('English', english_grade)
                student.add_subject('Social Studies', social_grade)
                student.add_subject('Science', science_grade)
                
                # Calculate average - will be done automatically by the Student class
                student.calculate_average()
                
                imported_students.append(student)
        
        # Append to existing students or replace
        choice = input("Append to existing students? (y/n): ").lower()
        if choice == 'y':
            students_list.extend(imported_students)
        else:
            students_list.clear()
            students_list.extend(imported_students)
        
        print(f"Successfully imported {len(imported_students)} students from {filename}")
        return students_list
    except Exception as e:
        print(f"Error importing data: {e}")
        return students_list
