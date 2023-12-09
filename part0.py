"""
PCL 1 Fall Semester 2023 - Course Project
Part 0: Book Selection
Students: <person 1>, <person 2>
"""

# --- Imports ---
import os
import re
import json
import sys
# --- Don't add other imports here ---

NER_CARROLL = ["Alice", "Wonderland", "Rabbit", "Hatter", "Cat", "Queen", "King", "Turtle", "Duchess", "Caterpillar"]
NER_CARROLL = [x.lower() for x in NER_CARROLL]

NER_SHAKESPEAR = ["BENEDICK", 
"LEONATO",
"ANTONIO",  
"BALTHASAR",
"BORACHIO",
"CONRADE",
"DOGBERRY",
"VERGES",
"FRIAR",
"FRANCIS",
"Sexton",
"Boy",
"HERO",
"BEATRICE",
"MARGARET",
"URSULA"]
NER_SHAKESPEAR = [x.lower() for x in NER_SHAKESPEAR]

NER_WILDE = ["John", "Worthing",
"Algernon", "Moncrieff",
"Chasuble",
"Canon",
"Merriman",
"Butler",
"Lane",
"Manservant",
"Bracknell",
"Gwendolen",
"Fairfax",
"Cardew",
"Cecily",
"Prism",
"Governess"]
NER_WILDE = [x.lower() for x in NER_WILDE]

SENT_CARROL = ["joy",
"happy",
"amusing",
"loving",
"funny",
"dear",
"rude",
"angrily",
"angry",
"dull",
"cry",
"sadly",
"sad",
]
SENT_CARROL = [x.lower() for x in SENT_CARROL]

SENT_SHAKESPEAR = ["joy",
"love",
"loving",
"happy",
"modest",
"kindness",
"mock",
"hate",
"torture",
"death",
"bastard"]
SENT_SHAKESPEAR = [x.lower() for x in SENT_SHAKESPEAR]

SENT_WILDE = ["love",
"loving",
"interesting",
"darling",
"attractive",
"unpleasant",
"hate",
"vulgar",
"terrible",
"painful"]
SENT_WILDE = [x.lower() for x in SENT_WILDE]

def count_words(text:list, words:list)->dict:
    """
    Counts the number of times each word appears in the text
    :param text: list of words
    :param words: list of words to count
    :return: dictionary with words as keys and number of times they appear in the text as values
    """

    words_count_per_text = {}

    for word in text:
        if word in words:
            if word not in words_count_per_text:
                words_count_per_text[word] = 1
            else:
                words_count_per_text[word] += 1

    return words_count_per_text

def read_files(directory)->dict:
    """
    Reads all the files in the directory and counts the number of times each word appears in each text
    :param directory: directory with the texts
    :param count_words: function to count the words
    :return: sorted dictionary with a number of the text and the counts of each word 
    """

    texts_vocab = {}
    number_pattern = re.compile(r'\d+')

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r') as f:
                text = f.read().lower()
                text = re.sub(r'[^\w\s]', '', text).split()
                number = int("".join(number_pattern.findall(filename)))
                texts_vocab[number] = text

    return {key: texts_vocab[key] for key in sorted(texts_vocab)}

def json_conversion(data:dict, words:list, count_words=count_words)->dict:
    """
    Convert the data to separate JSON strings for each chapter.
    """
    chapter_json_strings = {}

    for key, value in data.items():

        # Calculate word counts for each chapter
        chapter_counts = count_words(value, words)

        # Format data for the current chapter
        formatted_data = {f"Chapter {key}": chapter_counts}

        # Convert the formatted data to JSON format
        json_data = json.dumps(formatted_data, indent=2)

        # Store the JSON string for the current chapter
        chapter_json_strings[key] = json_data

    return chapter_json_strings


def write_as_json(data, file_path, chapters_path):
    """
    Write the data to a JSON file.
    """
    # Get the book title from the file path
    book_title = os.path.splitext(os.path.basename(file_path))[0]
    last_part = os.path.splitext(os.path.basename(chapters_path))[0]

    for chapter, json_string in data.items():

        # Format the chapter name
        chapter_name = f"Chapter{chapter}"

        # Create the output file path
        output_file_path = f"{book_title}_{chapter_name}_{last_part}.json"

        with open(output_file_path, "w") as f:
            f.write(json_string)


def main():
    """
    Main function.
    """
    # Dictionary with the words to count for each book (NER)
    words_list_ner = {'Importance_of_being_earnest': NER_WILDE,
                      'Alice_in_wonderland': NER_CARROLL,
                      'Much_ado_about_nothing': NER_SHAKESPEAR}

    # Dictionary with the words to count for each book (Sentiment)
    words_list_sentiment = {'Importance_of_being_earnest': SENT_WILDE,
                            'Alice_in_wonderland': SENT_CARROL,
                            'Much_ado_about_nothing': SENT_SHAKESPEAR}
    # Check if the number of arguments is correct
    if len(sys.argv) != 4:
        print("Usage: python3 part0.py ner_or_sentiment <path_to_the_book> <path_to_the_chapters>")
        sys.exit(1)
    # Get the book path
    book_path = sys.argv[2]
    # get the book title
    book_title = os.path.splitext(os.path.basename(book_path))[0]
    # Get the chapters path
    chapters_path = sys.argv[3]
    # Define which words to count
    ner_or_sentiment = sys.argv[1]

    if "ner" in ner_or_sentiment:
        words = words_list_ner[book_title]

    elif "sentiment" in ner_or_sentiment:
        words = words_list_sentiment[book_title]
    # Read the files
    file = read_files(chapters_path)
    # Convert the data to JSON
    json_converted_file = json_conversion(file, words=words)
    # Write the data to a JSON file
    write_as_json(json_converted_file, book_path, chapters_path)

# This is the standard boilerplate that calls the main() function when the program is executed.
if __name__ == '__main__':
    main()
