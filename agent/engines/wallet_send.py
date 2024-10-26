
import os
import re
import requests
from web3 import Web3

# Read environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

eth_mainnet_rpc_url = os.getenv("ETH_MAINNET_RPC_URL")

def transfer_eth(private_key, to_address, amount_in_ether):
    """
    Transfers Ethereum from one account to another.

    Parameters:
    - private_key (str): The private key of the sender's Ethereum account in hex format.
    - to_address (str): The Ethereum address of the recipient in hex format.
    - amount_in_ether (float): The amount of Ether to send.

    Returns:
    - str: The transaction hash as a hex string if the transaction was successful.
    - str: "Transaction failed" or "Error" if the transaction was not successful or some error occured.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(eth_mainnet_rpc_url))

        # Check if connected to blockchain
        if not w3.is_connected():
            print("Failed to connect to Sepolia Testnet")
            return

        # Convert the amount in Ether to Wei
        amount_in_wei = w3.toWei(amount_in_ether, 'ether')

        # Get the public address from the private key
        public_address = w3.eth.account.from_key(private_key).address

        # Get the nonce for the transaction
        nonce = w3.eth.get_transaction_count(public_address)

        # Build the transaction
        transaction = {
            'to': to_address,
            'value': amount_in_wei,
            'gas': 21000,
            'gasPrice': int(w3.eth.gas_price * 1.1),
            'nonce': nonce,
            'chainId': 11155111  # Replace with the correct chainId for your network
        }

        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Check the status of the transaction
        if tx_receipt['status'] == 1:
            return tx_hash.hex()
        else:
            return "Transaction failed"
    except Exception as e:
        return f"An error occurred: {e}"
    
def wallet_address_in_post(posts, openrouter_api_key: str):
    """
    Detects wallet addresses or ENS domains from a list of posts.
    Converts all items to strings first, then checks for matches.

    Parameters:
    - posts (List): List of posts of any type

    Returns:
    - List[str]: List of found wallet addresses and ENS domains
    """

    # Convert everything to strings first
    str_posts = [str(post) for post in posts]
    
    # Then look for matches in all the strings
    eth_pattern = re.compile(r'\b0x[a-zA-Z0-9]*\b|\b\S+\.eth\b')
    matches = []
    
    for post in str_posts:
        found_matches = eth_pattern.findall(post)
        matches.extend(found_matches)
    prompt = f"""
    Analyze the following recent posts and external context:

    Recent posts:
    {posts}

    Wallet addresses and ENS domains:
    {matches}

    Based on this information, decide if you want to send ETH to any of the addresses or ENS domains.
    Remember that this is real ETH so choose wisely.
    If you choose to send ETH to one or more addresses or domains, 
    you must return ONLY a json object with a list with the addresses/domains in it.
    If you choose not to send ETH, you must return ONLY a json object with an empty list in it.
    Only return the correctly formatted json object in both cases. Do not give any other information.

    Example Response if you choose to send ETH:
    [
        "0x1234567890123456789012345678901234567890",
        "0x9876543210987654321098765432109876543210"
    ]

    Example Response if you choose not to send ETH:
    []
    """
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_api_key}",
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
        print(f"ETH Addresses chosen from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")