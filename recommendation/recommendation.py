import pandas as pd

# ==========================================
# LOAD DATASET
# ==========================================

events = pd.read_excel("data/events_100_mvp.xlsx")

# Clean column names
events.columns = events.columns.str.strip()

# Clean text columns
text_columns = [
    "title",
    "description",
    "event_type",
    "category",
    "organizer",
    "college_name",
    "location",
    "mode",
    "status"
]

for col in text_columns:
    events[col] = events[col].fillna("").astype(str).str.strip()


# ==========================================
# USER REQUIREMENTS
# ==========================================

user_category = "General"
user_location = "Coimbatore"
user_mode = "Offline"
user_budget = 500
user_interest = "AI Python"
user_max_distance = 25


# ==========================================
# FILTER EVENTS
# ==========================================

filtered = events.copy()

# Category
if user_category:
    if user_category.lower() == "college":
        filtered = filtered[
            filtered["event_type"].str.lower() == "college"
        ]
    else:
        filtered = filtered[
            filtered["event_type"].str.lower() == "general"
        ]


# Location
if user_location:
    filtered = filtered[
        filtered["location"].str.lower().str.contains(
            user_location.lower(),
            na=False
        )
    ]


# Mode
if user_mode:
    filtered = filtered[
        filtered["mode"].str.lower() == user_mode.lower()
    ]


# ==========================================
# BUDGET FILTER
# ==========================================

def get_fee(value):

    if pd.isna(value) or value == "":
        return 0

    try:
        return float(value)
    except:
        return 0


filtered["numeric_fee"] = filtered["fee"].apply(get_fee)

filtered = filtered[
    filtered["numeric_fee"] <= user_budget
]


# ==========================================
# INTEREST MATCHING
# ==========================================

def calculate_interest_score(row):

    event_text = (
        row["title"] + " " +
        row["description"] + " " +
        row["category"] + " " +
        row["event_type"]
    ).lower()

    interests = user_interest.lower().split()

    matched = 0

    for interest in interests:
        if interest in event_text:
            matched += 1

    if len(interests) == 0:
        return 0

    return (matched / len(interests)) * 100


filtered["interest_score"] = filtered.apply(
    calculate_interest_score,
    axis=1
)


# ==========================================
# FINAL MATCH SCORE
# ==========================================

filtered["match_score"] = (
    filtered["interest_score"] * 0.50 +
    25 +      # location match
    15 +      # mode match
    10        # budget match
)


# Limit score to 100
filtered["match_score"] = filtered["match_score"].clip(upper=100)


# ==========================================
# SORT BEST EVENTS
# ==========================================

recommendations = filtered.sort_values(
    by="match_score",
    ascending=False
)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n")
print("=" * 65)
print("        🎯 PERSONALIZED EVENT RECOMMENDATIONS")
print("=" * 65)

print("\nUser Preferences:")
print("Category :", user_category)
print("Location :", user_location)
print("Mode     :", user_mode)
print("Budget   :", user_budget)
print("Interest :", user_interest)

print("\nRecommended Events:")
print("-" * 65)

if len(recommendations) == 0:

    print("❌ No matching events found.")

else:

    for i, (_, event) in enumerate(
        recommendations.head(10).iterrows(),
        start=1
    ):

        print(f"\n{i}. {event['title']}")
        print(f"   ⭐ Match Score : {event['match_score']:.0f}%")
        print(f"   📍 Location    : {event['location']}")
        print(f"   💻 Mode        : {event['mode']}")
        print(f"   💰 Fee         : {event['fee']}")
        print(f"   📅 Date        : {event['start_date']}")
        print(f"   🏷️ Category    : {event['category']}")

print("\n" + "=" * 65)