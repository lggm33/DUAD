addEventListener('DOMContentLoaded', () => {
    const myButton = document.getElementById('myButton');
    const myParagraph = document.getElementById('myParagraph');
    myButton.addEventListener('click', () => {
        myParagraph.style.backgroundColor = getRandomColorFromArray(colors);
    });
});

const colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'pink'];

function getRandomColorFromArray(array) {
    return array[Math.floor(Math.random() * array.length)];
}

