import json
from youtube_transcript_api import YouTubeTranscriptApi

def format_timestamp(seconds):
    """Converts seconds to HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Define the video URL as a constant
video_url = "https://www.youtube.com/watch?v=cfEfA1qNb-c"

def get_transcript(video_url):
    """Extracts the transcript from a YouTube video and returns it in JSON format."""
    try:
        video_id = video_url.split("v=")[-1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        formatted_transcript = [
            {
                "sentence": entry["text"],
                "start_time": format_timestamp(entry["start"]),
                "end_time": format_timestamp(entry["start"] + entry["duration"])
            }
            for entry in transcript
        ]
        
        return json.dumps(formatted_transcript, indent=4, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve transcript: {str(e)}"})

if __name__ == "__main__":
    result = get_transcript(video_url)
    print(result)
