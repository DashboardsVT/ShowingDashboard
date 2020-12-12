from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd
import dash
import dash_table
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1L3A18y5mgTj86FeRO8npq1xHgOdJ88BUehM3hi90hYA'
RANGE_NAME = '2020!A:H'

DASHBOARD_NAME = 'ShowingDashboard'
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
def get_google_sheet(spreadsheet_id, range_name):
    """ Retrieve sheet data using OAuth credentials and Google Python API. """
    scopes = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    # Setup the Sheets API
    store = file.Storage('credentials/credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials/client_secret.json', scopes)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    gsheet = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return gsheet


def gsheet2df(gsheet):
    """ Converts Google sheet data to a Pandas DataFrame.
    Note: This script assumes that your data contains a header file on the first row!

    Also note that the Google API returns 'none' from empty cells - in order for the code
    below to work, you'll need to make sure your sheet doesn't contain empty cells,
    or update the code to account for such instances.

    """
    header = gsheet.get('values', [])[0]   # Assumes first line is header!
    values = gsheet.get('values', [])[1:]  # Everything else is data.
    if not values:
        print('No data found.')
    else:
        all_data = []
        for col_id, col_name in enumerate(header):
            column_data = []
            for row in values:
                column_data.append(row[col_id])
            ds = pd.Series(data=column_data, name=col_name)
            all_data.append(ds)
        df = pd.concat(all_data, axis=1)
        return df


gsheet = get_google_sheet(SPREADSHEET_ID, RANGE_NAME)
df = gsheet2df(gsheet)
df['class_type']='?'
df['description']='?'
df[['created_date','created_time']]=df.Created.str.split(", ",expand=True)
# df_working_hours = df[df['created_time'] <= "5:00 PM" and df['created_time']>= "10:00 PM"]
df['Created_datetime'] = pd.to_datetime(df['Created'])
df['created_date'] = pd.to_datetime(df['created_date'])
df['created_time'] = pd.to_datetime(df['created_time'])
df = df.set_index(df['Created_datetime'])
# df_working_hours = df
df_weekdays = df[df.index.dayofweek < 5]
df_weekends = df[df.index.dayofweek >= 5]
df_working_hours = df_weekdays.between_time(start_time='22:00',end_time='17:00', include_start= True, include_end=True)
df_off_hours_weekday = df_weekdays.between_time(start_time='17:00',end_time='22:00', include_start= True, include_end=True)
df_working_hours['description'] = 'Working Hours'
df_off_hours_weekday['description'] = 'Weekday After Hours'
df_weekends['description'] = 'Weekend Hours'
df_off_hours = df_weekends.append(df_off_hours_weekday)
df_off_hours['class_type'] = 'Off Hours'
df_working_hours['class_type'] = 'Working Hours'
df_all = df_working_hours.append(df_off_hours)
# fig = px.scatter(df,x='Created',y=)
app = dash.Dash(__name__)
# df_all.groupby()
test = df_all.groupby(['class_type','description']).size().reset_index(name='counts')
# test = pd.DataFrame({'Classification': ['Working Hours','Off hours', 'weekends'],
#                      'showings_requested':[df_working_hours['Created'].count(),
#                               df_off_hours_weekday['Created'].count(),
#                               df_weekends['Created'].count()]})
print(f'''df_working_hours.count(): {df_working_hours['Created'].count()}''')
print( f'''df_off_hours.count(): {df_off_hours['Created'].count()}''')
fig1 = px.bar(test, x='class_type', y='counts', color='description', labels=dict(class_type='Time When Showings Were Requested',counts='# of Showings Requested'), title='Keeley Painter 2020 Showings YTD (12/12/2020)')

# df_all = df_all.sort_values('Created')
fig2 = px.scatter(df_all, x='Created_datetime', y='created_date', color='description')
# fig2.update_xaxes(type='date')
# fig2 = px.scatter(df_working_hours, x='Created', y='created_date')
# fig3 = px.scatter(df_off_hours_weekday, x='Created', y='created_date')
# fig4 = px.scatter(df_weekends, x='Created', y='created_date')
app.layout = html.Div([
        dbc.Form([
            dcc.Graph(id=f'{DASHBOARD_NAME}_plot1', figure=fig1)
            ],
        ),
        dbc.Form([
            dcc.Graph(id=f'{DASHBOARD_NAME}_plot2', figure=fig2)
            ],
        ),
        # dbc.Form([
        #         dcc.Graph(id=f'{DASHBOARD_NAME}_plot3', figure=fig3)
        #     ],
        # ),
        # dbc.Form([
        #         dcc.Graph(id=f'{DASHBOARD_NAME}_plot4', figure=fig4)
        #     ],
        # ),
        dbc.Form([
            html.Label('TEST'),
            dash_table.DataTable(
                id='test',
                columns=[{"name": i, "id": i} for i in test.columns],
                data=test.to_dict('records'),
            )
        ]),
        dbc.Form([
            dash_table.DataTable(
                id='table_off_hours',
                columns=[{"name": i, "id": i} for i in df_off_hours.columns],
                data=df_off_hours.to_dict('records'),
            )
        ]),
        dbc.Form([
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
            )
        ])
     ],
)

if __name__ == '__main__':
    app.run_server(debug=True)
# def main():
#     gsheet = get_google_sheet(SPREADSHEET_ID, RANGE_NAME)
#     df = gsheet2df(gsheet)
#     print('Dataframe size = ', df.shape)
#     print(df.head())
#
#     """Shows basic usage of the Sheets API.
#     Prints values from a sample spreadsheet.
#     """
    # creds = None
    # # The file token.pickle stores the user's access and refresh tokens, and is
    # # created automatically when the authorization flow completes for the first
    # # time.
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'credentials/client_secret.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open('token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)
    #
    # service = build('sheets', 'v4', credentials=creds)
    #
    # # Call the Sheets API
    # sheet = service.spreadsheets()
    # result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
    #                             range=SAMPLE_RANGE_NAME).execute()
    # values = result.get('values', [])

    # if not values:
    #     print('No data found.')
    # else:
    #     print('Name, Major:')
    #     for row in values:
    #         # Print columns A and E, which correspond to indices 0 and 4.
    #         print('%s, %s' % (row[0], row[4]))

if __name__ == '__main__':
    main()
