import streamlit as st
import requests
import isodate
from datetime import datetime

st.set_page_config(layout="wide")  # Mode plein écran pour optimiser la mise en page
st.title("🎬 YouTube Video Info & AI Summary")

# ➤ Zone d'entrée URL + bouton dans la même ligne (Row 1)
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

            # ➤ Informations Générales (Row 2 - Pleine largeur)
            st.markdown("---")
            st.markdown(
                f"""
                <h2>📌 {video_info['title']}</h2>
                <p style="font-size:18px">
                    📅 <b>Date de publication :</b> {format_date(video_info['publishedAt'])}<br>
                    👀 <b>Vues :</b> {int(video_info['viewCount']):,} <br>
                    👍 <b>Likes :</b> {int(video_info['likeCount']):,} <br>
                    ⏳ <b>Durée :</b> {format_duration(video_info['duration'])}
                </p>
                """,
                unsafe_allow_html=True
            )
            st.markdown("---")

            # ➤ Résumé IA (Row 3 - Pleine largeur)
            st.subheader("📑 Résumé IA")
            st.write(video_info.get("summary", "Résumé non disponible."))
            st.markdown("---")

            # ➤ Deux colonnes : Chapitres (gauche) & Vidéo (droite) (Row 4)
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.subheader("📖 Chapitres")
                chapters = video_info.get("chapters", [])
                if isinstance(chapters, list) and chapters:
                    with st.container():
                        for chapter in chapters:
                            st.markdown(f"### ⏲️ {chapter['start_time']} - {chapter['end_time']}")
                            st.markdown(f"**📌 {chapter['title']}**")
                            st.write(f"📄 {chapter['content']}")  # Résumé du chapitre
                        st.markdown("---")
                else:
                    st.write("Aucun chapitre disponible.")

            with col_right:
                st.subheader("🎥 Vidéo")
                st.markdown(
                    f"""
                    <iframe width="100%" height="400" src="https://www.youtube.com/embed/{video_id}" 
                    frameborder="0" allowfullscreen></iframe>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error("❌ Erreur lors de la récupération des informations.")
