addEventListener('DOMContentLoaded', () => {
    const myButton = document.getElementById('myButton');
    const userId = document.getElementById('userId');
    myButton.addEventListener('click', () => {
        displayUser(userId.value);
    });
});

const url = 'https://reqres.in/'
const apiKey = 'reqres-free-v1'

async function getUser(userId) {

  const response = await fetch(`${url}api/users/${userId}`, {
    method: 'GET',
    headers: {
      'x-api-key': apiKey
    }
  });
  if (response.status === 404) {
    throw new Error('User not found');
  }
  if (!response.ok) {
    throw new Error('Unexpected error');
  }
  const data = await response.json();
  return data;

}

async function displayUser(userId) {
  const user = document.getElementById('user');
  try {
    const response = await getUser(userId);
    user.innerHTML = `
        <h2>${response.data.first_name} ${response.data.last_name}</h2>
        <p>${response.data.email}</p>
        <img src="${response.data.avatar}" alt="${response.data.first_name} ${response.data.last_name}">
    `;
  } catch (error) {
    user.innerHTML = `
        <p>Error: ${error.message}</p>
    `;
  }
}