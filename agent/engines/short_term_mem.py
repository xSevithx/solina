# Short Term Memory Engine
# Objective: Ephemeral memory. This would simulate scrolling through 4chan or twitter, looking at the most recent posts in their timeline and including that in the post making context to make a decision on whether to reply or not.

# Inputs: 
# Latest top 10 posts 
# Real world context / input from news or external sources

# Outputs: 
# processed information into an internal thought / monologue about current posts and relevance

import json
import time
from typing import List, Dict
import requests
from sqlalchemy.orm import class_mapper


# Can modify the type depending on the format that twitter api returns for posts
# external_context in case you want to include information from other sources 
def generate_short_term_memory(posts: List[Dict], external_context: List[str], llm_api_key: str) -> str:
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
    Focus on key themes, trends, and potential areas of interest MOST IMPORTANTLY based on the External Context tweets. 
    Recent posts don't need to be considered unless they are relevant to the External Context tweets. Refer to the username if thinking about someone.
    Your current priors and your inherent awareness of yourself and what's going on can have an impact too. Stick to your persona, do your thing, write in the way that suits you! 
    Doesn't have to be legible to anyone but you.
    """
    
    tries = 0
    max_tries = 3
    while tries < max_tries:
        try:
            url = "https://api.hyperbolic.xyz/v1/completions"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm_api_key}"
            }
            
            data = {
                "prompt": prompt,
                "model": "meta-llama/Meta-Llama-3.1-405B",
                "max_tokens": 512,
                "presence_penalty": 0,
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['text']
                print(f"Short-term memory generated with response: {content}")
                if content and content.strip():
                    return content
                
            print(f"Attempt {tries + 1} failed for short-term memory generation. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error on attempt {tries + 1}: {str(e)}")
            tries += 1
            time.sleep(5)  # Add a small delay between retries