function convert_temperatures_to_fahrenheit(list_of_temperatures_celsius) {
  return list_of_temperatures_celsius.map(temperature => temperature * 1.8 + 32);
}

const list_of_temperatures_celsius = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30];

const list_of_temperatures_fahrenheit = convert_temperatures_to_fahrenheit(list_of_temperatures_celsius);

console.log("List of temperatures in Fahrenheit: ");
console.log(list_of_temperatures_fahrenheit);