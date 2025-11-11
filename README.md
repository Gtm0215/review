# Movie Review & Engagement Tracker (Streamlit)

This is a demo Python/Streamlit project that simulates tracking which parts of a movie are played or skipped by users, collects reviews, and shows simple analytics.

## Features
- Add movies (title, duration, description, mp4 URL)
- Simulate playback events (play/skip) and store them in SQLite
- Add reviews and ratings
- Analytics page that shows counts by timestamps and average ratings

## Run locally
1. Clone this repo or download the ZIP.
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run:
   ```
   streamlit run movie_review_system.py
   ```

## Deploy to Streamlit Community Cloud
1. Push the repository to GitHub.
2. Create a new app on Streamlit Community Cloud and connect your GitHub repo.
3. Set the main file to `movie_review_system.py` and deploy.

## Notes & Next steps
- This demo uses manual simulation buttons for playback events because `st.video` does not provide playback events.
- For real tracking, integrate a custom Streamlit component with a JS player that posts events back to the app.