from src.model.geo_sample import GEOSample


def get_gender(geo_sample: GEOSample) -> str:
    """
    Returns the sex of the organism the sample was taken from or None
    if the sex cannot be determined.
    :geo_sample: GEO Sample (GSM) to get the sex of.
    :return: "male", "female" or None
    """
    sex = geo_sample.characteristics.get(
        "sex") or geo_sample.characteristics.get("gender")
    if not sex:
        return None
    sex = sex.strip().lower()
    if sex in ["male", "m"]:
        return "male"
    elif sex in ["female", "f"]:
        return "female"
    return None
