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
print("Configuring Gemini API...")
genai.configure(api_key=GEMINI_API_KEY)
print("Gemini API configured successfully!")

app = Flask(__name__)

def get_youtube_video_info(video_id):
    """ Retrieve video details from YouTube API """
    print(f"Fetching YouTube video info for video ID: {video_id}")
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )
    response = request.execute()
    
    if not response["items"]:
        print("No video found.")
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
    print("Video info retrieved successfully!")
    return info

def get_video_transcription(video_id):
    """ Retrieve video transcription if available """
    print(f"Fetching transcription for video ID: {video_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        print("Transcription retrieved successfully!")
        return text
    except Exception as e:
        print(f"Error retrieving transcription: {e}")
        return "Transcription not available."

def generate_summary(transcription):
    """ Generate a summary using Gemini AI """
    if transcription == "Transcription not available.":
        print("No transcription available, skipping summary generation.")
        return "Summary not available."
    
    prompt = f"""
    Summarize this YouTube video transcription in a **concise and informative** way.
    Focus on the key takeaways and **main points** without losing the meaning.

    Transcription:
    {transcription}

    Summary:
    """
    
    try:
        print("Generating summary with Gemini AI...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            print("Summary generated successfully!")
            return response.text if response.text else "Summary generation failed."
        else:
            print("Error: Gemini AI did not return a valid response.")
            return "Error generating summary."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Error generating summary: {e}"

@app.route("/video_info", methods=["GET"])
def get_video_info():
    """ API endpoint to return video details, transcription, and summary """
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    video_id = video_url.split("v=")[-1]
    
    video_info = get_youtube_video_info(video_id)
    if not video_info:
        return jsonify({"error": "Video not found"}), 404
    
    transcription = get_video_transcription(video_id)
    summary = generate_summary(transcription)
    
    video_info["transcription"] = transcription
    video_info["summary"] = summary
    
    return jsonify(video_info)

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)

# Testing Gemini AI with a sample text
sample_text = "This is a test text to check Gemini AI functionality. The AI should return a short summary of this text."
print("Testing Gemini AI summary function...")
test_summary = generate_summary(sample_text)
print(f"Generated Summary: {test_summary}")
