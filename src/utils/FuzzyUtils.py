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
fuzzy_match
    Performs approximate string matching against a list of known choices
    and caches the results.
"""

# Import necessary modules
import re

from rapidfuzz import process


def normalize(
    text: str | None,
    prefix_sub: list[str] | None = None,
) -> str | None:
    """
    Cleans and standardizes an input string.

    This function performs two main steps:
    1. Removes all excessive whitespace and strips leading/trailing spaces.
    2. Replaces repeated occurrences of common prefixes (e.g., 'บางบาง'
        or 'คลองคลอง') with a single instance of the prefix.

    Parameters
    ----------
    text : str or None
        The input string to be normalized. Returns None if input is None.
    prefix_sub : list of str or None, optional
        A list of prefixes to be checked and reduced if they appear
        consecutively more than once. **If None, defaults to ["บาง", "คลอง"].**

    Returns
    -------
    str or None
        The normalized string, or None if the input was None.

    Examples
    --------
    >>> normalize("  บางบางนา ")
    'บางนา'
    >>> normalize("คลอง คลองตัน")
    'คลองตัน'
    >>> normalize("   Hello World  ", prefix_sub=['World'])
    'Hello World'
    """

    if text is None:
        return None

    prefix_sub = prefix_sub or ["บาง", "คลอง"]

    t = str(text)
    t = re.sub(r"\s+", " ", t).strip()

    for prefix in prefix_sub:
        t = re.sub(rf"({prefix})\1+", r"\1", t)

    return t


def fuzzy_match(
    text: str | None, choices: list[str], cache: dict[str, str], cutoff: float = 60
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

    match = process.extractOne(text, choices, score_cutoff=cutoff)
    result = match[0] if match else text
    cache[text] = result
    return result
