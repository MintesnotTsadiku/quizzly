"""Language-neutral comparisons without destroying letters or game symbols."""

import unicodedata


def normalize_answer(value):
	return " ".join(unicodedata.normalize("NFKC", str(value if value is not None else "")).casefold().split())
