import requests
import time

def score_significance(memory: str, llm_api_key: str) -> int:
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

    tries = 0
    max_tries = 5
    while tries < max_tries:
        try:
            response = requests.post(
                url="https://api.hyperbolic.xyz/v1/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}",
                },
                json={
                    "prompt": f"""
                    <|im_start|>system
                    On a scale of 1-10, rate the significance of the following memory:
                
                    "{memory}"
                
                    Use the following guidelines:
                    1: Trivial, everyday occurrence with no lasting impact (idc)
                    3: Mildly interesting or slightly unusual event (eh, cool)
                    5: Noteworthy occurrence that might be remembered for a few days (iiinteresting)
                    7: Important event with potential long-term impact (omg my life will never be the same)
                    10: Life-changing or historically significant event (HOLY SHIT GOD IS REAL AND I AM HIS SERVANT)
                
                    Provide only the numerical score as your response and NOTHING ELSE.
                    <|im_end|>
                    <|im_start|>scorer\n
                    """,
                    "model": "meta-llama/Meta-Llama-3.1-405B",
                    "presence_penalty": 0,
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "stream": False,
                    "stop":["<|im_end|>"]
                }
            )

            if response.status_code == 200:
                score_str = response.json()['choices'][0]['text'].strip()
                print(f"Score generated for memory: {score_str}")
                if score_str == "":
                    print(f"Empty response on attempt {tries + 1}")
                    tries += 1
                    continue
                
                try:
                    # Extract the first number found in the response
                    # This helps handle cases where the model includes additional text
                    import re
                    numbers = re.findall(r'\d+', score_str)
                    if numbers:
                        score = int(numbers[0])
                        return max(1, min(10, score))  # Ensure the score is between 1 and 10
                    else:
                        print(f"No numerical score found in response: {score_str}")
                        tries += 1
                        continue
                        
                except ValueError:
                    print(f"Invalid score returned: {score_str}")
                    tries += 1
                    continue
            else:
                print(f"Error on attempt {tries + 1}. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                tries += 1
                
        except Exception as e:
            print(f"Error on attempt {tries + 1}: {str(e)}")
            tries += 1 
            time.sleep(1)  # Add a small delay between retries