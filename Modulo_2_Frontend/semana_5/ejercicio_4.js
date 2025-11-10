function get_words_from_text(text) {
  const words = [];
  let word = "";
  for (let i = 0; i < text.length; i++) {
    if (text[i] !== " ") {
      word += text[i];
    } else {
      words.push(word);
      word = "";
    }
  }
  words.push(word);
  return words;
}

const text = "Este es un texto!";
const words = get_words_from_text(text);

console.log("Words from text: ");
console.log(words);