from tweepy import Client, Paginator, TweepyException
from dotenv import load_dotenv
import os
# Load environment variables from a .env file
load_dotenv()

# Accessing environment variables
consumer_key = os.environ.get('X_CONSUMER_KEY')
consumer_secret = os.environ.get('X_CONSUMER_SECRET')
access_token = os.environ.get('X_ACCESS_TOKEN')
access_token_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')

client = Client(
        consumer_key=consumer_key, 
        consumer_secret=consumer_secret, 
        access_token=access_token, 
        access_token_secret=access_token_secret
    )

def send_post(content: str) -> str:
    """
    Posts a tweet on behalf of the user.

    Parameters:
    - content: The message to tweet.
    """
    try:
        response = client.create_tweet(text=content)
        if response.data:
            print(f"Tweet posted: {content}")
            return response.data['id']
        else:
            print(f"Failed to post tweet: {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred while posting the tweet: {e}")
        return None