import json
import os
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurer l'API Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialiser Flask
app = Flask(__name__)

def get_video_transcription(video_id):
    """ Récupère la transcription brute d'une vidéo YouTube """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription: {e}")
        return None

def segment_transcription_by_topics(transcript):
    """ Segmente la transcription en chapitres avec Gemini """
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

def format_timestamp(seconds):
    """ Convertit des secondes en format HH:MM:SS """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def hhmmss_to_seconds(timestamp):
    """ Convertit HH:MM:SS en secondes """
    h, m, s = map(int, timestamp.split(":"))
    return h * 3600 + m * 60 + s

def get_transcript_with_timestamps(video_id):
    """ Récupère la transcription avec les timestamps """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return [
            {
                "sentence": entry["text"],
                "start_time": format_timestamp(entry["start"]),
                "end_time": format_timestamp(entry["start"] + entry["duration"])
            }
            for entry in transcript
        ]
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la transcription avec timestamps : {e}")
        return None

def assign_timestamps(chapters, transcript):
    """ Associe les timestamps aux chapitres """
    timestamped_chapters = []
    previous_end_time = None
    current_index = 0

    for chapter in chapters:
        script_words = chapter["script"].split()
        last_10_words = " ".join(script_words[-15:])
        start_time = None
        end_time = None

        for i in range(current_index, len(transcript)):
            entry = transcript[i]
            if entry["sentence"] in last_10_words:
                end_time = entry["end_time"]
                current_index = i
                break

        if previous_end_time:
            previous_end_time_seconds = hhmmss_to_seconds(previous_end_time)
            start_time = format_timestamp(previous_end_time_seconds + 1)
        else:
            start_time = transcript[0]["start_time"]

        if end_time and hhmmss_to_seconds(end_time) < hhmmss_to_seconds(start_time):
            print(f"⚠️ Problème détecté : {start_time} → {end_time} ({chapter['title']})")
            end_time = None

        timestamped_chapters.append({
            "title": chapter["title"],
            "content": chapter["content"],
            "start_time": start_time,
            "end_time": end_time
        })

        previous_end_time = end_time if end_time else previous_end_time

    return timestamped_chapters

@app.route("/video_info", methods=["GET"])
def get_video_info():
    """ API pour récupérer les infos, résumé et chapitres d'une vidéo """
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "Aucune URL fournie"}), 400

    video_id = video_url.split("v=")[-1]
    transcription = get_video_transcription(video_id)
    if not transcription:
        return jsonify({"error": "Impossible de récupérer la transcription"}), 404

    transcript_with_timestamps = get_transcript_with_timestamps(video_id)
    chapters = segment_transcription_by_topics(transcription)
    if not chapters or not transcript_with_timestamps:
        return jsonify({"error": "Erreur lors de la segmentation ou récupération des timestamps"}), 500

    timestamped_chapters = assign_timestamps(chapters, transcript_with_timestamps)

    # ✅ Affichage des chapitres et descriptions dans le terminal
    print("\n📚 Chapitres générés avec description :")
    for chapter in timestamped_chapters:
        print(f"🔹 {chapter['start_time']} → {chapter['end_time']} : {chapter['title']}")
        print(f"   📝 Description : {chapter['content']}\n")

    return jsonify({"chapters": timestamped_chapters})

if __name__ == "__main__":
    app.run(debug=True)
