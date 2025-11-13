const list_of_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

function get_pairs_numbers_with_for(list_of_numbers) {
  const list_of_pairs_numbers = [];
  for (let i = 0; i < list_of_numbers.length; i++) {
    if (list_of_numbers[i] % 2 === 0) {
        list_of_pairs_numbers.push(list_of_numbers[i]);
    }
  }
  return list_of_pairs_numbers;
}

function get_pairs_numbers_with_filter(list_of_numbers) {
  return list_of_numbers.filter(number => number % 2 === 0);
}


const list_of_pairs_numbers = get_pairs_numbers_with_for(list_of_numbers);

console.log("List of pairs numbers with for: ");
console.log(list_of_pairs_numbers);

const list_of_pairs_numbers_with_filter = get_pairs_numbers_with_filter(list_of_numbers);

console.log("List of pairs numbers with filter: ");
console.log(list_of_pairs_numbers_with_filter);

