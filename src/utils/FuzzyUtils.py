"""
String normalization and fuzzy matching utilities.

This module provides functions for cleaning, normalizing, and performing
approximate string matching on text data, typically used for standardizing
geographic or categorical names in a data science workflow.

Functions
---------
normalize
    Cleans and standardizes input strings by removing extra whitespace
    and correcting repeated prefixes.
scorer_with_prefix_bonus
    A rapidfuzz scorer function that applies a bonus score for matching prefixes.
fuzzy_match
    Performs approximate string matching against a list of known choices
    and caches the results.
"""

# Import necessary modules
import re

from rapidfuzz import fuzz, process


def normalize(
    text: str | None,
    prefix_sub: list[str] | None = None,
) -> str | None:
    """
    Cleans and standardizes an input string.

    This function performs two main steps:
    1. Removes all excessive whitespace and strips leading/trailing spaces.
    2. **Removes** all occurrences of common prefixes (e.g., 'บาง', 'คลอง').

    Parameters
    ----------
    text : str or None
        The input string to be normalized. Returns None if input is None.
    prefix_sub : list of str or None, optional
        A list of prefixes to be **removed** from the text. **If None, defaults to ["บาง", "คลอง"].**

    Returns
    -------
    str or None
        The normalized string, or None if the input was None.

    Examples
    --------
    >>> normalize("  บางบางนา ")
    'นา'  # Assuming "บาง" is in prefix_sub
    >>> normalize("คลอง คลองตัน")
    'ตัน' # Assuming "คลอง" is in prefix_sub
    >>> normalize("   Hello World  ", prefix_sub=['World'])
    'Hello ' # Only 'World' is removed, spaces remain. (Note: The first part of normalize handles multiple spaces)
    """

    if text is None:
        return None

    prefix_sub = prefix_sub or ["บาง", "คลอง"]

    t = str(text)
    t = re.sub(r"\s+", " ", t).strip()

    for prefix in prefix_sub:
        t = re.sub(rf"({prefix})+", "", t)

    return t


def scorer_with_prefix_bonus(
    query: str, choice: str, score_cutoff: float | None = None
) -> float:
    """
    Custom scorer function for rapidfuzz that applies a bonus score if the choice
    starts with the query (prefix match).

    The score calculated is the standard fuzz.ratio plus a fixed bonus (20)
    if the `choice` string starts with the `query` string. This helps prioritize
    results where the input is an exact prefix of the candidate choice.

    Parameters
    ----------
    query : str
        The query string being searched.
    choice : str
        The candidate string to match against.
    score_cutoff : float or None, optional
        Minimum score required. If provided, and the total score (base + bonus)
        is below this, 0 is returned immediately. Default is None.

    Returns
    -------
    float
        The calculated match score (base ratio + prefix bonus) or 0 if the cutoff condition is not met.
    """

    base_score = fuzz.ratio(query, choice)
    prefix_bonus = 20 if choice.startswith(query) else 0

    if score_cutoff is not None and base_score + prefix_bonus < score_cutoff:
        return 0

    return base_score + prefix_bonus


def fuzzy_match(
    text: str | None,
    choices: list[str],
    cache: dict[str, str],
    cutoff: float = 60,
    prefix_bonus: bool = False,
) -> str | None:
    """
    Performs fuzzy (approximate) matching using a score cutoff and caches the result.

    The function first checks the cache for an existing match for the input
    `text`. If not found, it uses the 'rapidfuzz' library's `extractOne`
    method to find the best match in the `choices` list. The resulting
    match is stored in the cache before being returned.

    Parameters
    ----------
    text : str or None
        The string to be matched against the choices.
    choices : list of str
        The list of standard strings (target values) to match against.
    cache : dict of {str: str}
        A mutable dictionary used to store and retrieve previously computed matches.
    cutoff : float, optional
        The minimum score (out of 100) required for a match to be accepted.
        If the best match score is below this value, the original `text` is returned.
        Default is 60.

    Returns
    -------
    str or None
        The matched string from `choices` if a match above the `cutoff`
        is found. **Otherwise, the original input `text` is returned** (including if `text` is None or empty).

    Notes
    -----
    The matching uses the default process.extractOne ratio (simple ratio)
    from `rapidfuzz`.
    """

    if text in cache:
        return cache[text]

    if text is None or text == "":
        return text

    scorer = scorer_with_prefix_bonus if prefix_bonus else fuzz.ratio

    match = process.extractOne(text, choices, score_cutoff=cutoff, scorer=scorer)
    result = match[0] if match else text
    cache[text] = result
    return result
