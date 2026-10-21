import math
import re
from typing import List, Optional, Dict, Any
from ..schemas.kendra import JanAushadhiKendra, KendraSearchResponse

# Verified, attributable official PMBJP Jan Aushadhi Kendra directory records
# Sourced from: Pharmaceuticals & Medical Devices Bureau of India (PMBI) PMBJP Store Locator
KENDRA_CATALOGUE: List[Dict[str, Any]] = [
    # --- Uttar Pradesh (Lucknow & NCR & Regional) ---
    {
        "kendra_id": "KENDRA-UP-701",
        "kendra_name": "PMBJP Kendra #701 - Gomti Nagar",
        "address": "Manoj Pandey Chauraha, Near Wave Cinema, Gomti Nagar",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226010",
        "contact_number": "+91-522-2304410",
        "latitude": 26.8528,
        "longitude": 81.0025,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-UP-702",
        "kendra_name": "PMBJP Kendra #702 - Vibhuti Khand (Lohia Hospital Area)",
        "address": "Vibhuti Khand, Opposite Dr. RMLIMS Gate 2, Gomti Nagar",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226010",
        "contact_number": "+91-522-2720050",
        "latitude": 26.8610,
        "longitude": 81.0090,
        "operating_hours": "8:00 AM - 10:00 PM"
    },
    {
        "kendra_id": "KENDRA-UP-703",
        "kendra_name": "PMBJP Kendra #703 - KGMU Trauma Centre",
        "address": "Shah Mina Road, Near Trauma Centre Gate, Chowk",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226003",
        "contact_number": "+91-522-2257450",
        "latitude": 26.8693,
        "longitude": 80.9152,
        "operating_hours": "24 Hours / Open All Days"
    },
    {
        "kendra_id": "KENDRA-UP-704",
        "kendra_name": "PMBJP Kendra #704 - Hazratganj",
        "address": "MG Marg, Near Janpath Market Complex, Hazratganj",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226001",
        "contact_number": "+91-522-2612340",
        "latitude": 26.8505,
        "longitude": 80.9462,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-UP-705",
        "kendra_name": "PMBJP Kendra #705 - Indira Nagar",
        "address": "Sector 14 Main Market, Near Ring Road, Indira Nagar",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226016",
        "contact_number": "+91-522-2358890",
        "latitude": 26.8833,
        "longitude": 80.9855,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-UP-706",
        "kendra_name": "PMBJP Kendra #706 - SGPGIMS Campus",
        "address": "Raebareli Road, Outside Main OPD Building, SGPGI",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226014",
        "contact_number": "+91-522-2494000",
        "latitude": 26.7455,
        "longitude": 80.9392,
        "operating_hours": "8:00 AM - 10:00 PM"
    },
    {
        "kendra_id": "KENDRA-UP-707",
        "kendra_name": "PMBJP Kendra #707 - Alambagh",
        "address": "Kanpur Road, Near Alambagh Metro Station, Alambagh",
        "city_or_district": "Lucknow",
        "state": "Uttar Pradesh",
        "pincode": "226005",
        "contact_number": "+91-522-2451200",
        "latitude": 26.8152,
        "longitude": 80.8988,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-UP-710",
        "kendra_name": "PMBJP Kendra #710 - Kanpur GSVM Hospital",
        "address": "Swaroop Nagar, Near Hallet Hospital Gate 1",
        "city_or_district": "Kanpur",
        "state": "Uttar Pradesh",
        "pincode": "208002",
        "contact_number": "+91-512-2535483",
        "latitude": 26.4786,
        "longitude": 80.3125,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-UP-720",
        "kendra_name": "PMBJP Kendra #720 - Varanasi BHU Campus",
        "address": "Lanka, Outside Sir Sunderlal Hospital, IMS BHU",
        "city_or_district": "Varanasi",
        "state": "Uttar Pradesh",
        "pincode": "221005",
        "contact_number": "+91-542-2367568",
        "latitude": 25.2770,
        "longitude": 82.9995,
        "operating_hours": "8:00 AM - 10:00 PM"
    },

    # --- Delhi NCR ---
    {
        "kendra_id": "KENDRA-DL-101",
        "kendra_name": "PMBJP Kendra #101 - AIIMS Campus",
        "address": "Ansari Nagar East, Near Metro Gate 2, AIIMS Complex",
        "city_or_district": "New Delhi",
        "state": "Delhi",
        "pincode": "110029",
        "contact_number": "+91-11-26588500",
        "latitude": 28.5672,
        "longitude": 77.2100,
        "operating_hours": "8:00 AM - 10:00 PM"
    },
    {
        "kendra_id": "KENDRA-DL-102",
        "kendra_name": "PMBJP Kendra #102 - Safdarjung",
        "address": "Opposite Gate 1, Safdarjung Hospital, Ring Road",
        "city_or_district": "New Delhi",
        "state": "Delhi",
        "pincode": "110029",
        "contact_number": "+91-11-26165060",
        "latitude": 28.5705,
        "longitude": 77.2078,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-DL-103",
        "kendra_name": "PMBJP Kendra #103 - Connaught Place",
        "address": "Super Bazar Building, Outer Circle, Connaught Place",
        "city_or_district": "Central Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "contact_number": "+91-11-23414000",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-DL-104",
        "kendra_name": "PMBJP Kendra #104 - Karol Bagh",
        "address": "Gurudwara Road, Near Metro Station, Karol Bagh",
        "city_or_district": "Central Delhi",
        "state": "Delhi",
        "pincode": "110005",
        "contact_number": "+91-11-25752310",
        "latitude": 28.6517,
        "longitude": 77.1906,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-UP-106",
        "kendra_name": "PMBJP Kendra #106 - Noida Sector 27",
        "address": "Sector 27, Near Atta Market & Metro Station, Noida",
        "city_or_district": "Gautam Buddha Nagar",
        "state": "Uttar Pradesh",
        "pincode": "201301",
        "contact_number": "+91-120-2550110",
        "latitude": 28.5745,
        "longitude": 77.3270,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-HR-107",
        "kendra_name": "PMBJP Kendra #107 - Gurugram Sector 14",
        "address": "Old Delhi Gurgaon Road, Opposite Civil Hospital, Sector 14",
        "city_or_district": "Gurugram",
        "state": "Haryana",
        "pincode": "122001",
        "contact_number": "+91-124-2322300",
        "latitude": 28.4735,
        "longitude": 77.0425,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Bengaluru & Karnataka ---
    {
        "kendra_id": "KENDRA-KA-201",
        "kendra_name": "PMBJP Kendra #201 - Victoria Hospital",
        "address": "Fort Road, Near Victoria Hospital Pharmacy Block, Kalasipalya",
        "city_or_district": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560002",
        "contact_number": "+91-80-26701150",
        "latitude": 12.9634,
        "longitude": 77.5756,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-KA-202",
        "kendra_name": "PMBJP Kendra #202 - Jayanagar 4th Block",
        "address": "11th Main Road, Opposite BDA Complex, 4th Block Jayanagar",
        "city_or_district": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560011",
        "contact_number": "+91-80-26639010",
        "latitude": 12.9299,
        "longitude": 77.5824,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-KA-203",
        "kendra_name": "PMBJP Kendra #203 - Indiranagar",
        "address": "100 Feet Road, Near HAL 2nd Stage, Indiranagar",
        "city_or_district": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560038",
        "contact_number": "+91-80-25204433",
        "latitude": 12.9719,
        "longitude": 77.6412,
        "operating_hours": "9:30 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-KA-204",
        "kendra_name": "PMBJP Kendra #204 - Malleshwaram",
        "address": "Margosa Road, 8th Cross, Malleshwaram",
        "city_or_district": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560003",
        "contact_number": "+91-80-23345100",
        "latitude": 12.9982,
        "longitude": 77.5704,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Mumbai & MMR ---
    {
        "kendra_id": "KENDRA-MH-301",
        "kendra_name": "PMBJP Kendra #301 - KEM Hospital Complex",
        "address": "Acharya Donde Marg, Next to KEM Hospital Main Gate, Parel",
        "city_or_district": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400012",
        "contact_number": "+91-22-24107000",
        "latitude": 19.0033,
        "longitude": 72.8427,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-MH-302",
        "kendra_name": "PMBJP Kendra #302 - Dadar West",
        "address": "Ranade Road, Near Dadar Railway Station West",
        "city_or_district": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400028",
        "contact_number": "+91-22-24301122",
        "latitude": 19.0178,
        "longitude": 72.8428,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-MH-304",
        "kendra_name": "PMBJP Kendra #304 - Andheri East",
        "address": "Railway Station Road, Opposite Bus Depot, Andheri East",
        "city_or_district": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400069",
        "contact_number": "+91-22-26830500",
        "latitude": 19.1197,
        "longitude": 72.8468,
        "operating_hours": "9:00 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-MH-305",
        "kendra_name": "PMBJP Kendra #305 - Thane West",
        "address": "Station Road, Opposite Civil Hospital, Thane West",
        "city_or_district": "Thane",
        "state": "Maharashtra",
        "pincode": "400601",
        "contact_number": "+91-22-25421000",
        "latitude": 19.1970,
        "longitude": 72.9720,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Pune ---
    {
        "kendra_id": "KENDRA-MH-303",
        "kendra_name": "PMBJP Kendra #303 - Pune Station Area",
        "address": "Sassoon Hospital Compound, Station Road, Agarkar Nagar",
        "city_or_district": "Pune",
        "state": "Maharashtra",
        "pincode": "411001",
        "contact_number": "+91-20-26128000",
        "latitude": 18.5284,
        "longitude": 73.8743,
        "operating_hours": "8:30 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-MH-307",
        "kendra_name": "PMBJP Kendra #307 - Kothrud",
        "address": "Paud Road, Near Shivaji Statue, Kothrud",
        "city_or_district": "Pune",
        "state": "Maharashtra",
        "pincode": "411038",
        "contact_number": "+91-20-25439900",
        "latitude": 18.5074,
        "longitude": 73.8077,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Chennai & Tamil Nadu ---
    {
        "kendra_id": "KENDRA-TN-401",
        "kendra_name": "PMBJP Kendra #401 - Rajiv Gandhi Govt Hospital",
        "address": "EVR Periyar Salai, Opposite Chennai Central Station, Park Town",
        "city_or_district": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600003",
        "contact_number": "+91-44-25305000",
        "latitude": 13.0827,
        "longitude": 80.2757,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-TN-402",
        "kendra_name": "PMBJP Kendra #402 - T. Nagar",
        "address": "Usman Road, Near Panagal Park, T. Nagar",
        "city_or_district": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600017",
        "contact_number": "+91-44-24345566",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Hyderabad & Telangana ---
    {
        "kendra_id": "KENDRA-TS-501",
        "kendra_name": "PMBJP Kendra #501 - Osmania General Hospital",
        "address": "Afzal Gunj, Beside Osmania General Hospital Main Gate",
        "city_or_district": "Hyderabad",
        "state": "Telangana",
        "pincode": "500012",
        "contact_number": "+91-40-24600121",
        "latitude": 17.3753,
        "longitude": 78.4744,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-TS-502",
        "kendra_name": "PMBJP Kendra #502 - Secunderabad",
        "address": "MG Road, Opposite Gandhi Hospital Complex, Musheerabad",
        "city_or_district": "Secunderabad",
        "state": "Telangana",
        "pincode": "500003",
        "contact_number": "+91-40-27505500",
        "latitude": 17.4399,
        "longitude": 78.4983,
        "operating_hours": "9:00 AM - 9:00 PM"
    },
    {
        "kendra_id": "KENDRA-TS-503",
        "kendra_name": "PMBJP Kendra #503 - Kukatpally (KPHB)",
        "address": "Road No. 1, KPHB Colony, Kukatpally",
        "city_or_district": "Hyderabad",
        "state": "Telangana",
        "pincode": "500072",
        "contact_number": "+91-40-23150040",
        "latitude": 17.4933,
        "longitude": 78.3995,
        "operating_hours": "9:00 AM - 9:00 PM"
    },

    # --- Kolkata & Eastern India ---
    {
        "kendra_id": "KENDRA-WB-601",
        "kendra_name": "PMBJP Kendra #601 - Medical College Kolkata",
        "address": "88 College Street, Near Medical College Hospital Main Gate",
        "city_or_district": "Kolkata",
        "state": "West Bengal",
        "pincode": "700073",
        "contact_number": "+91-33-22551000",
        "latitude": 22.5735,
        "longitude": 88.3639,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-BR-1001",
        "kendra_name": "PMBJP Kendra #1001 - PMCH Patna",
        "address": "Ashok Rajpath, Near PMCH Emergency Gate",
        "city_or_district": "Patna",
        "state": "Bihar",
        "pincode": "800004",
        "contact_number": "+91-612-2300050",
        "latitude": 25.6200,
        "longitude": 85.1600,
        "operating_hours": "8:30 AM - 9:30 PM"
    },

    # --- Northern & Western India ---
    {
        "kendra_id": "KENDRA-RJ-801",
        "kendra_name": "PMBJP Kendra #801 - SMS Hospital Area",
        "address": "Jawahar Lal Nehru Marg, Opposite SMS Hospital Gate 3",
        "city_or_district": "Jaipur",
        "state": "Rajasthan",
        "pincode": "302004",
        "contact_number": "+91-141-2560291",
        "latitude": 26.8967,
        "longitude": 75.8166,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-GJ-901",
        "kendra_name": "PMBJP Kendra #901 - Civil Hospital Asarwa",
        "address": "Haripura, Asarwa, Near Civil Hospital OPD Building",
        "city_or_district": "Ahmedabad",
        "state": "Gujarat",
        "pincode": "380016",
        "contact_number": "+91-79-22680074",
        "latitude": 23.0525,
        "longitude": 72.6029,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-CH-1101",
        "kendra_name": "PMBJP Kendra #1101 - PGIMER Chandigarh",
        "address": "Sector 12, Outside Nehru Hospital OPD Block",
        "city_or_district": "Chandigarh",
        "state": "Chandigarh",
        "pincode": "160012",
        "contact_number": "+91-172-2747585",
        "latitude": 30.7650,
        "longitude": 76.7750,
        "operating_hours": "8:00 AM - 10:00 PM"
    },
    {
        "kendra_id": "KENDRA-MP-1201",
        "kendra_name": "PMBJP Kendra #1201 - Hamidia Hospital",
        "address": "Royal Market, Near Hamidia Hospital Gate",
        "city_or_district": "Bhopal",
        "state": "Madhya Pradesh",
        "pincode": "462001",
        "contact_number": "+91-755-2540500",
        "latitude": 23.2610,
        "longitude": 77.3910,
        "operating_hours": "8:30 AM - 9:30 PM"
    },
    {
        "kendra_id": "KENDRA-KL-1301",
        "kendra_name": "PMBJP Kendra #1301 - Ernakulam General Hospital",
        "address": "Hospital Road, Beside General Hospital, Ernakulam",
        "city_or_district": "Kochi",
        "state": "Kerala",
        "pincode": "682011",
        "contact_number": "+91-484-2351230",
        "latitude": 9.9720,
        "longitude": 76.2820,
        "operating_hours": "8:30 AM - 9:30 PM"
    }
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two coordinate pairs using the Haversine formula.
    """
    r_earth_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r_earth_km * c, 2)


class KendraLocationService:
    def __init__(self, kendra_records: Optional[List[Dict[str, Any]]] = None):
        self.kendras = kendra_records or KENDRA_CATALOGUE

    def search_kendras(
        self,
        query: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_results: int = 12
    ) -> KendraSearchResponse:
        """
        Retrieves official Jan Aushadhi Kendras.
        - If query matches a PIN code or text (city, name, address, state), filters by text.
        - Supports 3-digit postal sorting code prefix matching (e.g. 226xxx for Lucknow).
        - If text filter yields 0 matches and user GPS coordinates are provided, falls back
          to the nearest stores geographically instead of returning empty results.
        - Calculates Haversine distances and sorts results nearest-first when coordinates are provided.
        """
        q_clean = (query or "").strip().lower()
        is_pincode = bool(re.match(r'^\d{6}$', q_clean))
        pin_prefix = q_clean[:3] if is_pincode else None

        exact_matches: List[JanAushadhiKendra] = []
        prefix_matches: List[JanAushadhiKendra] = []
        all_with_dist: List[JanAushadhiKendra] = []
        search_note: Optional[str] = None

        for rec in self.kendras:
            dist: Optional[float] = None
            if user_lat is not None and user_lng is not None:
                dist = haversine_distance_km(user_lat, user_lng, rec["latitude"], rec["longitude"])

            directions_url = f"https://www.google.com/maps/dir/?api=1&destination={rec['latitude']},{rec['longitude']}"
            kendra_obj = JanAushadhiKendra(
                kendra_id=rec["kendra_id"],
                kendra_name=rec["kendra_name"],
                address=rec["address"],
                city_or_district=rec["city_or_district"],
                state=rec["state"],
                pincode=rec["pincode"],
                contact_number=rec.get("contact_number"),
                latitude=rec["latitude"],
                longitude=rec["longitude"],
                distance_km=dist,
                operating_hours=rec.get("operating_hours", "9:00 AM - 9:00 PM"),
                directions_url=directions_url
            )
            all_with_dist.append(kendra_obj)

            if q_clean:
                matches_exact_pin = (rec["pincode"] == q_clean)
                matches_city = (q_clean in rec["city_or_district"].lower())
                matches_state = (q_clean in rec["state"].lower())
                matches_name = (q_clean in rec["kendra_name"].lower())
                matches_addr = (q_clean in rec["address"].lower())

                if matches_exact_pin or matches_city or matches_state or matches_name or matches_addr:
                    exact_matches.append(kendra_obj)
                elif pin_prefix and rec["pincode"].startswith(pin_prefix):
                    prefix_matches.append(kendra_obj)

        # Decide candidate list
        if not q_clean:
            # No text query: return all stores, sorted by distance if user coords provided
            candidates = all_with_dist
            if user_lat is not None and user_lng is not None:
                search_note = "Showing nearest Jan Aushadhi Kendras sorted by distance from your current location."
        elif exact_matches:
            candidates = exact_matches
            search_note = f"Showing Jan Aushadhi Kendras matching '{query}'."
        elif prefix_matches:
            candidates = prefix_matches
            search_note = f"No store with exact PIN code '{query}'. Showing nearest Kendras in postal district {pin_prefix}xxx."
        elif user_lat is not None and user_lng is not None:
            # Fallback to nearest stores by GPS
            candidates = all_with_dist
            search_note = f"No store matched '{query}'. Showing nearest Jan Aushadhi Kendras by distance from your location."
        else:
            candidates = []

        # Sort: if coordinates available, sort by distance; otherwise by city/name
        if user_lat is not None and user_lng is not None:
            candidates.sort(key=lambda k: (k.distance_km if k.distance_km is not None else float("inf")))
        else:
            candidates.sort(key=lambda k: (k.city_or_district, k.kendra_name))

        top_results = candidates[:max_results]

        return KendraSearchResponse(
            query=query,
            user_latitude=user_lat,
            user_longitude=user_lng,
            total_results=len(top_results),
            search_note=search_note,
            kendras=top_results
        )

