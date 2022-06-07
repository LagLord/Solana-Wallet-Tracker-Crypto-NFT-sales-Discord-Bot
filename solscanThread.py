import asyncio
import json
import time

import nextcord
import requests
from config import *
from multiprocessing.pool import ThreadPool as Pool
from nextcord import ButtonStyle
from nextcord.ui import Button, View

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.5005.61 Safari/537.36 '
}

accounts = ACCOUNTS
pool_size = 5
previous_hash = None
current_time = time.time() - time_to_track
messages = []

client = nextcord.Client()
channel = None


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    global channel
    channel = client.get_channel(CHANNEL_ID)
    client.loop.create_task(send_message())


# Get the latest Block
async def get_block():
    while True:
        url = "https://public-api.solscan.io/block/last?limit=1"
        resp = requests.get(url, headers=headers)
        resp = json.loads(resp.text)
        global previous_hash
        print(resp)
        try:
            previous_hash = resp[0]["result"]["blockTime"]
            time_delta = time.time() - previous_hash
            print(time.time(), previous_hash, time_delta)
            return time_delta
        except:
            print("getting block time 1")
            await asyncio.sleep(1)


def get_image(trx):
    url = f"https://api-mainnet.magiceden.dev/v2/tokens/{trx}"
    resp = requests.get(url, headers=headers)
    resp = json.loads(resp.text)
    image_url = resp['image']
    collection = resp['collection'].upper().replace("_", " ")
    return image_url, collection


def get_price(trx):
    url = f"https://api-mainnet.magiceden.dev/v2/tokens/{trx}/activities?offset=0&limit=1"
    resp = requests.get(url, headers=headers)
    resp = json.loads(resp.text)
    try:
        print(resp)
        if resp[0]['type'] != 'buyNow':
            return False
        price = resp[0]['price']
        price = str(price)
        token = " SOL"
        return price + token

    except:
        return False


async def send_message():
    await asyncio.sleep(5)
    await client.wait_until_ready()
    print("started")
    while True:
        global messages, channel
        await get_transactions()

        if len(messages) > 0:

            print(messages)
            for message in messages:
                print(messages)
                print("messaging start 1")
                b1 = Button(label="View Transaction", style=ButtonStyle.blurple, url=f"https://solscan.io/tx/{message[1]}")
                b2 = Button(label="View Token", style=ButtonStyle.blurple, url=f"https://solscan.io/token/{message[2]}")
                myView = View(timeout=10)
                myView.add_item(b1)
                myView.add_item(b2)
                await channel.send(embed=message[0], view=myView)
            messages = []


def scrape_and_message(data, name):
    print("scraping start 1")
    for trx in data:

        # if it isn't a transfer skip

        if trx["postBalance"] == trx["preBalance"]:
            continue

        # Checking whether it's a coin or NFT

        if "symbol" in trx:
            if trx["changeType"] == "inc":

                message = nextcord.Embed(title=f"**{name}**", description="BOUGHT",  color=0x00aa88)
                message.add_field(name=f"Token Name", value=trx['symbol'], inline=True)
                message.add_field(name=f"Wallet address", value=trx['owner'], inline=True)
                # message = f"{name} (wallet {trx['owner']}) has just purchased {trx['symbol']}."

            else:
                message = nextcord.Embed(title=f"**{name}**", description="SOLD", color=0x00F10909)
                message.add_field(name=f"Token Name", value=trx['symbol'], inline=True)
                message.add_field(name=f"Wallet address", value=trx['owner'], inline=True)
                # message = f"{name} (wallet {trx['owner']}) has just sold {trx['symbol']}."

        # When it's an NFT another API call to retrieve the NFT name

        else:
            url = f"https://public-api.solscan.io/token/meta?tokenAddress={trx['tokenAddress']}"

            resp = requests.get(url, headers=headers)
            resp = json.loads(resp.text)
            nft_name = resp["name"]
            nft_symbol = resp["symbol"]
            image_url, collection = get_image(trx['tokenAddress'])
            price = get_price(trx['tokenAddress'])
            if not price:
                print("The transaction involved transfer of assets between wallets of the same User.")
                continue

            if trx["changeType"] == "inc":
                # message = f"{name} (wallet {trx['owner']}) has just purchased {nft_name}({nft_symbol})."
                message = nextcord.Embed(title=f"**{name}**", color=0x00aa88)
                message.add_field(name=f"Bought Price:", value=price, inline=False)
                message.add_field(name=f"Project Name", value=collection, inline=True)
                message.add_field(name=f"Wallet address", value=trx['owner'], inline=True)
                message.set_image(url=image_url)
            else:
                message = nextcord.Embed(title=f"**{name}**", color=0x00F10909)
                message.add_field(name=f"Sold Price:", value=price, inline=False)
                message.add_field(name=f"Project Name", value=collection, inline=True)
                message.add_field(name=f"Wallet address", value=trx['owner'], inline=True)
                message.set_image(url=image_url)
                # message = f"{name} (wallet {trx['owner']}) has just sold {nft_name}({nft_symbol})."
        global messages, channel
        messages.append([message, trx['signature'][0], trx['tokenAddress']])
        print("end")


async def get_transactions():
    global current_time

    # while True:

    if current_time < (time.time() - time_to_track):
        print(time.time())
        pool = Pool(pool_size)
        time_gap = await get_block()
        previous_time = int((time.time() - time_to_track - time_gap) // 1)
        current_time = int((time.time()) // 1)
        now_time = int((time.time() - time_gap) // 1)
        for account in accounts:
            pool.apply_async(get_data, (account, previous_time, now_time))
        pool.close()
        pool.join()
        print(time.time())


def get_data(account, previous_time, current_time):
    # url = f'https://public-api.solscan.io/account/transactions?account={accounts[account]}'
    url = f"https://public-api.solscan.io/account/splTransfers?account={accounts[account]}&fromTime={previous_time}&toTime={current_time}&offset=0&limit=50"
    resp = requests.get(url, headers=headers)
    try:
        resp = json.loads(resp.text)
        print(resp)
        transactions = resp["data"]
        if len(transactions) == 0:
            print("No transactions at this moment from : ", account)

            return
        print(account, transactions)

        scrape_and_message(transactions, account)
    except:
        print(resp)


# client.loop.create_task(send_message())

client.run(BOT_TOKEN)
