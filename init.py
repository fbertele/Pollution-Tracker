import sqlite3


def create_db(db_name):
    ''' Create the database '''
    conn = sqlite3.connect(f'{db_name}')
    c = conn.cursor()
    poll_names = ('SO2', 'PM10', 'PM2', 'NO2', 'CO', 'O3', 'C6H6')
    for poll in poll_names:
        query = f' CREATE TABLE {poll} (timestamp text, Liguria real, Marche real, Pascal real, Senato real, Verziere real)'
        c.execute(query)
    query = f' CREATE TABLE meteo (timestamp text, AvgTemp real, Humidity integer, Wind integer, Precipitation text)'
    c.execute(query)
    conn.commit()
    conn.close()
