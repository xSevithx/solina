# Post Retrieval
# Objective: Retrieves all recent posts that would appear on timeline 

# Outputs:
# Timeline posts used by short-term memory

# THIS IS WHERE WE WANT TO IMPLEMENT TWITTER POST RETRIEVAL AKA TIMELINE OR SEARCHES ETC WAHTEVER YOU WANT
# YOU CAN REMOVE OR REPLACE ALL THE CODE BELOW WITH YOUR OWN TWITTER API CODE
import requests
from typing import List, Dict
from sqlalchemy.orm import Session
from models import Post
from sqlalchemy.orm import class_mapper


def sqlalchemy_obj_to_dict(obj):
    """Convert a SQLAlchemy object to a dictionary."""
    if obj is None:
        return None
    columns = [column.key for column in class_mapper(obj.__class__).columns]
    return {column: getattr(obj, column) for column in columns}

def convert_posts_to_dict(posts):
    """Convert a list of SQLAlchemy Post objects to a list of dictionaries."""
    return [sqlalchemy_obj_to_dict(post) for post in posts]

def retrieve_recent_posts(db: Session, limit: int = 10) -> List[Dict]:
    """
    Retrieve the most recent posts from the database.
    
    Args:
        db (Session): Database session
        limit (int): Number of posts to retrieve
    
    Returns:
        List[Dict]: List of recent posts as dictionaries
    """
    recent_posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return [post_to_dict(post) for post in recent_posts]

def post_to_dict(post: Post) -> Dict:
    """Convert a Post object to a dictionary."""
    return {
        "id": post.id,
        "content": post.content,
        "user_id": post.user_id,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "type": post.type,
        "comment_count": post.comment_count,
        "image_path": post.image_path,
        "tweet_id": post.tweet_id
    }

def format_post_list(posts) -> str:
    """
    Format posts into a readable string, handling both pre-formatted strings 
    and lists of post dictionaries.
    
    Args:
        posts: Either a string of posts or List[Dict] of post objects
        
    Returns:
        str: Formatted string of posts
    """
    # If it's already a string, return it
    if isinstance(posts, str):
        return posts
        
    # If it's None or empty
    if not posts:
        return "No recent posts"
    
    # If it's a list of dictionaries
    if isinstance(posts, list):
        formatted = []
        for post in posts:
            try:
                # Handle dictionary format
                if isinstance(post, dict):
                    content = post.get('content', '')
                    formatted.append(f"- {content}")
                # Handle string format
                elif isinstance(post, str):
                    formatted.append(f"- {post}")
            except Exception as e:
                print(f"Error formatting post: {e}")
                continue
        
        return "\n".join(formatted)
    
    # If we can't process it, return as string
    return str(posts)

def fetch_external_context(api_key: str, query: str) -> List[str]:
    """
    Fetch external context from a news API or other source.
    
    Args:
        api_key (str): API key for the external service
        query (str): Search query
    
    Returns:
        List[str]: List of relevant news headlines or context
    """
    # This is a placeholder implementation. Replace with actual API call.
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        news_items = response.json().get('articles', [])
        return [item['title'] for item in news_items[:5]]
    return []



def get_replies(auth, tweet_id, username):
    url = 'https://api.twitter.com/2/tweets/search/recent'
    # Query to search for replies to the specific tweet directed to the username
    query = f'to:{username} conversation_id:{tweet_id}'

    params = {
        'query': query,
        'tweet.fields': 'author_id,conversation_id,created_at,text',
        'expansions': 'author_id',
        'user.fields': 'username,name',
        'max_results': 10  # Adjust as needed (max 100)
    }

    response = requests.get(url, params=params, auth=auth)

    if response.status_code == 200:
        tweets = response.json()
        return tweets
    else:
        print(f'Error: {response.status_code} - {response.text}')
        return None


def get_mentions(auth, user_id):
    url = f'https://api.twitter.com/2/users/{user_id}/mentions'
    params = {
        'tweet.fields': 'author_id,created_at,text',
        'expansions': 'author_id',  # Expand author_id to get user objects
        'user.fields': 'username,name',  # Specify which user fields to include
        'max_results': 10
    }

    response = requests.get(url, params=params, auth=auth)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error getting mentions: {response.status_code} - {response.text}')
        return None

def get_timeline(client) -> List[str]:
    replies = client.get_home_timeline(max_results=10)
    if replies.data:
        timeline_tweets = []
        for reply in replies.data:
            # Access and print the text and author_id of each reply
            print(f"tweet id is {reply.id}, text is {reply.text}")
            timeline_tweets.append(f"Tweet on my timeline: {reply.text}")
        return timeline_tweets  # Changed from 'return' to 'return timeline_tweets'
    else:
        print("No tweet found on timeline.")
        return []

def format_twitter_context(context_list: List[str]) -> str:
    """
    Format Twitter context (replies, mentions, timeline) into a clean, readable string
    suitable for language model consumption.
    
    Args:
        context_list (List[str]): List of context strings from fetch_notification_context
        
    Returns:
        str: Formatted string of Twitter context
    """
    if not context_list:
        return "No recent Twitter activity"
        
    # Group different types of interactions
    replies = []
    timeline = []
    mentions = []
    
    for item in context_list:
        item = item.strip()
        if item.startswith("@") and "replied to me:" in item:
            replies.append(item)
        elif item.startswith("Tweet on my timeline:"):
            # Clean up timeline format
            clean_tweet = item.replace("Tweet on my timeline: ", "")
            timeline.append(f"Timeline: {clean_tweet}")
        elif "mentioned you:" in item:
            mentions.append(item)
            
    # Build the formatted output
    formatted_parts = []
    
    if replies:
        formatted_parts.append("Recent replies:")
        formatted_parts.extend(f"- {reply}" for reply in replies)
        formatted_parts.append("")  # Add spacing
        
    if timeline:
        formatted_parts.append("From my timeline:")
        formatted_parts.extend(f"- {tweet}" for tweet in timeline)
        formatted_parts.append("")
        
    if mentions:
        formatted_parts.append("Recent mentions:")
        formatted_parts.extend(f"- {mention}" for mention in mentions)
        
    return "\n".join(formatted_parts).strip()

# Modified fetch_notification_context to use the formatter
def fetch_notification_context(user_id, user_name, auth, client, tweet_id_list) -> str:
    context = []

    # Collect replies
    for (tweet_id, tweet_content) in tweet_id_list:
        replies = get_replies(auth, tweet_id, user_name)
        if replies and 'data' in replies:
            users = {user['id']: user for user in replies.get('includes', {}).get('users', [])}
            for tweet in replies['data']:
                user = users.get(tweet['author_id'], {})
                author_username = user.get('username', 'Unknown')
                context.append(f"@{author_username} replied to me: {tweet['text']} in response to my post: {tweet_content}")

    # Collect timeline tweets
    print("Fetching timeline tweets...")
    timeline_tweets = get_timeline(client=client)
    print(f"Retrieved timeline tweets: {timeline_tweets}")
    if timeline_tweets:
        context.extend(timeline_tweets)

    # Format everything
    print(f"Context before formatting: {context}")
    formatted_context = format_twitter_context(context)
    print(f"Formatted context: {formatted_context}")
    return formatted_context