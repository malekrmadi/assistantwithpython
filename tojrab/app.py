from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API with the provided key
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

def get_youtube_video_info(video_id):
    """ Retrieve video details from YouTube API """
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
    """ Retrieve video transcription if available """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except Exception:
        return "Transcription not available."

def generate_summary(transcription):
    """ Generate a summary using Gemini API """
    if transcription == "Transcription not available.":
        return "Summary not available because the transcription could not be retrieved."

    prompt = f"""
    Summarize this YouTube video transcription in a **concise and informative** way.
    Focus on the key takeaways and **main points** without losing the meaning.

    Transcription: 
    {transcription}

    Summary:
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text if response and hasattr(response, 'text') else "Summary generation failed."
    except Exception as e:
        return f"Error generating summary: {e}"

def generate_chapters(transcription):
    """ Generate structured chapters with timestamps from the transcription """
    if transcription == "Transcription not available.":
        return "Chapters not available because the transcription could not be retrieved."

    prompt = f"""
    Analyze the following YouTube video transcription and divide it into 4-5 logical chapters.
    Each chapter should have a title and the corresponding timestamps (start and end).

    Format your response as a JSON array where each item is structured as:
    {{ "start": "hh:mm:ss", "end": "hh:mm:ss", "title": "Chapter Title" }}

    Transcription:
    {transcription}

    Chapters:
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text if response and hasattr(response, 'text') else "Chapters generation failed."
    except Exception as e:
        return f"Error generating chapters: {e}"

@app.route("/video_info", methods=["GET"])
def get_video_info():
    """ API endpoint to return video details, transcription, summary, and chapters """
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = video_url.split("v=")[-1]
    
    video_info = get_youtube_video_info(video_id)
    if not video_info:
        return jsonify({"error": "Video not found"}), 404

    transcription = get_video_transcription(video_id)
    summary = generate_summary(transcription)
    chapters = generate_chapters(transcription)

    video_info["transcription"] = transcription
    video_info["summary"] = summary
    video_info["chapters"] = chapters

    return jsonify(video_info)

if __name__ == "__main__":
    app.run(debug=True)
