from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API
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
    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "publishedAt": video["snippet"]["publishedAt"],
        "viewCount": video["statistics"].get("viewCount", "N/A"),
        "likeCount": video["statistics"].get("likeCount", "N/A"),
        "duration": video["contentDetails"]["duration"],
    }

def get_video_transcription(video_id):
    """ Retrieve video transcription if available """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception:
        return "Transcription not available."

def generate_summary_and_chapters(transcription):
    """ Generate a structured summary and chapter timestamps using Gemini AI """
    if transcription == "Transcription not available.":
        return "Summary not available.", []

    prompt = f"""
    Analyze the following YouTube video transcription and create:
    1. A **concise summary** of the key takeaways.
    2. A list of **3 to 4 structured chapters** with **timestamps** (start and end time).
    
    Format the chapters as a **JSON array** with:
    - "start_time": Time the section starts (e.g., "0:00")
    - "end_time": Time the section ends (e.g., "4:30")
    - "summary": A brief title summarizing the section

    Transcription: 
    {transcription}

    Return the response in **pure JSON format** (without extra text).
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        if response and hasattr(response, 'text'):
            output = response.text.strip()
            return extract_summary_and_chapters(output)

        return "Summary generation failed.", []
    except Exception as e:
        return f"Error generating summary: {e}", []

def extract_summary_and_chapters(response_text):
    """ Extracts structured summary and chapters from Gemini's JSON output """
    try:
        import json
        data = json.loads(response_text)

        summary = data.get("summary", "Summary not available.")
        chapters = data.get("chapters", [])

        return summary, chapters
    except Exception:
        return "Summary not available.", []

@app.route("/video_info", methods=["GET"])
def get_video_info():
    """ API endpoint to return video details, structured summary, and transcription """
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = video_url.split("v=")[-1]
    
    video_info = get_youtube_video_info(video_id)
    if not video_info:
        return jsonify({"error": "Video not found"}), 404

    transcription = get_video_transcription(video_id)
    summary, structured_summary = generate_summary_and_chapters(transcription)

    video_info["transcription"] = transcription
    video_info["summary"] = summary
    video_info["structured_summary"] = structured_summary  # Added structured chapters

    return jsonify(video_info)

if __name__ == "__main__":
    app.run(debug=True)
