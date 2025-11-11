import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "movie_review.db")

# ---------------------------
# DATABASE SETUP
# ---------------------------
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create necessary tables
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    duration INTEGER,
    description TEXT,
    url TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    timestamp TEXT,
    action TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    rating INTEGER,
    comment TEXT
)
''')
conn.commit()

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def add_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, password))
        conn.commit()
        return True
    except Exception as e:
        return False

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    data = c.fetchone()
    return data

def add_movie(title, duration, description, url):
    c.execute('INSERT INTO movies (title, duration, description, url) VALUES (?,?,?,?)', (title, duration, description, url))
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
st.set_page_config(page_title="Movie Review Engagement Tracker", layout="wide")
st.title("🎬 Movie Review & Engagement Tracker")

if 'user' not in st.session_state:
    st.session_state['user'] = None

menu = ["Signup", "Login", "Admin - Add Movie", "Watch Movie", "Analytics", "Add Review", "Help"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------------------
# SIGNUP
# ---------------------------
if choice == "Signup":
    st.subheader("Create a New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Signup"):
        if new_user.strip() == "" or new_pass.strip() == "":
            st.error("Please provide username and password.")
        elif add_user(new_user, new_pass):
            st.success("✅ Account created successfully! Please login from the Login menu.")
        else:
            st.error("Username already exists or invalid.")

# ---------------------------
# LOGIN
# ---------------------------
elif choice == "Login":
    st.subheader("Login to your account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state['user'] = {"id": user[0], "username": user[1]}
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid login credentials.")

# ---------------------------
# ADMIN - ADD MOVIE
# ---------------------------
elif choice == "Admin - Add Movie":
    st.subheader("🎞️ Add New Movie (Admin)")
    st.info("This 'Admin' page is not access-protected in this demo. In production, add role checks.")
    title = st.text_input("Movie Title")
    duration = st.number_input("Duration (in minutes)", 1, 10000, value=120)
    desc = st.text_area("Description")
    url = st.text_input("Video URL (mp4 link) — you can use public mp4 links or a CDN URL")

    if st.button("Add Movie"):
        if title.strip() == "" or url.strip() == "":
            st.error("Title and URL are required.")
        else:
            add_movie(title, duration, desc, url)
            st.success(f"Movie '{title}' added successfully!")

# ---------------------------
# WATCH MOVIE
# ---------------------------
elif choice == "Watch Movie":
    st.subheader("🎥 Watch Movie")
    movies = pd.read_sql_query("SELECT * FROM movies", conn)

    if len(movies) == 0:
        st.info("No movies available yet. Add one in 'Admin - Add Movie'.")
    else:
        movie_name = st.selectbox("Select Movie", movies['title'])
        movie = movies[movies['title'] == movie_name].iloc[0]

        # show video using st.video
        if movie['url'].strip() != "":
            st.video(movie['url'])
        else:
            st.warning("No video url for this movie.")

        st.write(f"**Description:** {movie['description']}")
        st.write(f"⏱️ Duration: {movie['duration']} mins")

        st.markdown("---")
        st.markdown("### Simulated tracking (for demo)")
        st.write("Since Streamlit's native `st.video` doesn't expose playback events, this demo provides buttons to simulate user actions (play, pause, skip). Later you can extend with a Streamlit component that captures JS player events.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Simulate: play at 00:02:30"):
                if st.session_state['user'] is None:
                    st.warning("Please login (or we will record as anonymous user id=0).")
                uid = st.session_state['user']['id'] if st.session_state['user'] else 0
                log_view(uid, int(movie['id']), '00:02:30', 'play')
                st.success("Logged play event.")
        with col2:
            if st.button("Simulate: skip at 00:10:15"):
                uid = st.session_state['user']['id'] if st.session_state['user'] else 0
                log_view(uid, int(movie['id']), '00:10:15', 'skip')
                st.success("Logged skip event.")
        with col3:
            if st.button("Simulate: play at 00:20:45"):
                uid = st.session_state['user']['id'] if st.session_state['user'] else 0
                log_view(uid, int(movie['id']), '00:20:45', 'play')
                st.success("Logged play event.")

        st.markdown("---")
        if st.checkbox("Show raw view events for this movie"):
            df_movie_views = pd.read_sql_query(f"SELECT * FROM views WHERE movie_id={int(movie['id'])}", conn)
            st.dataframe(df_movie_views)

# ---------------------------
# ADD REVIEW
# ---------------------------
elif choice == "Add Review":
    st.subheader("📝 Add Review")
    movies = pd.read_sql_query("SELECT * FROM movies", conn)
    if len(movies) == 0:
        st.warning("No movies to review.")
    else:
        movie_name = st.selectbox("Select Movie", movies['title'])
        rating = st.slider("Rate (1–5)", 1, 5, 4)
        comment = st.text_area("Your Comment")

        if st.button("Submit Review"):
            uid = st.session_state['user']['id'] if st.session_state['user'] else 0
            movie_id = int(movies[movies['title'] == movie_name].iloc[0]['id'])
            add_review(uid, movie_id, rating, comment)
            st.success("Thank you for your review! 🎉")

# ---------------------------
# ANALYTICS
# ---------------------------
elif choice == "Analytics":
    st.subheader("📊 Engagement Analytics")

    df_views = pd.read_sql_query("SELECT * FROM views", conn)
    df_reviews = pd.read_sql_query("SELECT * FROM reviews", conn)
    movies_df = pd.read_sql_query("SELECT * FROM movies", conn)

    if df_views.empty:
        st.info("No view data yet. Use 'Watch Movie' to simulate events.")
    else:
        st.markdown("### 🔥 Watch vs Skip by Timestamp")
        # Aggregate counts by timestamp and action
        agg = df_views.groupby(['timestamp','action']).size().reset_index(name='count')
        chart = alt.Chart(agg).mark_bar().encode(
            x='timestamp:N',
            y='count:Q',
            color='action:N',
            tooltip=['timestamp','action','count']
        )
        st.altair_chart(chart, use_container_width=True)

        st.markdown("### Heatmap-like summary (timestamps intensity)")
        heat = df_views.groupby('timestamp').size().reset_index(name='views')
        heat_chart = alt.Chart(heat).mark_rect().encode(
            x='timestamp:N',
            y=alt.Y('views:Q', axis=alt.Axis(title='views')),
            tooltip=['timestamp','views']
        )
        st.altair_chart(heat_chart, use_container_width=True)

    if df_reviews.empty:
        st.info("No reviews yet.")
    else:
        st.markdown("### ⭐ Average Ratings by Movie")
        avg = df_reviews.groupby('movie_id')['rating'].mean().reset_index()
        # join title
        avg = avg.merge(movies_df[['id','title']], left_on='movie_id', right_on='id', how='left')
        avg_chart = alt.Chart(avg).mark_bar().encode(
            x='title:N',
            y='rating:Q',
            tooltip=['title','rating']
        )
        st.altair_chart(avg_chart, use_container_width=True)

        st.markdown("### Latest Reviews")
        latest = df_reviews.sort_values('id', ascending=False).head(20)
        latest = latest.merge(movies_df[['id','title']], left_on='movie_id', right_on='id', how='left')
        st.dataframe(latest[['title','rating','comment']])

# ---------------------------
# HELP
# ---------------------------
elif choice == "Help":
    st.subheader("How to use this project")
    st.markdown("""
    1. Go to **Admin - Add Movie** and add a movie (use a public MP4 url for demo).
    2. Signup / Login (optional). The demo records anonymous events as user id 0.
    3. Go to **Watch Movie** and use the simulate buttons to log play/skip events.
    4. Go to **Analytics** to view aggregated events and reviews.
    5. To deploy on Streamlit Cloud / Streamlit Community Cloud, push this repo (including this file) to GitHub and connect it in your Streamlit account.
    """)
    st.markdown("""> Note: For production-grade playback tracking you will need a JS-based player component that sends playback events to the Python backend. This demo uses manual simulation buttons to keep everything purely Python/Streamlit-based.""", unsafe_allow_html=True)