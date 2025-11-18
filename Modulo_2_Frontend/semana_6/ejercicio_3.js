document.addEventListener('DOMContentLoaded', () => {
  const employeeYes = document.getElementById('employeeYes');
  const employeeNo = document.getElementById('employeeNo');
  const employeeId = document.getElementById('employeeId');

  if (employeeYes.checked) {
    employeeId.style.display = 'block';
    employeeIdLabel.style.display = 'block';
  } else {
    employeeId.style.display = 'none';
    employeeIdLabel.style.display = 'none';
  }
  
  employeeNo.addEventListener('change', () => {
    if (employeeNo.checked) {
      employeeId.style.display = 'none';
      employeeIdLabel.style.display = 'none';
    }
  });

  employeeYes.addEventListener('change', () => {
    if (employeeYes.checked) {
      employeeId.style.display = 'block';
      employeeIdLabel.style.display = 'block';
    } 
  });
  
});