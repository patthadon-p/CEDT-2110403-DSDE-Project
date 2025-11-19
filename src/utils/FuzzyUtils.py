# Import necessary modules
import re

from rapidfuzz import process


def normalize(
    text: str | None,
    prefix_sub: list[str] | None = None,
) -> str | None:
    if text is None:
        return None

    prefix_sub = prefix_sub or ["บาง", "คลอง"]

    t = str(text)
    t = re.sub(r"\s+", " ", t).strip()

    for prefix in prefix_sub:
        t = re.sub(rf"({prefix})\1+", r"\1", t)

    return t


def fuzzy_match(
    text: str | None, choices: list[str], cache: dict[str, str]
) -> str | None:
    if text in cache:
        return cache[text]

    if text is None or text == "":
        return text

    match = process.extractOne(text, choices, score_cutoff=60)
    result = match[0] if match else text
    cache[text] = result
    return result
