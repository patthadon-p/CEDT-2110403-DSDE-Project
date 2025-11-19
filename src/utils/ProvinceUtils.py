"""
Data loading and standardization utility for province names.

This module provides a function to load a mapping of acceptable province
name variants and transform it into a quick-lookup whitelist dictionary.
This is primarily used for standardizing inconsistent text inputs to a
single official name.

Functions
---------
load_province_whitelist
    Loads a JSON mapping of province names and generates a dictionary
    where variant names map back to a single standard name.
"""

# Import necessary modules
import json

# Import utility functions
from .ConfigUtils import read_config_path


def load_province_whitelist(filepath: str = "") -> dict:
    """
    Loads a province name mapping and creates a reverse-lookup whitelist dictionary.

    The function loads a JSON file expected to be structured as a dictionary
    where keys are standard province names (str) and values are lists of
    acceptable spelling variants (list[str]). It inverts this structure
    to create a dictionary where every variant name maps directly to its
    corresponding standard name.

    Parameters
    ----------
    filepath : str, optional
        The absolute path to the JSON file containing the province name mapping.
        If provided, this path overrides the path specified in the config file
        under 'province_whitelist_path'. Default is "".

    Returns
    -------
    dict of {str: str}
        A dictionary where each variant province name (key) maps to its
        official standard name (value).

    Raises
    ------
    FileNotFoundError
        If the resolved file path does not exist.
    JSONDecodeError
        If the file content is not valid JSON.
        
    See Also
    --------
    .ConfigUtils.read_config_path : The utility function used to resolve the path.

    Examples
    --------
    If the JSON file contains:
    {'Standard Name A': ['Variant 1', 'Variant A'], 'Standard Name B': ['Var B']}

    The returned dictionary will be:
    {'Variant 1': 'Standard Name A', 'Variant A': 'Standard Name A', 'Var B': 'Standard Name B'}
    """

    filepath = read_config_path(key="province_whitelist_path", filepath=filepath)

    with open(filepath, encoding="utf-8") as file:
        provinces = json.load(file)

    whitelist = {}
    for standard_name, variants in provinces.items():
        for name in variants:
            whitelist[name] = standard_name

    return whitelist
