import csv
import os
from utils import clear_console

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
            # Remove average from fieldnames
            fieldnames = ['name', 'section', 'spanish_grade', 'english_grade', 
                          'social_grade', 'science_grade']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for student in students_list:
                # Create a copy of student data without the average field
                student_data = {k: student[k] for k in fieldnames}
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
                # Convert grades to float
                row['spanish_grade'] = float(row['spanish_grade'])
                row['english_grade'] = float(row['english_grade'])
                row['social_grade'] = float(row['social_grade'])
                row['science_grade'] = float(row['science_grade'])
                
                # Calculate average internally after import
                avg_grade = (row['spanish_grade'] + row['english_grade'] + 
                             row['social_grade'] + row['science_grade']) / 4
                row['average'] = round(avg_grade, 2)
                
                imported_students.append(row)
        
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
