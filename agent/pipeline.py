import json
import time
from sqlalchemy.orm import Session
from db.db_setup import get_db
from engines.post_retriever import (
    retrieve_recent_posts,
    fetch_external_context,
    fetch_notification_context,
    format_post_list
)
from engines.short_term_mem import generate_short_term_memory
from engines.long_term_mem import (
    create_embedding,
    retrieve_relevant_memories,
    store_memory,
)
from engines.post_maker import generate_post
from engines.significance_scorer import score_significance
from engines.post_sender import send_post
from engines.wallet_send import transfer_eth, wallet_address_in_post, get_wallet_balance
from engines.follow_user import follow_by_username, decide_to_follow_users
from models import Post, User
from twitter.account import Account


def run_pipeline(
    db: Session,
    account: Account,
    private_key_hex: str,
    eth_mainnet_rpc_url: str,
    llm_api_key: str,
    openrouter_api_key: str,
    openai_api_key: str,
):
    """
    Run the main pipeline for generating and posting content.

    Args:
        db (Session): Database session
        account (Account): Twitter/X API account instance
        private_key_hex (str): Ethereum wallet private key
        eth_mainnet_rpc_url (str): Ethereum RPC URL
        llm_api_key (str): API key for LLM service
        openrouter_api_key (str): API key for OpenRouter
        openai_api_key (str): API key for OpenAI
    """
    # Step 1: Retrieve recent posts
    recent_posts = retrieve_recent_posts(db)
    formatted_recent_posts = format_post_list(recent_posts)
    print(f"Recent posts: {formatted_recent_posts}")

    # Step 2: Fetch external context
    reply_fetch_list = []
    for e in recent_posts:
        reply_fetch_list.append((e["tweet_id"], e["content"]))
    notif_context = fetch_notification_context(account, reply_fetch_list)
    # print(f"fetched context tweet ids: {new_ids}\n")
    print("Notifications:\n")
    for notif in notif_context:
        print(f"- {notif}\n")
    external_context = notif_context

    if len(notif_context) > 0:
        # Step 2.5 check wallet addresses in posts
        balance_ether = get_wallet_balance(private_key_hex, eth_mainnet_rpc_url)
        print(f"Agent wallet balance is {balance_ether} ETH now.\n")
        
        if balance_ether > 0.3:
            tries = 0
            max_tries = 2
            while tries < max_tries:
                wallet_data = wallet_address_in_post(
                    notif_context, private_key_hex, eth_mainnet_rpc_url, llm_api_key
                )
                print(f"Wallet addresses and amounts chosen from Posts: {wallet_data}")
                try:
                    wallets = json.loads(wallet_data)
                    if len(wallets) > 0:
                        # Send ETH to the wallet addresses with specified amounts
                        for wallet in wallets:
                            address = wallet["address"]
                            amount = wallet["amount"]
                            transfer_eth(
                                private_key_hex, eth_mainnet_rpc_url, address, amount
                            )
                        break
                    else:
                        print("No wallet addresses or amounts to send ETH to.")
                        break
                except json.JSONDecodeError as e:
                    print(f"Error parsing wallet data: {e}")
                    tries += 1
                    continue
                except KeyError as e:
                    print(f"Missing key in wallet data: {e}")
                    break
        
        time.sleep(5)

        # Step 2.75 decide if follow some users
        tries = 0
        max_tries = 2
        while tries < max_tries:
            decision_data = decide_to_follow_users(notif_context, openrouter_api_key)
            print(f"Decisions from Posts: {decision_data}")
            try:
                decisions = json.loads(decision_data)
                if len(decisions) > 0:
                    # Follow the users with specified scores
                    for decision in decisions:
                        username = decision["username"]
                        score = decision["score"]
                        if score > 0.98:
                            follow_by_username(account, username)
                            print(
                                f"user {username} has a high rizz of {score}, now following."
                            )
                        else:
                            print(
                                f"Score {score} for user {username} is below or equal to 0.98. Not following."
                            )
                    break
                else:
                    print("No users to follow.")
                    break
            except json.JSONDecodeError as e:
                print(f"Error parsing decision data: {e}")
                tries += 1
                continue
            except KeyError as e:
                print(f"Missing key in decision data: {e}")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
    
    time.sleep(5)

    # Step 3: Generate short-term memory
    short_term_memory = generate_short_term_memory(
        recent_posts, external_context, llm_api_key
    )
    print(f"Short-term memory: {short_term_memory}")

    # Step 4: Create embedding for short-term memory
    short_term_embedding = create_embedding(short_term_memory, openai_api_key)

    # Step 5: Retrieve relevant long-term memories
    long_term_memories = retrieve_relevant_memories(db, short_term_embedding)
    print(f"Long-term memories: {long_term_memories}")

    # Step 6: Generate new post
    new_post_content = generate_post(short_term_memory, long_term_memories, formatted_recent_posts, external_context, llm_api_key)
    new_post_content = new_post_content.strip('"')
    print(f"New post content: {new_post_content}")

    # Step 7: Score the significance of the new post
    significance_score = score_significance(new_post_content, llm_api_key)
    print(f"Significance score: {significance_score}")

    # Step 8: Store the new post in long-term memory if significant enough
    if significance_score >= 7:
        new_post_embedding = create_embedding(new_post_content, openai_api_key)
        store_memory(db, new_post_content, new_post_embedding, significance_score)

    # Step 9: Save the new post to the database
    ai_user = db.query(User).filter(User.username == "errorerrorttyl").first()
    if not ai_user:
        ai_user = User(username="errorerrorttyl", email="errorerrorttyl@example.com")
        db.add(ai_user)
        db.commit()

    # THIS IS WHERE YOU WOULD INCLUDE THE POST_SENDER.PY FUNCTION TO SEND THE NEW POST TO TWITTER ETC
    if significance_score >= 5: # Only Bangers! lol
        res = send_post(account, new_post_content)
        rest_id = (res.get('data', {})
                    .get('create_tweet', {})
                    .get('tweet_results', {})
                    .get('result', {})
                    .get('rest_id'))

        if rest_id is not None:
            print(f"Posted with tweet_id: {rest_id}")
            new_db_post = Post(
                content=new_post_content,
                user_id=ai_user.id,
                username=ai_user.username,
                type="text",
                tweet_id=rest_id,
            )
            db.add(new_db_post)
            db.commit()

    print(
        f"New post generated with significance score {significance_score}: {new_post_content}"
    )