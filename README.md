# 🎯 AI-Powered Event Recommendation System

An AI-assisted personalized event discovery platform that helps users find relevant events based on their interests, budget, location, date, time, event mode, distance, and availability.

The system combines **machine learning-based text similarity, Flask APIs, SQLite database management, and a web-based frontend** to provide a complete event discovery and planning experience.

---

## 🚀 Features

* 🤖 **Personalized Event Recommendations**

  * Uses TF-IDF vectorization and cosine similarity to identify relevant events.
  * Ranks events based on their similarity to the user's search query.

* 🎯 **Match Score**

  * Displays a similarity-based match score for recommended events.

* 🔍 **Smart Event Search**

  * Search events by title, description, category, event type, organizer, college, location, and mode.

* 👤 **User Account Management**

  * User registration and login.
  * Stores user information securely in the database.

* 📝 **User Preferences**

  * Users can specify:

    * Interests
    * Preferred location
    * Event mode
    * Budget
    * Preferred date
    * Preferred time
    * Maximum travel distance

* ⏰ **Availability-Based Event Matching**

  * Users can enter their available date and time.
  * The system identifies events that fit within their available schedule.

* 📌 **Event Registration**

  * Users can register for events.
  * Registered events can be viewed later.

* 📅 **Calendar Integration**

  * Events can be exported as calendar files for easier planning.

* 🔔 **Reminders and Notifications**

  * Users can create reminders for registered events.
  * Notification information is stored and displayed through the system.

* 📍 **Location-Aware Event Information**

  * Displays event location and college/organizer information where available.

---

## 🧠 Recommendation System

The recommendation engine follows this workflow:

```text
User enters a search query
          ↓
     Text Processing
          ↓
      TF-IDF Vectorization
          ↓
     Query Vector
          ↓
Compare with Event Vectors
          ↓
    Cosine Similarity
          ↓
    Similarity Scores
          ↓
     Rank Events
          ↓
Top Recommended Events
```

### TF-IDF

**TF-IDF (Term Frequency-Inverse Document Frequency)** converts text into numerical vectors.

It determines the importance of words within the event information and user query.

### Cosine Similarity

Cosine similarity measures how similar the user's query vector is to each event vector.

A higher similarity score indicates that the event text is more closely related to the user's query.

For example:

```text
Event A → 0.91
Event B → 0.76
Event C → 0.42
Event D → 0.18
```

The system ranks the events based on these similarity scores.

> Note: The similarity score represents textual similarity, not the probability that a user will attend the event.

---

## 🏗️ System Architecture

```text
                    USER
                     │
                     ▼
             Web Frontend
          HTML + CSS + JavaScript
                     │
                     │ HTTP / JSON
                     ▼
             Flask REST API
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
       SQLite     ML Model    Event Data
      Database      .pkl       Dataset
          │          │          │
          └──────────┼──────────┘
                     ▼
              JSON Response
                     │
                     ▼
                 Frontend
                     │
                     ▼
              Display Results
```

---

## 🛠️ Technologies Used

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask
* Flask-CORS
* REST APIs

### Machine Learning

* Scikit-learn
* TF-IDF Vectorization
* Cosine Similarity
* Joblib

### Database

* SQLite

### Data Processing

* Pandas
* Excel dataset

---

## 🗄️ Database

The project uses **SQLite** as the database.

The database stores information related to:

```text
users
events
user_preferences
user_activity
registrations
availability
notifications
```

The database is used for user accounts, preferences, registrations, availability information, activity tracking, and notifications.

---

## 📊 Dataset

The project uses an event dataset containing information such as:

* Event ID
* Event title
* Description
* Event type
* Category
* Organizer
* College name
* Location
* Latitude
* Longitude
* Event mode
* Fee
* Start date
* Start time
* End date
* Registration deadline
* Team size
* Status
* Source URL

The current project uses an event dataset containing **100 events**.

Dataset file:

```text
data/events_100_complete.xlsx
```

---

## 📁 Project Structure

```text
event-recommendation-system/
│
├── backend/
│   ├── app.py
│   └── database.db
│
├── data/
│   └── events_100_complete.xlsx
│
├── frontend.js/
│   ├── index.html
│   ├── dashboard.html
│   ├── events.html
│   ├── preferences.html
│   ├── registered.html
│   ├── availability.html
│   ├── script.js
│   └── style.css
│
├── ml/
│   └── event_recommender_model.pkl
│
├── recommendation/
│   └── recommendation.py
│
├── .gitignore
└── README.md
```

---

## 🔄 Complete Workflow

```text
1. User creates an account
             ↓
2. User logs in
             ↓
3. User provides preferences
             ↓
4. Preferences are stored in SQLite
             ↓
5. User searches for an event
             ↓
6. Flask receives the request
             ↓
7. TF-IDF converts the query into a vector
             ↓
8. Cosine similarity compares it with event vectors
             ↓
9. Events are ranked by similarity
             ↓
10. Recommended events are returned as JSON
             ↓
11. Frontend displays the recommendations
             ↓
12. User can register for an event
             ↓
13. User can save availability
             ↓
14. Matching events are identified
             ↓
15. User can create reminders
             ↓
16. Event can be added to calendar
```

---

## ▶️ How to Run

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd event-recommendation-system
```

### 2. Create and activate the virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install flask flask-cors pandas scikit-learn joblib openpyxl
```

### 4. Start the Flask backend

Open Terminal 1:

```powershell
cd backend
python app.py
```

The backend runs at:

```text
http://127.0.0.1:5000
```

### 5. Start the frontend

Open Terminal 2:

```powershell
cd frontend.js
python -m http.server 5500
```

The frontend runs at:

```text
http://127.0.0.1:5500/
```

### 6. Open the website

Open your browser and visit:

```text
http://127.0.0.1:5500/
```

---

## 🔌 Important API Endpoints

| Method | Endpoint                             | Purpose                      |
| ------ | ------------------------------------ | ---------------------------- |
| GET    | `/`                                  | Check backend                |
| GET    | `/api/health`                        | Backend and ML health check  |
| POST   | `/api/signup`                        | Create account               |
| POST   | `/api/login`                         | User login                   |
| GET    | `/api/events`                        | Get all events               |
| GET    | `/api/events/<event_id>`             | Get one event                |
| POST   | `/api/recommendations`               | Generate recommendations     |
| POST   | `/api/preferences`                   | Save user preferences        |
| POST   | `/api/register`                      | Register for an event        |
| GET    | `/api/registrations/<user_id>`       | Get registered events        |
| POST   | `/api/activity`                      | Record user activity         |
| GET    | `/api/search?q=<query>`              | Search events                |
| POST   | `/api/availability`                  | Save free time               |
| GET    | `/api/free-time-events/<user_id>`    | Find events during free time |
| GET    | `/api/notifications/<user_id>`       | Get notifications            |
| POST   | `/api/reminder`                      | Create event reminder        |
| GET    | `/api/calendar/<user_id>/<event_id>` | Generate calendar event      |
| GET    | `/api/database-test`                 | Test database connection     |

---

## 💡 Innovation

### 🤖 AI-Assisted Recommendations

Uses text similarity to identify events relevant to the user's natural-language search.

### 🎯 Personalized Discovery

Combines user preferences such as interests, budget, location, mode, date, time, and distance.

### ⏰ Availability-Aware Discovery

Finds events that fit within the user's available schedule.

### 🔍 Smart Search

Searches multiple event attributes rather than only event titles.

### 📅 Integrated Event Planning

Combines discovery, registration, reminders, availability, and calendar integration.

### 🔔 Notification Support

Provides event reminders and notification information for registered activities.

---

## 🔮 Future Enhancements

* XGBoost or other supervised learning models for improved personalized ranking.
* Real-time event data collection from external event platforms.
* Google Maps integration for route and travel-time estimation.
* Advanced recommendation models using user behavior.
* Multilingual natural-language search.
* Email/SMS/push notifications.
* Real-time event availability and registration status.
* Improved explainable recommendations showing why each event was selected.

---

## ⚠️ Security Note

For production deployment, passwords should **never be stored as plain text**.

A production version should use secure password hashing such as:

```text
Werkzeug password hashing
bcrypt
Argon2
```

Sensitive configuration values should also be stored using environment variables.

---

## 👩‍💻 Project

**AI-Powered Event Recommendation System**

Built using:

```text
Python
Flask
SQLite
Scikit-learn
TF-IDF
Cosine Similarity
HTML
CSS
JavaScript
Pandas
```

---
