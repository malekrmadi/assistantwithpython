import streamlit as st
import requests
import isodate
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🎬 YouTube Video Info & AI Summary")

# ➤ Zone d'entrée URL + bouton dans la même ligne
col1, col2 = st.columns([4, 1])
with col1:
    video_url = st.text_input("🔗 Entrez l'URL de la vidéo YouTube:")
with col2:
    submit_button = st.button("📥 Obtenir les infos")

# ➤ Fonction pour extraire l'ID de la vidéo YouTube
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# ➤ Conversion de la date ISO 8601 en format lisible
def format_date(iso_date):
    try:
        date_obj = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return date_obj.strftime("%d %B %Y à %Hh%M")
    except:
        return iso_date

# ➤ Conversion de la durée ISO 8601 en minutes et secondes
def format_duration(iso_duration):
    try:
        duration = isodate.parse_duration(iso_duration)
        minutes, seconds = divmod(int(duration.total_seconds()), 60)
        return f"{minutes} min {seconds} sec"
    except:
        return iso_duration

# ➤ Récupération des infos si le bouton est cliqué
if submit_button and video_url:
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("❌ URL YouTube invalide.")
    else:
        api_url = f"http://127.0.0.1:5000/video_info?url={video_url}"
        response = requests.get(api_url)

        if response.status_code == 200:
            video_info = response.json()

            # ➤ Informations Générales et Résumé
            st.markdown("---")
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**📌 {video_info['title']}**")
                st.write(f"📅 **Date de publication :** {format_date(video_info['publishedAt'])}")
                st.write(f"👀 **Vues :** {int(video_info['viewCount']):,}")
                st.write(f"👍 **Likes :** {int(video_info['likeCount']):,}")
                st.write(f"⏳ **Durée :** {format_duration(video_info['duration'])}")

            with col2:
                st.subheader("📑 Résumé IA")
                st.write(video_info.get("summary", "Résumé non disponible."))
            st.markdown("---")

            # ➤ Vidéo (Row unique)
            st.subheader("🎥 Vidéo")
            st.markdown(
                f"""
                <iframe width="100%" height="400" src="https://www.youtube.com/embed/{video_id}?autoplay=1" 
                frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                """,
                unsafe_allow_html=True
            )
            st.markdown("---")

            # ➤ Chapitres (Stylisés)
            st.subheader("📖 Chapitres")
            chapters = video_info.get("chapters", [])
            if chapters:
                for chapter in chapters:
                    st.markdown(
                        f"""
                        <div style="background-color:#f0f2f6; padding:10px; border-radius:8px; margin-bottom:8px;">
                            <h4 style="color:#1f77b4;">⏳ {chapter['title']}</h4>
                            <p style="margin:5px 0; font-size:14px; color:#666;">
                                🕒 {chapter['start_time']} - {chapter['end_time']}
                            </p>
                            <p style="font-size:15px; color:#333;">{chapter['content']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.write("Aucun chapitre disponible.")
        else:
            st.error("❌ Erreur lors de la récupération des informations.")
