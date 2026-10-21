import re
import unicodedata
from typing import List, Tuple, Optional
from ..schemas.medicine import ExtractedAttributes

DOSAGE_FORMS = [
    "tablet", "tablets", "capsule", "capsules", "injection", "injections",
    "gel", "ointment", "cream", "syrup", "suspension", "solution",
    "drops", "eye drops", "ear drops", "nasal spray", "inhaler", "rotacaps",
    "respuels", "respules", "lotion", "mouthwash", "powder", "granules",
    "emulsion", "patch", "suppository", "bandage", "gauze", "condom"
]

RELEASE_TYPES = [
    ("prolonged release", "prolonged_release"),
    ("sustained release", "sustained_release"),
    ("extended release", "extended_release"),
    ("controlled release", "controlled_release"),
    ("gastro-resistant", "gastro_resistant"),
    ("gastro resistant", "gastro_resistant"),
    ("enteric coated", "enteric_coated"),
    ("enteric-coated", "enteric_coated"),
    ("mouth dissolving", "mouth_dissolving"),
    ("dispersible", "dispersible"),
    ("effervescent", "effervescent"),
    ("sr", "sustained_release"),
    ("pr", "prolonged_release"),
    ("er", "extended_release"),
    ("cr", "controlled_release"),
]

STRENGTH_REGEX = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|gm|ml|%w\/w|%w\/v|%v\/v|%|iu|u)\b",
    re.IGNORECASE
)

# Pharmacopoeial marks to distinguish from active molecules
PHARMACOPOEIA_REGEX = re.compile(r"\b(ip|bp|usp|ep|in)\b", re.IGNORECASE)

def normalize_text(text: str) -> str:
    """
    Standardizes whitespace, unicode characters, and lowercases text
    without stripping clinical values (strengths, numbers, forms).
    """
    if not text:
        return ""
    # Normalize unicode (NFKD decomposes e.g. accents)
    text = unicodedata.normalize("NFKD", text)
    # Replace non-breaking spaces and symbols
    text = text.replace("\u00a0", " ").replace("–", "-").replace("—", "-")
    # Replace tabs/newlines and collapse repeated spaces
    text = re.sub(r"\s+", " ", text)
    # Clean leading/trailing spaces
    return text.strip().lower()

def extract_attributes(raw_name: str, unit_size: Optional[str] = None) -> ExtractedAttributes:
    """
    Deterministically parses product name for clinical attributes
    such as ingredients, strengths, dosage form, and release characteristics.
    Attributes absent from catalogue records are explicitly declared missing.
    """
    norm = normalize_text(raw_name)
    
    # 1. Extract strengths
    strengths_found: List[str] = []
    for match in STRENGTH_REGEX.finditer(norm):
        strengths_found.append(f"{match.group(1)}{match.group(2).lower()}")
        
    # 2. Extract dosage form
    found_form: Optional[str] = None
    # Check multi-word forms first
    for form in sorted(DOSAGE_FORMS, key=len, reverse=True):
        pattern = r"\b" + re.escape(form) + r"\b"
        if re.search(pattern, norm):
            found_form = form.capitalize()
            break
            
    # 3. Extract release type
    found_release: Optional[str] = None
    for pattern_str, label in RELEASE_TYPES:
        if re.search(r"\b" + re.escape(pattern_str) + r"\b", norm):
            found_release = label
            break

    # 4. Extract active ingredients (coarse deterministic extraction)
    # Remove dosage form, pharmacopoeia marks, strengths, and connector words
    cleaned_for_ingredients = norm
    for s in STRENGTH_REGEX.finditer(norm):
        cleaned_for_ingredients = cleaned_for_ingredients.replace(s.group(0), " ")
    cleaned_for_ingredients = PHARMACOPOEIA_REGEX.sub(" ", cleaned_for_ingredients)
    for form in DOSAGE_FORMS:
        cleaned_for_ingredients = re.sub(r"\b" + re.escape(form) + r"\b", " ", cleaned_for_ingredients)
    for pattern_str, _ in RELEASE_TYPES:
        cleaned_for_ingredients = re.sub(r"\b" + re.escape(pattern_str) + r"\b", " ", cleaned_for_ingredients)
    
    # Split by connectors: 'and', '+', ',', '&', 'with'
    chunks = re.split(r"\s+(?:and|\+|\&|with)\s+|\s*,\s*", cleaned_for_ingredients)
    ingredients: List[str] = []
    for c in chunks:
        # remove punctuation and extra spaces
        c_clean = re.sub(r"[^\w\s]", "", c).strip()
        # filter out empty or very short non-substantive words
        words = [w.capitalize() for w in c_clean.split() if len(w) > 2 and w not in ["the", "for", "per"]]
        if words:
            ingredients.append(" ".join(words))

    # Explicit missing attributes (never assume what isn't recorded in catalogue)
    missing: List[str] = ["manufacturer", "brand_name", "batch_number", "expiry_date"]
    if not found_form:
        missing.append("dosage_form")
    if not strengths_found:
        missing.append("strength")

    return ExtractedAttributes(
        ingredients=ingredients,
        strengths=strengths_found,
        dosage_form=found_form,
        release_type=found_release,
        pack_quantity=unit_size.strip() if unit_size else None,
        explicitly_missing_attributes=missing
    )
