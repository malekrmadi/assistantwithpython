from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurer l'API Gemini
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

def get_youtube_video_info(video_id):
    """ Récupère les informations d'une vidéo YouTube """
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )
    response = request.execute()

    if not response["items"]:
        return None

    video = response["items"][0]
    info = {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "publishedAt": video["snippet"]["publishedAt"],
        "viewCount": video["statistics"].get("viewCount", "N/A"),
        "likeCount": video["statistics"].get("likeCount", "N/A"),
        "duration": video["contentDetails"]["duration"],
    }
    return info

def get_video_transcription(video_id):
    """Récupère la transcription en français ou en anglais si indisponible"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr', 'en'])
        return transcript
    except Exception as e:
        print(f"Erreur : {e}")
        return None

def format_timestamp(seconds):
    """ Convertit un timestamp en hh:mm:ss """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def hhmmss_to_seconds(timestamp):
    """ Convertit un timestamp hh:mm:ss en secondes """
    h, m, s = map(int, timestamp.split(":"))
    return h * 3600 + m * 60 + s

def get_transcript_with_timestamps(video_id):
    """ Récupère la transcription avec timestamps """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr', 'en'])
        return [
            {
                "sentence": entry["text"],
                "start_time": format_timestamp(entry["start"]),
                "end_time": format_timestamp(entry["start"] + entry["duration"])
            }
            for entry in transcript
        ]
    except Exception:
        return None

def generate_summary(transcription):
    """ Génère un résumé avec Gemini """
    if not transcription:
        return "Résumé non disponible."

    full_text = " ".join([entry["text"] for entry in transcription])
    prompt = f"""
    Résume cette transcription de manière claire et concise et assure toi que tu me rende le resuméé en français :
    
    {full_text}

    Résumé :
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, 'text') else "Résumé non disponible."
    except Exception:
        return "Erreur lors de la génération du résumé."

def segment_transcription_by_topics(transcription):
    """ Segmente la transcription en chapitres thématiques """
    if not transcription:
        return None

    full_text = "\n".join(entry["text"] for entry in transcription)
    prompt = f"""
    Segmente ce texte en chapitres basés sur les sujets abordés.
    Retourne une liste de chapitres au format JSON :
    [
      {{"title": "Nom du chapitre", "content": "Texte du chapitre", "script": "Texte du segment"}}
    ]
    Transcription :
    {full_text}
    Assure-toi que la réponse soit bien formatée en JSON.
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
    except Exception:
        return None

def assign_timestamps(chapters, transcript):
    """ Associe chaque chapitre à un timestamp """
    if not chapters or not transcript:
        return None

    timestamped_chapters = []
    previous_end_time = None
    current_index = 0

    for chapter in chapters:
        script_words = chapter["script"].split()
        last_10_words = " ".join(script_words[-15:])
        
        start_time = previous_end_time or transcript[0]["start_time"]
        end_time = None

        for i in range(current_index, len(transcript)):
            entry = transcript[i]
            if entry["sentence"] in last_10_words:
                end_time = entry["end_time"]
                current_index = i
                break
        
        timestamped_chapters.append({
            "title": chapter["title"],
            "content": chapter["content"],
            "start_time": start_time,
            "end_time": end_time or start_time
        })
        
        previous_end_time = end_time or previous_end_time

    return timestamped_chapters

@app.route("/video_summary", methods=["GET"])
def video_summary():
    """ API pour récupérer le résumé et les chapitres d'une vidéo YouTube """
    video_url = request.args.get("url")  # Lien statique par défaut
    if not video_url:
        return jsonify({"error": "Aucune URL fournie"}), 400

    video_id = video_url.split("v=")[-1]
    
    # Récupération de la transcription de la vidéo
    transcription = get_video_transcription(video_id)
    
    if not transcription:
        return jsonify({"error": "Transcription non disponible"}), 404
    
    # Génération du résumé complet de la vidéo
    summary = generate_summary(transcription)
    
    # Récupération des chapitres thématiques
    chapters = segment_transcription_by_topics(transcription)
    timestamped_chapters = assign_timestamps(chapters, get_transcript_with_timestamps(video_id))

    # Formatage de la réponse
    response = {
        "summary": summary,
        "chapters": [
            {
                "title": chapter["title"],
                "start_time": chapter["start_time"],
                "end_time": chapter["end_time"],
                "chapter_summary": generate_summary([{"text": chapter["content"]}])  # Résumé du chapitre
            }
            for chapter in timestamped_chapters
        ] if timestamped_chapters else []
    }

    # Affichage de la réponse dans le terminal
    print('on attend')
    print(json.dumps(response, indent=2))

    # Retourner la réponse JSON
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
