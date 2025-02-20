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
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(part="snippet,statistics,contentDetails", id=video_id)
    response = request.execute()
    
    if not response["items"]:
        return None
    
    video = response["items"][0]
    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "publishedAt": video["snippet"]["publishedAt"],
        "viewCount": video["statistics"].get("viewCount", "N/A"),
        "likeCount": video["statistics"].get("likeCount", "N/A"),
        "duration": video["contentDetails"]["duration"],
    }

def get_video_transcription(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return None

def format_timestamp(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def get_transcript_with_timestamps(video_id):
    try:
        return [
            {"sentence": entry["text"], "start_time": format_timestamp(entry["start"])}
            for entry in YouTubeTranscriptApi.get_transcript(video_id)
        ]
    except Exception:
        return None

def generate_summary(transcription):
    if not transcription:
        return "Résumé non disponible."
    
    full_text = " ".join([entry["text"] for entry in transcription])
    prompt = f"""
    Résume cette transcription dans sa langue originale :
    {full_text}
    Résumé :
    """
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text.strip() if response and hasattr(response, 'text') else "Résumé non disponible."
    except Exception:
        return "Erreur lors de la génération du résumé."

def segment_transcription_by_topics(transcription):
    if not transcription:
        return None
    
    full_text = "\n".join(entry["text"] for entry in transcription)
    prompt = f"""
    Segmente ce texte en chapitres thématiques au format JSON :
    {full_text}
    """
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
    except Exception:
        return None

@app.route("/video_info", methods=["GET"])
def get_video_info():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "Aucune URL fournie"}), 400
    
    video_id = video_url.split("v=")[-1]
    video_info = get_youtube_video_info(video_id)
    if not video_info:
        return jsonify({"error": "Vidéo non trouvée"}), 404
    
    transcription = get_video_transcription(video_id)
    summary = generate_summary(transcription)
    chapters = segment_transcription_by_topics(transcription)
    
    video_info["summary"] = summary
    video_info["transcription"] = transcription or "Transcription non disponible."
    video_info["chapters"] = chapters or "Chapitres non disponibles."

        # Ajout du print pour voir le JSON des chapitres
    print(json.dumps(video_info["chapters"], indent=4, ensure_ascii=False))
    
    return jsonify(video_info)

if __name__ == "__main__":
    app.run(debug=True)
