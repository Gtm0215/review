import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from streamlit_player import st_player

# ---------------------------
# DATABASE SETUP
# ---------------------------
conn = sqlite3.connect('movie_review.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    duration INTEGER,
    description TEXT,
    url TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    timestamp TEXT,
    action TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    rating INTEGER,
    comment TEXT
)''')

# For smart analytics
c.execute('''CREATE TABLE IF NOT EXISTS smart_watch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    timestamp REAL,
    event TEXT
)''')
conn.commit()

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def add_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, password))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return c.fetchone()

def add_movie(title, duration, description, url):
    c.execute('INSERT INTO movies (title, duration, description, url) VALUES (?,?,?,?)',
              (title, duration, description, url))
    conn.commit()

def log_view(user_id, movie_id, timestamp, action):
    c.execute('INSERT INTO views (user_id, movie_id, timestamp, action) VALUES (?,?,?,?)',
              (user_id, movie_id, timestamp, action))
    conn.commit()

def add_review(user_id, movie_id, rating, comment):
    c.execute('INSERT INTO reviews (user_id, movie_id, rating, comment) VALUES (?,?,?,?)',
              (user_id, movie_id, rating, comment))
    conn.commit()

# ---------------------------
# STREAMLIT APP
# ---------------------------
st.set_page_config(page_title="Movie Review & Smart Analytics", layout="wide")
st.title("🎬 Movie Review & Engagement Tracker")

if 'user' not in st.session_state:
    st.session_state['user'] = None

menu = [
    "Signup", "Login", "Admin - Add Movie",
    "Watch Movie", "Add Review", "Analytics",
    "Smart Analytics (Auto Detection)", "Help"
]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------------------
# SIGNUP
# ---------------------------
if choice == "Signup":
    st.subheader("🧑‍💻 Create Account")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if add_user(user, pw):
            st.success("✅ Account created successfully! Please log in.")
        else:
            st.error("Username already exists!")

# ---------------------------
# LOGIN
# ---------------------------
elif choice == "Login":
    st.subheader("🔐 Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        data = login_user(user, pw)
        if data:
            st.session_state['user'] = {"id": data[0], "username": data[1]}
            st.success(f"Welcome, {user}!")
        else:
            st.error("Invalid credentials.")

# ---------------------------
# ADMIN - ADD MOVIE
# ---------------------------
elif choice == "Admin - Add Movie":
    st.subheader("🎞️ Add New Movie (Admin Only)")
    title = st.text_input("Movie Title")
    duration = st.number_input("Duration (in minutes)", 1, 500)
    desc = st.text_area("Description")
    url = st.text_input("Video URL (MP4 or YouTube link)")

    if st.button("Add Movie"):
        add_movie(title, duration, desc, url)
        st.success(f"✅ '{title}' added successfully!")

# ---------------------------
# WATCH MOVIE
# ---------------------------
elif choice == "Watch Movie":
    st.subheader("🎥 Watch Movie")
    df = pd.read_sql_query("SELECT * FROM movies", conn)
    if df.empty:
        st.warning("No movies available. Add some in 'Admin - Add Movie'.")
    else:
        name = st.selectbox("Select Movie", df['title'])
        movie = df[df['title'] == name].iloc[0]

        st.video(movie['url'])
        st.write(f"**Description:** {movie['description']}")
        st.write(f"⏱️ Duration: {movie['duration']} minutes")

        # Simulate playback logs (for demo)
        if st.button("Simulate Watch Events"):
            uid = st.session_state['user']['id'] if st.session_state['user'] else 0
            log_view(uid, int(movie['id']), "00:03:00", "play")
            log_view(uid, int(movie['id']), "00:10:15", "skip")
            log_view(uid, int(movie['id']), "00:20:45", "play")
            st.success("✅ Simulated watching data saved!")

# ---------------------------
# ADD REVIEW
# ---------------------------
elif choice == "Add Review":
    st.subheader("📝 Add Movie Review")
    df = pd.read_sql_query("SELECT * FROM movies", conn)
    if df.empty:
        st.info("No movies yet.")
    else:
        name = st.selectbox("Select Movie", df['title'])
        rating = st.slider("Rate (1–5)", 1, 5)
        comment = st.text_area("Write your review")

        if st.button("Submit"):
            uid = st.session_state['user']['id'] if st.session_state['user'] else 0
            mid = int(df[df['title'] == name].iloc[0]['id'])
            add_review(uid, mid, rating, comment)
            st.success("✅ Review added successfully!")

# ---------------------------
# ANALYTICS
# ---------------------------
elif choice == "Analytics":
    st.subheader("📊 Engagement Analytics")
    views = pd.read_sql_query("SELECT * FROM views", conn)
    reviews = pd.read_sql_query("SELECT * FROM reviews", conn)
    if not views.empty:
        chart = alt.Chart(views).mark_bar().encode(
            x='timestamp', y='count():Q', color='action'
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No engagement data yet.")
    if not reviews.empty:
        avg = reviews.groupby('movie_id')['rating'].mean().reset_index()
        st.bar_chart(avg.set_index('movie_id'))
    else:
        st.info("No reviews yet.")

# ---------------------------
# SMART ANALYTICS (AUTO DETECTION)
# ---------------------------
elif choice == "Smart Analytics (Auto Detection)":
    st.subheader("🤖 Smart Engagement Detection (Automatic)")
    df = pd.read_sql_query("SELECT * FROM movies", conn)
    if df.empty:
        st.warning("No movies found. Add one first.")
    else:
        name = st.selectbox("Select Movie", df['title'])
        movie = df[df['title'] == name].iloc[0]

        st.write(f"**Now playing:** {movie['title']}")
        events = st_player(
            movie['url'],
            key=f"player_{movie['id']}",
            events=["onProgress", "onPlay", "onPause"],
            height=400
        )

        # Log playback data automatically
        if events and "time" in events:
            current_time = round(events["time"], 1)
            c.execute("INSERT INTO smart_watch (movie_id, timestamp, event) VALUES (?,?,?)",
                      (int(movie['id']), current_time, "play"))
            conn.commit()

        st.markdown("---")
        st.markdown("### 🔥 Scene Engagement Heatmap")

        data = pd.read_sql_query(f"SELECT * FROM smart_watch WHERE movie_id={int(movie['id'])}", conn)
        if not data.empty:
            data["segment"] = (data["timestamp"] // 10) * 10
            summary = data.groupby("segment").size().reset_index(name="views")

            chart = alt.Chart(summary).mark_bar().encode(
                x=alt.X("segment:Q", title="Scene (seconds)"),
                y=alt.Y("views:Q", title="Views"),
                tooltip=["segment", "views"]
            )
            st.altair_chart(chart, use_container_width=True)

            top_scene = summary.loc[summary['views'].idxmax()]
            st.success(f"🔥 Most watched scene: {top_scene.segment:.0f}s – {top_scene.segment + 10:.0f}s")
        else:
            st.info("Start watching to generate analytics data!")

# ---------------------------
# HELP
# ---------------------------
elif choice == "Help":
    st.subheader("ℹ️ Help & Instructions")
    st.markdown("""
    **How to use:**
    1. Go to *Admin - Add Movie* and add some movie URLs (like public MP4 or YouTube links).  
    2. Sign up and log in as a user.  
    3. Use *Watch Movie* or *Smart Analytics (Auto Detection)* to track engagement.  
    4. Go to *Analytics* to view graphs and insights.  
    5. The *Smart Analytics* section auto-detects which scenes are most viewed and highlights them.
    """)
