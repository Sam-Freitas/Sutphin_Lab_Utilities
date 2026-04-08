# import pandas as pd
import sys,os,glob
from pandas import read_csv

df = read_csv('system_metrics.csv')
print('Max ram usage:    ', round(max(df['ram_used'])*(1e-9),2), '(GiB)')
print('Max ram percent:  ', max(df['ram_percent']), '%')
