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
        "image_path": post.image_path
    }


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