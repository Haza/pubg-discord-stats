import sqlite3
from pubg_python import PUBG, Shard


def InitMatchesPerUser(api: PUBG, userList: dict):
    conn = sqlite3.connect('pubg.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS matches")
    c.execute("CREATE TABLE IF NOT EXISTS matches (match_id varchar(125), username varchar(64))")
    players = api.players().filter(player_names=userList['users'])
    for player in players:
        if hasattr(player, matches):
            for match in player.matches:
                c.execute("insert into matches values (?, ?)",
                          [match.id, player.name])
                conn.commit()
                print('Adding data for user ' + player.name + ', match ' + match.id)
    # Close db connection
    conn.close()
