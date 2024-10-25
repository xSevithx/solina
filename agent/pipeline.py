from sqlalchemy.orm import Session
from db.db_setup import get_db
from engines.post_retriever import retrieve_recent_posts, fetch_external_context, fetch_notification_context
from engines.short_term_mem import generate_short_term_memory
from engines.long_term_mem import create_embedding, retrieve_relevant_memories, store_memory
from engines.post_maker import generate_post
from engines.significance_scorer import score_significance
from engines.post_sender import send_post
from engines.wallet_send import transfer_eth
from models import Post, User

def run_pipeline(db: Session, user_id, user_name, auth, private_key_hex: str, openrouter_api_key: str, openai_api_key: str):
    """
    Run the main pipeline for generating and posting content.
    
    Args:
        db (Session): Database session
        openrouter_api_key (str): API key for OpenRouter
        openai_api_key (str): API key for OpenAI
        your_site_url (str): Your site URL for OpenRouter API
        your_app_name (str): Your app name for OpenRouter API
        news_api_key (str): API key for news service
    """
    # Step 1: Retrieve recent posts
    recent_posts = retrieve_recent_posts(db)
    print(f"Recent posts: {recent_posts}")
    
    # Step 2: Fetch external context
    # LEAVING THIS EMPTY FOR ANYTHING YOU WANT TO SUBSTITUTE (NEWS API, DATA SOURCE ETC)
    reply_fetch_list = []
    for e in recent_posts:
        reply_fetch_list.append((e["tweet_id"], e["content"]))
    notif_context = fetch_notification_context(user_id, user_name, auth, reply_fetch_list)
    print(f"Notifications: {notif_context}")
    external_context = notif_context
    
    # Step 3: Generate short-term memory
    short_term_memory = generate_short_term_memory(recent_posts, external_context, openrouter_api_key)
    print(f"Short-term memory: {short_term_memory}")
    
    # Step 4: Create embedding for short-term memory
    short_term_embedding = create_embedding(short_term_memory, openai_api_key)
    print(f"Short-term embedding: {short_term_embedding}")
    
    # Step 5: Retrieve relevant long-term memories
    long_term_memories = retrieve_relevant_memories(db, short_term_embedding)
    print(f"Long-term memories: {long_term_memories}")
    
    # Step 6: Generate new post
    new_post_content = generate_post(short_term_memory, long_term_memories, recent_posts, openrouter_api_key)
    print(f"New post content: {new_post_content}")

    # Step 7: Score the significance of the new post
    significance_score = score_significance(new_post_content, openrouter_api_key)
    print(f"Significance score: {significance_score}")
    
    # Step 8: Store the new post in long-term memory if significant enough
    # CHANGE THIS TO WHATEVER YOU WANT TO DETERMINE HOW RELEVANT A POST / SHORT TERM MEMORY NEEDS TO BE TO WARRANT A RESPONSE
    if significance_score >= 7:
        new_post_embedding = create_embedding(new_post_content, openai_api_key)
        store_memory(db, new_post_content, new_post_embedding, significance_score)
    
    # Step 9: Save the new post to the database
    # Update these values to whatever you want
    ai_user = db.query(User).filter(User.username == "ai_bot").first()
    if not ai_user:
        ai_user = User(username="ai_bot", email="ai_bot@example.com")
        db.add(ai_user)
        db.commit()

    # THIS IS WHERE YOU WOULD INCLUDE THE POST_SENDER.PY FUNCTION TO SEND THE NEW POST TO TWITTER ETC
    # Only Bangers!
    if significance_score >= 3:
        tweet_id = send_post(auth, new_post_content)
        print(tweet_id)
        if tweet_id:
            new_db_post = Post(content=new_post_content, user_id=ai_user.id, type="text", tweet_id=tweet_id)
            db.add(new_db_post)
            db.commit()
    
    print(f"New post generated with significance score {significance_score}: {new_post_content}")


# if __name__ == "__main__":

#     db = next(get_db())
#     run_pipeline(
#         db,
#         openrouter_api_key="your_openrouter_api_key",
#         openai_api_key="your_openai_api_key",
#         news_api_key="your_news_api_key"
#     )