import pytest
from app.services.kendra_service import KendraLocationService, haversine_distance_km

@pytest.fixture
def kendra_svc():
    return KendraLocationService()

def test_haversine_distance():
    # Distance between AIIMS Delhi (28.5672, 77.2100) and Connaught Place (28.6315, 77.2167) is ~7.1 km
    d = haversine_distance_km(28.5672, 77.2100, 28.6315, 77.2167)
    assert 6.0 <= d <= 8.5

def test_search_kendras_by_pincode(kendra_svc):
    res = kendra_svc.search_kendras(query="110029")
    assert res.total_results >= 1
    assert any("AIIMS" in k.kendra_name or "Safdarjung" in k.kendra_name for k in res.kendras)
    # Check non-negotiable stock disclaimer is present
    assert "Stock availability has not been verified" in res.stock_verification_disclaimer

def test_search_kendras_by_city(kendra_svc):
    res = kendra_svc.search_kendras(query="Bengaluru")
    assert res.total_results >= 2
    assert all(k.city_or_district == "Bengaluru" for k in res.kendras)

def test_search_kendras_proximity_sorting(kendra_svc):
    # Search from Delhi coordinates
    res = kendra_svc.search_kendras(user_lat=28.5670, user_lng=77.2090, max_results=5)
    assert res.total_results > 0
    # Results must be sorted ascending by distance
    distances = [k.distance_km for k in res.kendras if k.distance_km is not None]
    assert distances == sorted(distances)
    # First result should be within 1 km (AIIMS/Safdarjung)
    assert distances[0] < 1.0

def test_search_kendras_lucknow_pincode_226010(kendra_svc):
    res = kendra_svc.search_kendras(query="226010", user_lat=26.85356, user_lng=81.02665)
    assert res.total_results >= 1
    assert any("Gomti Nagar" in k.kendra_name or "Vibhuti Khand" in k.kendra_name for k in res.kendras)
    # Nearest store should be within 5 km
    assert res.kendras[0].distance_km is not None
    assert res.kendras[0].distance_km < 5.0

def test_search_kendras_pincode_prefix_fallback(kendra_svc):
    # A PIN code with no exact store in Lucknow (226099) should match postal circle 226
    res = kendra_svc.search_kendras(query="226099")
    assert res.total_results >= 1
    assert all(k.pincode.startswith("226") for k in res.kendras)
    assert "226xxx" in (res.search_note or "")

def test_search_kendras_geo_fallback(kendra_svc):
    # Unknown text with user coordinates should fall back to nearest stores geographically
    res = kendra_svc.search_kendras(query="UnknownLocalityXYZ", user_lat=26.85356, user_lng=81.02665)
    assert res.total_results > 0
    assert "No store matched" in (res.search_note or "")
    # Should return nearest Lucknow stores
    assert res.kendras[0].distance_km is not None
    assert res.kendras[0].distance_km < 10.0

