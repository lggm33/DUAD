const fs = require('fs').promises;
const path = require('path');

const url = 'https://pokeapi.co/api/v2/pokemon/'

function getPokemonPromiseAll(pokemonList) {
  console.log("🚀 Starting Promise.all - Will wait for ALL promises to resolve");
  
  const promises = pokemonList.map(pokemon => {
    console.log(`⏳ Fetching ${pokemon}...`);
    return fetch(`${url}${pokemon}`)
      .then(response => response.json())
      .then(data => {
        console.log(`✅ ${pokemon} resolved (but waiting for others...)`);
        return data.name;
      });
  });
  
  return Promise.all(promises);
}

getPokemonPromiseAll(['pikachu', 'charmander', 'squirtle']).then(pokemonNames => {
  console.log("================================================");
  console.log("🎉 Promise.all COMPLETE - All promises resolved!");
  console.log("📋 Showing ALL results:");
  pokemonNames.forEach(name => {
    console.log(name);
  });
  console.log("================================================\n");
  runPromiseAny();
});

function getPokemonPromiseAny(pokemonList) {
  console.log("🚀 Starting Promise.any - Will return FIRST promise that resolves");
  
  const promises = pokemonList.map(pokemon => {
    console.log(`⏳ Fetching ${pokemon}...`);
    return fetch(`${url}${pokemon}`)
      .then(response => response.json())
      .then(data => {
        console.log(`✅ Promise.any - ${pokemon} resolved`);
        return data.name;
      });
  });
  
  return Promise.any(promises);
}

getPokemonPromiseAny(['pikachu', 'charmander', 'squirtle']).then(pokemonName => {
    console.log("================================================");
    console.log("🎉 Promise.any COMPLETE - First promise resolved!");
    console.log("📋 Showing FIRST result:");
    console.log(pokemonName);
    console.log("(Other promises may still be resolving in background)");
    console.log("================================================\n");
});

function runPromiseAny() {
    getPokemonPromiseAny(['pikachu', 'charmander', 'squirtle']).then(pokemonName => {
        console.log("================================================");
        console.log("🎉 Promise.any COMPLETE - First promise resolved!");
        console.log("📋 Showing FIRST result:");
        console.log(pokemonName);
        console.log("(Other promises may still be resolving in background)");
        console.log("================================================\n");
        runCreateTextFromPromises();
    });
}

function createPromise(text, time) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(text);
        }, time);
    });
}

const textAndTimeList = [
    { text: "very", time: 300 },
    { text: "dogs", time: 100 },
    { text: "cute", time: 400 },
    { text: "are", time: 200 },
]

function createTextFromPromises(textAndTimeList) {
    const words = [];
    
    const promises = textAndTimeList.map(item => {
        return createPromise(item.text, item.time).then(text => {
            words.push(text);
        });
    });
    
    return Promise.all(promises).then(() => {
        return words.join(' ');
    });
}


function runCreateTextFromPromises() {
    createTextFromPromises(textAndTimeList).then(texts => {
        console.log("================================================");
        console.log("Creating text from promises (ordered by resolution time):");
        console.log(texts);
        runIsPairPromise();
    });
}

function isPairPromise(number) {
    return new Promise((resolve) => {
      console.log("================================================");
      console.log("Starting is pair promise");
      console.log("Number: ", number);
      return number % 2 === 0 ? resolve("Is pair") : resolve("Is not pair");
    });
}


function runIsPairPromise() {
    isPairPromise(3).then(message => {
        console.log(message);
        runFindCommonWords();
    });
}

function readFile(fileName) {
    const filePath = path.join(__dirname, fileName);
    return fs.readFile(filePath, 'utf8')
        .then(text => {
            return text.trim().split('\n').map(word => word.trim());
        });
}

function findCommonWords() {
    const file1Promise = readFile('text1.txt');
    const file2Promise = readFile('text2.txt');
    
    return Promise.all([file1Promise, file2Promise]).then(([words1, words2]) => {
        const commonWords = words1.filter(word => words2.includes(word));
        return commonWords;
    });
}

function runFindCommonWords() {
    findCommonWords().then(commonWords => {
        console.log("================================================");
        console.log("Common words in both files:");
        console.log(commonWords);
        console.log("================================================");
        console.log("Hidden message:");
        console.log(commonWords.join(' '));
        console.log("================================================\n");
    });
}

