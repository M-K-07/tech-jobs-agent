from supadata import Supadata, SupadataError
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the client
supadata = Supadata(api_key=os.getenv("SUPADATA_API_KEY"))


def get_transcript(video_id):
    
    transcript = supadata.transcript(
        url=f"https://www.youtube.com/watch?v={video_id}",  
        lang="en",  
        text=True,  
        mode="auto"  
    )

    # For immediate results
    if hasattr(transcript, 'content'):
        # print(f"Transcript: {transcript.content}")
        return transcript.content
    else:
        print(f"Processing started with job ID: {transcript.job_id}")