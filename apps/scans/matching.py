import difflib

from django.apps import apps as django_apps


def confidence_percent(query, candidate):
    """Return how similar two strings are, from 0 to 100."""
    return difflib.SequenceMatcher(
        None,
        query.lower().strip(),
        candidate.lower().strip(),
    ).ratio() * 100


def find_best_match(text):
    """Return (medicine, confidence) for the closest brand or generic name.

    The medicine model is loaded by app label so the scans feature does not
    import another feature app directly.
    """
    Medicine = django_apps.get_model("medicines", "Medicine")

    cleaned = text.strip()
    if not cleaned:
        return None, 0.0

    best_medicine = None
    best_score = 0.0

    for medicine in Medicine.objects.all():
        brand_score = confidence_percent(cleaned, medicine.brand_name)
        generic_score = confidence_percent(cleaned, medicine.generic_name)
        score = max(brand_score, generic_score)

        if score > best_score:
            best_score = score
            best_medicine = medicine

    return best_medicine, best_score


def match_status(confidence):
    """Map a confidence score to the three UI outcomes."""
    if confidence > 90:
        return "matched"
    if confidence >= 70:
        return "confirm"
    return "manual"
