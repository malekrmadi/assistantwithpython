import streamlit as st
import requests

# URL de l'API Flask
API_URL = "http://127.0.0.1:5000/video_info"

# Interface Streamlit
st.title("🎬 Assistant YouTube")

# Entrée pour l'URL de la vidéo
video_url = st.text_input("Entrez l'URL YouTube :")

if st.button("Analyser la vidéo"):
    if video_url:
        response = requests.get(API_URL, params={"url": video_url})

        if response.status_code == 200:
            video_info = response.json()

            # ✅ Vérification avant d'afficher le titre
            video_title = video_info.get("title", "Titre inconnu")
            st.subheader(f"📌 {video_title}")

            # ✅ Vérification des chapitres
            chapters = video_info.get("chapters", [])
            if chapters:
                st.write("📚 **Chapitres générés :**")

                for idx, chapter in enumerate(chapters, start=1):
                    title = chapter.get("title", f"Chapitre {idx}")
                    description = chapter.get("content", "Pas de description disponible")
                    start_time = chapter.get("start_time", "??:??:??")
                    end_time = chapter.get("end_time", "??:??:??")

                    # Affichage dans l'interface
                    st.write(f"🔹 **{title}** ({start_time} → {end_time})")
                    st.write(f"📝 {description}")
                    st.write("---")

                    # ✅ Affichage dans le terminal aussi
                    print(f"📌 Chapitre {idx}: {title}")
                    print(f"⏳ {start_time} → {end_time}")
                    print(f"📝 {description}")
                    print("-" * 50)

            else:
                st.error("❌ Aucun chapitre trouvé.")
        
        else:
            st.error(f"Erreur API : {response.status_code} - {response.text}")
    else:
        st.warning("⚠️ Veuillez entrer une URL YouTube.")
