import requests
import json
import sqlite3
import discord
import asyncio

client = discord.Client()

@asyncio.coroutine
def background_tasks():
    yield from client.wait_until_ready()
    channel_all_messages = discord.Object(id=conf_channel_all_message_id)
    channel_win_id = discord.Object(id=conf_channel_win_id)
    while not client.is_closed:
        matchDict = {}
        for user, user_id in userList.items():
            # ===========
            userDict = {}

            # Recuperation des listes des matches distant
            distant_match_ids, stats = getDistantMatches(user_id)

            # Recuperation de la liste des matchs locaux
            conn, local_match_ids = getLocalMatches(user)

            # On recupere le delta entre les 2
            delta = list(set(distant_match_ids) - set(local_match_ids))

            # on peut maintenant supprimer le local.
            c = conn.cursor()
            c.execute("DELETE FROM matches WHERE username = ?", (user,))
            conn.commit()

            # Et le re-peupler avec les nouveaux items.

            for stat in stats:
                c.execute("insert into matches values (?, ?, ?)", [stat['match_id'], stat['participant']['user']['nickname'], json.dumps(stat)])
                conn.commit()

            # Puis on re-recupere les stats correspondants aux delta.
            for delta_item in delta:
                c = conn.cursor()
                c.execute("SELECT data FROM matches WHERE username = ? AND id = ?", (user, delta_item, ))
                data = c.fetchone()[0]
                data_json = json.loads(data)
                # ***
                userDict[user] = data_json
                matchDict.setdefault(delta_item, []).append(userDict)

        for match_id, users in matchDict.items():
            if (len(users) > 1):
                em = discord.Embed(title='temporary',
                                       description='temporary', colour=0xDEADBF)
                username_list = []
                for user_data in users:
                    try:
                        username, data_json = user_data.popitem()
                        username_list.append(username)
                        # Get stats
                        damage_dealt, final_rank, kill, longest_kill_2, total_player = getBasicStats(data_json)
                        em.add_field(name='--------------', value='**'+username+'**', inline = False)
                        em.add_field(name = 'kill', value  = str(kill))
                        em.add_field(name = 'Longest kill', value = str(longest_kill_2) + 'm')
                        em.add_field(name = 'Dégats fait', value = str(damage_dealt))
                    except KeyError:
                        pass

                # We can get the last values of final_rank and total_player, they should be the same for everyone.
                description_string = 'Ils ont fini ' + str(final_rank) + 'èmes sur ' + str(total_player)
                if (final_rank == 1):
                    description_string = 'Ils ont fini ' + str(final_rank) + 'ers sur ' + str(total_player)

                em.title = ', '.join(username_list) + ' ont fini un match !'
                if (final_rank == 1):
                    em.title = 'Winner Winner Chicken Dinner ! ' + ', '.join(username_list) + ' ont fini un match !'
                    em.color = 0x6ebf6e
                    # Win message
                    em_win = discord.Embed(title='Winner Winner Chicken Dinner ! ' + ', '.join(username_list) + ' ont gagné !',
                                       description='GG !', colour=0x6ebf6e)
                    yield from client.send_message(channel_win_id, embed=em_win)


                em.description = description_string
                em.set_author(name='PUBG', icon_url=client.user.default_avatar_url)
                yield from client.send_message(channel_all_messages, embed=em)

            else:
                for user_data in users:
                    try:
                        username, data_json = user_data.popitem()
                        # Get stats
                        damage_dealt, final_rank, kill, longest_kill_2, total_player = getBasicStats(data_json)
                        description_string = 'Il a fini ' + str(final_rank) + ' sur ' + str(total_player)
                        if (final_rank == 1):
                            em = discord.Embed(
                                title='Winner Winner Chicken Dinner ! ' + str(username) + ' vient de finir un match !',
                                description=description_string,
                                colour=0x6ebf6e)
                            em_win = discord.Embed(
                                title='Winner Winner Chicken Dinner ! ' + str(username) + ' a gagné !',
                                description='GG !', colour=0x6ebf6e)
                            yield from client.send_message(channel_win_id, embed=em_win)
                        else:
                            em = discord.Embed(title=str(username) + ' vient de finir un match !',
                                               description=description_string, colour=0xDEADBF)

                        em.add_field(name='kill', value=str(kill))
                        em.add_field(name='Longest kill', value=str(longest_kill_2) + 'm')
                        em.add_field(name='Dégats fait', value=str(damage_dealt))

                        em.set_author(name='PUBG', icon_url=client.user.default_avatar_url)

                        yield from client.send_message(channel_all_messages, embed=em)
                    except KeyError:
                        pass

        yield from asyncio.sleep(int(refresh_time))


def getBasicStats(data_json):
    total_player = data_json['total_rank']
    final_rank = data_json['participant']['stats']['rank']
    kill = data_json['participant']['stats']['combat']['kda']['kills']
    longest_kill = data_json['participant']['stats']['combat']['kda']['longest_kill']
    longest_kill_2 = "{:.2f}".format(longest_kill)
    damage_dealt = data_json['participant']['stats']['combat']['damage']['damage_dealt']
    return damage_dealt, final_rank, kill, longest_kill_2, total_player


def getLocalMatches(user):
    conn = sqlite3.connect('pubg.db')
    c = conn.cursor()
    c.execute("SELECT id FROM matches WHERE username = ?", (user,))
    local_match_ids = []
    for row in c:
        local_match_ids.append(row[0])
    return conn, local_match_ids

def getDistantMatches(user_id):
    stats_api_res = requests.get(
        'https://pubg.op.gg/api/users/' + user_id + '/matches/recent?season=2018-04&server=eu&queue_size=&mode=')
    stats = stats_api_res.json()['matches']['items']
    distant_match_ids = []
    for stat in stats:
        distant_match_ids.append(stat['match_id'])
    return distant_match_ids, stats

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    conn = sqlite3.connect('pubg.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS matches")
    c.execute("CREATE TABLE IF NOT EXISTS matches (id varchar(125), username varchar(64), data json)")
    # Close db connection

    for user, user_id in userList.items():
        stats_api_res = requests.get('https://pubg.op.gg/api/users/' + user_id + '/matches/recent?season=2018-04&server=eu&queue_size=&mode=')
        stats = stats_api_res.json()['matches']['items']
        for stat in stats:
            c.execute("insert into matches values (?, ?, ?)", [stat['match_id'], stat['participant']['user']['nickname'], json.dumps(stat)])
            conn.commit()
        print('Adding data for user ' + user)

    conn.close()

userList = json.load(open('users.json'))
data = json.load(open('config.json'))

client_run = data['client_run']
conf_channel_all_message_id = data['channel_all_message_id']
conf_channel_win_id = data['channel_win_id']
refresh_time = data['refresh']
client.loop.create_task(background_tasks())
client.run(client_run)
