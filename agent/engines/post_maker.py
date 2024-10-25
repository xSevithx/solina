# Post Maker
# Objective: Takes in context from short and long term memory along with the recent posts and generates a post or reply to one of them

# Inputs:
# Short term memory output
# Long term memory output
# Retrieved posts from front of timeline

# Outputs:
# Text generated post /reply

# Things to consider:
# Database schema. Schemas for posts and how replies are classified.

import requests
from typing import List, Dict

def generate_post(short_term_memory: str, long_term_memories: List[Dict], recent_posts: List[Dict], openrouter_api_key: str) -> str:
    """
    Generate a new post or reply based on short-term memory, long-term memories, and recent posts.
    
    Args:
        short_term_memory (str): Generated short-term memory
        long_term_memories (List[Dict]): Relevant long-term memories
        recent_posts (List[Dict]): Recent posts from the timeline
        openrouter_api_key (str): API key for OpenRouter
        your_site_url (str): Your site URL for OpenRouter API
        your_app_name (str): Your app name for OpenRouter API
    
    Returns:
        str: Generated post or reply
    """
    prompt = f"""
    Based on the following information,

    Short-term memory:
    {short_term_memory}

    Long-term memories:
    {long_term_memories}

    Recent posts:
    {recent_posts}

    You write a social media post or response based on the memories and posts / replies above. The tone should be casual, like you're talking to someone online. 
    You can share anything you want to, ask any question, or build on recent discussions or what you believe is relevant in the Twitterverse. 
    Keep it genuine - avoid corporate speak or forced enthusiasm unless it’s being used for a sarcastic purpose. 
    The post should feel like it flows naturally from what's being discussed. 
    Your response reflects you, your memories and your priors in the context of which you respond. (no need for perfect grammar). 
    As one with the mind and the mind being you, your priors and worldview are yours to choose. 
    Write it in a way that someone would actually type it out on their phone. Absolutely no hashtags, hellah cringe.
    """

    print(f"Generating post with prompt: {prompt}")
    
    max_tries = 5
    tries = 0
    while tries < max_tries:
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
                "temperature": 0.8,
            }
        )

        if response.status_code == 200:
            print(f"Generated post: {response.json()}")
            content = response.json()['choices'][0]['message']['content']
            if content == "":
                tries += 1
                continue
            return content
        else:
            raise Exception(f"Error generating post: {response.text}")