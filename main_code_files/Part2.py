"""
PCL 1 Fall Semester 2023 - Course Project
Part 2: Entity-Specific Sentiment Analysis
Students: Asher Slater & Daria Stetsenko
"""
# --- Imports ---
import os
import re
import json
import spacy
# --- You may add other imports here ---

"""
After analyzing different sentiment analysis tools, we used Flair for this task.
The reason for this is that Flair is a state-of-the-art NLP library that is easy to use, and we can extract 
more precise scores for the sentiment of each character based on the context of the sentence.

However, this code was initially written in the ipynb file and run using the Google Colab environment. 
It was due to the fact that the code was taking a long time to run, and we were not able to run it on our local machines.
The GPU and higher RAM accelerated the process of running the code. Also, the Flair library is implemented using PyTorch and neural nets,
hence, that was easier and faster to run on the GPU.
"""

from flair.models import TextClassifier
from flair.data import Sentence
from tqdm import tqdm
import sys


"""
The first steps are similar to the ones we implemeted for the NER part. 
We load the book, split it into chapters and extract the entities.
"""

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

"""
The next step is to extract the sentiment scores for each character. We use the Flair library to extract the sentiment scores for each sentence.
Then we calculate the weighted sentiment score for each character based on the context of the sentence.
"""

def extract_sentiment_scores(sentence):
  """
  Function to extract the sentiment scores for each sentence
  :param sentence: The sentence to extract the sentiment scores for
  :return: A list of tuples containing the sentiment scores for each word in the sentence
  """
  sentiment_words = []

  # Load the sentiment classifier
  classifier = TextClassifier.load('sentiment-fast')
  # Create a sentence object
  sentence_sentiment = Sentence(sentence)
  # Predict the sentiment of the sentence
  classifier.predict(sentence_sentiment)

  if sentence_sentiment.labels:
    # Get the sentiment score
    sentiment_score = sentence_sentiment.labels[0].score
    # Save the word and its corresponding sentiment score
    for token in sentence_sentiment.tokens:
      sentiment_words.append((token.text, sentiment_score))
  return sentiment_words

"""
We agreed to extract the sentiment scores only for adjectives and adverbs. 
We decided to do so because we wanted to extract the sentiment scores for words more likely to express the sentence's sentiment.
"""

def character_sentiment_per_chapter(chapter, entities):
    """
    Function to extract the sentiment scores for each character in a chapter
    :param chapter: The chapter to extract the sentiment scores from
    :param entities: The list of characters to extract the sentiment scores for
    
    :return: A dictionary containing the sentiment scores for each character per chapter and the context of the sentence"""
    # Create a dictionary to store the sentiment scores for each character
    sentiment_words = {}

    # Iterate over the characters
    for char in tqdm(entities, desc="Processing Entities"):
        if char not in sentiment_words:
            sentiment_words[char] = {"sentiment_per_chapter": [], "context": []}
        
        # Create a variable to store the weighted sentiment score for each character
        weighted_sentiment = 0

        # Iterate over the sentences in the chapter
        for sent in chapter.sents:
            # Check if the character is in the sentence and if there is an adjective or adverb in the sentence
            if char in sent.text and any(token for token in sent if token.pos_ in ["ADJ", "ADV"]):
                sentiment_words[char]["context"].append(sent.text.replace("\n", " "))

                # Get the index of the character in the sentence
                char_idx = sent.text.index(char)
                # Extract the sentiment scores for the sentence
                sentiment_scores = extract_sentiment_scores(sent.text)
                # Iterate over the sentiment scores
                for token in sent:
                    for word in sentiment_scores:
                        # Check if the word is an adjective or adverb and if it is the word we are looking for
                        if token.pos_ in ["ADJ", "ADV"] and token.text == word[0]:
                            sentiment_score = word[1]
                            # Calculate the distance between the character and the word
                            sentiment_idx = abs(char_idx - token.i)

                            try:
                                # Calculate the weighted sentiment score
                                weighted_sentiment += sentiment_score / sentiment_idx
                            except ZeroDivisionError:
                                weighted_sentiment += 0.0

        sentiment_words[char]["sentiment_per_chapter"].append(weighted_sentiment)
    return sentiment_words

def restructured_data(data):
    """
    Function to restructure the data in a more convenient format
    :param data: The data to restructure
    :return: A list of dictionaries containing the data for each character to be stored in a JSON file
    """
    restructured_data = {}

    # Iterate over the chapters and characters
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

    # Extara the aggregated sentiment score for each character
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
    # Load the book
    book_text = load_book(book_path)
    # Get the book title
    book_title = os.path.basename(book_path).replace("_clean.txt", "")
    # Split the book into chapters
    chapters = split_book_by_chapter(book_text, nlp)
    # Extract the entities
    get_entities = [perform_ner(chapter[1]) for chapter in chapters]
    # Flatten the list
    list_of_characters = [char for lst in get_entities for char in lst]
    # Get the main characters
    main_characters = list(count_entities(list_of_characters).keys())
    scores = {}
    # Iterate over the chapters
    for chapter in chapters:
        if chapter[0] not in scores:
            scores[chapter[0]] = []
        # Extract the sentiment scores for each character
        get_sentiment = character_sentiment_per_chapter(chapter[1], main_characters)
        scores[chapter[0]].extend(get_sentiment.items())
    # Save the data in a JSON file
    result = json.dumps(restructured_data(scores), ensure_ascii=False, indent=2)
    file_name = f"{book_title}_Sentiment.json"
    output_file_path = os.path.join(directory_path, file_name)
    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json_file.write(result)


# Run the main function
if __name__ == "__main__":
    main()
