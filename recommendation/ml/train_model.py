import pandas as pd
import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml"
)


# ============================================================
# FIND EXCEL FILE
# ============================================================

excel_files = [
    file for file in os.listdir(DATA_DIR)
    if file.lower().endswith((".xlsx", ".xls"))
    and not file.startswith("~$")
]

if not excel_files:
    raise FileNotFoundError(
        "No Excel file found inside data folder."
    )

excel_file = os.path.join(
    DATA_DIR,
    excel_files[0]
)

print("📂 Dataset:", excel_file)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_excel(excel_file)

print("✅ Dataset loaded")
print("📊 Number of events:", len(df))
print("📋 Columns:", list(df.columns))


# ============================================================
# CLEAN DATA
# ============================================================

text_columns = [
    "title",
    "description",
    "category",
    "event_type",
    "organizer",
    "location",
    "mode"
]

for column in text_columns:

    if column not in df.columns:
        df[column] = ""

    df[column] = (
        df[column]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )


# ============================================================
# CREATE EVENT TEXT
# ============================================================

df["event_text"] = (
    df["title"] + " "
    + df["description"] + " "
    + df["category"] + " "
    + df["event_type"] + " "
    + df["organizer"] + " "
    + df["location"] + " "
    + df["mode"]
)


# ============================================================
# TF-IDF
# ============================================================

print()
print("🤖 Training AI recommendation model...")

vectorizer = TfidfVectorizer(
    stop_words="english"
)

event_vectors = vectorizer.fit_transform(
    df["event_text"]
)


# ============================================================
# EVENT SIMILARITY
# ============================================================

similarity_matrix = cosine_similarity(
    event_vectors
)


# ============================================================
# SAVE MODEL
# ============================================================

model_data = {

    "data": df,

    "vectorizer": vectorizer,

    "event_vectors": event_vectors,

    "similarity_matrix": similarity_matrix

}


model_path = os.path.join(
    MODEL_DIR,
    "event_recommender_model.pkl"
)


joblib.dump(
    model_data,
    model_path
)


# ============================================================
# SUCCESS
# ============================================================

print()
print("==========================================")
print("🎉 ML MODEL TRAINING COMPLETED")
print("==========================================")
print()
print("Events trained :", len(df))
print("Model saved to :", model_path)
print()
print("🤖 Recommendation model is ready!")