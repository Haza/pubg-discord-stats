import json
import discord
import asyncio
from pubg_python import PUBG, Shard

from prefly import InitMatchesPerUser

client = discord.Client()

@asyncio.coroutine
def background_tasks():
    yield from client.wait_until_ready()
    channel_all_messages = discord.Object(id=config['discord']['channel_all_messages'])
    counter = 0
    while not client.is_closed:
        counter = counter + 1
        yield from client.send_message(channel_all_messages, counter)
        yield from asyncio.sleep(int(config['refresh']))

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# *****************
# Init
# *****************
config = json.load(open('config.json'))
api = PUBG(config['api']['key'], Shard.PC_EU)
userList = json.load(open('users.json'))

InitMatchesPerUser(api, userList)


#client.loop.create_task(background_tasks())
#client.run(config['discord']['client_run'])