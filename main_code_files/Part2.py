"""
PCL 1 Fall Semester 2023 - Course Project
Part 0: Book Selection
Students: <person 1>, <person 2>
"""
# --- Imports ---
import os
import re
import json
import spacy
# --- You may add other imports here ---
from flair.models import TextClassifier
from flair.data import Sentence
from tqdm import tqdm
import sys

def load_book(book_path):
    """
    Function to load a book from a text file
    :param book_path: Path to the book text file
    :return: The book text as a string 
    """
    
    with open(book_path, 'r', encoding='utf-8') as book_file:
        book_text = book_file.read()
    return book_text

def extract_chapter_numbers(text):
    match = re.search(r'\b([IVXLCDM]+|\d+(\.\d+)?)\.', text)

    if match:
        return match.group(1)
    return None

CHAPTERS = ["Chapter", "CHAPTER", "ACT"]

def split_book_by_chapter(cleaned_text, spacy_model):
    """
    Split the book into chapters
    :param cleaned_text: the text of the book with the headers and footers removed
    :return: a list of chapters
    """
    add_chapter = []


    for title in CHAPTERS:
        cleaned_text = cleaned_text.replace(title, "Chapter ")
    chapters = re.split(r'\bChapter\b', cleaned_text)
    
    for chapter in chapters:
      if len(chapter) > 1000:
        number = extract_chapter_numbers(chapter)
        add_chapter.append((number, spacy_model(chapter[2:])))

    return add_chapter

def perform_ner(text):
    """
    Function to perform named entity recognition on a text
    :param text: The text to perform NER on
    :param spacy_model: The spaCy model to use for NER
    :return: A list of named entities
    """
    
    entities = []

    for ent in text.ents:
        if ent.label_ == "PERSON":
            entities.append(ent.text)

    return entities

def count_entities(entities:list)->list:
    """
    Counts the number of times each entity appears in the text
    :param text: 
    :param words: list of words to count
    :return: dictionary with words as keys and number of times they appear in the text as values
    """
    set_entities = set(entities)
    entities_tuples = {}

    for word in set_entities:
        count = entities.count(word)
        if count > 5:
            entities_tuples[word] = count

    return entities_tuples

def extract_sentiment_scores(sentence):
  sentiment_words = []
  classifier = TextClassifier.load('sentiment-fast')
  sentence_sentiment = Sentence(sentence)
  classifier.predict(sentence_sentiment)

  if sentence_sentiment.labels:
    sentiment_score = sentence_sentiment.labels[0].score
    for token in sentence_sentiment.tokens:
      sentiment_words.append((token.text, sentiment_score))
  return sentiment_words


def character_sentiment_per_chapter(chapter, entities):
    sentiment_words = {}

    for char in entities:
        if char not in sentiment_words:
            sentiment_words[char] = []

        weighted_sentiment = 0

        for sent in chapter.sents:
          if char in sent.text and any(token for token in sent if token.pos_ in ["ADJ", "ADV"]):
            sentiment_words[char] = {"sentiment_per_chapter":[],
                                     "context": []}
            sentiment_words[char]["context"].append(sent.text)
              
            char_idx = sent.text.index(char)

            sentiment_scores = extract_sentiment_scores(sent.text)

            for token in sent:
                for word in sentiment_scores:
                  if token.pos_ in ["ADJ", "ADV"] and token.text == word[0]:
                    sentiment_score = word[1]
                    sentiment_idx = abs(char_idx - token.i)

                    try:
                        weighted_sentiment += sentiment_score / sentiment_idx
                    except ZeroDivisionError:
                        weighted_sentiment += 0.0
        sentiment_words[char]["sentiment_per_chapter"].append(weighted_sentiment)

    return sentiment_words


def character_sentiment_per_chapter(chapter, entities):
    sentiment_words = {}

    for char in tqdm(entities, desc="Processing Entities"):
        if char not in sentiment_words:
            sentiment_words[char] = {"sentiment_per_chapter": [], "context": []}

        weighted_sentiment = 0

        for sent in chapter.sents:
            if char in sent.text and any(token for token in sent if token.pos_ in ["ADJ", "ADV"]):
                sentiment_words[char]["context"].append(sent.text.replace("\n", " "))
              
                char_idx = sent.text.index(char)

                sentiment_scores = extract_sentiment_scores(sent.text)

                for token in sent:
                    for word in sentiment_scores:
                        if token.pos_ in ["ADJ", "ADV"] and token.text == word[0]:
                            sentiment_score = word[1]
                            sentiment_idx = abs(char_idx - token.i)

                            try:
                                weighted_sentiment += sentiment_score / sentiment_idx
                            except ZeroDivisionError:
                                weighted_sentiment += 0.0

        sentiment_words[char]["sentiment_per_chapter"].append(weighted_sentiment)
        print(sentiment_words)
                

    return sentiment_words

def restructured_data(data):
    restructured_data = {}

    for chapter, characters in data.items():
        for name, details in characters:
            if name not in restructured_data:
                restructured_data[name] = {
                    "name": name,
                    "sentiments": [],
                    "aggregated_sentiment": 0.0,
                    "context": []
                }

            # Append sentiments and context
            restructured_data[name]["sentiments"].extend(
                [(chapter, sentiment) for sentiment in details["sentiment_per_chapter"]]
            )
            restructured_data[name]["context"].extend(details["context"])

    # Calculate aggregated sentiment for each character
    for name, details in restructured_data.items():
        if details["sentiments"]:
            details["aggregated_sentiment"] = sum(sentiment[1] for sentiment in details["sentiments"])

    return list(restructured_data.values())

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 Part2.py <path_to_the_book> <path_to_store_json>")
        sys.exit(1)
    book_path = sys.argv[1]
    directory_path = sys.argv[2]
    nlp = spacy.load("en_core_web_lg")

    book_text = load_book(book_path)
    book_title = os.path.basename(book_path).replace("_clean.txt", "")

    chapters = split_book_by_chapter(book_text, nlp)
    get_entities = [perform_ner(chapter[1]) for chapter in chapters]
    list_of_characters = [char for lst in get_entities for char in lst]

    main_characters = list(count_entities(list_of_characters).keys())
    scores = {}

    for chapter in chapters:
        if chapter[0] not in scores:
            scores[chapter[0]] = []

        get_sentiment = character_sentiment_per_chapter(chapter[1], main_characters)
        scores[chapter[0]].extend(get_sentiment.items())
    
    result = json.dumps(restructured_data(scores), ensure_ascii=False, indent=2)
    file_name = f"{book_title}_Sentiment.json"
    output_file_path = os.path.join(directory_path, file_name)
    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json_file.write(result)


# Run the main function
if __name__ == "__main__":
    main()
