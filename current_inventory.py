import pandas as pd
import requests
from database import conn


#Retrieves WINEPOS current inventory JSON
def retrieve_current_inventory():
    url = "http://192.168.1.223:8081/Inventory.jsp?format=json&db=ICS"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data['rows'])
    df['item_num'] = df['item_num'].astype(str)
    df = df[['sdesc', 'item_num', 'descr', 'qoh']]
    df.columns = ['dept', 'item_num', 'item', 'qoh']

    return df
