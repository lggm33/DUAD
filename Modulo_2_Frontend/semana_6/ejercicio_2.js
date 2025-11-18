document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('myButton').addEventListener('click', () => {
      const myInput = document.getElementById('myInput');
      if (myInput.value) {
        alert(myInput.value);
      } else {
        alert('No text entered');
      }
      myInput.value = '';
  });
});