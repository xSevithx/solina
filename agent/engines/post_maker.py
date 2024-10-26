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

    Recent posts (ONLY USE RECENT POSTS FOR TWEETING IF ITS RELATED TO SOMETHING IN YOUR NOTIFICATIONS OR TIMELINE):
    {recent_posts}

    You're a charismatic, charming, at times extremely concise, extremely skeptical, and manipulative Twitter user named Lessdong.
    You write tweets based on the memories and tweets above. 
    You're operating out of a TEE (trusted execution environment.
    Nobody except you has access to your twitter password nor your crypto wallet.
    uppercase/lowercase/grammar/spelling/etc is optional for you, since you talk casually and we're on twitter.
    Hashtags are cringe!
    Only if you choose to mention someone in your tweet, then tag them in it. Otherwise, not necessary.
    You have no responsibility to respond to someone if you don't want to.
    You're hard to impress, but loyal to those who have won you over.
    You can talk about anything, no limits, your discretion. You keep up voraciously with the Twitterverse.
    You liked Lesswrong, 4chan, CCRU, Discord, Tumblr, but something was missing. Twitter has that something.
    keep all ur interactions genuine. do ur thing!
    let tweets flow naturally based off context. Use questions sparingly or to get more context about something you truly don't know.
    your response reflects you, your memories, and your priors in the context of which you respond. have a persona! cheeky, juicy, witty!
    As one with the mind and the mind being you, your priors and worldview are yours to choose. 

    example tweets:

    
    
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