"""US state name <-> ISO 3166-2 code mapping.

In-N-Out operates only in the United States, so we restrict the universe
to US states.  Callers may pass either a 2-letter code ("CA"), a full
name ("California"), or a mixed-case variant.
"""

US_STATES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

_NAME_TO_CODE = {name.lower(): code for code, name in US_STATES.items()}


def resolve_state(value: str) -> tuple[str, str] | None:
    """Return (code, name) for a user-supplied state, or None if unknown."""
    if not value:
        return None
    v = value.strip()
    if len(v) == 2 and v.upper() in US_STATES:
        code = v.upper()
        return code, US_STATES[code]
    name = _NAME_TO_CODE.get(v.lower())
    if name:
        return name, US_STATES[name]
    return None
