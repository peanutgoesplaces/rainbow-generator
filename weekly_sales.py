import pandas as pd
import requests
from datetime import date, timedelta, datetime
from tkinter import messagebox

#Generates DataFrame of Previous Weeks Sales
def generate_weekly_sales_df():
    global start_date
    global end_date

    today=date.today()

    start_date = date.today() - timedelta(days=7)
    end_date = date.today() - timedelta(days=4)

    #Use these for manual entry
    # start_date = date(2026,8,17)
    # end_date = date(2026,8,23)


    #WINE POS JSON WebReports for Previous Week
    #Only Works On Order Day Thursday
    if today.weekday() == 4:
        url = (f"http://192.168.1.223:8081/ItemsSold.jsp?"
               f"format=json&db=ICS&"
               f"start_date={start_date}&"
               f"end_date={end_date}")
        try:
            response = requests.get(url)
            data = response.json()
            df = pd.DataFrame(data['rows'])
            #print(df[df['descr'].str.contains('MARL')])
            return df


        except requests.exceptions.Timeout:
            messagebox.showinfo("Connection Timed Out")

        except requests.exceptions.ConnectionError:
            messagebox.showinfo("Could N Connect to POS Server")

        except requests.exceptions.HTTPError as e:
            messagebox.showinfo(f"HTTP Error {e}")

            return None
    else:
        messagebox.showinfo(f"{datetime.now().strftime('%A')}", "Weekly Sales Not Updated")
