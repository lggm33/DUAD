function isPair(number, RunNumberEven, RunNumberOdd) {
    if (number % 2 === 0) {
        RunNumberEven();
    } else {
        RunNumberOdd();
    }
}

function RunNumberEven() {
    console.log("The number is even");
}

function RunNumberOdd() {
    console.log("The number is odd");
}

isPair(9, RunNumberEven, RunNumberOdd);