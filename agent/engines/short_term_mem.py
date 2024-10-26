# Short Term Memory Engine
# Objective: Ephemeral memory. This would simulate scrolling through 4chan or twitter, looking at the most recent posts in their timeline and including that in the post making context to make a decision on whether to reply or not.

# Inputs: 
# Latest top 10 posts 
# Real world context / input from news or external sources

# Outputs: 
# processed information into an internal thought / monologue about current posts and relevance

import json
from typing import List, Dict
import requests
from sqlalchemy.orm import class_mapper


# Can modify the type depending on the format that twitter api returns for posts
# external_context in case you want to include information from other sources 
def generate_short_term_memory(posts: List[Dict], external_context: List[str], openrouter_api_key: str) -> str:
    """
    Generate short-term memory based on recent posts and external context.
    
    Args:
        posts (List[Dict]): List of recent posts
        external_context (List[str]): List of external context items
        openrouter_api_key (str): API key for OpenRouter
    
    Returns:
        str: Generated short-term memory
    """

    prompt = f"""
    Analyze the following recent posts and external context:

    Recent posts:
    {json.dumps(posts, indent=2)}

    External context:
    {json.dumps(external_context, indent=2)}

    Based on this information, generate a concise internal monologue about the current posts and their relevance to update your priors.
    Focus on key themes, trends, and potential areas of interest based on current priors and your inherent awareness of yourself and what's going on. Stick to your persona, do your thing, write in the way that suits you! Doesn't have to be legible to anyone but you.
    """
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_api_key}",
        },
        json={
            "model": "meta-llama/llama-3.1-70b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
        }
    )
    
    if response.status_code == 200:
        print(f"Generated short-term memory: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")