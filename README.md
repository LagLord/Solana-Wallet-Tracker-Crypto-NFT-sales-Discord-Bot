# Solana-Wallet-Tracker-Crypto-NFT-sales-Discord-Bot
Python script for tracking Solscan wallet transactions of certain addresses for NFT sales getting info from Magic Eden and sending messages in real time to your channel.

**********************    Requirements     *********************

You need to add a config file which contains all the creds.

The config file will look like this:

BOT_TOKEN = "Your Bot token"

CHANNEL_ID = Your channel ID where you want to receive a nice embedded message

time_to_track = 600  # Time in seconds you want the loop to run 600 = 5 minutes transactions

ACCOUNTS = {"Wallet name": "Wallet Address"}
