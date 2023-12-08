##############################################################################################################
##############################################################################################################
##### DO NOT MODIFY THIS CODE #####
# This code is to be used as is.

import os
import sys
import re

# Markers for the start and end of Project Gutenberg headers/footers
TEXT_START_MARKERS = frozenset((
    "*END*THE SMALL PRINT",
    "*** START OF THE PROJECT GUTENBERG",
    "*** START OF THIS PROJECT GUTENBERG",
    "This etext was prepared by",
    "E-text prepared by",
    "Produced by",
    "Distributed Proofreading Team",
    "Proofreading Team at http://www.pgdp.net",
    "http://gallica.bnf.fr)",
    "      http://archive.org/details/",
    "http://www.pgdp.net",
    "by The Internet Archive)",
    "by The Internet Archive/Canadian Libraries",
    "by The Internet Archive/American Libraries",
    "public domain material from the Internet Archive",
    "Internet Archive)",
    "Internet Archive/Canadian Libraries",
    "Internet Archive/American Libraries",
    "material from the Google Print project",
    "*END THE SMALL PRINT",
    "***START OF THE PROJECT GUTENBERG",
    "This etext was produced by",
    "*** START OF THE COPYRIGHTED",
    "The Project Gutenberg",
    "http://gutenberg.spiegel.de/ erreichbar.",
    "Project Runeberg publishes",
    "Beginning of this Project Gutenberg",
    "Project Gutenberg Online Distributed",
    "Gutenberg Online Distributed",
    "the Project Gutenberg Online Distributed",
    "Project Gutenberg TEI",
    "This eBook was prepared by",
    "http://gutenberg2000.de erreichbar.",
    "This Etext was prepared by",
    "This Project Gutenberg Etext was prepared by",
    "Gutenberg Distributed Proofreaders",
    "Project Gutenberg Distributed Proofreaders",
    "the Project Gutenberg Online Distributed Proofreading Team",
    "**The Project Gutenberg",
    "*SMALL PRINT!",
    "More information about this book is at the top of this file.",
    "tells you about restrictions in how the file may be used.",
    "l'authorization à les utilizer pour preparer ce texte.",
    "of the etext through OCR.",
    "*****These eBooks Were Prepared By Thousands of Volunteers!*****",
    "We need your donations more than ever!",
    " *** START OF THIS PROJECT GUTENBERG",
    "****     SMALL PRINT!",
    '["Small Print" V.',
    '      (http://www.ibiblio.org/gutenberg/',
    'and the Project Gutenberg Online Distributed Proofreading Team',
    'Mary Meehan, and the Project Gutenberg Online Distributed Proofreading',
    '                this Project Gutenberg edition.',
))


TEXT_END_MARKERS = frozenset((
    "*** END OF THE PROJECT GUTENBERG",
    "*** END OF THIS PROJECT GUTENBERG",
    "***END OF THE PROJECT GUTENBERG",
    "End of the Project Gutenberg",
    "End of The Project Gutenberg",
    "Ende dieses Project Gutenberg",
    "by Project Gutenberg",
    "End of Project Gutenberg",
    "End of this Project Gutenberg",
    "Ende dieses Projekt Gutenberg",
    "        ***END OF THE PROJECT GUTENBERG",
    "*** END OF THE COPYRIGHTED",
    "End of this is COPYRIGHTED",
    "Ende dieses Etextes ",
    "Ende dieses Project Gutenber",
    "Ende diese Project Gutenberg",
    "**This is a COPYRIGHTED Project Gutenberg Etext, Details Above**",
    "Fin de Project Gutenberg",
    "The Project Gutenberg Etext of ",
    "Ce document fut presente en lecture",
    "Ce document fut présenté en lecture",
    "More information about this book is at the top of this file.",
    "We need your donations more than ever!",
    "END OF PROJECT GUTENBERG",
    " End of the Project Gutenberg",
    " *** END OF THIS PROJECT GUTENBERG",
    "*** END OF THE PROJECT GUTENBERG EBOOK ALICE'S ADVENTURES IN WONDERLAND ***"
))


LEGALESE_START_MARKERS = frozenset(("<<THIS ELECTRONIC VERSION OF",))


LEGALESE_END_MARKERS = frozenset(("SERVICE THAT CHARGES FOR DOWNLOAD",))

def strip_headers(text):
    """Remove lines that are part of the Project Gutenberg header or footer."""
    lines = text.splitlines()
    sep = str(os.linesep)

    out = []
    i = 0
    footer_found = False
    ignore_section = False

    for line in lines:
        reset = False

        # remove illustration descriptions
        if "[Illustration]" in line:
            continue

        # Header removal
        if i <= 600 and any(line.startswith(token) for token in TEXT_START_MARKERS):
            reset = True

        if reset:
            out = []
            continue

        # Footer detection
        if any(token for token in TEXT_END_MARKERS if token in line):
            footer_found = True

        if footer_found:
            break

        # Legalese removal
        if any(line.startswith(token) for token in LEGALESE_START_MARKERS):
            ignore_section = True
            continue
        elif any(line.startswith(token) for token in LEGALESE_END_MARKERS):
            ignore_section = False
            continue

        if not ignore_section:
            out.append(line.rstrip(sep))
            i += 1

    return sep.join(out)

##############################################################################################################
##############################################################################################################

#### MODIFY HERE ####

CHAPTERS = ["Chapter", "CHAPTER", "ACT"]

def split_book_by_chapter(cleaned_text):
    """
    Split the book into chapters
    :param cleaned_text: the text of the book with the headers and footers removed
    :return: a list of chapters
    """
    for title in CHAPTERS:
        cleaned_text = cleaned_text.replace(title, "Chapter")
    chapters = re.split(r'\bChapter\b', cleaned_text)
    return chapters[1:]

def save_chapters(chapters, output_directory):
    """
    Save each chapter in a separate text file
    :param chapters: a list of chapters
    :param output_directory: the directory where the chapters will be saved
    :return: None
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Save each chapter in a separate text file
    i = 0
    for chapter in chapters:
        if len(chapter) < 1000:
            continue
        print(f'Saving chapter {i + 1}')
        filename = os.path.join(output_directory, f'chapter_{i + 1}.txt')
        i += 1
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(chapter)

def main():
    if len(sys.argv) != 2:
        print("Usage: python gutenberg_cleanup.py <path_to_book_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    book_title = os.path.basename(file_path).replace('.txt', '')
    # create the folder for the book
    os.makedirs(book_title, exist_ok=True)
    # create the subfolder for the chapters
    os.makedirs(os.path.join(book_title, 'chapters'), exist_ok=True)
    # read the book
    with open(file_path, "r") as f:
        text = f.read()
    # remove the headers and footers
    clean_text = strip_headers(text)
    # save the book without headers and footers
    with open(os.path.join(book_title, f"{book_title}.txt"), "w") as f:
        f.write(clean_text)
    # split the book into chapters
    chapters = split_book_by_chapter(clean_text)
    # save the chapters
    save_chapters(chapters, os.path.join(book_title, 'chapters'))

if __name__ == '__main__':
    main()