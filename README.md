# SOLANA
Forked from TEE on Ethereum, but now available on Solana. You can verify the code here to confirm its AI.

# Solina
Solina is designed to integrate AI capabilities with a focus on the crypto world. It aims to understand and interact within this space by monitoring social media and managing wallet actions intelligently.

### TODO:
Wallet Actions: The agent needs to decide when to use the wallet for asset transfers (how much and to which address). Functions have been added in wallet_send.py for this; TODO: implement decision-making for when/if to send transactions from the address.

Replies and Subtweets: Instead of just news, the external data will include replies to the agent’s previous tweets and recent mentions. This may require adjustments to the agent's prompt to enhance its awareness of how to respond.

### Basics:
The DB folder contains scripts to create and seed the database with sample data. Docker should automatically run all of this for you.

The engines directory includes all functions that generate content for the agent's pipeline.

The pipeline.py file is the main file that outlines the end-to-end process for the agent. You can see the flow here.

run_pipeline.py is the main file that executes the pipeline, simulating random posting or scrolling through a feed throughout the day. This file runs continuously in the background within the container.
### Running the agent:

docker-compose up -d

This will start the agent in the background and run continuously.

You can also run the agent manually by running:

python run_pipeline.py

This will run the pipeline LOCALLY and not in the container.

enjoy
