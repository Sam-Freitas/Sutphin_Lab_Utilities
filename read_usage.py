import datetime
from pandas import read_csv

df = read_csv('system_metrics.csv')
print(datetime.datetime.now())
print('Max ram usage:    ', round(max(df['ram_used'])*(1e-9),2), '(GiB)')
print('Max ram percent:  ', max(df['ram_percent']), '%')
print('')
print('Current ram usage:    ', round((df['ram_used'].values[-1])*(1e-9),2), '(GiB)')
print('Current ram percent:  ', df['ram_percent'].values[-1], '%')
