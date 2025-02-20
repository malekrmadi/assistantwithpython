import json
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 🔹 Étape 1 : Récupérer la transcription brute
def get_video_transcription(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription: {e}")
        return None

# 🔹 Étape 2 : Segmentation par sujets avec Gemini
def segment_transcription_by_topics(transcript):
    full_text = "\n".join(entry["text"] for entry in transcript)
    
    prompt = f"""
    Voici la transcription complète d'une vidéo YouTube. Segmente le texte en chapitres basés sur les sujets abordés.
    Renvoie une liste de segments sous la forme JSON valide :
    [
      {{"title": "Nom du chapitre", "content": "Texte du résumé", "script": "Texte complet du chapitre"}}
    ]
    
    Transcription :
    {full_text}
    
    Assure-toi que la réponse soit bien formatée en JSON.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        formatted_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        chapters = json.loads(formatted_response)
        return chapters
    except Exception as e:
        print(f"⚠️ Erreur de segmentation par sujets : {e}")
        return None

# 🔹 Étape 3 : Associer les timestamps
def format_timestamp(seconds):
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes:02}:{sec:02}"

def assign_timestamps(transcript, chapters):
    timestamped_chapters = []
    previous_end_time = None  

    for chapter in chapters:
        script_text = chapter["script"]
        last_words = " ".join(script_text.split()[-10:])  # Prendre les 10 derniers mots

        start_time = None
        end_time = None

        for entry in transcript:
            sentence = entry["text"]
            if last_words in sentence:
                end_time = entry["start"] + entry["duration"]

            if start_time is None and script_text.startswith(sentence):
                start_time = entry["start"]

        # Si on ne trouve pas de fin, on met le dernier timestamp disponible
        if end_time is None and timestamped_chapters:
            end_time = timestamped_chapters[-1]["end"] + 5  # Ajout d'un buffer

        # Ajuster le start_time basé sur le chapitre précédent
        if previous_end_time is not None:
            start_time = previous_end_time + 1  # Décalage de 1 sec

        timestamped_chapters.append({
            "title": chapter["title"],
            "start": format_timestamp(start_time),
            "end": format_timestamp(end_time)
        })
        previous_end_time = end_time

    return timestamped_chapters

# 🔹 Étape 4 : Exécuter le processus
video_url = "https://www.youtube.com/watch?v=cfEfA1qNb-c"
video_id = video_url.split("v=")[-1]

transcription = get_video_transcription(video_id)
if transcription:
    print("\n✅ Transcription récupérée avec succès !")
    print(f"📜 Nombre total de phrases : {len(transcription)}\n")

    segmented_chapters = segment_transcription_by_topics(transcription)
    if segmented_chapters:
        timestamped_chapters = assign_timestamps(transcription, segmented_chapters)

        print("\n📚 Chapitres générés avec timestamps :")
        for chapter in timestamped_chapters:
            print(f" - {chapter['start']} → {chapter['end']} : {chapter['title']}")
    else:
        print("❌ Erreur lors de la segmentation des chapitres.")
else:
    print("❌ Impossible de récupérer la transcription.")
