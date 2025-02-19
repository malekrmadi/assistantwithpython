import json
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurer l'API Gemini
genai.configure(api_key=GEMINI_API_KEY)

# URL YouTube statique pour le test
video_url = "https://www.youtube.com/watch?v=cfEfA1qNb-c"
video_id = video_url.split("v=")[-1]

# 🔹 Étape 1 : Récupérer la transcription brute
def get_video_transcription(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription: {e}")
        return None

# 🔹 Étape 2 : Demander à Gemini de segmenter la transcription par sujets
def segment_transcription_by_topics(transcript):
    """Envoie la transcription complète à Gemini pour qu'il découpe en chapitres logiques."""
    full_text = "\n".join(entry["text"] for entry in transcript)

    prompt = f"""
    Voici la transcription complète d'une vidéo YouTube. Segmente le texte en chapitres basés sur les sujets abordés.
    
    Renvoie une liste de segments sous la forme JSON valide :
    [
      {{"title": "Nom du chapitre", "content": "Texte de ce chapitre", "script": "Texte complet du segment"}}
    ]
    
    Transcription :
    {full_text}
    
    Assure-toi que la réponse soit bien formatée en JSON.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        print("\n🔍 DEBUG: Réponse brute de Gemini :\n", response.text)  # ✅ DEBUGGING

        # Nettoyage de la réponse avant parsing JSON
        formatted_response = response.text.strip().replace("```json", "").replace("```", "").strip()

        # S'assurer que la réponse est bien au format JSON
        if not formatted_response.startswith("[") or not formatted_response.endswith("]"):
            print("⚠️ Erreur : La réponse de Gemini n'est pas un JSON valide.")
            return None

        # Convertir en liste Python
        chapters = json.loads(formatted_response)
        return chapters
    except json.JSONDecodeError as e:
        print(f"⚠️ Erreur de parsing JSON : {e}")
        return None
    except Exception as e:
        print(f"⚠️ Erreur de segmentation par sujets : {e}")
        return None

# 🔹 Étape 3 : Associer chaque chapitre à ses timestamps
def assign_timestamps(transcript, chapters):
    """Associe chaque chapitre avec ses timestamps en fonction de la transcription brute."""
    timestamped_chapters = []

    for chapter in chapters:
        chapter_text = chapter["script"]  # Utilisation du script complet pour ajuster les timestamps
        start_time = None
        end_time = None

        # Trouver le premier et dernier mot du chapitre dans la transcription
        for entry in transcript:
            if chapter_text.startswith(entry["text"]) and start_time is None:
                start_time = entry["start"]
            if chapter_text.endswith(entry["text"]):
                end_time = entry["start"] + entry["duration"]

        if start_time is not None and end_time is not None:
            timestamped_chapters.append({
                "title": chapter["title"],
                "start": start_time,
                "end": end_time
            })
        else:
            print(f"⚠️ Impossible de trouver les timestamps pour le chapitre : {chapter['title']}")

    return timestamped_chapters

# 🔹 Étape 4 : Convertir les timestamps en format lisible (mm:ss)
def format_timestamp(seconds):
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes:02}:{sec:02}"

# 🔹 Étape 5 : Exécuter tout le processus
transcription = get_video_transcription(video_id)

if transcription:
    print("\n✅ Transcription récupérée avec succès !")
    print(f"📜 Nombre total de phrases : {len(transcription)}\n")

    # Segmentation par sujets
    segmented_chapters = segment_transcription_by_topics(transcription)
    
    if segmented_chapters:
        timestamped_chapters = assign_timestamps(transcription, segmented_chapters)

        print("\n📚 Chapitres générés avec timestamps :")
        for chapter in timestamped_chapters:
            print(f" - {format_timestamp(chapter['start'])} → {format_timestamp(chapter['end'])} : {chapter['title']}")
    else:
        print("❌ Erreur lors de la segmentation des chapitres.")
else:
    print("❌ Impossible de récupérer la transcription.")
