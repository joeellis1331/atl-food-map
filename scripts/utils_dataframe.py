import pandas

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
this function returns each sheet as a html, to use to display in webpage
'''
def sheet_to_html(file_path):
    excel_file = pandas.ExcelFile(file_path)
    #loops through each sheet
    for sheet_name in excel_file.sheet_names:
        #ignores general info and to try list sheets
        if sheet_name not in ['General Notes']:
            sheet_data = excel_file.parse(sheet_name)
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


