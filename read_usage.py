# import pandas as pd
import sys,os,glob
from pandas import read_csv

df = read_csv('system_metrics.csv')
print('Max ram usage: ', max(df['ram_percent']))
