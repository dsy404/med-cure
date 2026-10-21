from typing import List, Optional
from pydantic import BaseModel, Field

class JanAushadhiKendra(BaseModel):
    kendra_id: str
    kendra_name: str
    address: str
    city_or_district: str
    state: str
    pincode: str
    contact_number: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    operating_hours: str = "9:00 AM - 9:00 PM"
    source_attribution: str = (
        "Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP), "
        "Pharmaceuticals & Medical Devices Bureau of India (PMBI)"
    )
    data_freshness: str = "Official Verified PMBJP Network 2026"
    directions_url: Optional[str] = None

class KendraSearchResponse(BaseModel):
    query: Optional[str] = None
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    total_results: int
    search_note: Optional[str] = None
    kendras: List[JanAushadhiKendra] = Field(default_factory=list)
    stock_verification_disclaimer: str = (
        "CRITICAL NOTICE: Stock availability has not been verified. "
        "MedWise verifies official Kendra registry locations, but individual store inventory "
        "fluctuates daily. Always contact the Kendra directly by telephone before visiting."
    )

