
import os
import re
import requests
from web3 import Web3
from ens import ENS

def get_wallet_balance(eth_mainnet_rpc_url, private_key):
    w3 = Web3(Web3.HTTPProvider(eth_mainnet_rpc_url))
    public_address = w3.eth.account.from_key(private_key).address

    # Retrieve and print the balance of the account in Ether
    balance_wei = w3.eth.get_balance(public_address)
    balance_ether = w3.fromWei(balance_wei, 'ether')

    print(f"Agent wallet balance is {balance_ether} ETH now.\n")
    return balance_ether


def transfer_eth(private_key, eth_mainnet_rpc_url, to_address, amount_in_ether):
    """
    Transfers Ethereum from one account to another.

    Parameters:
    - private_key (str): The private key of the sender's Ethereum account in hex format.
    - to_address (str): The Ethereum address or ENS name of the recipient.
    - amount_in_ether (float): The amount of Ether to send.

    Returns:
    - str: The transaction hash as a hex string if the transaction was successful.
    - str: "Transaction failed" or an error message if the transaction was not successful or an error occurred.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(eth_mainnet_rpc_url))

        # Check if connected to blockchain
        if not w3.is_connected():
            print("Failed to connect to ETH Mainnet")
            return "Connection failed"

        # Set up ENS
        w3.ens = ENS.fromWeb3(w3)

        # Resolve ENS name to Ethereum address if necessary
        if Web3.is_address(to_address):
            # The to_address is a valid Ethereum address
            resolved_address = Web3.to_checksum_address(to_address)
        else:
            # Try to resolve as ENS name
            resolved_address = w3.ens.address(to_address)
            if resolved_address is None:
                return f"Could not resolve ENS name: {to_address}"

        print(f"Transferring to {resolved_address}")

        # Convert the amount in Ether to Wei
        amount_in_wei = w3.toWei(amount_in_ether, 'ether')

        # Get the public address from the private key
        account = w3.eth.account.from_key(private_key)
        public_address = account.address

        # Get the nonce for the transaction
        nonce = w3.eth.get_transaction_count(public_address)

        # Build the transaction
        transaction = {
            'to': resolved_address,
            'value': amount_in_wei,
            'gas': 21000,
            'gasPrice': int(w3.eth.gas_price * 1.1),
            'nonce': nonce,
            'chainId': 1  # Mainnet chain ID
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

def wallet_address_in_post(posts, private_key, eth_mainnet_rpc_url: str, openrouter_api_key: str):
    """
    Detects wallet addresses or ENS domains from a list of posts.
    Converts all items to strings first, then checks for matches.

    Parameters:
    - posts (List): List of posts of any type

    Returns:
    - List[Dict]: List of dicts with 'address' and 'amount' keys
    """

    # Convert everything to strings first
    str_posts = [str(post) for post in posts]
    
    # Then look for matches in all the strings
    eth_pattern = re.compile(r'\b0x[a-fA-F0-9]{40}\b|\b\S+\.eth\b')
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

    Current balance of ETH in your wallet: 
    {get_wallet_balance(private_key, eth_mainnet_rpc_url)} ETH

    Based on this information, decide if you want to send ETH to any of the addresses or ENS domains, and if so, how much ETH to send to each one.
    Remember that this is real ETH from your own resources, so choose wisely.
    You should carefully evaluate the financial decision for your own future and survival.
    The total amount of transfers should never exceed your wallet balance.
    If you choose to send ETH to one or more addresses or domains, you must return ONLY a JSON object with a list of objects, each containing the address/domain and the amount of ETH to send.

    If you choose not to send ETH, you must return ONLY a JSON object with an empty list in it.
    Only return the correctly formatted JSON object in both cases. Do not give any other information.

    Example Response if you choose to send ETH:
    [
        {{"address": "0x1234567890123456789012345678901234567890", "amount": 0.5}},
        {{"address": "0x9876543210987654321098765432109876543210", "amount": 1.0}}
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
        print(f"ETH Addresses and amounts chosen from Posts: {response.json()}")
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error generating short-term memory: {response.text}")
