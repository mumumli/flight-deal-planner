#!/usr/bin/env python3
"""Carrier classification — low-cost vs full-service, plus display names.

The planner filters on *capability*, not on brand: "do you accept low-cost
carriers" is a real preference; "do you like Scoot" is not. This module is the
mapping that makes the first question answerable.

Codes are IATA airline designators as they appear in fare data. A carrier not
listed here is treated as unknown and kept (never silently dropped).
"""

# Carriers that sell an unbundled fare: cabin bag only, no checked bag, no seat.
LOW_COST = {
    "TR",  # Scoot
    "AK", "FD", "QZ", "D7", "Z2", "XT",  # AirAsia group
    "VJ", "VZ",  # VietJet / Thai VietJet
    "5J", "DG",  # Cebu Pacific
    "JT", "IW", "IU",  # Lion Air group
    "SL",  # Thai Lion Air
    "9C",  # Spring Airlines
    "JQ", "GK",  # Jetstar Airways / Jetstar Japan (3K ceased 2025-07)
    "DD",  # Nok Air
    "8B",  # TransNusa
    "UO",  # HK Express
    "TW",  # T'way
    "7C",  # Jeju Air
}

# Carriers whose base fare includes checked baggage (20–30kg) and a meal.
FULL_SERVICE = {
    "SQ", "MH", "TG", "VN", "GA", "CI", "BR", "KE", "OZ", "NH", "JL", "QF",
    "EK", "QR", "TK", "CX", "KL", "BA", "LH", "AF", "MU", "CZ", "CA", "HU",
    "ZH", "MF", "3U", "PG", "PR", "BL", "VN", "UL", "AI", "6E", "HX",
    "PG",  # Bangkok Airways
    "BI",  # Royal Brunei
    "8M",  # Myanmar Airways International
    "OD",  # Batik Air Malaysia
    "OQ",  # Chongqing Airlines
    "8L",  # Lucky Air
    "KN",  # China United
}

NAMES = {
    "TR": "Scoot", "SQ": "Singapore Airlines", "AK": "AirAsia", "FD": "Thai AirAsia",
    "QZ": "Indonesia AirAsia", "D7": "AirAsia X", "VJ": "VietJet", "VZ": "Thai VietJet",
    "5J": "Cebu Pacific", "JT": "Lion Air", "SL": "Thai Lion Air", "9C": "Spring Airlines",
    "JQ": "Jetstar", "GK": "Jetstar Japan", "DD": "Nok Air", "8B": "TransNusa",
    "UO": "HK Express", "MH": "Malaysia Airlines", "TG": "Thai Airways",
    "VN": "Vietnam Airlines", "GA": "Garuda Indonesia", "CI": "China Airlines",
    "BR": "EVA Air", "KE": "Korean Air", "OZ": "Asiana", "NH": "ANA",
    "JL": "Japan Airlines", "QF": "Qantas", "EK": "Emirates", "QR": "Qatar Airways",
    "TK": "Turkish Airlines", "CX": "Cathay Pacific", "KL": "KLM",
    "MU": "China Eastern", "CZ": "China Southern", "CA": "Air China",
    "HU": "Hainan Airlines", "ZH": "Shenzhen Airlines", "MF": "Xiamen Airlines",
    "PG": "Bangkok Airways", "PR": "Philippine Airlines", "BI": "Royal Brunei",
}


# Fare data renders marketing carriers inconsistently ("THAI" vs "Thai Airways",
# "Shenzhen Air China" vs "Shenzhen Airlines"), so match on aliases, longest first
# -- otherwise "thai" would swallow "Thai AirAsia".
ALIASES = {
    "thai airasia": "FD", "thai vietjet": "VZ", "thai lion": "SL",
    "thai airways": "TG", "thai": "TG",
    "singapore airlines": "SQ", "scoot": "TR", "airasia": "AK",
    "vietjet": "VJ", "vietnam airlines": "VN", "cebu pacific": "5J",
    "batik air": "OD", "malaysia airlines": "MH", "garuda": "GA",
    "china airlines": "CI", "eva air": "BR", "korean air": "KE",
    "asiana": "OZ", "ana": "NH", "japan airlines": "JL", "jal": "JL",
    "qantas": "QF", "emirates": "EK", "qatar": "QR", "turkish": "TK",
    "cathay": "CX", "klm": "KL", "spring": "9C", "jetstar japan": "GK",
    "jetstar": "JQ", "shenzhen air": "ZH", "china southern": "CZ",
    "china eastern": "MU", "air china": "CA", "hainan": "HU",
    "chongqing airlines": "OQ", "xiamen": "MF", "lion air": "JT",
    "super air jet": "IU", "nok air": "DD", "hk express": "UO",
    "bangkok airways": "PG", "philippine airlines": "PR",
    "royal brunei": "BI", "srilankan": "UL", "gulf air": "GF",
    "oman air": "WY", "british airways": "BA",
}
ALIAS_ORDER = sorted(ALIASES.items(), key=lambda kv: -len(kv[0]))
NAME_TO_CODE = {v.lower(): k for k, v in NAMES.items()}


def code_of(name):
    """Best-effort IATA code from a carrier display name ('THAI' -> 'TG')."""
    n = (name or "").strip().lower()
    if not n:
        return ""
    if n in NAME_TO_CODE:
        return NAME_TO_CODE[n]
    for alias, code in ALIAS_ORDER:
        if n.startswith(alias) or alias in n:
            return code
    return ""


def classify_name(name):
    return classify(code_of(name))


def is_low_cost(code):
    return (code or "").upper() in LOW_COST


def classify(code):
    c = (code or "").upper()
    if c in LOW_COST:
        return "low-cost"
    if c in FULL_SERVICE:
        return "full-service"
    return "unknown"


def airline_filter(preference):
    """Map a capability preference to a Google Flights airline list.

    Returning None means "no filter" — the scanner then sees every carrier,
    which is the right default because a filter also caps what the result list
    can show you.
    """
    pref = (preference or "any").lower()
    if pref in ("any", "", None):
        return None
    if pref == "low_cost":
        return sorted(LOW_COST)
    if pref == "no_low_cost":
        return sorted(FULL_SERVICE)
    return None
