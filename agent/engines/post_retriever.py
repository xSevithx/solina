import requests
from typing import List, Dict
from sqlalchemy.orm import Session
from models import Post
from sqlalchemy.orm import class_mapper
from twitter.account import Account
from twitter.scraper import Scraper


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
        "tweet_id": post.tweet_id,
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
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        news_items = response.json().get("articles", [])
        return [item["title"] for item in news_items[:5]]
    return []


def parse_tweet_data(tweet_data):
    """Parse tweet data from the X API response."""
    try:
        all_tweets_info = []
        entries = tweet_data['data']['home']['home_timeline_urt']['instructions'][0]['entries']
        
        for entry in entries:
            entry_id = entry.get('entryId', '')
            tweet_id = entry_id.replace('tweet-', '') if entry_id.startswith('tweet-') else None
            
            if 'itemContent' not in entry.get('content', {}) or \
               'tweet_results' not in entry.get('content', {}).get('itemContent', {}):
                continue
                
            tweet_info = entry['content']['itemContent']['tweet_results'].get('result')
            if not tweet_info:
                continue
                
            try:
                user_info = tweet_info['core']['user_results']['result']['legacy']
                tweet_details = tweet_info['legacy']
                
                readable_format = {
                    "Tweet ID": tweet_id or tweet_details.get('id_str'),
                    "Entry ID": entry_id,
                    "Tweet Information": {
                        "text": tweet_details['full_text'],
                        "created_at": tweet_details['created_at'],
                        "likes": tweet_details['favorite_count'],
                        "retweets": tweet_details['retweet_count'],
                        "replies": tweet_details['reply_count'],
                        "language": tweet_details['lang'],
                        "tweet_id": tweet_details['id_str']
                    },
                    "Author Information": {
                        "name": user_info['name'],
                        "username": user_info['screen_name'],
                        "followers": user_info['followers_count'],
                        "following": user_info['friends_count'],
                        "account_created": user_info['created_at'],
                        "profile_image": user_info['profile_image_url_https']
                    },
                    "Tweet Metrics": {
                        "views": tweet_info.get('views', {}).get('count', '0'),
                        "bookmarks": tweet_details.get('bookmark_count', 0)
                    }
                }
                if tweet_details['favorite_count'] > 20 and user_info['followers_count'] > 300 and tweet_details['reply_count'] > 3:
                    all_tweets_info.append(readable_format)
            except KeyError:
                continue
                
        return all_tweets_info
            
    except KeyError as e:
        return f"Error parsing data: {e}"


def get_root_tweet_id(tweets, start_id):
    """Find the root tweet ID of a conversation."""
    current_id = start_id
    while True:
        tweet = tweets.get(str(current_id))
        if not tweet:
            return current_id
        parent_id = tweet.get('in_reply_to_status_id_str')
        if not parent_id or parent_id not in tweets:
            return current_id
        current_id = parent_id


def format_conversation_for_llm(data, tweet_id):
    """Convert a conversation tree into LLM-friendly format."""
    tweets = data['globalObjects']['tweets']
    users = data['globalObjects']['users']
    
    def get_conversation_chain(current_id, processed_ids=None):
        if processed_ids is None:
            processed_ids = set()
            
        if not current_id or current_id in processed_ids:
            return []
            
        processed_ids.add(current_id)
        current_tweet = tweets.get(str(current_id))
        if not current_tweet:
            return []
            
        user = users.get(str(current_tweet['user_id']))
        username = f"@{user['screen_name']}" if user else "Unknown User"
        
        chain = [{
            'id': current_id,
            'username': username,
            'text': current_tweet['full_text'],
            'reply_to': current_tweet.get('in_reply_to_status_id_str')
        }]
        
        for potential_reply_id, potential_reply in tweets.items():
            if potential_reply.get('in_reply_to_status_id_str') == current_id:
                chain.extend(get_conversation_chain(potential_reply_id, processed_ids))
        
        return chain

    root_id = get_root_tweet_id(tweets, tweet_id)
    conversation = get_conversation_chain(root_id)
    
    if not conversation:
        return "No conversation found."

    # Format the conversation for LLM
    output = ["New reply to my original conversation thread or a Mention from somebody:"]
    
    for i, tweet in enumerate(conversation, 1):
        reply_context = (f"[Replying to {next((t['username'] for t in conversation if t['id'] == tweet['reply_to']), 'unknown')}]"
                        if tweet['reply_to'] else "[Original tweet]")
            
        output.append(f"{i}. {tweet['username']} {reply_context}:")
        output.append(f"   \"{tweet['text']}\"")
        output.append("")
    
    return "\n".join(output)


def find_all_conversations(data):
    """Find and format all conversations in the data."""
    tweets = data['globalObjects']['tweets']
    processed_roots = set()
    conversations = []

    sorted_tweets = sorted(
        tweets.items(),
        key=lambda x: x[1]['created_at'],
        reverse=True
    )

    for tweet_id, _ in sorted_tweets:
        root_id = get_root_tweet_id(tweets, tweet_id)
        
        if root_id not in processed_roots:
            processed_roots.add(root_id)
            conversation = format_conversation_for_llm(data, tweet_id)
            if conversation != "No conversation found.":
                conversations.append(conversation)

    if not conversations:
        return "No conversations found."
    
    return "\n\n".join(conversations)


def get_timeline(account: Account) -> List[str]:
    """Get timeline using the new Account-based approach."""
    timeline = account.home_latest_timeline(10)
    
    tweets_info = parse_tweet_data(timeline[0])
    filtered_timeline = []
    for t in tweets_info:
        filtered_timeline.append(f'New post on my timeline from @{t["Author Information"]["username"]}: {t["Tweet Information"]["text"]}\n')
        # print(f'Tweet ID: {t["Tweet ID"]}, on my timeline: {t["Author Information"]["username"]} said {t["Tweet Information"]["text"]}\n')
    return filtered_timeline


def fetch_notification_context(account: Account, tweet_id_list) -> str:
    """Fetch notification context using the new Account-based approach."""
    context = []
    
    # Get timeline posts
    timeline = get_timeline(account)
    context.extend(timeline)
    notifications = account.notifications()
    context.append(find_all_conversations(notifications))

    return context