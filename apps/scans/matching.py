import difflib
import re

from django.apps import apps as django_apps

# Prescription words are letters, digits, and a few separators. Everything else
# (dashes, bullets, Rx marks) becomes a space so "Coumadin." still matches.
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_MIN_PHRASE_LETTERS = 4


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


def candidate_phrases(text, max_words=3):
    """Split OCR output into the short phrases a medicine name could occupy.

    A prescription page contains a doctor's name, instructions, and dosages
    around the medicine, so comparing the whole page to one brand name scores
    badly. Sliding windows of one to three words give "Coumadin" and
    "Lithium carbonate" a fair comparison.
    """
    words = _WORD_RE.findall(text.lower())
    phrases = set()

    for size in range(1, max_words + 1):
        for start in range(len(words) - size + 1):
            phrase = " ".join(words[start:start + size])
            if len(phrase.replace(" ", "")) >= _MIN_PHRASE_LETTERS:
                phrases.add(phrase)

    return phrases


def find_best_match_in_text(text):
    """Return (medicine, confidence, snippet) for a block of OCR text.

    Each candidate phrase is compared with every brand and generic name; the
    highest ratio wins. This is the OCR counterpart to find_best_match(), which
    assumes the user typed just the medicine name.
    """
    Medicine = django_apps.get_model("medicines", "Medicine")

    phrases = candidate_phrases(text)
    if not phrases:
        return None, 0.0, ""

    best_medicine = None
    best_score = 0.0
    best_phrase = ""

    for medicine in Medicine.objects.all():
        names = (medicine.brand_name, medicine.generic_name)

        for phrase in phrases:
            for name in names:
                score = confidence_percent(phrase, name)
                if score > best_score:
                    best_score = score
                    best_medicine = medicine
                    best_phrase = phrase

    # Below the confirm threshold the phrase is noise, not a candidate name.
    if best_score < 70:
        best_phrase = ""

    return best_medicine, best_score, best_phrase


def match_status(confidence):
    """Map a confidence score to the three UI outcomes."""
    if confidence > 90:
        return "matched"
    if confidence >= 70:
        return "confirm"
    return "manual"
