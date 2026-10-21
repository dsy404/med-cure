"""
Verified brand-to-generic alias registry for Indian healthcare.
Each alias documents:
- Brand name
- Expected active molecule(s)
- Default strength/form
- Source provenance
"""
from typing import Dict, Optional, List
from pydantic import BaseModel

class BrandAlias(BaseModel):
    brand_name: str
    active_molecule: str
    target_search_term: str
    typical_strength: Optional[str] = None
    dosage_form: Optional[str] = None
    provenance: str = "Verified Indian Brand Reference (CDSCO / Jan Aushadhi Parliamentary Records)"

# Dictionary of lowercase normalized brand names to BrandAlias
BRAND_ALIASES: Dict[str, BrandAlias] = {
    "dolo 650": BrandAlias(
        brand_name="Dolo 650",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol 650mg",
        typical_strength="650mg",
        dosage_form="Tablet"
    ),
    "dolo": BrandAlias(
        brand_name="Dolo",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol Tablets IP 650 mg",
        typical_strength="650mg",
        dosage_form="Tablet"
    ),
    "calpol 500": BrandAlias(
        brand_name="Calpol 500",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol 500mg",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "calpol 650": BrandAlias(
        brand_name="Calpol 650",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol 650mg",
        typical_strength="650mg",
        dosage_form="Tablet"
    ),
    "crocin 500": BrandAlias(
        brand_name="Crocin 500",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol 500mg",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "crocin 650": BrandAlias(
        brand_name="Crocin 650",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol 650mg",
        typical_strength="650mg",
        dosage_form="Tablet"
    ),
    "crocin": BrandAlias(
        brand_name="Crocin",
        active_molecule="Paracetamol",
        target_search_term="Paracetamol",
        dosage_form="Tablet"
    ),
    "augmentin 625": BrandAlias(
        brand_name="Augmentin 625",
        active_molecule="Amoxycillin and Potassium Clavulanate",
        target_search_term="Amoxycillin and Potassium Clavulanate Tablets 625mg",
        typical_strength="625mg",
        dosage_form="Tablet"
    ),
    "augmentin": BrandAlias(
        brand_name="Augmentin",
        active_molecule="Amoxycillin and Potassium Clavulanate",
        target_search_term="Amoxycillin and Potassium Clavulanate",
        dosage_form="Tablet"
    ),
    "pan 40": BrandAlias(
        brand_name="Pan 40",
        active_molecule="Pantoprazole",
        target_search_term="Pantoprazole Gastro-Resistant Tablets IP 40 mg",
        typical_strength="40mg",
        dosage_form="Tablet"
    ),
    "pantocid 40": BrandAlias(
        brand_name="Pantocid 40",
        active_molecule="Pantoprazole",
        target_search_term="Pantoprazole Gastro-Resistant Tablets IP 40 mg",
        typical_strength="40mg",
        dosage_form="Tablet"
    ),
    "pantop 40": BrandAlias(
        brand_name="Pantop 40",
        active_molecule="Pantoprazole",
        target_search_term="Pantoprazole Gastro-Resistant Tablets IP 40 mg",
        typical_strength="40mg",
        dosage_form="Tablet"
    ),
    "omez 20": BrandAlias(
        brand_name="Omez 20",
        active_molecule="Omeprazole",
        target_search_term="Omeprazole Capsules IP 20 mg",
        typical_strength="20mg",
        dosage_form="Capsule"
    ),
    "shelcal 500": BrandAlias(
        brand_name="Shelcal 500",
        active_molecule="Calcium Carbonate and Vitamin D3",
        target_search_term="Calcium and Vitamin D3 Tablets",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "atorva 10": BrandAlias(
        brand_name="Atorva 10",
        active_molecule="Atorvastatin",
        target_search_term="Atorvastatin Tablets IP 10mg",
        typical_strength="10mg",
        dosage_form="Tablet"
    ),
    "lipitor 10": BrandAlias(
        brand_name="Lipitor 10",
        active_molecule="Atorvastatin",
        target_search_term="Atorvastatin Tablets IP 10mg",
        typical_strength="10mg",
        dosage_form="Tablet"
    ),
    "telma 40": BrandAlias(
        brand_name="Telma 40",
        active_molecule="Telmisartan",
        target_search_term="Telmisartan Tablets IP 40 mg",
        typical_strength="40mg",
        dosage_form="Tablet"
    ),
    "telmikind 40": BrandAlias(
        brand_name="Telmikind 40",
        active_molecule="Telmisartan",
        target_search_term="Telmisartan Tablets IP 40 mg",
        typical_strength="40mg",
        dosage_form="Tablet"
    ),
    "glycomet 500": BrandAlias(
        brand_name="Glycomet 500",
        active_molecule="Metformin Hydrochloride",
        target_search_term="Metformin Hydrochloride Prolonged Release Tablets IP 500 mg",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "allegra 120": BrandAlias(
        brand_name="Allegra 120",
        active_molecule="Fexofenadine",
        target_search_term="Fexofenadine Hydrochloride Tablets IP 120 mg",
        typical_strength="120mg",
        dosage_form="Tablet"
    ),
    "azithral 500": BrandAlias(
        brand_name="Azithral 500",
        active_molecule="Azithromycin",
        target_search_term="Azithromycin Tablets IP 500 mg",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "combiflam": BrandAlias(
        brand_name="Combiflam",
        active_molecule="Ibuprofen and Paracetamol",
        target_search_term="Ibuprofen 400mg and Paracetamol 325mg Tablets IP",
        dosage_form="Tablet"
    ),
    "cifran 500": BrandAlias(
        brand_name="Cifran 500",
        active_molecule="Ciprofloxacin",
        target_search_term="Ciprofloxacin Tablets IP 500 mg",
        typical_strength="500mg",
        dosage_form="Tablet"
    ),
    "montair lc": BrandAlias(
        brand_name="Montair LC",
        active_molecule="Montelukast and Levocetirizine",
        target_search_term="Montelukast 10mg and Levocetirizine 5mg Tablets",
        dosage_form="Tablet"
    ),
    "ecosprin 75": BrandAlias(
        brand_name="Ecosprin 75",
        active_molecule="Aspirin (Acetylsalicylic Acid)",
        target_search_term="Aspirin Gastro-resistant Tablets IP 75 mg",
        typical_strength="75mg",
        dosage_form="Tablet"
    ),
    "ecosprin 150": BrandAlias(
        brand_name="Ecosprin 150",
        active_molecule="Aspirin (Acetylsalicylic Acid)",
        target_search_term="Aspirin Gastro-resistant Tablets IP 150 mg",
        typical_strength="150mg",
        dosage_form="Tablet"
    ),
    "amlong 5": BrandAlias(
        brand_name="Amlong 5",
        active_molecule="Amlodipine",
        target_search_term="Amlodipine Tablets IP 5mg",
        typical_strength="5mg",
        dosage_form="Tablet"
    ),
    "meftal spas": BrandAlias(
        brand_name="Meftal Spas",
        active_molecule="Mefenamic Acid and Dicyclomine",
        target_search_term="Mefenamic Acid 250mg and Dicyclomine 10mg Tablets",
        dosage_form="Tablet"
    ),
}

import re

def lookup_brand_alias(query: str) -> Optional[BrandAlias]:
    """
    Checks if a normalized query matches a known verified brand alias.
    First checks exact string, then tries stripping dosage/strength suffix (e.g. 'Crocin 325' -> 'Crocin').
    """
    clean = query.strip().lower()
    if clean in BRAND_ALIASES:
        return BRAND_ALIASES[clean]

    # Try removing trailing strength/numbers: 'crocin 325' -> 'crocin'
    base_name = re.sub(r'\s*\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml)?\b', '', clean).strip()
    if base_name and base_name in BRAND_ALIASES:
        return BRAND_ALIASES[base_name]

    return None

