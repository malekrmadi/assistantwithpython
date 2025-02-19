import streamlit as st
import requests

# Title of the app
st.title("🎬 YouTube Video Info & AI Summary")

# Input field for YouTube video URL
video_url = st.text_input("🔗 Enter YouTube Video URL:", "")

# Fetch video details when the button is clicked
if st.button("📥 Get Video Info"):
    if video_url:
        # Call the Flask API
        api_url = f"http://127.0.0.1:5000/video_info?url={video_url}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            video_info = response.json()
            
            # Display Video Information
            st.subheader(f"📌 {video_info['title']}")
            st.write(f"📅 **Published on:** {video_info['publishedAt']}")
            st.write(f"👀 **Views:** {video_info['viewCount']}")
            st.write(f"👍 **Likes:** {video_info['likeCount']}")
            st.write(f"⏳ **Duration:** {video_info['duration']}")
            st.write(f"📝 **Description:** {video_info['description']}")

            # Display AI-generated summary
            with st.expander("📑 AI Summary of the Video"):
                st.write(video_info["summary"])

            # Display transcription in a collapsible section
            with st.expander("📜 Full Transcription"):
                st.write(video_info["transcription"])

        else:
            st.error("❌ Error: Unable to retrieve video info. Check the URL.")
    else:
        st.warning("⚠️ Please enter a valid URL.")
