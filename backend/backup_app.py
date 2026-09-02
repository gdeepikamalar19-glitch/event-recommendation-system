from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import pandas as pd
import os
import math
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE = os.path.join(BACKEND_DIR, "database.db")


# ============================================================
# FIND EXCEL FILE
# ============================================================

def find_excel_file():

    if not os.path.exists(DATA_DIR):
        return None

    excel_files = []

    for filename in os.listdir(DATA_DIR):

        if filename.startswith("~$"):
            continue

        if filename.lower().endswith((".xlsx", ".xls")):
            excel_files.append(
                os.path.join(DATA_DIR, filename)
            )

    if not excel_files:
        return None

    preferred_names = [
        "events_100_mvp.xlsx",
        "events_100.xlsx",
        "events.xlsx",
        "event_data.xlsx"
    ]

    for preferred in preferred_names:

        path = os.path.join(DATA_DIR, preferred)

        if os.path.exists(path):
            return path

    excel_files.sort()

    return excel_files[0]


EXCEL_FILE = find_excel_file()


# ============================================================
# DATABASE
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    os.makedirs(BACKEND_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (

            event_id TEXT PRIMARY KEY,

            title TEXT,
            description TEXT,
            event_type TEXT,
            category TEXT,
            organizer,
            college_name TEXT,

            location TEXT,

            latitude REAL,
            longitude REAL,

            mode TEXT,
            fee REAL,

            start_date TEXT,
            start_time TEXT,

            end_date TEXT,
            end_time TEXT,

            registration_deadline TEXT,

            min_team_size INTEGER,
            max_team_size INTEGER,

            status TEXT,

            source_url TEXT
        )
    """)

    # --------------------------------------------------------
    # USER PREFERENCES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE,

            preferred_location TEXT,
            preferred_mode TEXT,

            budget REAL,

            interests TEXT,

            preferred_date TEXT,

            preferred_start_time TEXT,
            preferred_end_time TEXT,

            max_distance_km REAL,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # USER ACTIVITY
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            event_id TEXT,

            action TEXT NOT NULL,

            search_location TEXT,

            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE,

            FOREIGN KEY(event_id)
            REFERENCES events(event_id)
            ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # REGISTRATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            event_id TEXT,

            registered_at DATETIME
            DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, event_id),

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE,

            FOREIGN KEY(event_id)
            REFERENCES events(event_id)
            ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            date TEXT,

            start_time TEXT,
            end_time TEXT,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            event_id TEXT,

            notification_type TEXT,

            message TEXT,

            reminder_time TEXT,

            is_sent INTEGER DEFAULT 0,

            created_at DATETIME
            DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE,

            FOREIGN KEY(event_id)
            REFERENCES events(event_id)
            ON DELETE CASCADE
        )
    """)

    conn.commit()

    # --------------------------------------------------------
    # DATABASE MIGRATION
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(events)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "end_time" not in columns:

        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN end_time TEXT
        """)

    # --------------------------------------------------------
    # INDEXES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_events_start_date
        ON events(start_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_events_category
        ON events(category)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_events_location
        ON events(location)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_activity_user
        ON user_activity(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_registration_user
        ON registrations(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_availability_user
        ON availability(user_id)
    """)

    conn.commit()
    conn.close()

    print("✅ Database tables created successfully!")


# ============================================================
# SAFE VALUE
# ============================================================

def safe_value(value, default=""):

    if value is None:
        return default

    try:

        if pd.isna(value):
            return default

    except Exception:
        pass

    return value


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value, default=""):

    value = safe_value(value, default)

    return str(value).strip()


# ============================================================
# NORMALIZE DATE
# ============================================================

def normalize_date(value):

    value = safe_value(value, "")

    if value == "":
        return ""

    try:

        if isinstance(value, pd.Timestamp):

            return value.strftime("%Y-%m-%d")

        parsed = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.notna(parsed):

            return parsed.strftime("%Y-%m-%d")

    except Exception:
        pass

    text = str(value).strip()

    if " " in text:
        text = text.split(" ")[0]

    return text


# ============================================================
# NORMALIZE TIME
# ============================================================

def normalize_time(value):

    value = safe_value(value, "")

    if value == "":
        return ""

    try:

        if isinstance(value, pd.Timestamp):

            return value.strftime("%H:%M")

        if isinstance(value, datetime):

            return value.strftime("%H:%M")

        if hasattr(value, "hour") and hasattr(value, "minute"):

            return (
                f"{int(value.hour):02d}:"
                f"{int(value.minute):02d}"
            )

    except Exception:
        pass

    text = str(value).strip()

    formats = (
        "%H:%M",
        "%H:%M:%S",
        "%I:%M %p",
        "%I %p",
        "%I:%M:%S %p"
    )

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                text,
                fmt
            )

            return parsed.strftime("%H:%M")

        except ValueError:
            continue

    return text[:5]


# ============================================================
# NORMALIZE NUMBER
# ============================================================

def normalize_number(value, default=None):

    value = safe_value(value, default)

    if value is None:
        return default

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# NORMALIZE INTEGER
# ============================================================

def normalize_integer(value, default=None):

    value = safe_value(value, default)

    if value is None:
        return default

    try:

        return int(float(value))

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# IMPORT EXCEL
# ============================================================

def import_events():

    global EXCEL_FILE

    EXCEL_FILE = find_excel_file()

    print()
    print("========================================")
    print("           EXCEL IMPORT")
    print("========================================")

    if EXCEL_FILE is None:

        print("❌ Excel file not found!")
        print("Put your Excel file inside:")
        print(DATA_DIR)

        return

    print("✅ Excel file found:")
    print(EXCEL_FILE)

    try:

        df = pd.read_excel(EXCEL_FILE)

    except Exception as error:

        print("❌ Error reading Excel:")
        print(error)

        return

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    print("📊 Excel columns:")
    print(list(df.columns))

    print(
        f"📊 Total events found: {len(df)}"
    )

    if "event_id" not in df.columns:

        print(
            "❌ Excel must contain event_id column."
        )

        return

    conn = get_db()

    imported_count = 0
    skipped_count = 0

    for _, row in df.iterrows():

        event_id = normalize_text(
            row.get("event_id", "")
        )

        if not event_id:

            skipped_count += 1
            continue

        title = normalize_text(
            row.get("title", "")
        )

        description = normalize_text(
            row.get("description", "")
        )

        event_type = normalize_text(
            row.get("event_type", "")
        )

        category = normalize_text(
            row.get("category", "")
        )

        organizer = normalize_text(
            row.get("organizer", "")
        )

        college_name = normalize_text(
            row.get("college_name", "")
        )

        location = normalize_text(
            row.get("location", "")
        )

        latitude = normalize_number(
            row.get("latitude")
        )

        longitude = normalize_number(
            row.get("longitude")
        )

        mode = normalize_text(
            row.get("mode", "")
        )

        fee = normalize_number(
            row.get("fee", 0),
            0
        )

        start_date = normalize_date(
            row.get("start_date", "")
        )

        start_time = normalize_time(
            row.get("start_time", "")
        )

        end_date = normalize_date(
            row.get("end_date", "")
        )

        end_time = normalize_time(
            row.get("end_time", "")
        )

        registration_deadline = normalize_date(
            row.get("registration_deadline", "")
        )

        min_team_size = normalize_integer(
            row.get("min_team_size")
        )

        max_team_size = normalize_integer(
            row.get("max_team_size")
        )

        status = normalize_text(
            row.get("status", "")
        )

        source_url = normalize_text(
            row.get("source_url", "")
        )

        try:

            conn.execute("""
                INSERT INTO events (

                    event_id,
                    title,
                    description,
                    event_type,
                    category,
                    organizer,
                    college_name,
                    location,
                    latitude,
                    longitude,
                    mode,
                    fee,
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                    registration_deadline,
                    min_team_size,
                    max_team_size,
                    status,
                    source_url

                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?
                )

                ON CONFLICT(event_id)
                DO UPDATE SET

                    title = excluded.title,
                    description = excluded.description,
                    event_type = excluded.event_type,
                    category = excluded.category,
                    organizer = excluded.organizer,
                    college_name = excluded.college_name,
                    location = excluded.location,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    mode = excluded.mode,
                    fee = excluded.fee,
                    start_date = excluded.start_date,
                    start_time = excluded.start_time,
                    end_date = excluded.end_date,
                    end_time = excluded.end_time,
                    registration_deadline =
                        excluded.registration_deadline,
                    min_team_size =
                        excluded.min_team_size,
                    max_team_size =
                        excluded.max_team_size,
                    status = excluded.status,
                    source_url = excluded.source_url

            """, (
                event_id,
                title,
                description,
                event_type,
                category,
                organizer,
                college_name,
                location,
                latitude,
                longitude,
                mode,
                fee,
                start_date,
                start_time,
                end_date,
                end_time,
                registration_deadline,
                min_team_size,
                max_team_size,
                status,
                source_url
            ))

            imported_count += 1

        except Exception as error:

            skipped_count += 1

            print(
                f"⚠️ Could not import "
                f"{event_id}: {error}"
            )

    conn.commit()
    conn.close()

    print(
        f"✅ {imported_count} events imported/updated!"
    )

    if skipped_count:
        print(
            f"⚠️ {skipped_count} rows skipped."
        )

    print("========================================")


# ============================================================
# SIGNUP
# ============================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json(
        silent=True
    ) or {}

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
            "error":
                "name, email and password are required"
        }), 400

    hashed_password = generate_password_hash(
        password
    )

    conn = get_db()

    try:

        cursor = conn.execute("""
            INSERT INTO users (
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            hashed_password
        ))

        conn.commit()

        user_id = cursor.lastrowid

    except sqlite3.IntegrityError:

        conn.rollback()

        return jsonify({
            "error":
                "Email already registered"
        }), 409

    except Exception as error:

        conn.rollback()

        print("❌ Signup error:", error)

        return jsonify({
            "error":
                "Could not create account"
        }), 500

    finally:

        conn.close()

    return jsonify({
        "message":
            "Signup successful",
        "user_id":
            user_id
    }), 201


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not email or not password:

        return jsonify({
            "error":
                "email and password are required"
        }), 400

    conn = get_db()

    user = conn.execute("""
        SELECT
            id,
            name,
            email,
            password
        FROM users
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    conn.close()

    if not user:

        return jsonify({
            "error":
                "Invalid email or password"
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "error":
                "Invalid email or password"
        }), 401

    return jsonify({

        "message":
            "Login successful",

        "user": {

            "id":
                user["id"],

            "name":
                user["name"],

            "email":
                user["email"]

        }

    }), 200


# ============================================================
# GET ALL EVENTS
# ============================================================

@app.route("/api/events", methods=["GET"])
def get_events():

    conn = get_db()

    events = conn.execute("""
        SELECT *
        FROM events
        ORDER BY
            start_date,
            start_time
    """).fetchall()

    conn.close()

    return jsonify([
        dict(event)
        for event in events
    ])


# ============================================================
# GET SINGLE EVENT
# ============================================================

@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id):

    conn = get_db()

    event = conn.execute("""
        SELECT *
        FROM events
        WHERE event_id = ?
    """, (
        event_id,
    )).fetchone()

    conn.close()

    if not event:

        return jsonify({
            "error":
                "Event not found"
        }), 404

    return jsonify(
        dict(event)
    )


# ============================================================
# SEARCH EVENTS
# ============================================================

@app.route("/api/search", methods=["GET"])
def search_events():

    query = request.args.get(
        "q",
        ""
    ).strip()

    user_id = request.args.get(
        "user_id",
        type=int
    )

    if not query:

        return jsonify({
            "error":
                "Search query required"
        }), 400

    search_pattern = f"%{query}%"

    conn = get_db()

    events = conn.execute("""
        SELECT *
        FROM events

        WHERE
            title LIKE ?
            OR category LIKE ?
            OR event_type LIKE ?
            OR location LIKE ?
            OR organizer LIKE ?
            OR college_name LIKE ?
            OR description LIKE ?
            OR mode LIKE ?

        ORDER BY
            start_date,
            start_time

    """, (
        search_pattern,
        search_pattern,
        search_pattern,
        search_pattern,
        search_pattern,
        search_pattern,
        search_pattern,
        search_pattern
    )).fetchall()

    if user_id:

        conn.execute("""
            INSERT INTO user_activity (
                user_id,
                action,
                search_location
            )
            VALUES (?, 'search', ?)
        """, (
            user_id,
            query
        ))

        conn.commit()

    conn.close()

    return jsonify([
        dict(event)
        for event in events
    ])


# ============================================================
# RECORD ACTIVITY
# ============================================================

@app.route("/api/activity", methods=["POST"])
def record_activity():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get("user_id")
    event_id = data.get("event_id")

    action = str(
        data.get("action", "")
    ).strip().lower()

    search_location = data.get(
        "search_location"
    )

    allowed_actions = [
        "search",
        "view",
        "like",
        "save",
        "register"
    ]

    if not user_id or not action:

        return jsonify({
            "error":
                "user_id and action are required"
        }), 400

    if action not in allowed_actions:

        return jsonify({
            "error":
                "Invalid action"
        }), 400

    conn = get_db()

    if event_id:

        event = conn.execute("""
            SELECT event_id
            FROM events
            WHERE event_id = ?
        """, (
            event_id,
        )).fetchone()

        if not event:

            conn.close()

            return jsonify({
                "error":
                    "Event not found"
            }), 404

    conn.execute("""
        INSERT INTO user_activity (
            user_id,
            event_id,
            action,
            search_location
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        event_id,
        action,
        search_location
    ))

    conn.commit()
    conn.close()

    return jsonify({

        "message":
            "Activity recorded",

        "action":
            action

    })


# ============================================================
# SAVE USER PREFERENCES
# ============================================================

@app.route("/api/preferences", methods=["POST"])
def save_preferences():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get("user_id")

    if not user_id:

        return jsonify({
            "error":
                "user_id is required"
        }), 400

    location = str(
        data.get("location", "")
    ).strip()

    mode = str(
        data.get("mode", "")
    ).strip().lower()

    budget = normalize_number(
        data.get("budget")
    )

    interests = str(
        data.get("interests", "")
    ).strip()

    preferred_date = normalize_date(
        data.get("preferred_date", "")
    )

    preferred_start_time = normalize_time(
        data.get("preferred_start_time", "")
    )

    preferred_end_time = normalize_time(
        data.get("preferred_end_time", "")
    )

    max_distance_km = normalize_number(
        data.get("max_distance_km")
    )

    if (
        preferred_start_time
        and preferred_end_time
    ):

        try:

            start = datetime.strptime(
                preferred_start_time,
                "%H:%M"
            )

            end = datetime.strptime(
                preferred_end_time,
                "%H:%M"
            )

            if end <= start:

                return jsonify({
                    "error":
                        "preferred_end_time must be after preferred_start_time"
                }), 400

        except ValueError:

            return jsonify({
                "error":
                    "Invalid preferred time format"
            }), 400

    conn = get_db()

    try:

        existing = conn.execute("""
            SELECT id
            FROM user_preferences
            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()

        if existing:

            conn.execute("""
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

            """, (
                location,
                mode,
                budget,
                interests,
                preferred_date,
                preferred_start_time,
                preferred_end_time,
                max_distance_km,
                user_id
            ))

            action = "updated"

        else:

            conn.execute("""
                INSERT INTO user_preferences (

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

            """, (
                user_id,
                location,
                mode,
                budget,
                interests,
                preferred_date,
                preferred_start_time,
                preferred_end_time,
                max_distance_km
            ))

            action = "created"

        conn.commit()

    except Exception as error:

        conn.rollback()

        print(
            "❌ Error saving preferences:",
            error
        )

        return jsonify({
            "error":
                "Could not save preferences"
        }), 500

    finally:

        conn.close()

    return jsonify({

        "message":
            "Preferences saved successfully",

        "action":
            action,

        "preferences": {

            "user_id":
                user_id,

            "preferred_location":
                location,

            "preferred_mode":
                mode,

            "budget":
                budget,

            "interests":
                interests,

            "preferred_date":
                preferred_date,

            "preferred_start_time":
                preferred_start_time,

            "preferred_end_time":
                preferred_end_time,

            "max_distance_km":
                max_distance_km

        }

    })


# ============================================================
# GET USER PREFERENCES
# ============================================================

@app.route("/api/preferences/<int:user_id>", methods=["GET"])
def get_preferences(user_id):

    conn = get_db()

    preferences = conn.execute("""
        SELECT *
        FROM user_preferences
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()

    conn.close()

    if not preferences:

        return jsonify({
            "user_id":
                user_id,

            "preferences":
                None
        })

    return jsonify(
        dict(preferences)
    )


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    try:

        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

    except (
        TypeError,
        ValueError
    ):

        return None

    radius = 6371.0

    dlat = math.radians(
        lat2 - lat1
    )

    dlon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(
            math.radians(lat1)
        )
        *
        math.cos(
            math.radians(lat2)
        )
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# ============================================================
# GET USER ACTIVITY
# ============================================================

@app.route("/api/activity/<int:user_id>", methods=["GET"])
def get_activity(user_id):

    conn = get_db()

    activities = conn.execute("""
        SELECT
            ua.*,
            e.title,
            e.category,
            e.event_type,
            e.location

        FROM user_activity ua

        LEFT JOIN events e
        ON ua.event_id = e.event_id

        WHERE ua.user_id = ?

        ORDER BY
            ua.timestamp DESC
    """, (
        user_id,
    )).fetchall()

    conn.close()

    return jsonify([
        dict(activity)
        for activity in activities
    ])


# ============================================================
# PERSONALIZED EXPLORE FEED
# ============================================================

@app.route("/api/explore/<int:user_id>", methods=["GET"])
def explore_feed(user_id):

    requested_distance = request.args.get(
        "max_distance_km",
        type=float
    )

    conn = get_db()

    # --------------------------------------------------------
    # USER PREFERENCES
    # --------------------------------------------------------

    user = conn.execute("""
        SELECT *
        FROM user_preferences
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()

    preferred_location = ""
    preferred_mode = ""
    budget = None
    interests = ""
    max_distance = requested_distance

    if user:

        preferred_location = (
            user["preferred_location"]
            or ""
        ).lower().strip()

        preferred_mode = (
            user["preferred_mode"]
            or ""
        ).lower().strip()

        budget = user["budget"]

        interests = (
            user["interests"]
            or ""
        ).lower().strip()

        if max_distance is None:

            max_distance = (
                user["max_distance_km"]
            )

    # --------------------------------------------------------
    # USER ACTIVITY
    # --------------------------------------------------------

    activities = conn.execute("""
        SELECT *
        FROM user_activity
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (
        user_id,
    )).fetchall()

    category_scores = {}
    type_scores = {}
    location_scores = {}

    searched_locations = []

    # --------------------------------------------------------
    # LEARN FROM BEHAVIOUR
    # --------------------------------------------------------

    weights = {
        "view": 5,
        "like": 15,
        "save": 20,
        "register": 25
    }

    for activity in activities:

        action = (
            activity["action"]
            or ""
        ).lower()

        if action == "search":

            search_location = (
                activity["search_location"]
                or ""
            ).lower().strip()

            if search_location:

                searched_locations.append(
                    search_location
                )

                location_scores[
                    search_location
                ] = (
                    location_scores.get(
                        search_location,
                        0
                    ) + 10
                )

        event_id = activity["event_id"]

        if not event_id:
            continue

        event = conn.execute("""
            SELECT
                category,
                event_type,
                location
            FROM events
            WHERE event_id = ?
        """, (
            event_id,
        )).fetchone()

        if not event:
            continue

        category = (
            event["category"]
            or ""
        ).lower().strip()

        event_type = (
            event["event_type"]
            or ""
        ).lower().strip()

        location = (
            event["location"]
            or ""
        ).lower().strip()

        weight = weights.get(
            action,
            0
        )

        category_scores[category] = (
            category_scores.get(
                category,
                0
            ) + weight
        )

        type_scores[event_type] = (
            type_scores.get(
                event_type,
                0
            ) + weight
        )

        location_scores[location] = (
            location_scores.get(
                location,
                0
            ) + weight
        )

    # --------------------------------------------------------
    # FETCH EVENTS
    # --------------------------------------------------------

    events = conn.execute("""
        SELECT *
        FROM events
        ORDER BY
            start_date,
            start_time
    """).fetchall()

    recommendations = []

    # --------------------------------------------------------
    # SCORE EVENTS
    # --------------------------------------------------------

    for event in events:

        score = 0

        reasons = []

        category = (
            event["category"]
            or ""
        ).lower().strip()

        event_type = (
            event["event_type"]
            or ""
        ).lower().strip()

        location = (
            event["location"]
            or ""
        ).lower().strip()

        title = (
            event["title"]
            or ""
        ).lower().strip()

        description = (
            event["description"]
            or ""
        ).lower()

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        if (
            preferred_location
            and preferred_location in location
        ):

            score += 20

            reasons.append(
                "matches your preferred location"
            )

        # ----------------------------------------------------
        # SEARCH HISTORY
        # ----------------------------------------------------

        for searched in searched_locations:

            if (
                searched
                and searched in location
            ):

                score += 15

                reasons.append(
                    "matches your search history"
                )

                break

        # ----------------------------------------------------
        # LEARNED LOCATION
        # ----------------------------------------------------

        if location in location_scores:

            score += min(
                location_scores[location],
                25
            )

            reasons.append(
                "matches places you interact with"
            )

        # ----------------------------------------------------
        # INTERESTS
        # ----------------------------------------------------

        if interests:

            interest_words = [
                word.strip()
                for word in interests.split(",")
                if word.strip()
            ]

            for interest in interest_words:

                if (
                    interest in category
                    or interest in event_type
                    or interest in title
                    or interest in description
                ):

                    score += 20

                    reasons.append(
                        "matches your interests"
                    )

                    break

        # ----------------------------------------------------
        # LEARNED CATEGORY
        # ----------------------------------------------------

        if category in category_scores:

            score += min(
                category_scores[category],
                30
            )

            reasons.append(
                "matches categories you interact with"
            )

        # ----------------------------------------------------
        # LEARNED EVENT TYPE
        # ----------------------------------------------------

        if event_type in type_scores:

            score += min(
                type_scores[event_type],
                20
            )

            reasons.append(
                "matches event types you prefer"
            )

        # ----------------------------------------------------
        # MODE
        # ----------------------------------------------------

        event_mode = (
            event["mode"]
            or ""
        ).lower().strip()

        if (
            preferred_mode
            and preferred_mode == event_mode
        ):

            score += 10

            reasons.append(
                "matches your preferred mode"
            )

        # ----------------------------------------------------
        # BUDGET
        # ----------------------------------------------------

        if budget is not None:

            try:

                event_fee = float(
                    event["fee"] or 0
                )

                if event_fee <= float(budget):

                    score += 10

                    reasons.append(
                        "within your budget"
                    )

            except (
                TypeError,
                ValueError
            ):

                pass

        score = min(score, 100)

        if not reasons:

            reasons.append(
                "available event matching your profile"
            )

        recommendations.append({

            "event":
                dict(event),

            "match_score":
                score,

            "distance_km":
                None,

            "reason":
                "; ".join(reasons)

        })

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    recommendations.sort(
        key=lambda item: (
            item["match_score"],
            item["event"].get(
                "start_date",
                ""
            ),
            item["event"].get(
                "start_time",
                ""
            )
        ),
        reverse=True
    )

    conn.close()

    return jsonify({

        "user_id":
            user_id,

        "recommendations":
            recommendations

    })


# ============================================================
# REGISTER FOR EVENT
# ============================================================

@app.route("/api/register", methods=["POST"])
def register_event():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get("user_id")
    event_id = data.get("event_id")

    if not user_id or not event_id:

        return jsonify({
            "error":
                "user_id and event_id are required"
        }), 400

    conn = get_db()

    event = conn.execute("""
        SELECT *
        FROM events
        WHERE event_id = ?
    """, (
        event_id,
    )).fetchone()

    if not event:

        conn.close()

        return jsonify({
            "error":
                "Event not found"
        }), 404

    existing = conn.execute("""
        SELECT id
        FROM registrations
        WHERE
            user_id = ?
            AND event_id = ?
    """, (
        user_id,
        event_id
    )).fetchone()

    if existing:

        conn.close()

        return jsonify({

            "message":
                "Already registered for this event",

            "event_id":
                event_id

        })

    conn.execute("""
        INSERT INTO registrations (
            user_id,
            event_id
        )
        VALUES (?, ?)
    """, (
        user_id,
        event_id
    ))

    conn.execute("""
        INSERT INTO user_activity (
            user_id,
            event_id,
            action
        )
        VALUES (?, ?, 'register')
    """, (
        user_id,
        event_id
    ))

    conn.commit()
    conn.close()

    return jsonify({

        "message":
            "Event registration successful",

        "event_id":
            event_id

    }), 201


# ============================================================
# GET REGISTERED EVENTS
# ============================================================

@app.route("/api/registrations/<int:user_id>", methods=["GET"])
def get_registrations(user_id):

    conn = get_db()

    rows = conn.execute("""
        SELECT
            e.*,
            r.registered_at

        FROM registrations r

        JOIN events e
        ON r.event_id = e.event_id

        WHERE r.user_id = ?

        ORDER BY
            e.start_date,
            e.start_time

    """, (
        user_id,
    )).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# CHECK REGISTRATION
# ============================================================

@app.route(
    "/api/registrations/<int:user_id>/<event_id>",
    methods=["GET"]
)
def check_registration(
    user_id,
    event_id
):

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM registrations
        WHERE
            user_id = ?
            AND event_id = ?
    """, (
        user_id,
        event_id
    )).fetchone()

    conn.close()

    return jsonify({

        "registered":
            row is not None,

        "registration":
            dict(row)
            if row
            else None

    })


# ============================================================
# SAVE FREE TIME
# ============================================================

@app.route("/api/availability", methods=["POST"])
def save_availability():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get("user_id")

    date = normalize_date(
        data.get("date", "")
    )

    start_time = normalize_time(
        data.get("start_time", "")
    )

    end_time = normalize_time(
        data.get("end_time", "")
    )

    if not all([
        user_id,
        date,
        start_time,
        end_time
    ]):

        return jsonify({
            "error":
                "user_id, date, start_time and end_time are required"
        }), 400

    try:

        start = datetime.strptime(
            start_time,
            "%H:%M"
        )

        end = datetime.strptime(
            end_time,
            "%H:%M"
        )

        if end <= start:

            return jsonify({
                "error":
                    "end_time must be after start_time"
            }), 400

    except ValueError:

        return jsonify({
            "error":
                "Time must use HH:MM format"
        }), 400

    conn = get_db()

    conn.execute("""
        INSERT INTO availability (
            user_id,
            date,
            start_time,
            end_time
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        date,
        start_time,
        end_time
    ))

    conn.commit()
    conn.close()

    return jsonify({

        "message":
            "Free time saved successfully",

        "availability": {

            "user_id":
                user_id,

            "date":
                date,

            "start_time":
                start_time,

            "end_time":
                end_time

        }

    }), 201


# ============================================================
# GET USER FREE TIMES
# ============================================================

@app.route(
    "/api/availability/<int:user_id>",
    methods=["GET"]
)
def get_availability(user_id):

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM availability
        WHERE user_id = ?
        ORDER BY
            date,
            start_time
    """, (
        user_id,
    )).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# DELETE FREE TIME
# ============================================================

@app.route(
    "/api/availability/<int:availability_id>",
    methods=["DELETE"]
)
def delete_availability(
    availability_id
):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM availability
        WHERE id = ?
    """, (
        availability_id,
    ))

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:

        return jsonify({
            "error":
                "Availability not found"
        }), 404

    return jsonify({

        "message":
            "Availability deleted"

    })


# ============================================================
# TIME TO MINUTES
# ============================================================

def time_to_minutes(time_string):

    try:

        parsed = datetime.strptime(
            str(time_string)[:5],
            "%H:%M"
        )

        return (
            parsed.hour * 60
            + parsed.minute
        )

    except Exception:

        return None


# ============================================================
# FIND EVENTS DURING FREE TIME
# ============================================================

@app.route(
    "/api/free-time-events/<int:user_id>",
    methods=["GET"]
)
def free_time_events(user_id):

    conn = get_db()

    availability_rows = conn.execute("""
        SELECT *
        FROM availability
        WHERE user_id = ?
        ORDER BY
            date,
            start_time
    """, (
        user_id,
    )).fetchall()

    events = conn.execute("""
        SELECT *
        FROM events
        ORDER BY
            start_date,
            start_time
    """).fetchall()

    result = []

    for event in events:

        event_date = (
            event["start_date"]
            or ""
        )

        event_start = time_to_minutes(
            event["start_time"]
        )

        if event_start is None:
            continue

        event_end = time_to_minutes(
            event["end_time"]
        )

        if event_end is None:

            event_end = (
                event_start + 60
            )

        for free in availability_rows:

            if event_date != (
                free["date"] or ""
            ):
                continue

            free_start = time_to_minutes(
                free["start_time"]
            )

            free_end = time_to_minutes(
                free["end_time"]
            )

            if (
                free_start is None
                or free_end is None
            ):
                continue

            if (
                event_start >= free_start
                and event_end <= free_end
            ):

                result.append({

                    "event":
                        dict(event),

                    "fits_free_time":
                        True,

                    "free_date":
                        free["date"],

                    "free_start":
                        free["start_time"],

                    "free_end":
                        free["end_time"]

                })

                break

    conn.close()

    return jsonify(result)


# ============================================================
# HELPER — EVENT DATETIME
# ============================================================

def get_event_datetime(event):

    try:

        start_date = normalize_date(
            event["start_date"]
        )

        start_time = normalize_time(
            event["start_time"]
        )

        if not start_date or not start_time:
            return None

        return datetime.strptime(
            f"{start_date} {start_time}",
            "%Y-%m-%d %H:%M"
        )

    except Exception:

        return None


# ============================================================
# CREATE REMINDER
# ============================================================

@app.route("/api/reminder", methods=["POST"])
def create_reminder():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get("user_id")
    event_id = data.get("event_id")

    minutes_before = data.get(
        "minutes_before",
        60
    )

    if not user_id or not event_id:

        return jsonify({
            "error":
                "user_id and event_id are required"
        }), 400

    try:

        minutes_before = int(
            minutes_before
        )

        if minutes_before < 0:
            raise ValueError

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error":
                "minutes_before must be a non-negative number"
        }), 400

    conn = get_db()

    event = conn.execute("""
        SELECT *
        FROM events
        WHERE event_id = ?
    """, (
        event_id,
    )).fetchone()

    if not event:

        conn.close()

        return jsonify({
            "error":
                "Event not found"
        }), 404

    event_datetime = get_event_datetime(
        event
    )

    if event_datetime is None:

        conn.close()

        return jsonify({
            "error":
                "Invalid event date/time"
        }), 400

    reminder_datetime = (
        event_datetime
        - timedelta(
            minutes=minutes_before
        )
    )

    reminder_time = (
        reminder_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    message = (
        f"Reminder: "
        f"{event['title'] or 'Event'} "
        f"is starting soon."
    )

    existing = conn.execute("""
        SELECT id
        FROM notifications
        WHERE
            user_id = ?
            AND event_id = ?
            AND notification_type = 'event_reminder'
            AND reminder_time = ?
    """, (
        user_id,
        event_id,
        reminder_time
    )).fetchone()

    if existing:

        conn.close()

        return jsonify({

            "message":
                "Reminder already exists",

            "reminder_time":
                reminder_time

        })

    conn.execute("""
        INSERT INTO notifications (
            user_id,
            event_id,
            notification_type,
            message,
            reminder_time
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        event_id,
        "event_reminder",
        message,
        reminder_time
    ))

    conn.commit()
    conn.close()

    return jsonify({

        "message":
            "Reminder created",

        "reminder_time":
            reminder_time

    }), 201


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@app.route(
    "/api/notifications/<int:user_id>",
    methods=["GET"]
)
def get_notifications(user_id):

    conn = get_db()

    rows = conn.execute("""
        SELECT
            n.id,
            n.user_id,
            n.event_id,
            n.notification_type,
            n.message,
            n.reminder_time,
            n.is_sent,
            n.created_at,

            e.title,
            e.start_date,
            e.start_time,
            e.location

        FROM notifications n

        LEFT JOIN events e
        ON e.event_id = n.event_id

        WHERE n.user_id = ?

        ORDER BY
            n.id DESC

    """, (
        user_id,
    )).fetchall()

    registrations = conn.execute("""
        SELECT e.*
        FROM registrations r
        JOIN events e
        ON e.event_id = r.event_id
        WHERE r.user_id = ?
    """, (
        user_id,
    )).fetchall()

    conn.close()

    notifications = [
        dict(row)
        for row in rows
    ]

    now = datetime.now()

    for row in registrations:

        event = dict(row)

        event_start = get_event_datetime(
            event
        )

        if event_start is None:
            continue

        minutes_left = (
            event_start - now
        ).total_seconds() / 60

        if 0 <= minutes_left <= 1440:

            if minutes_left <= 60:

                message = (
                    "⏰ "
                    + str(event["title"])
                    + " starts within 1 hour."
                )

            else:

                message = (
                    "🔔 "
                    + str(event["title"])
                    + " is coming up today."
                )

            notifications.insert(
                0,
                {
                    "id": None,

                    "user_id":
                        user_id,

                    "event_id":
                        event["event_id"],

                    "notification_type":
                        "smart_reminder",

                    "message":
                        message,

                    "reminder_time":
                        None,

                    "is_sent":
                        0,

                    "created_at":
                        datetime.now().isoformat(),

                    "title":
                        event["title"],

                    "start_date":
                        event["start_date"],

                    "start_time":
                        event["start_time"],

                    "location":
                        event["location"],

                    "minutes_until_event":
                        round(minutes_left)
                }
            )

    return jsonify(notifications)


# ============================================================
# GET DUE NOTIFICATIONS
# ============================================================

@app.route(
    "/api/notifications/<int:user_id>/due",
    methods=["GET"]
)
def get_due_notifications(user_id):

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_db()

    notifications = conn.execute("""
        SELECT
            n.*,
            e.title,
            e.start_date,
            e.start_time,
            e.location

        FROM notifications n

        LEFT JOIN events e
        ON n.event_id = e.event_id

        WHERE
            n.user_id = ?
            AND n.reminder_time <= ?
            AND n.is_sent = 0

        ORDER BY
            n.reminder_time

    """, (
        user_id,
        current_time
    )).fetchall()

    conn.close()

    return jsonify([
        dict(notification)
        for notification in notifications
    ])


# ============================================================
# MARK NOTIFICATION SENT
# ============================================================

@app.route(
    "/api/notifications/<int:notification_id>/sent",
    methods=["POST"]
)
def mark_notification_sent(notification_id):

    conn = get_db()

    cursor = conn.execute("""
        UPDATE notifications
        SET is_sent = 1
        WHERE id = ?
    """, (
        notification_id,
    ))

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:

        return jsonify({
            "error":
                "Notification not found"
        }), 404

    return jsonify({

        "message":
            "Notification marked as sent"

    })


# ============================================================
# CALENDAR EVENT
# ============================================================

@app.route(
    "/api/calendar/<int:user_id>/<event_id>",
    methods=["GET"]
)
def calendar_event(
    user_id,
    event_id
):

    conn = get_db()

    registration = conn.execute("""
        SELECT *
        FROM registrations
        WHERE
            user_id = ?
            AND event_id = ?
    """, (
        user_id,
        event_id
    )).fetchone()

    event = conn.execute("""
        SELECT *
        FROM events
        WHERE event_id = ?
    """, (
        event_id,
    )).fetchone()

    conn.close()

    if not event:

        return jsonify({
            "error":
                "Event not found"
        }), 404

    if not registration:

        return jsonify({
            "error":
                "Register for the event before adding it to calendar"
        }), 403

    start_date = normalize_date(
        event["start_date"]
    )

    start_time = normalize_time(
        event["start_time"]
    )

    try:

        start = datetime.strptime(
            f"{start_date} {start_time}",
            "%Y-%m-%d %H:%M"
        )

        end_date = normalize_date(
            event["end_date"]
        )

        if not end_date:
            end_date = start_date

        end_time = normalize_time(
            event["end_time"]
        )

        if end_time:

            end = datetime.strptime(
                f"{end_date} {end_time}",
                "%Y-%m-%d %H:%M"
            )

        else:

            end = start + timedelta(
                hours=1
            )

        if end <= start:

            end = start + timedelta(
                hours=1
            )

    except Exception:

        return jsonify({
            "error":
                "Invalid event date/time"
        }), 400

    def escape_ics(value):

        value = str(value or "")

        value = value.replace(
            "\\",
            "\\\\"
        )

        value = value.replace(
            ";",
            "\\;"
        )

        value = value.replace(
            ",",
            "\\,"
        )

        value = value.replace(
            "\n",
            "\\n"
        )

        return value

    title = escape_ics(
        event["title"] or "Event"
    )

    location = escape_ics(
        event["location"] or ""
    )

    description = escape_ics(
        event["description"] or ""
    )

    start_string = start.strftime(
        "%Y%m%dT%H%M%S"
    )

    end_string = end.strftime(
        "%Y%m%dT%H%M%S"
    )

    timestamp = datetime.utcnow().strftime(
        "%Y%m%dT%H%M%SZ"
    )

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Event Recommendation System//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:{escape_ics(event_id)}@event-recommender
DTSTAMP:{timestamp}
DTSTART:{start_string}
DTEND:{end_string}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""

    return Response(
        ics,
        mimetype="text/calendar",
        headers={
            "Content-Disposition":
                f"attachment; filename={event_id}.ics"
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/api/dashboard/<int:user_id>",
    methods=["GET"]
)
def dashboard(user_id):

    conn = get_db()

    registrations = conn.execute("""
        SELECT COUNT(*) AS count
        FROM registrations
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()["count"]

    saved = conn.execute("""
        SELECT COUNT(*) AS count
        FROM user_activity
        WHERE
            user_id = ?
            AND action = 'save'
    """, (
        user_id,
    )).fetchone()["count"]

    liked = conn.execute("""
        SELECT COUNT(*) AS count
        FROM user_activity
        WHERE
            user_id = ?
            AND action = 'like'
    """, (
        user_id,
    )).fetchone()["count"]

    viewed = conn.execute("""
        SELECT COUNT(*) AS count
        FROM user_activity
        WHERE
            user_id = ?
            AND action = 'view'
    """, (
        user_id,
    )).fetchone()["count"]

    searches = conn.execute("""
        SELECT COUNT(*) AS count
        FROM user_activity
        WHERE
            user_id = ?
            AND action = 'search'
    """, (
        user_id,
    )).fetchone()["count"]

    notifications = conn.execute("""
        SELECT COUNT(*) AS count
        FROM notifications
        WHERE
            user_id = ?
            AND is_sent = 0
    """, (
        user_id,
    )).fetchone()["count"]

    conn.close()

    return jsonify({

        "user_id":
            user_id,

        "registrations":
            registrations,

        "saved_events":
            saved,

        "liked_events":
            liked,

        "viewed_events":
            viewed,

        "searches":
            searches,

        "pending_notifications":
            notifications

    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "message":
            "Event Recommendation API is running",

        "status":
            "online",

        "database":
            DATABASE,

        "excel":
            EXCEL_FILE,

        "features": [

            "User Signup",
            "User Login",
            "Event Database",
            "Excel Import",
            "Event Search",

            "Personalized Recommendations",
            "Location Matching",
            "Budget Matching",
            "Mode Matching",
            "Interest Matching",
            "Behaviour Based Recommendations",

            "Search History",
            "View History",
            "Like History",
            "Save History",

            "Event Registration",
            "Registered Events",

            "Free Time Management",
            "Free Time Event Matching",

            "Calendar Integration",
            "ICS Calendar Download",

            "Smart Reminders",
            "Notifications",

            "Dashboard Statistics"

        ]

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    create_database()

    import_events()

    print()
    print("========================================")
    print("       EVENT RECOMMENDATION SYSTEM")
    print("========================================")

    print(
        "Database :",
        DATABASE
    )

    print(
        "Excel    :",
        EXCEL_FILE
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