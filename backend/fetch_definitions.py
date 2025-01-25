#!/usr/bin/env python3
"""Functions for fetching word definitions from Wiktionary.

This script reads words from existing wordlist files and fetches their definitions
from Wiktionary using batch queries for efficiency.

Usage:
    python3 fetch_definitions.py [-l LANGUAGE] [-n MAX_WORDS]
"""

import sys
import logging
import requests
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Rate limiting parameters
REQUEST_DELAY = 0.1  # 100ms between requests to be nice to the API

WordDefs = Dict[str, Optional[List[str]]]

def fetch_definitions_batch(words: List[str], language: str) -> WordDefs:
    """Fetch definitions for multiple words from Wiktionary using batch queries.
    
    Args:
        words: List of words to fetch definitions for
        language: Language code (e.g., "english", "spanish")
    
    Returns:
        Dictionary mapping words to their definitions (None if not found)
    """
    try:
        # Add delay for rate limiting
        time.sleep(REQUEST_DELAY)
        
        # Join words with | for batch query
        titles = '|'.join(words)
        
        params = {
            "action": "query",
            "titles": titles,
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "formatversion": "2",  # Use newer format
            "rvslots": "main"  # Required for newer format
        }

        response = requests.get(
            "https://en.wiktionary.org/w/api.php", params=params
        )
        response.raise_for_status()
        data = response.json()

        # Process batch response
        results = {}
        if "query" in data and "pages" in data["query"]:
            for page in data["query"]["pages"]:
                word = page["title"]
                if "missing" in page:
                    logging.debug(f"No content found for word: {word}")
                    results[word] = None
                    continue

                if "revisions" not in page:
                    logging.debug(f"No revisions found for word: {word}")
                    results[word] = None
                    continue

                content = page["revisions"][0]["slots"]["main"]["content"]
                
                # First check common words
                definitions = None
                if language.lower() == 'spanish':
                    common_meanings = {
                        'de': 'Of, from, or belonging to something or someone',
                        'en': 'In, on, or at a location or time',
                        'a': 'To, at, or towards a destination or recipient',
                        'por': 'For, by, or through something or someone',
                        'para': (
                            'For, in order to, or intended for someone or something'
                        ),
                        'con': 'With or along with someone or something',
                        'sin': 'Without or lacking something',
                        'que': (
                            'That, which, or who; used to connect clauses or '
                            'introduce subordinate clauses'
                        ),
                        'y': (
                            'And; used to connect words, phrases, clauses, or '
                            'sentences'
                        ),
                        'el': 'The; masculine singular definite article',
                        'la': 'The; feminine singular definite article',
                        'los': 'The; masculine plural definite article',
                        'las': 'The; feminine plural definite article',
                        'un': 'A or an; masculine singular indefinite article',
                        'una': 'A or an; feminine singular indefinite article',
                        'no': 'Not; used to express negation, denial, or refusal',
                        'sí': 'Yes; used to express affirmation or agreement',
                        'lo': 'The; neuter definite article used with adjectives',
                        'mi': 'My; first-person singular possessive adjective',
                        'tu': 'Your; second-person singular possessive adjective',
                        'su': (
                            'His, her, its, or their; third-person possessive '
                            'adjective'
                        )
                    }
                    if word.lower() in common_meanings:
                        definitions = [common_meanings[word.lower()]]
                elif language.lower() == 'english' and len(word) <= 3:
                    common_meanings = {
                        'the': 'The definite article used to indicate specific nouns',
                        'of': 'Expressing the relationship between a part and a whole',
                        'and': 'Used to connect words, phrases, clauses, or sentences',
                        'to': 'Expressing motion or direction toward a point',
                        'in': 'Located inside or within something',
                        'is': 'Third-person singular present of be',
                        'it': 'Third-person singular neuter pronoun',
                        'for': 'Intended to belong to or be used in connection with',
                        'as': 'Used for comparisons',
                        'on': 'Physically in contact with and supported by',
                        'at': 'Indicating location or position',
                        'by': 'Identifying the agent performing an action'
                    }
                    if word.lower() in common_meanings:
                        definitions = [common_meanings[word.lower()]]
                
                if not definitions:
                    # Find the language section
                    lang_title = language.title()
                    lang_pattern = rf"={{{2,3}}}\s*{lang_title}\s*={{{2,3}}}"
                    lang_sections = re.split(lang_pattern, content)
                    
                    if len(lang_sections) < 2:
                        logging.debug(f"No {language} section found for word: {word}")
                        results[word] = None
                        continue
                    
                    # Get content up to next language section
                    lang_content = lang_sections[1]
                    next_lang = re.search(r"={2,3}\s*[A-Z]", lang_content)
                    if next_lang:
                        lang_content = lang_content[:next_lang.start()]
                    
                    # Extract definitions
                    definitions = []
                    
                    # Look for definitions in various formats
                    def_patterns = [
                        r"# ([^\n]+)",  # Numbered definitions
                        r"\* ([^\n]+)",  # Bullet points
                        r"\{\{lb\|[^}]+\}\}\s*([^\n]+)",  # Label templates
                        r"\{\{def\|([^}]+)\}\}",  # Definition templates
                        r"\{\{gloss\|([^}]+)\}\}",  # Gloss templates
                        r"\{\{sense\|([^}]+)\}\}",  # Sense templates
                    ]
                    
                    for pattern in def_patterns:
                        matches = re.finditer(pattern, lang_content)
                        for match in matches:
                            definition = match.group(1).strip()
                            # Clean up wiki markup
                            # Clean up wiki markup
                            wiki_patterns = [
                                (r"\{\{[^}]+\}\}", ""),  # Remove templates
                                (r"\[\[([^]|]+\|)?([^]]+)\]\]", r"\2"),  # Links
                                (r"''([^']+)''", r"\1"),  # Italics
                                (r"#\s*", ""),  # List markers
                            ]
                            for pattern, repl in wiki_patterns:
                                definition = re.sub(pattern, repl, definition)
                            
                            if definition and len(definition) >= 10:
                                definitions.append(definition)
                                if len(definitions) >= 3:
                                    break
                        if definitions:
                            break
                
                results[word] = definitions if definitions else None

        return results

    except Exception as e:
        logging.error(f"Error fetching definitions batch: {str(e)}")
        return {}

def read_wordlist(language: str) -> List[str]:
    """Read words from a wordlist file.
    
    Args:
        language: Language name (e.g., "english", "spanish")
    
    Returns:
        List of words from the file
    """
    try:
        wordlists_dir = Path(__file__).parent / "wordlists"
        wordlist_file = wordlists_dir / f"{language}.txt"
        
        if not wordlist_file.exists():
            logging.error(f"Wordlist file not found: {wordlist_file}")
            return []
        
        words = []
        with open(wordlist_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                word = line.strip().split('\t')[0]
                if word:
                    words.append(word)
        
        return words
    except Exception as e:
        logging.error(f"Error reading wordlist: {str(e)}")
        return []

def save_definitions(words_with_defs: WordDefs, language: str) -> bool:
    """Save word definitions to a file.
    
    Args:
        words_with_defs: Dictionary mapping words to their definitions
        language: Language name (used for filename)
    
    Returns:
        True if save successful, False otherwise
    """
    try:
        wordlists_dir = Path(__file__).parent / "wordlists"
        wordlists_dir.mkdir(exist_ok=True)
        
        output_file = wordlists_dir / f"{language}_defs.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {language.title()} word list\n")
            for word, definitions in words_with_defs.items():
                if definitions:
                    definition_str = ' | '.join(definitions)
                    f.write(f"{word}\t{definition_str}\n")
                else:
                    f.write(f"{word}\n")
        return True
    except Exception as e:
        logging.error(f"Error saving definitions: {str(e)}")
        return False

def main():
    """Fetch and save definitions for words in wordlist files."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch word definitions from Wiktionary"
    )
    parser.add_argument(
        "-n",
        "--max-words",
        type=int,
        default=10000,
        help="Maximum number of words to process (default: 10000)",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        choices=["english", "spanish", "french", "german", "italian"],
        help="Language to process (default: all available)",
    )
    args = parser.parse_args()

    # Get list of languages to process
    wordlists_dir = Path(__file__).parent / "wordlists"
    if args.language:
        languages = [args.language]
    else:
        languages = [f.stem for f in wordlists_dir.glob("*.txt")]

    for language in languages:
        logging.info(f"Processing {language} words...")
        
        # Read words from wordlist
        words = read_wordlist(language)
        if not words:
            continue
        
        # Process words in batches
        batch_size = 50  # Maximum titles per request
        processed_words = {}
        
        for i in range(0, min(len(words), args.max_words), batch_size):
            batch = words[i:i + batch_size]
            
            # Fetch definitions for the batch
            definitions = fetch_definitions_batch(batch, language)
            processed_words.update(definitions)
            
            total_words = min(len(words), args.max_words)
            msg = f"Processed {len(processed_words)}/{total_words} words"
            logging.info(msg)
        
        # Save results
        if processed_words:
            if save_definitions(processed_words, language):
                num_words = len(processed_words)
                logging.info(f"Successfully saved {num_words} words with definitions")
            else:
                logging.error(f"Failed to save {language} definitions")
        else:
            logging.error(f"No definitions found for {language} words")

    return 0

if __name__ == "__main__":
    sys.exit(main())