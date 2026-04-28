from __future__ import annotations

import json
import os

DICTIONARY_PATH = os.path.join("assets", "phonemes", "multilingual_basic.json")


def load_dictionary() -> dict:
    with open(DICTIONARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def lyrics_to_phonemes(lyric: str, language: str = "en") -> list[str]:
    dictionary = load_dictionary()
    lang_dict = dictionary.get(language, {})
    token = lyric.strip().lower()
    if token in lang_dict:
        return lang_dict[token]

    phones: list[str] = []
    for char in token:
        phones.extend(lang_dict.get(char, [char]))
    return phones or ["la"]
