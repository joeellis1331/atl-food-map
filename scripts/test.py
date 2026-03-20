import pandas
import utils_dataframe

old_df = pandas.read_pickle('df_food_geocode.pkl')
old_df_drop = old_df.drop(['coordinates', 'latitude', 'longitude'], axis=1)
new_df = utils_dataframe.reformat_sheet('ATL-Food-and-Drink-Review-List.xlsx')

def clean(df):
    return df.map(lambda x: x.strip().lower() if isinstance(x, str) else x)
old_df_drop = clean(old_df_drop)
new_df = clean(new_df)

key_cols = list(new_df.columns)
#finds new columns (left)
merge_df = new_df.merge(
    old_df_drop,
    on=key_cols,
    how="left",
    indicator=True
)

new_entries = merge_df[merge_df['_merge'] == "left_only"].drop('_merge', axis = 1)



