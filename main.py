from tkinter.ttk import Treeview
import pandas as pd
from tkinter import *
from upload_to_db import insert_current_dataframe, insert_weekly_dataframe
from current_inventory import retrieve_current_inventory
from weekly_sales import generate_weekly_sales_df
from pandas.core.roperator import rpow
from datetime import date, datetime
from pathlib import Path
import sys
from database import conn

#I MOVED ORDER DF POPULATER FROM LINE 322 TO ABOVE THE REFRESH FUNCTION

pd.set_option('display.max_columns', None)

global cases_cost_total
global case_count
global vendor_tree


offset_df = pd.read_csv(r'C:\Users\dougl\PycharmProjects\rainbow\remove_ciggs - Sheet1.csv')
offset_df = offset_df.rename(columns={'qoh':'qtr'})
offset_df['item_num'] = offset_df['item_num'].astype(str)
#offset_df = offset_df.drop(columns=['Unnamed: 3'])

offset_df = offset_df.dropna()
offset_df['item_num'] = offset_df['item_num'].str.replace(".0","").str.zfill(5)
offset_df.to_csv('offset.csv', index=False)


#Manually Remove Items in remove_list
remove_df = pd.read_csv('remove_list.csv')
# remove_df.drop(index=0, inplace=True)
# remove_df.to_csv('remove_list.csv', index=False)

#___________________________________________________________
cursor = conn.cursor()
def create_display_df():
    # Create DataFrames from Database
    global display_df

    #Last Updated Current Inventory
    current_inventory = pd.read_sql(
        "SELECT * FROM current_inventory",
        conn
    )
    #Full Inventory List
    rainbow_inventory = pd.read_sql(
        "SELECT * FROM vision_master_list",
        conn
    )

    #Last Updated Weekly Sales
    weekly_sales_df = pd.read_sql(
        "SELECT * FROM weekly_sales",
        conn
    )

    #Merging all 3 DataFrames
    merged_df = pd.merge(rainbow_inventory, current_inventory.drop(columns=['item']),
                         on='item_num',
                         how='left'
                         )

    merged_df = pd.merge(merged_df.drop(columns=['current_date']), weekly_sales_df[['item_num', 'weekly_sales', 'week_end']],
                         on='item_num',
                         how='left'
                         )

    #Creates DataFrame for Program Display Using only the last Uploaded Entry
    display_df = merged_df[merged_df['week_end'] == merged_df['week_end'].max() ]
    #______________________________________________________________________________________________

    #SQL Query to Get Avg of Last Four Weeks of Sales
    cursor.execute("""
        SELECT
            item_num,
            ROUND(AVG(weekly_sales),2) AS four_week_avg,
            MAX(week_end) AS week_end
        FROM weekly_sales
        WHERE week_end IN (
            SELECT DISTINCT week_end
            FROM weekly_sales
            ORDER BY week_end DESC
            LIMIT 4
        )
        GROUP BY item_num
        ORDER BY item_num;
    
    """)
    four_week_avg = cursor.fetchall()
    four_week_avg_df = pd.DataFrame(four_week_avg,
                                    columns=['item_num', 'avg', 'week_end']
                                    )
    four_week_avg_df['avg'] = pd.to_numeric(four_week_avg_df['avg'])

    #SQL Query that Returns Second Previous Weeks Sales
    cursor.execute("""
        SELECT item_num, weekly_sales
        FROM weekly_sales AS previous_weeks_sales
        WHERE week_end = (
            SELECT MAX(week_end)
            FROM weekly_sales
            WHERE week_end < (
                SELECT MAX(week_end)
                FROM weekly_sales
            )
        )
    """)
    two_weeks_sales = cursor.fetchall()
    previous_weeks_df = pd.DataFrame(two_weeks_sales,
                                     columns=['item_num', 'previous_sales'])

    #Merging Second Previous Weeks Sales & Monthly Avg DataFrames to Display DataFrame
    display_df = pd.merge(display_df, previous_weeks_df[['item_num', 'previous_sales']],
                          on='item_num',
                          how='left'
                          )


    display_df = pd.merge(display_df, four_week_avg_df[['item_num','avg']],
                          on=['item_num'],
                          how='left'
                          )

    display_df = display_df.sort_values(by=['item'], ascending=True)
    #display_df.to_csv('display_df.csv', index=False)
    display_df['order'] = 'No'

    #Merging offset_df Which is a DataFrame Consisting of Cigarettes Owed to Accurately Display Current Inventory
    display_df = pd.merge(display_df, offset_df[['item_num', 'owed']],
                         on=['item_num'],
                         how='left'
                         )
    display_df = display_df.drop_duplicates(subset=['item_num'])

    display_df['owed'] = display_df['owed'].fillna(0)

    display_df = display_df.sort_values(by=['item'], ascending=True)

    display_df['adjusted'] = display_df['qoh'] - display_df['owed']

    #Algorithm to Determine What Has to be Ordered
    display_df.loc[
        (display_df['adjusted'] <= display_df['weekly_sales']) |
        (display_df['adjusted'] <= 1) |
        (display_df['adjusted'] <= display_df['avg'])|
        (display_df['adjusted'] <= display_df['previous_sales']),
         'order']='Yes'

    #Displays Cigarettes Not in the List of Removed Items
    display_df = display_df[
        ~display_df['item'].isin(remove_df['item'])
    ]
    #Saves Remove List
    display_df.to_csv('display_df.csv', index=False)
    return display_df

#____________________________________________________________

# Building GUI
#_____________________________________________________________
window = Tk()
window.title("Cigarette Order Generator")
window.geometry("1050x600")
window.configure(background="white")

# Builds Inventory Tree
def build_rainbow_tree():
    global vendor_tree
    display_df = create_display_df()
    vendor_tree = Treeview(window, columns=(['descr', 'adjusted_inventory', 'weekly_sales','previous_sales',
                                             'monthly_avg', 'case_cost', 'order']),
                           show='headings',
                           height=24)

    vendor_tree.column("descr", width=250, minwidth=200, anchor=CENTER)
    vendor_tree.column('adjusted_inventory', width=80, anchor=CENTER)
    vendor_tree.column("weekly_sales", width=70, anchor=CENTER)
    vendor_tree.column('previous_sales', width=70, anchor=CENTER)
    vendor_tree.column('monthly_avg', width=70, anchor=CENTER)
    vendor_tree.column("case_cost", width=80, anchor=CENTER)
    vendor_tree.column('order', width=60, anchor=CENTER)

    vendor_tree.heading("descr", text="Item")
    vendor_tree.heading("adjusted_inventory", text='Inventory')
    vendor_tree.heading("weekly_sales", text='Sales')
    vendor_tree.heading("previous_sales", text='Prev Sales')
    vendor_tree.heading('monthly_avg', text='Month Avg')
    vendor_tree.heading("case_cost", text="Case Cost")
    vendor_tree.heading("order", text="Order")

    vendor_tree.place(x=20, y=20)
    vendor_tree.delete(*vendor_tree.get_children())

    for _, row in display_df.iterrows():
        vendor_tree.insert('', 'end', values=(
            row['item'],
            row['adjusted'],
            row['weekly_sales'],
            row['previous_sales'],
            row['avg'],
            f"${row['case_cost']:.2f}",
            row['order']
        ))
    remove_list = []

    vendor_label = Label(window, text = "Rainbow\n"
                         "Cigarette\n"
                         "Order\n"
                         "Generator\n",
                         font=('Arial', 17, 'bold'),
                         bg="white",
                         )
    vendor_label.place(x=800, y=90)

    #Displays Item Removed
    remove_label = Label(window, text="", bg="white")
    remove_label.place(x=830, y=420)
    remove_item_label = Label(window, text="", bg="white")
    remove_item_label.place(x=790, y=440)

    #Adds Item to Removal List
    def remove_disco():
        global display_df
        selection = vendor_tree.selection()
        item = vendor_tree.item(selection[0], 'values')[0]

        if item not in remove_list:
            remove_list.append(item)
            df = pd.concat([pd.DataFrame(remove_list,columns=['item']),remove_df])
            df.to_csv('remove_list.csv', index=False)

            remove_label.configure(text='Removed:', anchor=CENTER)
            remove_item_label.configure(text = f'{item}', anchor=CENTER)

        display_df = display_df[
            ~display_df['item'].isin(remove_list)]


        vendor_tree.delete(*vendor_tree.get_children())
        for _, row in display_df.iterrows():
            vendor_tree.insert('', 'end', values=(
                row['item'],
                row['adjusted'],
                row['weekly_sales'],
                row['previous_sales'],
                row['avg'],
                f"${row['case_cost']:.2f}",
                row['order']
            ))

    remove_disco_button = Button(window, text="Remove Disco", command=remove_disco,
                                   font=('Arial', 14), bg='white', fg='black',)
    remove_disco_button.place(x=792, y=350)
build_rainbow_tree()
#______________________________________________________________________
#Creates DataFrame if Order == Yes & Window for Generate Order
def generate_order():
    order_window = Toplevel(window)
    order_window.title("Order Window")
    order_window.geometry("900x700")
    order_window.configure(background="white")

    order_df = display_df[
        display_df['order']=='Yes']

    #Algorithm to Decide How Many Cases Need to be Ordered
    import math
    import numpy as np
    order_df['cases_to_order'] = np.ceil(
        (order_df['weekly_sales'] - order_df['adjusted']) / order_df['case_size']
    ).clip(1).astype(int)
    order_df['total_case_cost'] = order_df['case_cost'] * order_df['cases_to_order']

    #Creates DataFrame of Items Not Being Ordered to Populate Full Inventory Button
    no_order_df = display_df[
        ~display_df['item_num'].isin(order_df['item_num'])
        ].sort_values(['adjusted','weekly_sales','avg'])
    no_order_df['cases_to_order'] = 0
    if no_order_df['cases_to_order'].empty:
        no_order_df['total_case_cost'] = no_order_df['case_cost']
    else:
        no_order_df['total_case_cost'] = no_order_df['case_cost'] * no_order_df['cases_to_order']



    #GUI For Order Window
    order_tree = Treeview(order_window, columns=(['item', 'adjusted', 'weekly_sales', 'case_cost',
                                                  'cases_to_order', 'total_case_cost']),
                          show='headings',
                          height=30
                          )

    order_tree.column("item", width=200, anchor=CENTER)
    order_tree.column("adjusted", width=75, anchor=CENTER)
    order_tree.column("weekly_sales", width=80, anchor=CENTER)
    order_tree.column("case_cost", width=80, anchor=CENTER)
    order_tree.column("cases_to_order", width=80, anchor=CENTER)
    order_tree.column('total_case_cost', width=100, anchor=CENTER)

    order_tree.heading("item", text="Item")
    order_tree.heading("adjusted", text="On Hand")
    order_tree.heading("weekly_sales", text="Weekly Sales")
    order_tree.heading("case_cost", text="Case Cost")
    order_tree.heading("cases_to_order", text="Order Amount")
    order_tree.heading("total_case_cost", text="Total Cost")

    for _, row in order_df.iterrows():
        order_tree.insert('','end', values=(
            row['item'],
            row['adjusted'],
            row['weekly_sales'],
            row['case_cost'],
            row['cases_to_order'],
            row['total_case_cost']
        ))
#__________________________________________________________________________
    #Refresh Function for After Data has been Updated
    def refresh():
        order_tree.delete(*order_tree.get_children())
        for _, row in order_df.iterrows():
            order_tree.insert('', 'end', values=(
                row['item'],
                row['adjusted'],
                row['weekly_sales'],
                row['case_cost'],
                row['cases_to_order'],
                row['total_case_cost']

            ))
#__________________________________________________________________________________
    #After Changing Case Quantities this Updates Case Quantity and Totals
    def update_labels():

        total_case_amount = sum(order_df['cases_to_order']) + sum(no_order_df['cases_to_order'])

        total_case_label = Label(order_window, text='Total Cases', bg='white',
                                 font=('Arial', 15, 'bold'))
        total_case_label.place(x=699, y=190)
        total_case_amount_label = Label(order_window, text=f"{total_case_amount}", width=15,
                                        bg='white',
                                        font=('Arial', 15, 'bold'))
        total_case_amount_label.place(x=662, y=240)

        total_order_cost = sum(order_df['total_case_cost']) + sum(no_order_df['total_case_cost'])

        total_order_label = Label(order_window, text='Total Cost', bg='white',
                                  font=('Arial', 15, 'bold'))
        total_order_label.place(x=700, y=305)
        total_order_amount_label = Label(order_window, text=f"${total_order_cost:.2f}", width=15,
                                         bg='white',
                                         font=('Arial', 15, 'bold'))
        total_order_amount_label.place(x=664, y=355)
    update_labels()


    update_entry = Entry(order_window, text='Update', bg='white', width=7,
                         justify=CENTER, font=('Arial', 12, 'bold'))
    update_entry.place(x=724, y=67)

    from PIL import Image, ImageTk
    #Rainbow Logo
    img = Image.open("logo.jpg")
    img = img.convert("RGBA")
    img = img.resize((150, 150))

    photo = ImageTk.PhotoImage(img)

    image_label = Label(order_window, image=photo, bg="white")
    image_label.image = photo
    image_label.place(x=677, y=400)

    #When an Item is Clicked to Update Order Quantity it Binds to Update Box
    def bind_case_count(event):
        item_selection = order_tree.selection()
        quantity = order_tree.item(item_selection, 'values')[4]

        update_entry.delete(0, 'end')
        update_entry.insert(END,quantity)

        #Deletes Current Quantity Upon Clicking
        def clear(event):
            update_entry.delete(0, 'end')
        update_entry.bind("<FocusIn>", clear)

    order_tree.bind('<<TreeviewSelect>>', bind_case_count)

    #Changes New Quantity to Order Value in Selection
    def update_order_quantity():
        item_selection = order_tree.selection()
        values = order_tree.item(item_selection, 'values')
        value_list = list(values)
        case_cost = float(values[3])
        value_list[4] = update_entry.get()
        value_list[5] = int(update_entry.get()) * case_cost

        item_name = value_list[0]

        #Updates DataFrame
        order_df.loc[
            order_df['item'] == item_name,
            'cases_to_order'] = int(update_entry.get())
        order_df.loc[
            order_df['item'] == item_name,
            'total_case_cost']= value_list[5]

        #Updates No Order DataFrame
        no_order_df.loc[
            no_order_df['item'] == item_name,
            'cases_to_order'] = int(update_entry.get())
        no_order_df.loc[
            no_order_df['item'] == item_name,
            'total_case_cost'] = value_list[5]


        order_tree.item(item_selection, values=value_list)


        update_labels()

    # Displays Rest of DataFrame to Include Items not in order_df
    def show_full_inventory():
        order_tree.insert('', 'end', values=('', '', '', '', '', '', ''))
        order_tree.insert('', 'end', values=('', '', '', '', '', '', ''))
        for _, row in no_order_df.iterrows():
            order_tree.insert('', 'end', values=(

                row['item'],
                row['adjusted'],
                row['weekly_sales'],
                row['case_cost'],
                row['cases_to_order'],
                row['total_case_cost'],

            ))


        print(no_order_df)

    update_button = Button(order_window, text="Update",
                           command=update_order_quantity,
                           font=('Arial', 12, 'bold'),)
    update_button.place(x=725, y=115)

    load_full_inventory_button = Button(order_window, text="Load Inventory",
                                        command=show_full_inventory,
                                        font=('Arial', 16),
                                        fg='black'
                                        )
    load_full_inventory_button.place(x=685, y=580)


    order_tree.place(x=20, y=20)

# Generates initial order
generate_order_button = Button(window, text="Generate Order", command=generate_order,
                               font=('Arial', 14), bg='white', fg='black',)
generate_order_button.place(x=790, y=250)

# Refreshes Current Days Inventory
def build_current():
    current = retrieve_current_inventory()

    master_df = pd.read_sql(
        "SELECT * FROM vision_master_list",
        conn
    )

    rainbow = current[current['dept'] == 'CIGARETTES']

    rainbow_full = pd.merge(master_df, rainbow.drop(columns=['item', 'dept']),
                            on='item_num',
                            how='left',
                            )
    rainbow_full['qoh'] = rainbow_full['qoh'].fillna(0)

    return rainbow_full

#Refreshes Current Weekly Sales
def build_new_weekly():
    new_weekly_sales = generate_weekly_sales_df()

    master_df = pd.read_sql(
        "SELECT * FROM vision_master_list",
        conn
    )

    new_weekly_sales = new_weekly_sales[['item_num', 'descr', 'size', 'qty']]
    new_weekly_sales.columns = ['item_num', 'item', 'size', 'weekly_sales']

    weekly_df_full = pd.merge(master_df, new_weekly_sales.drop(columns=['item', 'size']),
                              on='item_num',
                              how='left')
    weekly_df_full['weekly_sales'] = weekly_df_full['weekly_sales'].fillna(0)

    start_date = date(2026,8,17)
    end_date = date(2026,8,23)

    weekly_df_full['week_start'] = start_date
    weekly_df_full['week_end'] = end_date
    # weekly_df_full['week_start'] = date.today() - timedelta(days=7)
    # weekly_df_full['week_end'] = date.today() - timedelta(days=1)

    remove_col = weekly_df_full.pop('remove_list')
    weekly_df_full['remove_list'] = remove_col

    vendor = weekly_df_full.pop('vendor')
    weekly_df_full['vendor'] = vendor

    weekly_df_full['week_end'] = pd.to_datetime(weekly_df_full['week_end'])
    weekly_df_full['week_num'] = weekly_df_full['week_end'].dt.isocalendar().week
    print(weekly_df_full.head())

    return weekly_df_full

# Refreshes inventory display with updated inventory
#Is Refresh() redundant?
def refresh_display():
    global vendor_tree
    global display_df

    vendor_tree.delete(*vendor_tree.get_children())

    for _, row in display_df.iterrows():
        vendor_tree.insert('', 'end', values=(
            row['item'],
            row['adjusted'],
            row['weekly_sales'],
            row['previous_sales'],
            row['avg'],
            f"${row['case_cost']:.2f}",
            row['order']
        ))
# Runs function that pulls new inventory/sales, inserts in to database, and re-displays current inventory/sales
def build_new_display():
    global display_df
    new_display_current = build_current()
    insert_current_dataframe(new_display_current)
    try:
        new_display_weekly = build_new_weekly()
        insert_weekly_dataframe(new_display_weekly)
    except:
        pass

    display_df = create_display_df()
    refresh_display()


load_current_inventory_button = Button(window, text="Upload Current Inventory",
                                       command=build_new_display)
load_current_inventory_button.place(x=790, y=500)





window.mainloop()
