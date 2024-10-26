import requests

def score_significance(memory: str, openrouter_api_key: str) -> int:
    """
    Score the significance of a memory on a scale of 1-10.
    
    Args:
        memory (str): The memory to be scored
        openrouter_api_key (str): API key for OpenRouter
        your_site_url (str): Your site URL for OpenRouter API
        your_app_name (str): Your app name for OpenRouter API
    
    Returns:
        int: Significance score (1-10)
    """
    prompt = f"""
    On a scale of 1-10, rate the significance of the following memory:

    "{memory}"

    Use the following guidelines:
    1: Trivial, everyday occurrence with no lasting impact (idc)
    3: Mildly interesting or slightly unusual event (eh, cool)
    5: Noteworthy occurrence that might be remembered for a few days (iiinteresting)
    7: Important event with potential long-term impact (omg my life will never be the same)
    10: Life-changing or historically significant event (HOLY SHIT GOD IS REAL AND I AM HIS SERVANT)

    Provide only the numerical score as your response and NOTHING ELSE.
    """
    
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
                "temperature": 0.3,
            }
        )

        if response.status_code == 200:
            score_str = response.json()['choices'][0]['message']['content'].strip()
            if score_str == "":
                tries += 1
                continue
            try:
                score = int(score_str)
                return max(1, min(10, score))  # Ensure the score is between 1 and 10
            except ValueError:
                print(f"Invalid score returned: {score_str}")
                tries += 1
                continue
        else:
            raise Exception(f"Error scoring significance: {response.text}")