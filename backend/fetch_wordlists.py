#!/usr/bin/env python3
"""Functions for fetching word frequency lists from Wiktionary.

Currently supported languages:
- English (Wikipedia 2016 frequency list)
- Spanish (Spanish Wikipedia frequency list)

Future languages to be added:
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Arabic (ar)
- Vietnamese (vi)
"""

import sys
import logging
import requests
import re
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Rate limiting parameters
REQUEST_DELAY = 0.1  # 100ms between requests to be nice to the API


def fetch_wiktionary_words(
    language: str,
    config: dict,
    num_words: int,
) -> Optional[List[str]]:
    """Fetch word frequency list from Wiktionary.

    Args:
        language: Language name (e.g., "english")
        config: Language configuration containing pages and sections
        num_words: Maximum number of words to fetch

    Returns:
        List of words, or None if fetch fails
    """
    try:
        all_words = []
        seen_words = set()  # Track unique words across all pages

        # Handle both single page_path and multiple pages configurations
        pages = config.get("pages", [config.get("page_path")])
        sections = config.get("sections", [])

        for page in pages:
            if len(all_words) >= num_words:
                break

            for section in sections:
                params = {
                    "action": "parse",
                    "page": page,
                    "section": section,
                    "format": "json",
                    "prop": "text",
                }

                response = requests.get(
                    "https://en.wiktionary.org/w/api.php", params=params
                )
                response.raise_for_status()
                data = response.json()

                if "parse" not in data:
                    logging.error(
                        f"No content found in {language} frequency list "
                        f"page {page} section {section}"
                    )
                    continue

                # Extract words from the HTML content
                html_content = data["parse"]["text"]["*"]

                if language == "chinese":
                    # Extract Simplified Chinese characters from spans
                    word_pattern = (
                        r'<span class="Hans"[^>]*>'
                        r'<a[^>]+?title="([^"#]+)(?:#[^"]*)?">([^<]+)</a>'
                        r"</span>"
                    )
                else:
                    # Extract words from links (format: <a title="word">word</a>)
                    word_pattern = r'<a[^>]+?title="([^"#]+)(?:#[^"]*)?">([^<]+)</a>'

                for match in re.finditer(word_pattern, html_content):
                    title, word = match.groups()
                    # Check word validity: non-empty and not already seen
                    if word and word not in seen_words:
                        seen_words.add(word)
                        all_words.append(word)
                        if len(all_words) >= num_words:
                            break

                if len(all_words) >= num_words:
                    break

        if not all_words:
            logging.error(f"No words found in {language} frequency list")
            return None

        return all_words[:num_words]

    except Exception as e:
        logging.error(f"Error fetching {language} frequency list: {str(e)}")
        return None


def save_wordlist(words: List[str], language: str) -> bool:
    """Save word list to a file.

    Args:
        words: List of words to save
        language: Language name (used for filename, e.g., "english.txt")

    Returns:
        True if save successful, False otherwise
    """
    try:
        wordlists_dir = Path(__file__).parent / "wordlists"
        wordlists_dir.mkdir(exist_ok=True)

        output_file = wordlists_dir / f"{language}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {language.title()} word list\n")
            for word in words:
                f.write(f"{word}\n")
        return True
    except Exception as e:
        logging.error(f"Error saving {language} word list: {str(e)}")
        return False


def main():
    """Fetch and save word frequency lists."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch word frequency lists from Wiktionary"
    )
    parser.add_argument(
        "-n",
        "--num-words",
        type=int,
        default=10000,
        help="Number of words to fetch per language (default: 10000)",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        choices=["english", "spanish", "french", "german", "italian", "chinese"],
        help="Specific language to fetch (if not specified, fetches all languages)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Process all configured languages (default: True)",
    )
    args = parser.parse_args()

    # Language configurations
    configs = {
        "english": {
            "page_path": "Wiktionary:Frequency_lists/English/Wikipedia_(2016)",
            # Sections 1-1000 through 9001-10000
            "sections": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },
        "spanish": {
            # Spanish frequency lists in 1000-word segments
            "pages": [
                "Wiktionary:Frequency_lists/Spanish1000",  # 1-1000
                "Wiktionary:Frequency_lists/Spanish1001-2000",  # 1001-2000
                "Wiktionary:Frequency_lists/Spanish2001-3000",  # 2001-3000
                "Wiktionary:Frequency_lists/Spanish3001-4000",  # 3001-4000
                "Wiktionary:Frequency_lists/Spanish4001-5000",  # 4001-5000
                "Wiktionary:Frequency_lists/Spanish5001-6000",  # 5001-6000
                "Wiktionary:Frequency_lists/Spanish6001-7000",  # 6001-7000
                "Wiktionary:Frequency_lists/Spanish7001-8000",  # 7001-8000
                "Wiktionary:Frequency_lists/Spanish8001-9000",  # 8001-9000
                "Wiktionary:Frequency_lists/Spanish9001-10000",  # 9001-10000
            ],
            "sections": ["0"],  # Main section containing the word list
        },
        "french": {
            "page_path": (
                "Wiktionary:Frequency_lists/French_wordlist_opensubtitles_5000"
            ),
            "sections": ["0"],  # Main section containing the word list
        },
        "german": {
            "page_path": "Wiktionary:Frequency_lists/German/Mixed_web_3M",
            # Sections 1-10 correspond to ranges 1-1000 through 9001-10000
            "sections": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },
        "italian": {
            "page_path": "Wiktionary:Frequency_lists/Italian50k",
            "sections": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },
        "chinese": {
            "pages": [
                "Appendix:Mandarin_Frequency_lists/1-1000",
                "Appendix:Mandarin_Frequency_lists/1001-2000",
                "Appendix:Mandarin_Frequency_lists/2001-3000",
                "Appendix:Mandarin_Frequency_lists/3001-4000",
                "Appendix:Mandarin_Frequency_lists/4001-5000",
                "Appendix:Mandarin_Frequency_lists/5001-6000",
                "Appendix:Mandarin_Frequency_lists/6001-7000",
                "Appendix:Mandarin_Frequency_lists/7001-8000",
                "Appendix:Mandarin_Frequency_lists/8001-9000",
                "Appendix:Mandarin_Frequency_lists/9001-10000",
            ],
            "sections": ["0"],  # Main section containing the word list
        },
    }

    # Determine which languages to process
    languages_to_process = []
    if args.language:
        languages_to_process = [args.language]
    elif args.all:
        languages_to_process = list(configs.keys())

    if not languages_to_process:
        logging.error("No languages specified to process")
        return 1

    success = True
    for language in languages_to_process:
        config = configs[language]
        logging.info(f"Fetching {language} frequency list...")
        words = fetch_wiktionary_words(language, config, args.num_words)

        if words:
            if save_wordlist(words, language):
                logging.info(f"Successfully saved {len(words)} {language} words")
            else:
                logging.error(f"Failed to save {language} word list")
                success = False
        else:
            logging.error(f"Failed to fetch {language} frequency list")
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
