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

# Étape 1 : Récupérer la transcription brute
def get_video_transcription(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription: {e}")
        return None

# Étape 2 : Segmentation par thèmes avec Gemini
def segment_transcription_by_topics(transcript):
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
        formatted_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        chapters = json.loads(formatted_response)
        return chapters
    except Exception as e:
        print(f"⚠️ Erreur de segmentation par sujets : {e}")
        return None

# Étape 3 : Associer chaque phrase de la transcription à son timestamp
def format_timestamp(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def hhmmss_to_seconds(timestamp):
    h, m, s = map(int, timestamp.split(":"))
    return h * 3600 + m * 60 + s

def get_transcript_with_timestamps(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatted_transcript = [
            {
                "sentence": entry["text"],
                "start_time": format_timestamp(entry["start"]),
                "end_time": format_timestamp(entry["start"] + entry["duration"])
            }
            for entry in transcript
        ]
        return formatted_transcript
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription avec timestamps : {e}")
        return None

# Étape 4 : Assigner les timestamps aux chapitres
def assign_timestamps(chapters, transcript):
    timestamped_chapters = []
    previous_end_time = None
    current_index = 0  # Suivi de la position dans le transcript
    
    for chapter in chapters:
        script_text = chapter["script"].split()
        last_10_words = " ".join(script_text[-3:])
        
        start_time = None
        end_time = None
        
        # Rechercher la phrase qui correspond, sans revenir en arrière
        for i, entry in enumerate(transcript[current_index:], start=current_index):
            if last_10_words in entry["sentence"]:
                end_time = entry["end_time"]
                current_index = i  # Mettre à jour l'index pour ne pas revenir en arrière
                break
        
        if previous_end_time:
            previous_end_time_seconds = hhmmss_to_seconds(previous_end_time)
            start_time = format_timestamp(previous_end_time_seconds + 1)
        else:
            start_time = transcript[0]["start_time"]
        
        # Vérifier que le timestamp de fin est bien après le début
        if end_time and hhmmss_to_seconds(end_time) < hhmmss_to_seconds(start_time):
            print(f"⚠️ Problème détecté : {start_time} → {end_time} ({chapter['title']})")
            end_time = None  # Laisser None et corriger manuellement plus tard
        
        timestamped_chapters.append({
            "title": chapter["title"],
            "content": chapter["content"],
            "start_time": start_time,
            "end_time": end_time
        })
        
        previous_end_time = end_time if end_time else previous_end_time
    
    return timestamped_chapters

# Exécution du processus
transcription = get_video_transcription(video_id)
if transcription:
    print("\n✅ Transcription récupérée avec succès !")
    print(f"📜 Nombre total de phrases : {len(transcription)}\n")
    
    segmented_chapters = segment_transcription_by_topics(transcription)
    transcript_with_timestamps = get_transcript_with_timestamps(video_id)
    
    if segmented_chapters and transcript_with_timestamps:
        timestamped_chapters = assign_timestamps(segmented_chapters, transcript_with_timestamps)
        
        print("\n📚 Chapitres générés avec timestamps :")
        for chapter in timestamped_chapters:
            print(f" - {chapter['start_time']} → {chapter['end_time']} : {chapter['title']}")
    else:
        print("❌ Erreur lors de la segmentation des chapitres ou de la récupération des timestamps.")
else:
    print("❌ Impossible de récupérer la transcription.")
