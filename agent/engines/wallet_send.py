import os
import re
import requests
from web3 import Web3
from ens import ENS
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from engines.prompts import get_wallet_decision_prompt

def get_wallet_balance(private_key_hex, solana_rpc_url="https://api.mainnet-beta.solana.com"):
    client = Client(solana_rpc_url)
    wallet = Keypair.from_base58_string(private_key_hex)
    public_key = wallet.pubkey()
    # Retrieve and print the balance of the account in SOL
    balance_lamports = client.get_balance(public_key).value
    balance_sol = balance_lamports / 1_000_000_000  # 1 SOL = 1,000,000,000 Lamports

    return balance_sol


def transfer_sol(private_key, solana_rpc_url, to_address, amount_in_sol):
    """
    Transfers SOL from one account to another.

    Parameters:
    - private_key (str): The private key of the sender's Solana account in base58 format.
    - to_address (str): The Solana address of the recipient.
    - amount_in_sol (float): The amount of SOL to send.

    Returns:
    - str: The transaction signature if the transaction was successful.
    - str: "Transaction failed" or an error message if the transaction was not successful or an error occurred.
    """
    try:
        client = Client(solana_rpc_url)

        # Get the public key from the private key
        public_key = Pubkey.from_string(private_key)

        # Convert the amount in SOL to Lamports
        amount_in_lamports = int(amount_in_sol * 1_000_000_000)  # 1 SOL = 1,000,000,000 Lamports

        # Build the transaction
        transaction = {
            'to': Pubkey.from_string(to_address),
            'amount': amount_in_lamports,
            'from': public_key,
        }

        # Send the transaction
        tx_signature = client.send_transaction(transaction, public_key)

        return tx_signature
    except Exception as e:
        return f"An error occurred: {e}"
    
def wallet_address_in_post(posts, private_key, solana_rpc_url: str, llm_api_key: str):
    """
    Detects wallet addresses from a list of posts.
    Converts all items to strings first, then checks for matches.

    Parameters:
    - posts (List): List of posts of any type

    Returns:
    - List[Dict]: List of dicts with 'address' and 'amount' keys
    """

    # Convert everything to strings first
    str_posts = [str(post) for post in posts]
    
    # Then look for matches in all the strings
    sol_pattern = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
    matches = []
    
    for post in str_posts:
        found_matches = sol_pattern.findall(post)
        matches.extend(found_matches)
    
    wallet_balance = get_wallet_balance(private_key, solana_rpc_url)
    prompt = get_wallet_decision_prompt(posts, matches, wallet_balance)
    
    response = requests.post(
        url="https://api.hyperbolic.xyz/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_api_key}",
        },
        json={
            "messages": [
                {
                    "role": "system",
        	        "content": prompt
                },
                {
                    "role": "user",
                    "content": "Respond only with the wallet address(es) and amount(s) you would like to send to."
                }
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "presence_penalty": 0,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
        }
    )
    
    if response.status_code == 200:
        print(f"SOL Addresses and amounts chosen from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")
