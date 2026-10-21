import pytest
from app.services.data_loader import DataLoader

def test_data_loader_generic_products():
    loader = DataLoader()
    gen_count, ceil_count = loader.load_all()

    # Exact baseline counts from Phase 2 data cleaning
    assert gen_count == 2439
    assert ceil_count == 915
    assert loader.stats["generic_usable_price_count"] == 2095
    assert loader.stats["generic_count"] - loader.stats["generic_usable_price_count"] == 344

def test_zero_mrp_unusable():
    loader = DataLoader()
    loader.load_all()

    # Check that zero MRP products are strictly marked unusable for price comparison
    zero_mrp_prods = [p for p in loader.generic_products if p.price.amount_inr == 0.0]
    assert len(zero_mrp_prods) == 344
    for p in zero_mrp_prods:
        assert p.price.usable_for_comparison is False

def test_ceiling_prices_not_marked_usable_for_retail_comparison():
    loader = DataLoader()
    loader.load_all()

    # All ceiling price references must have usable_for_comparison = False
    for p in loader.ceiling_products:
        assert p.price.usable_for_comparison is False
        assert p.price.price_type == "ceiling_price_excluding_taxes"

def test_stable_id_lookup():
    loader = DataLoader()
    loader.load_all()

    p1 = loader.get_by_id("GEN-1")
    assert p1 is not None
    assert "Aceclofenac" in p1.name
    assert p1.price.amount_inr == 10.32

    p_nonexistent = loader.get_by_id("GEN-999999")
    assert p_nonexistent is None
