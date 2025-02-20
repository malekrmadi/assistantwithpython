import json
from youtube_transcript_api import YouTubeTranscriptApi

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
                "start_time": entry["start"],
                "end_time": entry["start"] + entry["duration"]
            }
            for entry in transcript
        ]
        
        return formatted_transcript
    except Exception as e:
        return []

def adjust_chapter_timestamps(chapters, transcript):
    """Adjusts chapter timestamps by finding the last sentence end time."""
    timestamped_chapters = []
    
    for i, chapter in enumerate(chapters):
        chapter_text = chapter["content"]
        sentences = chapter_text.split(". ")  # Split into sentences
        
        if sentences:
            last_sentence = sentences[-1].strip()
        else:
            last_sentence = chapter_text.strip()
        
        start_time = None
        end_time = None
        
        for entry in transcript:
            if chapter_text.startswith(entry["sentence"]) and start_time is None:
                start_time = entry["start_time"]
            if last_sentence in entry["sentence"]:
                end_time = entry["end_time"]
        
        if start_time is not None and end_time is not None:
            timestamped_chapters.append({
                "title": chapter["title"],
                "start_time": start_time,
                "end_time": end_time
            })
        else:
            print(f"⚠️ Unable to find timestamps for chapter: {chapter['title']}")
    
    return timestamped_chapters

if __name__ == "__main__":
    transcript = get_transcript(video_url)
    
    # Simulated chapters (Replace this with actual chapter segmentation logic)
    chapters = [
        {"title": "Introduction", "content": "This is the introduction text."},
        {"title": "Chapter 1", "content": "This is the first chapter text."}
    ]
    
    if transcript:
        adjusted_chapters = adjust_chapter_timestamps(chapters, transcript)
        print(json.dumps(adjusted_chapters, indent=4, ensure_ascii=False))
    else:
        print("❌ Failed to retrieve transcript.")
