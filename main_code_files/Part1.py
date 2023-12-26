"""
PCL 1 Fall Semester 2023 - Course Project
Part 1: Named Entity Recognition using spaCy
Students: Asher Slater & Daria Stetsenko
"""
# --- Imports ---
import os
import re
import json
import spacy
import nltk
import sys
# --- You may add other imports here ---

def load_book(book_path:str):
    """
    Function to load a book from a text file
    :param book_path: Path to the book text file
    :return: The book text as a string 
    """
    
    with open(book_path, 'r', encoding='utf-8') as book_file:
        book_text = book_file.read()
    return book_text


CHAPTERS = ["Chapter", "CHAPTER", "ACT"]

def split_book_by_chapter(cleaned_text, spacy_model):
    """
    Split the book into chapters
    :param cleaned_text: the text of the book with the headers and footers removed
    :return: a list of chapters
    """
    for title in CHAPTERS:
        cleaned_text = cleaned_text.replace(title, "Chapter")
    chapters = re.split(r'\bChapter\b', cleaned_text)
    add_chapter = []

    for c in chapters:
        new_chapter = "Chapter " + c[1:]
        add_chapter.append(new_chapter)

    # Convert each chapter to a spaCy document for further NER and sentences extraction
    chapters = [spacy_model(chapter) for chapter in add_chapter]

    return chapters


def perform_ner(chapters):
    """
    Function to perform named entity recognition on a text
    :param text: The text to perform NER on
    :param spacy_model: The spaCy model to use for NER
    :return: A list of named entities
    """
    
    entities = []
    for chapter in chapters:
        for ent in chapter.ents:
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
        # Choose only those characters that appear more than 5 times
        if count > 5:
            entities_tuples[word] = count

    return entities_tuples


def extract_chapter_numbers(text):
    """
    Extracts chapter numbers from the text
    """
    match = re.search(r'\b([IVXLCDM]+|\d+(\.\d+)?)\.', text)
    if match:
        return match.group(1)
    return None


def extract_character_lines_with_chapters(chapters, characters):
    """
    Extracts lines where a character is mentioned and a chapter where a line appears
    :param chapters: list of chapters
    :param characters: list of characters
    """
    current_chapter = None
    character_lines = {}

    for chapter in chapters:
        for line in chapter.sents:
            line = line.text.strip()
            if line.startswith("Chapter "):
                current_chapter = extract_chapter_numbers(line)
                continue

            for character in characters:
                if character in line:
                    # Check if the character already has an entry for the current sentence
                    existing_entry = next((entry for entry in character_lines.get(character, []) if entry[1] == line), None)

                    if existing_entry is None:
                        if character not in character_lines:
                            character_lines[character] = []
                        character_lines[character].append((current_chapter, line.replace("\n", "")))
    return character_lines


from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import math

def extract_features(character_sentences: dict) -> list:
    """
    Calculates the TF-IDF score for each entity
    :param character_sentences: dictionary containing characters and corresponding sentences, where they appear
    :return: list of TF-IDF vectors to use for clustering
    """
    # Tokenize and preprocess the sentences
    stop_words = set(stopwords.words('english'))

    def preprocess_sentence(sentence):
        # Remove punctuation, tokenize, and remove stop words
        tokens = re.sub(r'[^\w\s]', '', sentence)
        tokens = word_tokenize(tokens.lower())
        tokens = [word for word in tokens if word.isalpha()]
        tokens = [word for word in tokens if word not in stop_words]
        return tokens

    document_frequency = {}
    total_documents = len(character_sentences)

    # Count document frequency for each term
    for _, sentences in character_sentences.items():
        term_set = set()
        for _, sent in sentences:
            terms = preprocess_sentence(sent)
            term_set.update(terms)
        for term in term_set:
            document_frequency[term] = document_frequency.get(term, 0) + 1

    # Calculate TF-IDF score for each term
    tfidf_vectors = []
    term_list = list(document_frequency.keys())

    for _, sentences in character_sentences.items():
        term_frequency = {}
        terms_in_character = 0

        for _, sentence in sentences:
            terms = preprocess_sentence(sentence)
            terms_in_character += len(terms)

            for term in terms:
                term_frequency[term] = term_frequency.get(term, 0) + 1

        tfidf_vector = [term_frequency.get(term, 0) / terms_in_character * math.log(total_documents / (1 + document_frequency[term]))
                        for term in term_list]
        tfidf_vectors.append(tfidf_vector)

    return tfidf_vectors, term_list


def clustering_aliases(entities:list, character_sentences:dict):
    # Perform the TF-IDF feature extraction
    features, term_list = extract_features(character_sentences)

    # Create a KMeansClusterer object with the number of clusters, cosine distance, and 10 repeats
    n_clusters = len(set(entities))
    kclusterer = nltk.cluster.KMeansClusterer(n_clusters, distance=nltk.cluster.util.cosine_distance, repeats=10)

    # Cluster the feature vectors and assign a cluster label to each entity
    clusters = kclusterer.cluster(features, assign_clusters=True)

    # Create a dictionary with the cluster label as key and the entities in the cluster as values
    cluster_dict = {}
    for i, cluster in enumerate(clusters):
        if cluster not in cluster_dict:
            cluster_dict[cluster] = []
        cluster_dict[cluster].append(entities[i])

    # Convert the dictionary values to lists when keys are equal
    result_dict = {}
    for key, value in cluster_dict.items():
        if len(value) > 1:
            result_dict[key] = value
        else:
            result_dict[key] = value[0]

    return result_dict


def find_start_end_indices(substring, full_text):
    """
    Find the start and end indices of the character's name in the sentence
    """
    
    start_index = full_text.find(substring)
    end_index = start_index + len(substring)
    return start_index, end_index

def create_json_structure(characters_frequency, characters_aliases, characters_occurrences):
    """
    Creates a JSON structure from the extracted information
    :param characters_frequency: dictionary with characters and their frequency
    :param characters_aliases: dictionary with characters and their aliases
    :param characters_occurrences: dictionary with characters as keys, and (chaper, sentence) tuples as values
    """
    # Create a dictionary with the character's name as key and a list of their aliases as values
    get_aliases = {}
    for name in characters_occurrences.keys():
        for _, value in characters_aliases.items():
            if name in value:
                get_aliases[name] = value

    # Create a JSON structure
    json_structure = {"main_characters": []}

    for character in characters_frequency:
        aliases = get_aliases.get(character, [])
        occurrences = characters_occurrences.get(character, [])
        frequency = characters_frequency.get(character, 0)

        character_data = {
            "name": character,
            "aliases": aliases,
            "frequency": frequency,
            "occurrences": []
        }

        for chapter, context in occurrences:
            start_index, end_index = find_start_end_indices(character, context)

            occurrence_data = {
                "sentence": context,
                "chapter": chapter,
                "position": {"start": start_index, "end": end_index}
            }

            character_data["occurrences"].append(occurrence_data)

        json_structure["main_characters"].append(character_data)

    return json_structure

def write_as_json(book_path, resulting_json, directory_path):
    """
    Write the data to a JSON file.
    param book_path: path to the book text file
    param resulting_json: resulting JSON structure
    param directory_path: path to the directory where the JSON file should be stored
    """
    # Get the book title from the file path
    book_title = os.path.basename(book_path).replace("_clean.txt", "")
    result = json.dumps(resulting_json, ensure_ascii=False, indent=2)

    # Create the output file path
    file_name = f"{book_title}_MainCharacters_NER.json"
    output_file_path = os.path.join(directory_path, file_name)

    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json_file.write(result)


# Main Function
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 Part1.py <path_to_the_book> <path_to_store_json>")
        sys.exit(1)

    # Load the spaCy model
    nlp = spacy.load("en_core_web_lg")
    
    # Load the book
    book_path = sys.argv[1]
    # Get the path to the directory where the JSON file should be stored
    directory_path = sys.argv[2]
    # Load a book's text 
    book_text = load_book(book_path)
    chapters = [chapter for chapter in split_book_by_chapter(book_text, nlp) if len(chapter) > 1000]

    # Characters in the book
    extract_entities = perform_ner(chapters)
    # Characters frequency in the book
    characters_frequency = count_entities(extract_entities)
    # Get the most frequent characters
    main_characters = list(characters_frequency.keys())

    # Characters with their lines and chapters
    characters_occurrences = extract_character_lines_with_chapters(chapters, main_characters)
    # Characters with their aliases
    characters_aliases = clustering_aliases(main_characters, characters_occurrences)

    resulting_json = create_json_structure(characters_frequency, characters_aliases, characters_occurrences)
    write_as_json(book_path, resulting_json, directory_path)

# Run the main function
if __name__ == "__main__":
    main()
