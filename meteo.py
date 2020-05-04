from pollution import *
from dateutil.relativedelta import relativedelta
import locale


def month_helper(date):
    ''' Yields YYYY/MM from Jan 2002 until today '''
    locale.setlocale(locale.LC_ALL, 'it_IT')
    while date <= datetime.today().date():
        yield date.strftime('%Y/%B')
        date += relativedelta(months=1)


def get_met_data_month(time):
    print(f'Getting data for {time}')
    url = f'https://www.ilmeteo.it/portale/archivio-meteo/Milano/{time}?format=csv'
    page = requests.get(url).text
    values = page.split('\r\n')[1:-1]
    cols = [1, 2, 6, 8, 14]
    data = [row.split(';')[col].replace('"', '').strip() for row in values for col in cols]
    data = list(zip(*[iter(data)] * 5))
    return data


@connect_db
def insert_met_data(c):
    ''' Fetch and organize data for multiple days '''
    # Select last date in db
    c.execute(f'SELECT timestamp FROM meteo ORDER BY timestamp DESC LIMIT 1')
    last_date = datetime.fromisoformat(c.fetchone()[0]).date()
    data = []
    # Returns data for selected dates in format [[date, [val1, val1, ...], [val2, val2, ...], ...]]
    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Call max_workers concurrent instances of get_data_day()
        for future in executor.map(get_met_data_month, month_helper(last_date)):
            for day in future:
                print(future)
                day = [value if value else None for value in day]
                timestamps = datetime.strptime(day[0], '%d/%m/%Y').date().isoformat()
                data.append([timestamps, *day[1:]])
        query = f'INSERT INTO meteo VALUES (?,?,?,?,?)'
        c.executemany(query, data)
        #print(f'Inserted data {data}')


@connect_db
def select_met_data(c, start, end):
    val_names = ('Date', 'AvgTemp', 'Humidity', 'Wind', 'Precipitation')
    query = 'SELECT * FROM meteo WHERE timestamp BETWEEN date(?) and date(?) ORDER by timestamp'
    c.execute(query, (start, end))
    return dict(zip(val_names, (zip(*c.fetchall()))))


if __name__ == '__main__':
    data = insert_met_data()
    select_met_data('2020-02-02', '2020-03-02')
