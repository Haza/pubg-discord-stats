import json
import discord
import sqlite3
import asyncio
from pubg_python import PUBG, Shard

from prefly import InitMatchesPerUser

client = discord.Client()

@asyncio.coroutine
def background_tasks():
    yield from client.wait_until_ready()
    channel_all_messages = discord.Object(id=config['discord']['channel_all_messages'])
    while not client.is_closed:
        # Get all users latest match and check if we already have it.
        players = api.players().filter(player_names=userList['users'])
        for player in players:
            # Only get lastest match (for now)
            conn = sqlite3.connect('pubg.db')
            c = conn.cursor()
            c.execute("SELECT * FROM matches WHERE match_id = ? AND username = ?", (player.matches[0].id, player.name))
            # Can use c.rowcount (https://stackoverflow.com/questions/839069/cursor-rowcount-always-1-in-sqlite3-in-python3k)
            if (len(c.fetchall()) >= 1):
                # We already have the match, nothing to do.
                continue
            else:
                # New match found !
                em = discord.Embed(title='New match for ' + str(player.name) + ' found : ' + str(player.matches[0].id),
                              description='', colour=0x6ebf6e)
                # Todo :
                # * Update database
                # * Aggregate other user matches.
                # * Query matches API after aggregation to avoir duplicates (and save queries)
                yield from client.send_message(channel_all_messages, embed=em)

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

#InitMatchesPerUser(api, userList)


client.loop.create_task(background_tasks())
client.run(config['discord']['client_run'])