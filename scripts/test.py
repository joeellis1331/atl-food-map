import pickle
import pandas
import utils_dataframe
from difflib import get_close_matches

#test = pandas.read_pickle('geocode_cache.pkl')
#print(test)

# test = pandas.read_pickle('df_master.pkl')
# test.to_csv("test.csv")

utils_dataframe.update_name('df_master.pkl', 'Name', 0.8)