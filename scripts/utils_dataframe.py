import pandas
import numpy
from difflib import get_close_matches

'''
this function takes the main google sheet and combined all the separated sheets into one big dataframe.
It adds columns to delineate between restaurants, to try places, etc.
'''
def reformat_sheet(file_path):
    excel_file = pandas.ExcelFile(file_path)

    #creates empty dict to store keys as sheet names and values as the row/column data
    all_data = {}
    #color_counter
    color_counter = 0
    #loops through each sheet
    for sheet_name in excel_file.sheet_names:
        #ignores general info and to try list sheets
        if sheet_name not in ['General Notes']:
            sheet_data = excel_file.parse(sheet_name)
            #adds the sheet name, which signifies the place type (i.e. restaurant, bar, dessert) to pandas df
            sheet_data['place_type'] = sheet_name
            #assigns a numeric id to use for color later
            sheet_data['color_id'] = color_counter
            color_counter +=1
            #adds sheet to full data
            all_data[sheet_name] = sheet_data

    #creates one big dataframe
    combined_df = pandas.concat(all_data.values(), ignore_index=True)
    return combined_df

'''
this function identifies new additions to the gsheet xlsx file compared to the df_food_geocode.pkl
'''
def upsert_entries(df_gsheet, df_gsheet_old):
    #designates what defines a row as "new", in this case its name only
    key = ['Name']

    # finds rows that were entered previously, but have been updated (such as address or description change)
    df_gsheet_old_updated = df_gsheet_old.merge(df_gsheet[key], on=key, how='left', indicator=True)
    df_gsheet_old_updated = df_gsheet_old_updated[df_gsheet_old_updated['_merge'] == 'left_only'].drop(columns=['_merge'])

    # merges to detect new entries vs existing ones
    merged = df_gsheet.merge(
        df_gsheet_old,
        on=key,
        how='left',
        indicator=True,
        suffixes=('', '_old')
    )

    # split into old and new
    new_rows = merged[merged['_merge'] == 'left_only'][df_gsheet.columns]
    existing_rows = merged[merged['_merge'] == 'both'][df_gsheet.columns]

    # bring in old coords + location
    old_info = df_gsheet_old[key + ['latitude', 'longitude', 'Location']]
    existing_rows = existing_rows.merge(old_info, on=key, how='left', suffixes=('', '_old'))

    # detect location change
    location_changed_mask = existing_rows['Location'] != existing_rows['Location_old']

    # rows that NEED geocoding
    rows_to_geocode = pandas.concat([
        new_rows,
        existing_rows[location_changed_mask][df_gsheet.columns]
    ])

    # rows that can reuse coords
    existing_keep = existing_rows[~location_changed_mask].copy()
    # clean up helper columns
    existing_keep = existing_keep.drop(columns=['Location_old'])

    return df_gsheet_old_updated, existing_keep, rows_to_geocode


'''
this function returns each sheet as a html, to use to display in webpage
'''
def sheet_to_html(file_path):
    excel_file = pandas.ExcelFile(file_path)
    #loops through each sheet
    for sheet_name in excel_file.sheet_names:
        #ignores general info and to try list sheets
        if sheet_name not in ['General Notes']:
            sheet_data = excel_file.parse(sheet_name)
            #sheets display with NaN, this makes sure it displays as "None" as intended
            sheet_data = sheet_data.replace({numpy.nan: None})
            sheet_name = sheet_name.replace(' ', '_').lower()

            #saves html with no index
            html = sheet_data.to_html(index=False)
            # Inject custom CSS for header and body font sizes
            custom_style = """
            <style>
                table { width: 100%; border-collapse: collapse; }
                th { font-size: 2vw; }
                td { font-size: 1.5vw; }
            </style>
            """
            #appends styles to html
            html_with_style = custom_style + html
            # Writes to file
            with open(f'./sub_pages/spreadsheet_html/sheet_{sheet_name}.html', 'w', encoding='utf-8') as f:
                f.write(html_with_style)

'''
Sometimes I misspell a place's name, and in the current pipeline there is no way to handle that dynamically
without creating a duplicate. The below function checks for names which are nearly identical and allows
me to make changes update the df_master file so handle such cases.
'''
def update_name(df_path, check_column, cutoff):
    """
    Consolidated helper to find and fix similar names without duplicates.
    """
    df = pandas.read_pickle(df_path)

    # Step 1: build clusters of similar names
    clusters = []
    names = df[check_column].unique().tolist()

    for name in names:
        # Find matches above cutoff
        matches = set(get_close_matches(name, names, n=len(names), cutoff=cutoff))
        if len(matches) > 1:
            # Check if this cluster is already represented
            if not any(matches & cluster for cluster in clusters):
                clusters.append(matches)

    if not clusters:
        print("No similar names found, continuing...")
        return

    # Step 2: interactively handle each cluster
    print("\nSIMILAR NAMES DETECTED!\nSelect which name would you like to keep by entering the associated numeric ID\nType 'a' to keep all\nType 'q' to quit\n")
    for cluster in clusters:
        cluster = list(cluster)
        for i, n in enumerate(cluster):
            print(f"{i}: {n}")
        response = input()
        if response.lower() == 'q':
            break
        elif response.lower() == 'a':
            continue

        try:
            keep_idx = int(response)
            keep_name = cluster[keep_idx]
        except (ValueError, IndexError):
            print("Invalid input, skipping this cluster...")
            continue

        # Step 3: Remove rows for all other names in cluster
        for n in cluster:
            if n != keep_name:
                idx_to_remove = df.index[df[check_column] == n]
                df.drop(idx_to_remove, inplace=True)
                print(f"Removed '{n}' ({len(idx_to_remove)} row(s))\n")

    # Save updated df
    df.to_pickle(df_path)
    print(f"All updates saved to {df_path}!")

# Example usage:
# update_name("df_master.pkl")