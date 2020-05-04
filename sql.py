import sqlite3
import requests
from bs4 import BeautifulSoup as bSoup
from datetime import datetime, timedelta, date
from concurrent import futures


def connect_db(function):
    ''' Decorator to handle the connection to the database '''
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('assets/database2.db')
        c = conn.cursor()
        result = function(c, *args, **kwargs)
        conn.commit()
        conn.close()
        return result
    return wrapper


def interval(start, end):
    ''' Generator which yields days from start to end '''
    curr = start
    while curr <= end:
        yield curr
        curr += timedelta(days=1)


def date_helper(start, end):
    ''' Transform date strings (YYYY-MM-DD) into datetime objects and sort start, end '''
    start = datetime.fromisoformat(start).date()
    end = datetime.fromisoformat(end).date()
    yesterday = datetime.today().date() - timedelta(days=1)
    # Check that start is before end
    if end < start:
        start, end = end, start
    # Check that end is not in the future otherwise set yesterday as end
    end = min(end, yesterday)
    return start, end


def get_data_day(day):
    ''' Fetch and organize data for selected day '''
    print(f'Retriving data for {day}...')
    url = f'https://www.amat-mi.it/index.php?id_sezione=35&data_bollettino={day}'
    # Get page at url and extract the data table
    soup = bSoup(requests.get(url, timeout=13).text, 'lxml')
    error = soup.find('p', {'style': 'background-color: red; color: white;'})
    table = soup.find(
        'table', {'class': 'table table-condensed table-responsive text-center'})
    # If the data are not valid fill the database with None values
    if error or not table:
        print(f'No data for {day}, fill missing values with None')
        return [[None] * 5] * 7
    # Extract values from webpage
    values = [val.text.strip() for val in table.find_all('td')]
    # Group values by station (8 by 8) and select only correct info
    stations_names = ('Viale Liguria', 'Viale Marche', 'Via Pascal', 'Via Senato', 'Verziere')
    values = [elem for elem in zip(*[iter(values)] * 8) if elem[0] in stations_names]
    # Zip them into lists by pollutant
    values = list(zip(*values))
    # Remove missing values and stations names
    values = [[val.strip("< ").replace(',', '.') if val not in ('-', '', 'N.D.')
               else None for val in day] for day in values][1:]
    return values


def get_data(days):
    ''' Fetch and organize data for multiple days '''
    data = []
    # Returns data for selected dates in format [[date, [val1, val1, ...], [val2, val2, ...], ...]]
    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Call max_workers concurrent instances of get_data_day()
        for future in executor.map(get_data_day, days):
            data.append(future)
    return data


def create_db(db_name):
    conn = sqlite3.connect(f'{db_name}')
    c = conn.cursor()
    poll_names = ('SO2', 'PM10', 'PM2', 'NO2', 'CO', 'O3', 'C6H6')
    for poll in poll_names:
        query = f' CREATE TABLE {poll} (timestamp text, Liguria real, Marche real, Pascal real, Senato real, Verziere real)'
        c.execute(query)
    query = f' CREATE TABLE meteo (timestamp text, AvgTemp integer, Humidity integer, Wind integer, Precipitation text)'
    c.execute(query)
    conn.commit()
    conn.close()


@connect_db
def insert(c, start, end):
    ''' Fetch and insert data into db if not existing already '''
    tables = ('SO2', 'PM10', 'PM2', 'NO2', 'CO', 'O3', 'C6H6')
    c.execute('SELECT * from SO2')
    # Select all the already exisiting dates from db
    existing_dates = [elem[0] for elem in c.fetchall()]
    # List of requested dates to add
    req_dates = [date.isoformat() for date in interval(start, end)]
    # List of dates to be requested not already in the db
    new_dates = [date for date in req_dates if date not in existing_dates]
    # Get the data for the new_dates
    data = get_data(new_dates)
    # Insert the new data in the db
    for i, date in enumerate(new_dates):
        for j, table in enumerate(tables):
            # Insert for each day (i), for each table (j) the value of the pollutants
            query = f'INSERT INTO {table} VALUES (?,?,?,?,?,?)'
            c.execute(query, (date, *data[i][j]))


@connect_db
def select_interval(c, poll_name, start, end):
    ''' Return the values of every station for selected pollutant '''
    # Convert start, end to datetime.date() if not already
    if isinstance(start, str) and isinstance(end, str):
        start, end = date_helper(start, end)
    insert(start, end)
    query = f'SELECT * FROM {poll_name} WHERE timestamp BETWEEN date(?) AND date(?) ORDER BY timestamp'
    c.execute(query, (start, end))
    # Unzip timestamps and poll_values and sort them
    #sorted_data = zip(*c.fetchall())
    #sorted_data = zip(*sorted(c.fetchall(), key=lambda x: datetime.fromisoformat(x[0]).date()))
    #print(list(sorted_data) == data)
    # print(data)
    stations = ('Dates', 'Liguria', 'Marche', 'Pascal', 'Senato', 'Verziere')
    data = dict(zip(stations, zip(*c.fetchall())))
    return {k: v for k, v in data.items() if any(v)}


def select_last_month(poll_name):
    end = datetime.today().date() - timedelta(days=1)
    start = end - timedelta(days=31)
    return select_interval(poll_name, start, end)


def main():
    start, end = ['22-4-2018', '28-4-2020']
    table = 'PM10'
    # start, end = date_helper(start, end)
    data = select_interval(table, start, end)
    #data = last_month()
    # print(data)


if __name__ == '__main__':
    #db_name = 'assets/database.db'
    # create_db('assets/database2.db')
    data = select_interval('PM10', '2019-04-18', '2020-04-28')
    print(data)
