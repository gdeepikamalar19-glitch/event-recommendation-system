// ============================================================
// EVENT RECOMMENDER FRONTEND
// ============================================================

const API = "http://127.0.0.1:5000";


// ============================================================
// USER
// ============================================================

function getUser() {

    const user = localStorage.getItem("user");

    if (!user) {
        return null;
    }

    try {
        return JSON.parse(user);
    } catch (error) {
        console.error("Invalid user data:", error);
        return null;
    }
}


function getUserId() {

    const user = getUser();

    if (!user) {
        return null;
    }

    return user.id;
}


// ============================================================
// LOGIN / SIGNUP PAGE
// ============================================================

function showSignup() {

    const loginBox = document.getElementById("loginBox");
    const signupBox = document.getElementById("signupBox");

    if (loginBox) {
        loginBox.classList.add("hidden");
    }

    if (signupBox) {
        signupBox.classList.remove("hidden");
    }
}


function showLogin() {

    const signupBox = document.getElementById("signupBox");
    const loginBox = document.getElementById("loginBox");

    if (signupBox) {
        signupBox.classList.add("hidden");
    }

    if (loginBox) {
        loginBox.classList.remove("hidden");
    }
}


// ============================================================
// SIGNUP
// ============================================================

const signupForm = document.getElementById("signupForm");

if (signupForm) {

    signupForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name =
            document.getElementById("signupName").value.trim();

        const email =
            document.getElementById("signupEmail").value.trim();

        const password =
            document.getElementById("signupPassword").value;

        const message =
            document.getElementById("signupMessage");

        try {

            const response = await fetch(
                API + "/api/signup",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        name: name,
                        email: email,
                        password: password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {

                message.className = "error";

                message.textContent =
                    data.error || "Signup failed.";

                return;
            }

            message.className = "success";

            message.textContent =
                "Account created successfully! Please login.";

            signupForm.reset();

        } catch (error) {

            console.error("Signup error:", error);

            message.className = "error";

            message.textContent =
                "Cannot connect to backend.";
        }

    });

}


// ============================================================
// LOGIN
// ============================================================

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const email =
            document.getElementById("loginEmail").value.trim();

        const password =
            document.getElementById("loginPassword").value;

        const message =
            document.getElementById("loginMessage");

        try {

            const response = await fetch(
                API + "/api/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {

                message.className = "error";

                message.textContent =
                    data.error || "Login failed.";

                return;
            }

            localStorage.setItem(
                "user",
                JSON.stringify(data.user)
            );

            window.location.href = "dashboard.html";

        } catch (error) {

            console.error("Login error:", error);

            message.className = "error";

            message.textContent =
                "Cannot connect to backend.";
        }

    });

}


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    localStorage.removeItem("user");

    window.location.href = "index.html";
}


// ============================================================
// PROTECT PAGES
// ============================================================

function checkLogin() {

    const user = getUser();

    const currentPage =
        window.location.pathname
            .split("/")
            .pop();

    if (
        currentPage !== "index.html" &&
        currentPage !== "" &&
        !user
    ) {

        window.location.href = "index.html";
    }
}

checkLogin();


// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {

    const user = getUser();

    if (!user) {
        return;
    }

    const username =
        document.getElementById("username");

    if (username) {
        username.textContent = user.name;
    }

    try {

        // ----------------------------------------------------
        // LOAD ALL EVENTS
        // ----------------------------------------------------

        const eventsResponse =
            await fetch(API + "/api/events");

        const events =
            await eventsResponse.json();

        const totalEvents =
            document.getElementById("totalEvents");

        if (totalEvents) {
            totalEvents.textContent =
                events.length;
        }


        // ----------------------------------------------------
        // REGISTERED EVENTS
        // ----------------------------------------------------

        const regResponse =
            await fetch(
                API +
                "/api/registrations/" +
                user.id
            );

        const registered =
            await regResponse.json();

        const registeredCount =
            document.getElementById(
                "registeredCount"
            );

        if (registeredCount) {
            registeredCount.textContent =
                Array.isArray(registered)
                    ? registered.length
                    : 0;
        }


        // ----------------------------------------------------
        // NOTIFICATIONS
        // ----------------------------------------------------

        const notificationResponse =
            await fetch(
                API +
                "/api/notifications/" +
                user.id
            );

        const notifications =
            await notificationResponse.json();

        const notificationCount =
            document.getElementById(
                "notificationCount"
            );

        if (notificationCount) {

            notificationCount.textContent =
                Array.isArray(notifications)
                    ? notifications.length
                    : 0;
        }

        displayNotifications(notifications);


        // ----------------------------------------------------
        // ML RECOMMENDATIONS
        // ----------------------------------------------------

        let interests =
            user.interests ||
            user.interest ||
            "";

        /*
         If the user has not saved interests yet,
         use a default technology query.
        */

        if (!interests.trim()) {

            interests =
                "technology programming artificial intelligence machine learning Python";
        }

        console.log(
            "Sending interests to ML:",
            interests
        );


        const recommendationResponse =
            await fetch(
                API + "/api/recommendations",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        query: interests,

                        limit: 6
                    })
                }
            );


        const recommendationData =
            await recommendationResponse.json();


        console.log(
            "ML response:",
            recommendationData
        );


        if (!recommendationResponse.ok) {

            throw new Error(
                recommendationData.error ||
                "Recommendation API failed."
            );
        }


        displayMLRecommendations(
            recommendationData.recommendations
        );

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

        const container =
            document.getElementById(
                "recommendations"
            );

        if (container) {

            container.innerHTML =
                "<p>Unable to load recommendations.</p>";
        }
    }
}


// ============================================================
// DISPLAY ML RECOMMENDATIONS
// ============================================================

function displayMLRecommendations(
    recommendations
) {

    const container =
        document.getElementById(
            "recommendations"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";


    if (
        !recommendations ||
        recommendations.length === 0
    ) {

        container.innerHTML =
            "<p>No recommendations found.</p>";

        return;
    }


    recommendations.forEach(event => {

        const score =
            Math.round(
                (event.similarity_score || 0) * 100
            );


        container.innerHTML +=
            createEventCard(
                event,
                score,
                true
            );

    });
}


// ============================================================
// MANUAL ML RECOMMENDATION
// ============================================================

async function loadMLRecommendations(
    interests
) {

    const container =
        document.getElementById(
            "recommendations"
        );

    if (!container) {
        return;
    }


    if (
        !interests ||
        !interests.trim()
    ) {

        interests =
            "technology programming AI machine learning Python";
    }


    container.innerHTML =
        "<p>Finding events for you...</p>";


    try {

        const response =
            await fetch(
                API + "/api/recommendations",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        query: interests,

                        limit: 6
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Recommendation failed."
            );
        }


        console.log(
            "ML recommendations:",
            data
        );


        displayMLRecommendations(
            data.recommendations
        );


    } catch (error) {

        console.error(
            "ML recommendation error:",
            error
        );


        container.innerHTML =
            "<p>Unable to load recommendations.</p>";
    }
}


// ============================================================
// LOAD ALL EVENTS
// ============================================================

async function loadEvents() {

    const container =
        document.getElementById(
            "events"
        );

    if (!container) {
        return;
    }


    container.innerHTML =
        "<p>Loading events...</p>";


    try {

        const response =
            await fetch(
                API + "/api/events"
            );


        if (!response.ok) {

            throw new Error(
                "Backend error"
            );
        }


        const events =
            await response.json();


        container.innerHTML = "";


        if (
            !Array.isArray(events) ||
            events.length === 0
        ) {

            container.innerHTML =
                "<p>No events available.</p>";

            return;
        }


        events.forEach(event => {

            container.innerHTML +=
                createEventCard(
                    event,
                    null,
                    false
                );

        });


    } catch (error) {

        console.error(
            "Load events error:",
            error
        );


        container.innerHTML = `

            <div class="event-card">

                <h3>Cannot connect to backend</h3>

                <p>
                    Make sure Flask is running at
                    ${API}
                </p>

            </div>

        `;
    }
}


// ============================================================
// EVENT CARD
// ============================================================

function createEventCard(
    event,
    score,
    recommended
) {

    const safeTitle =
        event.title ||
        "Untitled Event";


    const description =
        event.description ||
        "No description available.";


    const location =
        event.location ||
        "Location not available";


    const date =
        event.start_date ||
        "Date not available";


    const time =
        event.start_time ||
        "Time not available";


    const fee =
        event.fee ?? 0;


    const category =
        event.category ||
        "General";


    const mode =
        event.mode ||
        "Not specified";


    const scoreHTML =
        score !== null &&
        score !== undefined
            ?
            `
            <div class="event-score">
                ⭐ ${score}% Match
            </div>
            `
            :
            "";


    return `

        <div class="event-card">

            <h3>
                ${safeTitle}
            </h3>

            ${scoreHTML}

            <p>
                ${description}
            </p>

            <p>
                📍 ${location}
            </p>

            <p>
                📅 ${date}
            </p>

            <p>
                ⏰ ${time}
            </p>

            <p>
                💰 ₹${fee}
            </p>

            <p>
                🏷️ ${category}
            </p>

            <p>
                💻 ${mode}
            </p>


            <button
                onclick="viewEvent('${event.event_id}')">

                View

            </button>


            <button
                onclick="registerEvent('${event.event_id}')">

                Register

            </button>


            <button
                onclick="saveEvent('${event.event_id}')">

                Save

            </button>

        </div>

    `;
}


// ============================================================
// VIEW EVENT
// ============================================================

async function viewEvent(eventId) {

    const userId =
        getUserId();


    if (!userId) {
        return;
    }


    try {

        const response =
            await fetch(
                API + "/api/activity",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id: userId,

                        event_id: eventId,

                        action: "view"
                    })
                }
            );


        if (!response.ok) {

            console.warn(
                "Activity endpoint returned:",
                response.status
            );

        }


        alert(
            "Event viewed. Your recommendations can learn from this."
        );


    } catch (error) {

        console.error(
            "View event error:",
            error
        );
    }
}


// ============================================================
// SAVE EVENT
// ============================================================

async function saveEvent(eventId) {

    const userId =
        getUserId();


    if (!userId) {
        return;
    }


    try {

        const response =
            await fetch(
                API + "/api/activity",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id: userId,

                        event_id: eventId,

                        action: "save"
                    })
                }
            );


        if (!response.ok) {

            console.warn(
                "Save endpoint returned:",
                response.status
            );
        }


        alert(
            "Event saved!"
        );


    } catch (error) {

        console.error(
            "Save event error:",
            error
        );
    }
}


// ============================================================
// REGISTER EVENT
// ============================================================

async function registerEvent(eventId) {

    const userId =
        getUserId();


    if (!userId) {

        alert(
            "Please login first."
        );

        return;
    }


    try {

        const response =
            await fetch(
                API + "/api/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id: userId,

                        event_id: eventId
                    })
                }
            );


        const data =
            await response.json();


        alert(
            data.message ||
            data.error ||
            "Registration completed."
        );


    } catch (error) {

        console.error(
            "Registration error:",
            error
        );


        alert(
            "Registration failed."
        );
    }
}


// ============================================================
// SEARCH EVENTS
// ============================================================

async function searchEvents() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );


    const container =
        document.getElementById(
            "events"
        );


    if (!searchInput || !container) {
        return;
    }


    const query =
        searchInput.value.trim();


    if (!query) {

        loadEvents();

        return;
    }


    try {

        const response =
            await fetch(
                API +
                "/api/search?q=" +
                encodeURIComponent(query)
            );


        const events =
            await response.json();


        container.innerHTML = "";


        if (
            !Array.isArray(events) ||
            events.length === 0
        ) {

            container.innerHTML =
                "<p>No matching events found.</p>";

            return;
        }


        events.forEach(event => {

            container.innerHTML +=
                createEventCard(
                    event,
                    null,
                    false
                );

        });


    } catch (error) {

        console.error(
            "Search error:",
            error
        );


        container.innerHTML =
            "<p class='error'>Search failed.</p>";
    }
}


// ============================================================
// PREFERENCES
// ============================================================

const preferencesForm =
    document.getElementById(
        "preferencesForm"
    );


if (preferencesForm) {

    preferencesForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const userId =
                getUserId();


            if (!userId) {
                return;
            }


            const interestsElement =
                document.getElementById(
                    "interests"
                );


            const interests =
                interestsElement
                    ? interestsElement.value.trim()
                    : "";


            const data = {

                user_id: userId,

                location:
                    document.getElementById(
                        "preferredLocation"
                    )?.value || "",

                mode:
                    document.getElementById(
                        "preferredMode"
                    )?.value || "",

                budget:
                    document.getElementById(
                        "budget"
                    )?.value || null,

                interests:
                    interests,

                preferred_date:
                    document.getElementById(
                        "preferredDate"
                    )?.value || "",

                preferred_start_time:
                    document.getElementById(
                        "preferredStartTime"
                    )?.value || "",

                preferred_end_time:
                    document.getElementById(
                        "preferredEndTime"
                    )?.value || "",

                max_distance_km:
                    document.getElementById(
                        "maxDistance"
                    )?.value || null
            };


            try {

                const response =
                    await fetch(
                        API +
                        "/api/preferences",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(data)
                        }
                    );


                const result =
                    await response.json();


                const message =
                    document.getElementById(
                        "preferencesMessage"
                    );


                if (!response.ok) {

                    if (message) {

                        message.className =
                            "error";

                        message.textContent =
                            result.error ||
                            "Failed to save.";
                    }

                    return;
                }


                if (message) {

                    message.className =
                        "success";

                    message.textContent =
                        "Preferences saved successfully!";
                }


                // ------------------------------------------------
                // SAVE INTERESTS LOCALLY
                // ------------------------------------------------

                const currentUser =
                    getUser();


                if (currentUser) {

                    currentUser.interests =
                        interests;


                    localStorage.setItem(
                        "user",
                        JSON.stringify(currentUser)
                    );
                }


                // ------------------------------------------------
                // IMMEDIATELY REFRESH ML
                // ------------------------------------------------

                await loadMLRecommendations(
                    interests
                );


            } catch (error) {

                console.error(
                    "Preferences error:",
                    error
                );


                const message =
                    document.getElementById(
                        "preferencesMessage"
                    );


                if (message) {

                    message.className =
                        "error";

                    message.textContent =
                        "Cannot connect to backend.";
                }
            }

        }
    );

}


// ============================================================
// REGISTERED EVENTS
// ============================================================

async function loadRegisteredEvents() {

    const container =
        document.getElementById(
            "registeredEvents"
        );


    if (!container) {
        return;
    }


    const userId =
        getUserId();


    if (!userId) {
        return;
    }


    try {

        const response =
            await fetch(
                API +
                "/api/registrations/" +
                userId
            );


        const events =
            await response.json();


        container.innerHTML = "";


        if (
            !Array.isArray(events) ||
            events.length === 0
        ) {

            container.innerHTML =
                "<p>You have not registered for any events.</p>";

            return;
        }


        events.forEach(event => {

            container.innerHTML += `

                <div class="event-card">

                    <h3>
                        ${event.title}
                    </h3>

                    <p>
                        📍 ${event.location || "N/A"}
                    </p>

                    <p>
                        📅 ${event.start_date || "N/A"}
                    </p>

                    <p>
                        ⏰ ${event.start_time || "N/A"}
                    </p>

                    <p>
                        📝 Registered:
                        ${event.registered_at || "N/A"}
                    </p>


                    <button
                        onclick="addToCalendar('${event.event_id}')">

                        Add to Calendar

                    </button>


                    <button
                        onclick="createReminder('${event.event_id}')">

                        Set Reminder

                    </button>

                </div>

            `;
        });


    } catch (error) {

        console.error(
            "Registered events error:",
            error
        );


        container.innerHTML =
            "<p class='error'>Cannot load registered events.</p>";
    }
}


// ============================================================
// CALENDAR
// ============================================================

function addToCalendar(eventId) {

    const userId =
        getUserId();


    if (!userId) {
        return;
    }


    const url =
        API +
        "/api/calendar/" +
        userId +
        "/" +
        eventId;


    window.open(
        url,
        "_blank"
    );
}


// ============================================================
// REMINDER
// ============================================================

async function createReminder(eventId) {

    const userId =
        getUserId();


    if (!userId) {
        return;
    }


    const minutes =
        prompt(
            "How many minutes before the event?",
            "60"
        );


    if (!minutes) {
        return;
    }


    try {

        const response =
            await fetch(
                API + "/api/reminder",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id: userId,

                        event_id: eventId,

                        minutes_before:
                            Number(minutes)
                    })
                }
            );


        const data =
            await response.json();


        alert(

            (data.message ||
                "Reminder created") +

            "\nReminder: " +

            (data.reminder_time || "")
        );


    } catch (error) {

        console.error(
            "Reminder error:",
            error
        );


        alert(
            "Could not create reminder."
        );
    }
}


// ============================================================
// AVAILABILITY / FREE TIME
// ============================================================

const availabilityForm =
    document.getElementById(
        "availabilityForm"
    );


if (availabilityForm) {

    availabilityForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const userId =
                getUserId();


            if (!userId) {

                alert(
                    "Please login first."
                );

                return;
            }


            const date =
                document.getElementById(
                    "availabilityDate"
                )?.value || "";


            const startTime =
                document.getElementById(
                    "availabilityStart"
                )?.value || "";


            const endTime =
                document.getElementById(
                    "availabilityEnd"
                )?.value || "";


            const message =
                document.getElementById(
                    "availabilityMessage"
                );


            if (
                !date ||
                !startTime ||
                !endTime
            ) {

                if (message) {

                    message.className =
                        "error";

                    message.textContent =
                        "Please fill all fields.";
                }

                return;
            }


            if (startTime >= endTime) {

                if (message) {

                    message.className =
                        "error";

                    message.textContent =
                        "End time must be after start time.";
                }

                return;
            }


            try {

                const response =
                    await fetch(
                        API +
                        "/api/availability",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                user_id: userId,

                                free_date: date,

                                free_start: startTime,

                                free_end: endTime
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    if (message) {

                        message.className =
                            "error";

                        message.textContent =
                            data.error ||
                            "Failed to save free time.";
                    }

                    return;
                }


                if (message) {

                    message.className =
                        "success";

                    message.textContent =
                        "Free time saved successfully!";
                }


                availabilityForm.reset();


                setTimeout(
                    loadFreeTimeEvents,
                    500
                );


            } catch (error) {

                console.error(
                    "Availability error:",
                    error
                );


                if (message) {

                    message.className =
                        "error";

                    message.textContent =
                        "Cannot connect to backend.";
                }
            }

        }
    );

}


// ============================================================
// FIND EVENTS DURING FREE TIME
// ============================================================

async function loadFreeTimeEvents() {

    const container =
        document.getElementById(
            "freeTimeEvents"
        );


    if (!container) {
        return;
    }


    const userId =
        getUserId();


    if (!userId) {

        container.innerHTML =
            "<p>Please login first.</p>";

        return;
    }


    container.innerHTML =
        "<p>Finding matching events...</p>";


    try {

        const response =
            await fetch(
                API +
                "/api/free-time-events/" +
                userId
            );


        const results =
            await response.json();


        if (!response.ok) {

            container.innerHTML =
                `
                <p class="error">
                    ${
                        results.error ||
                        "Could not load events."
                    }
                </p>
                `;

            return;
        }


        if (
            !Array.isArray(results) ||
            results.length === 0
        ) {

            container.innerHTML =
                `
                <p>
                    No events found during your free time.
                </p>
                `;

            return;
        }


        container.innerHTML = "";


        results.forEach(item => {

            const event =
                item.event || item;


            const title =
                event.title ||
                "Untitled Event";


            const startDate =
                event.start_date ||
                "N/A";


            const startTime =
                event.start_time ||
                "N/A";


            const endTime =
                event.end_time ||
                "N/A";


            const location =
                event.location ||
                "N/A";


            const mode =
                event.mode ||
                "N/A";


            const fee =
                event.fee ?? 0;


            const category =
                event.category ||
                "General";


            const freeMessage =
                item.free_time_message ||
                "You are free during this event.";


            const freeStart =
                item.free_start ||
                "";


            const freeEnd =
                item.free_end ||
                "";


            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "event-card";


            card.innerHTML = `

                <h3>
                    ${title}
                </h3>

                <p>
                    📅 ${startDate}
                </p>

                <p>
                    ⏰ ${startTime}
                    -
                    ${endTime}
                </p>

                <p>
                    📍 ${location}
                </p>

                <p>
                    💻 Mode:
                    ${mode}
                </p>

                <p>
                    💰 Fee:
                    ₹${fee}
                </p>

                <p>
                    🎯 Category:
                    ${category}
                </p>

                <p>
                    🕒 Your Free Time:
                    ${freeStart}
                    -
                    ${freeEnd}
                </p>

                <p class="success">
                    ${freeMessage}
                </p>


                <button
                    onclick="registerEvent('${event.event_id}')">

                    Register

                </button>

            `;


            container.appendChild(
                card
            );

        });


    } catch (error) {

        console.error(
            "Free time events error:",
            error
        );


        container.innerHTML =
            `
            <p class="error">
                Cannot connect to backend.
            </p>
            `;
    }
}


// ============================================================
// NOTIFICATIONS
// ============================================================

function displayNotifications(
    notifications
) {

    const container =
        document.getElementById(
            "notifications"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !notifications ||
        !Array.isArray(notifications) ||
        notifications.length === 0
    ) {

        container.innerHTML =
            "<p>No notifications.</p>";

        return;
    }


    notifications.forEach(
        notification => {

            container.innerHTML += `

                <div class="notification">

                    <strong>
                        🔔 ${notification.title || "Notification"}
                    </strong>

                    <p>
                        ${notification.message || ""}
                    </p>

                    <small>
                        Reminder:
                        ${notification.reminder_time || ""}
                    </small>

                </div>

            `;
        }
    );
}


// ============================================================
// PAGE INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "Event Recommender frontend loaded."
        );

        loadDashboard();

        loadEvents();

        loadRegisteredEvents();

        loadFreeTimeEvents();

    }
);