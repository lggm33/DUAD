
const student = {
	name: "John Doe",
	grades: [
		{name: "math",grade: 80},
		{name: "science",grade: 100},
		{name: "history",grade: 60},
		{name: "PE",grade: 90},
		{name: "music",grade: 98}
	]
}

function get_student_summary(student) {
  return {
    name: student.name,
    gradeAvg: student.grades.reduce((acc, grade) => acc + grade.grade, 0) / student.grades.length,
    highestGrade: student.grades.sort((a, b) => b.grade - a.grade)[0].name,
    lowestGrade: student.grades.sort((a, b) => a.grade - b.grade)[0].name,
  }
}

const student_summary = get_student_summary(student);

console.log("Student summary: ");
console.log(student_summary);