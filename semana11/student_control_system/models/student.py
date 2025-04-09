class Student:
    def __init__(self, name, section, average_grade=0, subjects_grades=None):
        self.name = name
        self.section = section
        self.average_grade = average_grade
        self.subjects_grades = subjects_grades or {}
        
    def add_subject(self, subject_name, grade):
        valid_subjects = ['Spanish', 'English', 'Social Studies', 'Science']
        if subject_name not in valid_subjects:
            raise ValueError(f"Invalid subject: {subject_name}")
        self.subjects_grades[subject_name] = float(grade)

    def calculate_average(self):
        total = sum(self.subjects_grades.values())
        self.average_grade = round(total / len(self.subjects_grades), 2)
