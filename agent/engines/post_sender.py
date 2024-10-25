# import tweepy

# def send_post(client: Client, content: str) -> str:
#     """
#     Posts a tweet on behalf of the user.

#     Parameters:
#     - content: The message to tweet.
#     """
#     try:
#         response = client.create_tweet(text=content)
#         if response.data:
#             print(f"Tweet posted: {content}")
#             return response.data['id']
#         else:
#             print(f"Failed to post tweet: {response.text}")
#             return None
#     except Exception as e:
#         print(f"An error occurred while posting the tweet: {e}")
#         return None
    
import requests

def send_post(auth, content: str) -> str:
    """
    Posts a tweet on behalf of the user.

    Parameters:
    - content: The message to tweet.
    """
    url = 'https://api.twitter.com/2/tweets'
    
    # Prepare the payload
    payload = {
        'text': content
    }
    
    # Add media if provided
    # if media_ids:
    #     payload['media'] = {
    #         'media_ids': media_ids
    #     }
        
    # Make the POST request
    try:
        response = requests.post(url, json=payload, auth=auth)
        
        if response.status_code == 201:  # Twitter API returns 201 for successful tweet creation
            tweet_data = response.json()
            return tweet_data['data']['id']
        else:
            print(f'Error: {response.status_code} - {response.text}')
            return None
            
    except Exception as e:
        print(f'Failed to post tweet: {str(e)}')
        return None