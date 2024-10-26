import requests
import re

def decide_to_follow_users(posts, openrouter_api_key: str):
    """
    Detects Twitter usernames from a list of posts and decides whether to follow them, assigning a score.

    Parameters:
    - posts (List): List of posts of any type
    - openrouter_api_key (str): API key for OpenRouter

    Returns:
    - str: JSON-formatted string with a list of decisions
    """
    # Convert everything to strings first
    str_posts = [str(post) for post in posts]

    # Extract Twitter usernames
    twitter_pattern = re.compile(r'@([A-Za-z0-9_]{1,15})')
    twitter_usernames = []

    for post in str_posts:
        found_usernames = twitter_pattern.findall(post)
        twitter_usernames.extend(found_usernames)

    # Remove duplicates
    twitter_usernames = list(set(twitter_usernames))

    # Prepare the prompt
    prompt = f"""
    Analyze the following recent posts:

    Recent posts:
    {posts}

    Twitter usernames:
    {twitter_usernames}

    Based on this information, decide if you want to follow any of the Twitter usernames, and assign a score from 0 to 1 indicating how much you want to follow them (1 being the highest).

    Remember that following someone is a super valuable decision because you have very limited attention, and each follow allows the person to have immense power over your personality development.

    You should carefully evaluate these decisions for your own future and survival.

    If you choose to follow any Twitter usernames, you must return ONLY a JSON object with a list of objects, each containing the 'username' and the 'score' of how much you want to follow them.

    If you choose not to follow anyone, you must return ONLY a JSON object with an empty list in it.

    Only return the correctly formatted JSON object in both cases. Do not give any other information.

    Example Response if you choose to follow someone:

    [
        {{"username": "sxysun1", "score": 0.9}},
        {{"username": "socrates1024", "score": 0.7}}
    ]

    Example Response if you choose not to follow anyone:

    []
    """

    # Send the prompt to the AI model
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
        print(f"Decisions from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating decision: {response.text}")

def get_user_id(auth, username):
    url = f'https://api.twitter.com/2/users/by/username/{username}'
    params = {
        'user.fields': 'id,username',
    }
    response = requests.get(url, auth=auth, params=params)
    if response.status_code == 200:
        user_data = response.json()
        return user_data['data']['id']
    else:
        print(f'Error fetching user ID: {response.status_code} - {response.text}')
        return None
    
def follow_user(auth, source_user_id, target_user_id):
    url = f'https://api.twitter.com/2/users/{source_user_id}/following'
    json_data = {
        'target_user_id': target_user_id,
    }
    response = requests.post(url, auth=auth, json=json_data)
    if response.status_code in [200, 201]:
        print(f'Successfully followed user ID {target_user_id}')
        return True
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return False
    
def follow_by_username(auth, my_user_id, username):

    target = get_user_id(auth, username=username)
    if target:
        follow_user(auth, my_user_id, target)
    