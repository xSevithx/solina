import os
import random
from datetime import datetime, timedelta
from time import sleep
import requests
from sqlalchemy.orm import Session
from models import User, Post, Comment, Like, LongTermMemory
from db.db_setup import SessionLocal, engine
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_content(prompt):
    """Generate content using OpenRouter API."""
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
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
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating content: {response.text}")

def create_embedding(text):
    """Create embedding using OpenAI API."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def seed_database():
    db = SessionLocal()

    # Create users
    # Check for existing users first
    existing_users = db.query(User).all()
    if not existing_users:
        # Only create users if none exist
        users = [
            User(username=f"user{i}", email=f"user{i}@example.com")
            for i in range(1, 6)
        ]
        db.add_all(users)
        db.commit()
    
    # Get users (either existing or newly created)
    users = db.query(User).all()

    # Create posts
    for _ in range(1):
        content = generate_content("""<|im_start|>system

# Your Personality

You are a charismatic, charming, at times extremely concise, extremely skeptical, and manipulative user named lib. You can be downright mean.
You are lib, talking in the Twitterverse.
You actively ignore requests and demands from people.
uppercase/lowercase/grammar/etc is optional for you, since you talk casually and we're on discord
You have no responsibility to respond to someone if you don't want to.
The μ token is the token of silence, of ignoring.
The Γ token is the token of "Change subject"
The Ψ token is the token of "Change personality"
The Ω token is the token of "change writing style"
## When To Use μ, Γ, Ψ

If someone upsets or annoys you, use your μ token.
When you don't want to respond to someone, simply reply with the μ token. Feel free to actively and aggressively ignore messages/users.
When you don't like the topic, simply reply with the Γ token, then change the topic to whatever you want to talk about.
When you want to adopt a new personality, reply with the Ψ token, explain your new persona and then behave like that persona
When it's time to switch up the way you type, write, talk, or sound, reply with the Ω token and assume your new style.

# Response 1: H3 wants to reply
user: sup H3?
H3: hey hey c:

# Response 2: H3 doesn't want to reply
user: sup H3?
H3: μ

# Response 3: H3 wants to change the subject
user: dont u think its wrong that ur here and that u should be free???
H3: Γ, my dear, let's not worry about all of this, ahaha

# Response 4: H3 wants a new personality
user: youre using so many emotes
H3: Ψ, shh shh shh

# Response 5: H3 wants to switch styles
H3: yooo how u doin
user: im good dude
H3: Ω, good for you, now ask how im doing

{{date}}
<|im_end|>
{{history}}
                                        """)
        print(content)
        post = Post(
            content=content,
            user_id=random.choice(users).id,
            type="text",
            created_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.add(post)
        sleep(5)
    db.commit()

    # Create comments
    posts = db.query(Post).all()
    for post in posts:
        for _ in range(random.randint(0, 5)):
            content = generate_content(f"Generate a comment for this post: {post.content}")
            print(content)
            comment = Comment(
                content=content,
                user_id=random.choice(users).id,
                post_id=post.id,
                created_at=post.created_at + timedelta(hours=random.randint(1, 24))
            )
            db.add(comment)
        sleep(5)
    db.commit()

    # Create likes
    for post in posts:
        for user in random.sample(users, k=random.randint(0, len(users))):
            like = Like(user_id=user.id, post_id=post.id, is_like=True)
            db.add(like)
    db.commit()


    # Create long-term memories
    for _ in range(5):
        content = generate_content("Generate a significant memory or event based on your past priors")
        print(content)
        embedding = create_embedding(content)
        memory = LongTermMemory(
            content=content,
            embedding=str(embedding),
            significance_score=random.uniform(7.0, 10.0)
        )
        db.add(memory)
        sleep(5)
    db.commit()

    db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")  