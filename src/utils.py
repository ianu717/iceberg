PREFERENCES = {
    "food",
    "culture",
    "nature",
    "bars",
    "local_favorites",
    "shopping",
    "coffee_shops",
    "walking_tours",
    "family_friendly",
    "vegetarian_vegan",
    "history",
    "festivals_events",
    "beaches",
    "nightlife",
    "budget_friendly",
}

DURATIONS = {
    "oneday",
    "threedays",
    "oneweek",
    "longstay",
}

COMPANIONS = {
    "solo",
    "partner",
    "friends",
    "family",
}

def extract_profile_selection(values: list[str]):
    preferences = []
    duration = None
    companion = None

    for value in values:
        if value in PREFERENCES:
            preferences.append(value)
        elif value in DURATIONS:
            duration = value
        elif value in COMPANIONS:
            companion = value

    return preferences, duration, companion