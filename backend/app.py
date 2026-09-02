from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import os
import sqlite3
import joblib

from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "backend",
    "database.db"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "event_recommender_model.pkl"
)

EXCEL_PATH = os.path.join(
    BASE_DIR,
    "data",
    "events_100_complete.xlsx"
)


# ============================================================
# LOAD ML MODEL
# ============================================================

model = None
events_df = None

try:
    model = joblib.load(MODEL_PATH)

    events_df = model["data"]

    print("========================================")
    print("🤖 ML MODEL LOADED SUCCESSFULLY")
    print("========================================")
    print("Model :", MODEL_PATH)
    print("Events:", len(events_df))

except Exception as e:

    print("========================================")
    print("❌ ML MODEL LOAD FAILED")
    print("========================================")
    print("Error:", e)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    conn = sqlite3.connect(DATABASE_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# HELPER - GET EVENT
# ============================================================

def get_event(event_id):

    if events_df is None:
        return None

    matches = events_df[
        events_df["event_id"].astype(str)
        == str(event_id)
    ]

    if matches.empty:
        return None

    return matches.iloc[0].fillna("").to_dict()


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "Event Recommender API is running"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "ml_model_loaded": model is not None,
        "events_loaded": (
            len(events_df)
            if events_df is not None
            else 0
        )
    })


# ============================================================
# SIGNUP
# ============================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        name = str(
            data.get("name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = str(
            data.get("password", "")
        )

        if not name or not email or not password:

            return jsonify({
                "error": "Name, email and password are required"
            }), 400

        conn = get_db_connection()

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing:

            conn.close()

            return jsonify({
                "error": "Email already registered"
            }), 409

        cursor = conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                password
            )
        )

        conn.commit()

        user_id = cursor.lastrowid

        conn.close()

        return jsonify({

            "status": "success",

            "message": "Account created successfully",

            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }

        }), 201

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = str(
            data.get("password", "")
        )

        if not email or not password:

            return jsonify({
                "error": "Email and password are required"
            }), 400

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT
                id,
                name,
                email,
                password
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if not user:

            return jsonify({
                "error": "Invalid email or password"
            }), 401

        if user["password"] != password:

            return jsonify({
                "error": "Invalid email or password"
            }), 401

        return jsonify({

            "status": "success",

            "message": "Login successful",

            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# GET ALL EVENTS
# ============================================================

@app.route("/api/events", methods=["GET"])
def get_events():

    try:

        if events_df is None:

            return jsonify({
                "error": "Event data is not loaded"
            }), 500

        events = events_df.copy()

        events = events.fillna("")

        result = events.to_dict(
            orient="records"
        )

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# GET ONE EVENT
# ============================================================

@app.route("/api/events/<event_id>", methods=["GET"])
def get_one_event(event_id):

    try:

        event = get_event(event_id)

        if event is None:

            return jsonify({
                "error": "Event not found"
            }), 404

        return jsonify(event)

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# ML RECOMMENDATIONS
# ============================================================

@app.route("/api/recommendations", methods=["POST"])
def recommendations():

    try:

        if model is None:

            return jsonify({
                "error": "ML model is not loaded"
            }), 500

        if events_df is None:

            return jsonify({
                "error": "Events are not loaded"
            }), 500

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        query = str(
            data.get("query", "")
        ).lower().strip()

        if not query:

            return jsonify({
                "error": "Please provide a query"
            }), 400

        vectorizer = model["vectorizer"]

        event_vectors = model["event_vectors"]

        query_vector = vectorizer.transform(
            [query]
        )

        similarities = cosine_similarity(
            query_vector,
            event_vectors
        )[0]

        limit = int(
            data.get("limit", 5)
        )

        limit = min(
            max(limit, 1),
            len(events_df)
        )

        top_indices = similarities.argsort()[
            -limit:
        ][::-1]

        recommendations_list = []

        for index in top_indices:

            event = (
                events_df
                .iloc[index]
                .fillna("")
                .to_dict()
            )

            event["similarity_score"] = round(
                float(similarities[index]),
                4
            )

            recommendations_list.append(event)

        return jsonify({

            "status": "success",

            "query": query,

            "recommendations":
                recommendations_list

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# SAVE USER PREFERENCES
# ============================================================

@app.route("/api/preferences", methods=["POST"])
def save_preferences():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_id = data.get("user_id")

        if not user_id:

            return jsonify({
                "error": "user_id is required"
            }), 400

        location = data.get(
            "location",
            ""
        )

        mode = data.get(
            "mode",
            ""
        )

        budget = data.get(
            "budget"
        )

        interests = data.get(
            "interests",
            ""
        )

        preferred_date = data.get(
            "preferred_date",
            ""
        )

        preferred_start_time = data.get(
            "preferred_start_time",
            ""
        )

        preferred_end_time = data.get(
            "preferred_end_time",
            ""
        )

        max_distance_km = data.get(
            "max_distance_km"
        )

        conn = get_db_connection()

        existing = conn.execute(
            """
            SELECT id
            FROM user_preferences
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE user_preferences
                SET
                    preferred_location = ?,
                    preferred_mode = ?,
                    budget = ?,
                    interests = ?,
                    preferred_date = ?,
                    preferred_start_time = ?,
                    preferred_end_time = ?,
                    max_distance_km = ?
                WHERE user_id = ?
                """,
                (
                    location,
                    mode,
                    budget,
                    interests,
                    preferred_date,
                    preferred_start_time,
                    preferred_end_time,
                    max_distance_km,
                    user_id
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO user_preferences
                (
                    user_id,
                    preferred_location,
                    preferred_mode,
                    budget,
                    interests,
                    preferred_date,
                    preferred_start_time,
                    preferred_end_time,
                    max_distance_km
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    location,
                    mode,
                    budget,
                    interests,
                    preferred_date,
                    preferred_start_time,
                    preferred_end_time,
                    max_distance_km
                )
            )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message":
                "Preferences saved successfully"

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# REGISTER FOR EVENT
# ============================================================

@app.route("/api/register", methods=["POST"])
def register_event():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_id = data.get("user_id")

        event_id = data.get("event_id")

        if not user_id or not event_id:

            return jsonify({
                "error":
                    "user_id and event_id are required"
            }), 400

        event = get_event(event_id)

        if event is None:

            return jsonify({
                "error": "Event not found"
            }), 404

        conn = get_db_connection()

        existing = conn.execute(
            """
            SELECT id
            FROM registrations
            WHERE user_id = ?
            AND event_id = ?
            """,
            (
                user_id,
                event_id
            )
        ).fetchone()

        if existing:

            conn.close()

            return jsonify({
                "status": "success",
                "message":
                    "Already registered for this event"
            })

        conn.execute(
            """
            INSERT INTO registrations
            (
                user_id,
                event_id
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                event_id
            )
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message":
                "Event registered successfully"

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# GET REGISTERED EVENTS
# ============================================================

@app.route("/api/registrations/<int:user_id>", methods=["GET"])
def registrations(user_id):

    try:

        conn = get_db_connection()

        rows = conn.execute(
            """
            SELECT
                event_id,
                registered_at
            FROM registrations
            WHERE user_id = ?
            ORDER BY registered_at DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        result = []

        for row in rows:

            event = get_event(
                row["event_id"]
            )

            if event:

                event["registered_at"] = \
                    row["registered_at"]

                result.append(event)

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# USER ACTIVITY
# ============================================================

@app.route("/api/activity", methods=["POST"])
def activity():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_id = data.get("user_id")

        event_id = data.get("event_id")

        action = data.get("action")

        search_location = data.get(
            "search_location"
        )

        if not user_id or not action:

            return jsonify({
                "error":
                    "user_id and action are required"
            }), 400

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO user_activity
            (
                user_id,
                event_id,
                action,
                search_location
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                event_id,
                action,
                search_location
            )
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message":
                "Activity recorded"

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# SEARCH EVENTS
# ============================================================

@app.route("/api/search", methods=["GET"])
def search_events():

    try:

        query = request.args.get(
            "q",
            ""
        ).strip().lower()

        if not query:

            return jsonify([])

        if events_df is None:

            return jsonify({
                "error": "Events are not loaded"
            }), 500

        events = events_df.copy()

        text_columns = [

            "title",
            "description",
            "category",
            "event_type",
            "organizer",
            "college_name",
            "location",
            "mode"

        ]

        existing_columns = [

            column
            for column in text_columns
            if column in events.columns

        ]

        mask = False

        for column in existing_columns:

            mask = (

                mask |

                events[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    regex=False
                )

            )

        results = events[
            mask
        ].fillna("")

        return jsonify(
            results.to_dict(
                orient="records"
            )
        )

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# SAVE AVAILABILITY
# ============================================================

@app.route("/api/availability", methods=["POST"])
def save_availability():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_id = data.get("user_id")

        free_date = data.get(
            "free_date"
        )

        free_start = data.get(
            "free_start"
        )

        free_end = data.get(
            "free_end"
        )

        if not all([
            user_id,
            free_date,
            free_start,
            free_end
        ]):

            return jsonify({
                "error":
                    "All availability fields are required"
            }), 400

        if free_start >= free_end:

            return jsonify({
                "error":
                    "End time must be after start time"
            }), 400

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO availability
            (
                user_id,
                date,
                start_time,
                end_time
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                free_date,
                free_start,
                free_end
            )
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message":
                "Free time saved successfully"

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# EVENTS DURING FREE TIME
# ============================================================

@app.route(
    "/api/free-time-events/<int:user_id>",
    methods=["GET"]
)
def free_time_events(user_id):

    try:

        conn = get_db_connection()

        free_times = conn.execute(
            """
            SELECT
                date,
                start_time,
                end_time
            FROM availability
            WHERE user_id = ?
            ORDER BY date DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        if events_df is None:

            return jsonify({
                "error": "Events are not loaded"
            }), 500

        results = []

        for free in free_times:

            free_date = str(
                free["date"]
            )

            free_start = str(
                free["start_time"]
            )

            free_end = str(
                free["end_time"]
            )

            for _, row in events_df.iterrows():

                event = row.fillna("").to_dict()

                event_date = str(
                    event.get(
                        "start_date",
                        ""
                    )
                )

                event_start = str(
                    event.get(
                        "start_time",
                        ""
                    )
                )

                event_end = str(
                    event.get(
                        "end_time",
                        ""
                    )
                )

                if event_date != free_date:
                    continue

                if not event_start:
                    continue

                if not event_end:
                    event_end = event_start

                if (
                    event_start >= free_start
                    and event_end <= free_end
                ):

                    results.append({

                        "event": event,

                        "fits_free_time": True,

                        "free_date":
                            free_date,

                        "free_start":
                            free_start,

                        "free_end":
                            free_end,

                        "free_time_message":
                            "You are free during this event."

                    })

        return jsonify(results)

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@app.route(
    "/api/notifications/<int:user_id>",
    methods=["GET"]
)
def notifications(user_id):

    try:

        conn = get_db_connection()

        rows = conn.execute(
            """
            SELECT
                id,
                event_id,
                notification_type,
                message,
                reminder_minutes,
                sent,
                created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        result = []

        for row in rows:

            event = get_event(
                row["event_id"]
            )

            title = (
                event.get("title")
                if event
                else "Event Notification"
            )

            reminder_time = ""

            if event:

                try:

                    event_date = event.get(
                        "start_date"
                    )

                    event_time = event.get(
                        "start_time"
                    )

                    if event_date and event_time:

                        event_dt = datetime.strptime(
                            f"{event_date} {event_time}",
                            "%Y-%m-%d %H:%M"
                        )

                        reminder_dt = (
                            event_dt -
                            timedelta(
                                minutes=
                                row["reminder_minutes"]
                                or 60
                            )
                        )

                        reminder_time = \
                            reminder_dt.strftime(
                                "%Y-%m-%d %H:%M"
                            )

                except Exception:

                    reminder_time = ""

            result.append({

                "id":
                    row["id"],

                "event_id":
                    row["event_id"],

                "title":
                    title,

                "message":
                    row["message"],

                "notification_type":
                    row["notification_type"],

                "reminder_minutes":
                    row["reminder_minutes"],

                "reminder_time":
                    reminder_time,

                "sent":
                    row["sent"],

                "created_at":
                    row["created_at"]

            })

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# CREATE REMINDER
# ============================================================

@app.route("/api/reminder", methods=["POST"])
def create_reminder():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_id = data.get(
            "user_id"
        )

        event_id = data.get(
            "event_id"
        )

        minutes_before = int(
            data.get(
                "minutes_before",
                60
            )
        )

        if not user_id or not event_id:

            return jsonify({
                "error":
                    "user_id and event_id are required"
            }), 400

        event = get_event(event_id)

        if event is None:

            return jsonify({
                "error": "Event not found"
            }), 404

        event_date = event.get(
            "start_date"
        )

        event_time = event.get(
            "start_time"
        )

        reminder_time = ""

        if event_date and event_time:

            try:

                event_dt = datetime.strptime(
                    f"{event_date} {event_time}",
                    "%Y-%m-%d %H:%M"
                )

                reminder_dt = (
                    event_dt -
                    timedelta(
                        minutes=minutes_before
                    )
                )

                reminder_time = \
                    reminder_dt.strftime(
                        "%Y-%m-%d %H:%M"
                    )

            except Exception:

                reminder_time = ""

        message = (
            f"Reminder for "
            f"{event.get('title', 'event')}"
        )

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO notifications
            (
                user_id,
                event_id,
                notification_type,
                message,
                reminder_minutes,
                sent
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                event_id,
                "reminder",
                message,
                minutes_before,
                0
            )
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message":
                "Reminder created successfully",

            "reminder_time":
                reminder_time

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# CALENDAR - DOWNLOAD ICS FILE
# ============================================================

@app.route(
    "/api/calendar/<int:user_id>/<event_id>",
    methods=["GET"]
)
def calendar(user_id, event_id):

    try:

        event = get_event(event_id)

        if event is None:

            return jsonify({
                "error": "Event not found"
            }), 404

        title = event.get(
            "title",
            "Event"
        )

        description = event.get(
            "description",
            ""
        )

        location = event.get(
            "location",
            ""
        )

        start_date = event.get(
            "start_date",
            ""
        )

        start_time = event.get(
            "start_time",
            "00:00"
        )

        end_date = event.get(
            "end_date",
            start_date
        )

        end_time = event.get(
            "end_time",
            start_time
        )

        try:

            start_dt = datetime.strptime(
                f"{start_date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            end_dt = datetime.strptime(
                f"{end_date} {end_time}",
                "%Y-%m-%d %H:%M"
            )

        except Exception:

            start_dt = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            )

            end_dt = (
                start_dt +
                timedelta(hours=1)
            )

        dt_format = "%Y%m%dT%H%M%S"

        ics = (

            "BEGIN:VCALENDAR\r\n"

            "VERSION:2.0\r\n"

            "PRODID:-//Event Recommender//EN\r\n"

            "BEGIN:VEVENT\r\n"

            f"UID:{event_id}@event-recommender\r\n"

            f"DTSTAMP:"
            f"{datetime.now().strftime(dt_format)}\r\n"

            f"DTSTART:"
            f"{start_dt.strftime(dt_format)}\r\n"

            f"DTEND:"
            f"{end_dt.strftime(dt_format)}\r\n"

            f"SUMMARY:{title}\r\n"

            f"DESCRIPTION:{description}\r\n"

            f"LOCATION:{location}\r\n"

            "END:VEVENT\r\n"

            "END:VCALENDAR\r\n"

        )

        return Response(

            ics,

            mimetype="text/calendar",

            headers={

                "Content-Disposition":
                    f"attachment; filename={event_id}.ics"

            }

        )

    except Exception as e:

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================
# DATABASE TEST
# ============================================================

@app.route(
    "/api/database-test",
    methods=["GET"]
)
def database_test():

    try:

        conn = get_db_connection()

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        conn.close()

        return jsonify({

            "status": "success",

            "database":
                DATABASE_PATH,

            "tables": [

                row["name"]

                for row in tables

            ]

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "error": str(e)

        }), 500


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":

    print()

    print("========================================")
    print("🚀 EVENT RECOMMENDER BACKEND")
    print("========================================")

    print(
        "Database :",
        DATABASE_PATH
    )

    print(
        "Excel    :",
        EXCEL_PATH
    )

    print(
        "ML Model :",
        MODEL_PATH
    )

    print(
        "API      :",
        "http://127.0.0.1:5000"
    )

    print("========================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )