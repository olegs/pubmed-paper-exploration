from typing import Tuple
import re
from src.model.geo_sample import GEOSample
from src.parsing.age.extract_age import extract_age, normalize_to_years


def is_age_key(key: str) -> bool:
    # We disqualify keys that contain the word "at" because then the age
    # becomes context-dependant.
    return ("age" in key.split(" ") or "age" in key.split("_")) and not "at" in key


def get_age_unit(text: str) -> str | None:
    """
    Extracts the age unit from a string if it is present.

    :param text: Text to extract the age unit from.
    :return: Age unit or None if there is no age unit. 
    """
    match = re.search(
        r'[\s_]+\(?(year|yr|month|mo|week|wk|w|day|d)s?', text)
    if match:
        return match.group(1)
    return None


def get_age(sample: GEOSample) -> float | Tuple[float, float] | None:
    """
    Returns the age or age range of the sample, or None if the age is 
    qualitative or not available.
    """
    age_keys = list(filter(is_age_key, sample.characteristics.keys()))
    age_is_not_available = len(age_keys) == 0
    if age_is_not_available:
        return None

    age_key = age_keys[0]
    unit = get_age_unit(age_key)
    age_str = sample.characteristics[age_key]
    age = extract_age(age_str, normalize=not unit)

    if not unit:
        return age

    if isinstance(age, tuple):
        return (normalize_to_years(age[0], unit), normalize_to_years(age[1], unit))

    return normalize_to_years(age, unit)
