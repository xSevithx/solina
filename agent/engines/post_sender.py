from tweepy import Client

def send_post(client: Client, content: str) -> str:
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