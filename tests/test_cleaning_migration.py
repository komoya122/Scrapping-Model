import pandas as pd
import json
from bs4 import BeautifulSoup
from curl_cffi import requests
from io import StringIO

url = "https://immi.homeaffairs.gov.au/what-we-do/migration-program-planning-levels"
session = requests.Session(impersonate="chrome")
response = session.get(url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')
hidden_input = soup.find('input', id='ctl00_PlaceHolderMain_PageSchemaHiddenField_Input')
val = hidden_input['value']
data = json.loads(val)
full_html = ""
for item in data.get('content', []):
    full_html += item.get('block', '')
tables = pd.read_html(StringIO(full_html))
df = tables[0]

print("Original columns:")
print(df.columns)
print("\nOriginal head:")
print(df.head())

# Clean up
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(0)

print("\nAfter drop level 0:")
print(df.columns)
print("\nHead after drop:")
print(df.head())

# Forward fill the first column (Visa Stream) if it contains NaN
if 'Visa Stream' in df.columns:
    df['Visa Stream'] = df['Visa Stream'].ffill()

print("\nHead after ffill:")
print(df.head())

# Look at state allocations too
url2 = "https://immi.homeaffairs.gov.au/what-we-do/state-and-territory-nomination-allocations"
response2 = session.get(url2, timeout=30)
tables2 = pd.read_html(StringIO(response2.text))
df2 = tables2[0]
print("\nState columns:")
print(df2.columns)
print(df2.head())
