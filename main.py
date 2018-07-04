import json
import discord
import sqlite3
import asyncio
import datetime
from pubg_python import PUBG, Shard
from prefly import InitMatchesPerUser

client = discord.Client()

@asyncio.coroutine
def background_tasks():
    yield from client.wait_until_ready()
    channel_all_messages = discord.Object(id=config['discord']['channel_all_messages'])
    channel_win_id = discord.Object(id=config['discord']['channel_win_id'])
    while not client.is_closed:
        conn = sqlite3.connect('pubg.db')
        # Get all users latest match and check if we already have it.
        players = api.players().filter(player_names=userList['users'])
        matchsDict = {}
        for player in players:
            # Only get latest match (for now)
            c = conn.cursor()
            print(str(datetime.datetime.now().time()) + ' | Checking user: ' + player.name)
            try:
                for player_match in player.matches:
                    c.execute("SELECT * FROM matches WHERE match_id = ? AND username = ?", (player_match.id, player.name))
                    # Can't use c.rowcount
                    # @see https://stackoverflow.com/questions/839069/cursor-rowcount-always-1-in-sqlite3-in-python3k
                    if (len(c.fetchall()) >= 1):
                        # We already have the match, nothing to do.
                        continue
                    else:
                        c.execute("insert into matches values (?, ?)",
                                 [player_match.id, player.name])
                        conn.commit()
                        matchsDict[player_match.id] = player_match.id
                        print(str(datetime.datetime.now().time()) + ' | > Adding match ' + player_match.id + ' for user ' + player.name)
            except AttributeError:
                continue

        for match_id in matchsDict:
            print(str(datetime.datetime.now().time()) + ' | Checking match ' + match_id)
            # Load the match
            match = api.matches().get(match_id)

            # Look for the roaster index, since we can't have this information
            # using only the API.
            roster_index = find_roaster_index(match)

            participant_list = []
            found_match = match.rosters[roster_index]
            # Build participant list.
            for participant in found_match.participants:
                participant_list.append(participant.name)

            # Get final rank of the players.
            rank = found_match.stats['rank'];
            if (len(participant_list) < 2):
                # Only one player.
                em = discord.Embed(
                    title=', '.join(participant_list) + ' a fini un match !',
                    description='', colour=0xDEADBF)
                description_string = 'Il a fini ' + str(rank) + 'ème !'
                if (rank == 1):
                    em.title = 'Winner Winner Chicken Dinner ! ' + ', '.join(participant_list) + ' a gagné !'
                    em.colour = 0x6ebf6e
                    em_win = discord.Embed(
                        title='Winner Winner Chicken Dinner ! ' + ', '.join(participant_list) + ' a gagné !',
                        description='GG !', colour=0x6ebf6e)
                    description_string = 'Il a fini ' + str(rank) + 'er !'
                    yield from client.send_message(channel_win_id, embed=em_win)

                em.add_field(name='kill', value=str(found_match.participants[0].kills))
                em.add_field(name='Longest kill', value=str(int(found_match.participants[0].longest_kill)) + 'm')
                em.add_field(name='Dégats fait', value=str(int(found_match.participants[0].damage_dealt)))

            else:
                # Multiple player.
                plist = " et ".join([", ".join(participant_list[:-1]), participant_list[-1]] if len(participant_list) > 2 else participant_list)
                em = discord.Embed(
                    title=plist + ' ont fini un match !',
                    description='', colour=0xDEADBF)
                description_string = 'Il ont fini ' + str(rank) + 'èmes !'
                if (rank == 1):
                    em.title = 'Winner Winner Chicken Dinner ! ' + plist + ' ont gagné !'
                    em.colour = 0x6ebf6e
                    em_win = discord.Embed(title='Winner Winner Chicken Dinner ! ' + plist + ' ont gagné !',
                                       description='GG !', colour=0x6ebf6e)
                    description_string = 'Il ont fini ' + str(rank) + ' ers !'
                    yield from client.send_message(channel_win_id, embed=em_win)


                for p in found_match.participants:
                    em.add_field(name='--------------', value='**' + p.name + '**', inline=False)
                    em.add_field(name='kill', value=str(p.kills))
                    em.add_field(name='Longest kill', value=str(int(p.longest_kill)) + 'm')
                    em.add_field(name='Dégats fait', value=str(int(p.damage_dealt)))

            em.description = description_string
            em.set_footer(text='match id : ' + match_id)
            yield from client.send_message(channel_all_messages, embed=em)
        conn.close()
        yield from asyncio.sleep(int(config['refresh']))


def find_roaster_index(match):
    found = False
    for idx, participants in enumerate(match.rosters):
        if found == True:
            break
        for team_player in participants.participants:
            if (team_player.name in userList['users']):
                found = True
                roster_index = idx
    return roster_index


@client.event
@asyncio.coroutine
def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    if message.content.startswith('!players'):
        plist = " et ".join(
            [", ".join(userList['users'][:-1]), userList['users'][-1]] if len(userList['users']) > 2 else userList['users'])
        msg = 'Tracked players : ' + plist.format(message)
        yield from client.send_message(message.channel, msg)


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
api = PUBG(config['api']['key'], Shard.PC_NA)
userList = json.load(open('users.json'))

# Pre-fly
InitMatchesPerUser(api, userList)

client.loop.create_task(background_tasks())
client.run(config['discord']['client_run'])