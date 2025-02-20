import streamlit as st
import requests

st.title("🎬 YouTube Video Info & AI Summary")

video_url = st.text_input("🔗 Entrez l'URL de la vidéo YouTube:")

if st.button("📥 Obtenir les infos"):
    if video_url:
        api_url = f"http://127.0.0.1:5000/video_info?url={video_url}"
        response = requests.get(api_url)

        if response.status_code == 200:
            video_info = response.json()

            st.subheader(f"📌 {video_info['title']}")
            st.write(f"📅 **Date de publication :** {video_info['publishedAt']}")
            st.write(f"👀 **Vues :** {video_info['viewCount']}")
            st.write(f"👍 **Likes :** {video_info['likeCount']}")
            st.write(f"⏳ **Durée :** {video_info['duration']}")

            with st.expander("📑 Résumé IA"):
                st.write(video_info.get("summary", "Résumé non disponible."))

            with st.expander("📜 Transcription complète"):
                st.write(video_info.get("transcription", "Transcription non disponible."))

            with st.expander("📖 Chapitres de la vidéo"):
                chapters = video_info.get("chapters", [])
                if isinstance(chapters, list):
                    for chapter in chapters:
                        st.write(f"⏲️ **{chapter['start_time']} - {chapter['end_time']}**: {chapter['title']}")
                else:
                    st.write(chapters)
        else:
            st.error("❌ Erreur lors de la récupération des informations.")
