const fs = require('fs');
const path = require('path');

function readWordsFromFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return content.split('\n')
            .map(word => word.trim())
            .filter(word => word.length > 0);
    } catch (error) {
        console.error(`Error reading file ${filePath}:`, error.message);
        return [];
    }
}

function findCommonWords(words1, words2) {
    const set2 = new Set(words2);
    return words1.filter(word => set2.has(word));
}

function displayHiddenMessage(commonWords) {
    if (commonWords.length === 0) {
        console.log("No common words found.");
        return;
    }
    
    console.log("Common words:", commonWords.join(", "));
    console.log("\nHidden message:", commonWords.join(" "));
}

function main() {
    const text1Path = path.join(__dirname, 'text1.txt');
    const text2Path = path.join(__dirname, 'text2.txt');
    
    const words1 = readWordsFromFile(text1Path);
    const words2 = readWordsFromFile(text2Path);
    
    console.log(`Words in text1.txt: ${words1.length}`);
    console.log(`Words in text2.txt: ${words2.length}\n`);
    
    const commonWords = findCommonWords(words1, words2);
    
    displayHiddenMessage(commonWords);
}

main();

