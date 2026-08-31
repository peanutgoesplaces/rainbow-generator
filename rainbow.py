from tkinter.ttk import Treeview

import pandas as pd
from tkinter import *
pd.set_option('display.max_columns', None)
global cases_cost_total
global case_count

remove_df = pd.read_csv('remove_list.csv')
#remove_df = pd.DataFrame(columns=['item'])

from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent



avg_df = pd.read_csv(BASE / "avg_monthly.csv")
df = pd.read_csv(BASE / "vision_inventory.csv")
remove_cig_df = pd.read_csv(BASE / "remove_ciggs_offset.csv")
current_week_inventory = pd.read_csv(BASE / "current_inventory.csv")

remove_cig_df['offset'] = remove_cig_df['offset'].fillna(0).astype(int)
remove_cig_df['qoh'] = remove_cig_df['qoh'].fillna(0).astype(int)

print(remove_cig_df['qoh'].dtype)



remove_cig_df = remove_cig_df.dropna()
remove_cig_df = remove_cig_df.rename(columns={'qoh' : 'qtr'})
#___________________________________________________________________
# avg_df = pd.read_csv(r"C:\Users\dougl\PycharmProjects\order_maker\avg_monthly.csv")

# df = pd.read_csv(r"C:\Users\dougl\Downloads\vision_inventory.csv")

#remove_cig_df = pd.read_csv('remove_ciggs_offset.csv')\

# current_week_inventory = pd.read_csv(r"C:\Users\dougl\PycharmProjects\PythonProject3\current_inventory.csv")
#_____________________________________________________________________

cigg_df = df[df['Vendor'] == '3']


cigg_df = cigg_df[['Item #', 'Description', 'Vendor', 'Case Size', 'Pack Qty', 'Case Price',
                   'Current Inventory On Hand', 'Item Case Cost']]
cigg_df = cigg_df.rename(columns={'Item #' : 'item_num', 'Current Inventory On Hand' : 'qoh',
                                  'Description' : 'descr', 'Item Case Cost' : 'case_cost'}
                         )
cigg_df  = cigg_df[
    ~cigg_df.duplicated('item_num', keep='first')
]

current_week_inventory = current_week_inventory[['item_num', 'qoh']]

current_df = cigg_df.drop(columns='qoh').merge(current_week_inventory,
                           on='item_num',
                           how='left')


weekly_df_list = []
remove_list = []

from pathlib import Path

folder = Path(r"C:\Users\dougl\PycharmProjects\meyers_json\weekly_sales")

for file in sorted(folder.glob("*.csv")):
    df = pd.read_csv(file)

    df['weekly_sales'] = pd.to_numeric(df['weekly_sales'].astype(str).str.replace(",", ""))
    weekly_df_list.append(df)




full_df = current_df.merge(weekly_df_list[-1][['item_num', 'weekly_sales' ]],
                           on='item_num',
                           how='left')
merged = pd.concat([weekly_df_list[-4], weekly_df_list[-3], weekly_df_list[-2], weekly_df_list[-1]],
                   ignore_index=True)

#print(merged.head())
#______________________________________________________________________
#USE THIS LATER FOR CIGG AVERAGES
# monthly_avg = (
#     merged.groupby('item_num', as_index=False)['weekly_sales'].mean()
#                .rename(columns={'weekly_sales' : 'avg_monthly'}))
# print(full_df.columns)
# print(monthly_avg.columns)
#
# full_df = pd.merge(full_df, monthly_avg[['item_num', 'avg_monthly']],
#                    on='item_num',
#                    how='left'
#                    )
#_____________________________________________________________________________________
full_df = pd.merge(full_df, avg_df[['item_num', 'monthly_avg']],

                   on='item_num',
                   how='left'
                   )



full_df = full_df.merge(remove_cig_df[['item_num', 'qtr', 'offset']],
                        on='item_num',
                        how='left')
full_df['qtr'] = full_df['qtr'].fillna(0)

full_df.to_csv("rainbow_check.csv", index=False)
print(full_df.columns)


full_df = full_df.loc[
    ~full_df['descr'].isin(remove_df['item'])]


full_df['weekly_sales'] = full_df['weekly_sales'].fillna(0)
full_df['qoh'] = full_df['qoh'].fillna(0)

full_df['order'] = 'No'
full_df['qoh'] = full_df['qoh'].astype(int)
full_df['qtr'] = full_df['qtr'].astype(int)

full_df['weekly_sales'] = full_df['weekly_sales'].astype(int)
full_df['offset'] =  full_df['offset'].fillna(0)
full_df['adjusted_inventory'] = (full_df['qoh'] - full_df['qtr']) - (full_df['offset'].astype(int))


full_df.loc[
    (full_df['adjusted_inventory'] <= 0) |
    (full_df['adjusted_inventory'] <= full_df['weekly_sales']) |
    (full_df['adjusted_inventory'] <= full_df['monthly_avg']),
    'order'] = 'Yes'





order_df = full_df[full_df['order']=='Yes']

order_df['cases_ordered'] = 0

order_df.loc[
    full_df['order'] == 'Yes',
     'cases_ordered'] = 1

window = Tk()
window.title("Cigarette Order Generator")
window.geometry("900x600")
window.configure(background="white")

vendor_tree = Treeview(window, columns=(['descr', 'adjusted_inventory', 'weekly_sales', 'monthly_avg',
                                         'case_cost', 'order']),
                       show='headings',
                       height=24)

vendor_tree.column("descr", width=250, minwidth=200, anchor=CENTER)
vendor_tree.column('adjusted_inventory', width=115, anchor=CENTER)
vendor_tree.column("weekly_sales", width=80, anchor=CENTER)
vendor_tree.column('monthly_avg', width=80, anchor=CENTER)
vendor_tree.column("case_cost", width=70, anchor=CENTER)
vendor_tree.column('order', width=70, anchor=CENTER)

vendor_tree.heading("descr", text="Item")
vendor_tree.heading("adjusted_inventory", text='Adjusted Inventory')
vendor_tree.heading("weekly_sales", text='Weekly Sales')
vendor_tree.heading('monthly_avg', text='Monthly Avg')
vendor_tree.heading("case_cost", text="Case Cost")
vendor_tree.heading("order", text="Order")

vendor_tree.place(x=20, y=20)


for _, row in full_df.iterrows():
    vendor_tree.insert('', 'end', values=(
                       row['descr'],
                       row['adjusted_inventory'],
                       row['weekly_sales'],
                       row['monthly_avg'],
                       row['case_cost'],
                       row['order'])

                       )
#________
def load_inventory():
    vendor_tree.delete(*vendor_tree.get_children())
    for _, row in full_df.iterrows():
        vendor_tree.insert('', 'end', values=(
            row['descr'],
            row['qoh'],
            row['weekly_sales'],
            row['monthly_avg'],
            row['case_cost'],
            row['order'])

                           )
#__________
def remove_items():
    global remove_df
    global full_df
    selection = vendor_tree.selection()
    item = vendor_tree.item(selection[0] ,'values')[0]


    if item not in remove_df['item']:
        remove_list.append(item)
        remove_df = pd.concat([pd.DataFrame(remove_list, columns=['item']), remove_df])
        remove_df.to_csv('remove_list.csv', index=False)

    full_df = full_df.loc[
        ~full_df['descr'].isin(remove_list)]

    load_inventory()

order_df['total_cases_cost'] = order_df['cases_ordered'] * order_df['case_cost']
total_cost = order_df['total_cases_cost'].sum()




def generate_order():

    order_window = Toplevel(window)
    order_window.title("Rainbow")
    order_window.geometry("900x600")
    order_window.configure(background="white")

    order_tree = Treeview(order_window,columns=(['descr', 'cases_ordered', 'adjusted_inventory','weekly_sales','monthly_avg',
                                                 'case_cost']),
                                                show='headings',
                                                height=26)

    order_tree.column("descr", width=250, anchor=CENTER)
    order_tree.column('cases_ordered', width=70, anchor=CENTER)
    order_tree.column("adjusted_inventory", width=115,anchor=CENTER)
    order_tree.column("weekly_sales", width=80, anchor=CENTER)
    order_tree.column("monthly_avg", width=80, anchor=CENTER)
    order_tree.column("case_cost", width=70, anchor=CENTER)


    order_tree.heading("descr", text="Item")
    order_tree.heading('cases_ordered', text='Cases Ordered')
    order_tree.heading("adjusted_inventory", text='Adjusted Inventory')
    order_tree.heading("weekly_sales", text='Weekly Sales')
    order_tree.heading('monthly_avg', text='Monthly Avg')
    order_tree.heading("case_cost", text="Case Cost")

    total_case_count = order_df['cases_ordered'].sum()


    for _, row in order_df.iterrows():
        order_tree.insert('', 'end', values=(
            row['descr'],
            row['cases_ordered'],
            row['adjusted_inventory'],
            row['weekly_sales'],
            row['monthly_avg'],
            row['case_cost']

        ))
    def case_entry_bind(event):
        selection = order_tree.selection()

        item = selection[0]
        case_quantity = order_tree.item(item, 'values')[1]

        case_update_entry.delete(0, 'end')
        case_update_entry.insert(0,case_quantity)


        def clear(event):
            case_update_entry.delete(0, 'end')
        case_update_entry.bind("<FocusIn>", clear)

    order_tree.bind('<<TreeviewSelect>>', case_entry_bind)


    def update():
        selection = order_tree.selection()
        selected_item= order_tree.item(selection[0], 'values')
        item_list= list(selected_item)
        item_list[1] = case_update_entry.get()

        order_tree.item(selection, values=item_list)
        item_name = item_list[0]

        order_df.loc[
            order_df['descr'] == item_name,
            'cases_ordered'] = int(case_update_entry.get())

        total_case_count = order_df['cases_ordered'].sum()
        case_count.configure(text= f"{total_case_count}")

        order_df['total_cases_cost'] = order_df['cases_ordered'] * order_df['case_cost']

        total_case_cost = order_df['total_cases_cost'].sum()
        cases_cost_total.configure(text=f"${total_case_cost:.2f}")




    update_button = Button(order_window, text = 'Update', font=('Arial', 16),
                           command=update)
    update_button.place(x=729, y=50)

    case_update_entry =  Entry(order_window, width=15, bg='white', fg='black')
    case_update_entry.place(x=727, y=120)

    case_count_label = Label(order_window, text = 'Case Count', bg='white',
                             font=('Arial', 16))
    case_count_label.place(x=713, y=200)

    case_count = Label(order_window, text = f"{total_case_count}",bg='white',
                       font=('Arial', 16))
    case_count.place(x=755, y=250)

    cases_cost_label = Label(order_window, text = 'Cases Cost',bg='white',
                             font=('Arial', 16))
    cases_cost_label.place(x=715, y=300)

    cases_cost_total = Label(order_window, text = f"${total_cost:.2f}",bg='white',
                             font=('Arial', 16))
    cases_cost_total.place(x=725, y=350)




    order_tree.place(x=20, y=20)


generate_button = Button(window, text = 'Generate Order', command=generate_order,
                         font = ('Arial', 16),)
generate_button.place(x=700, y=200)

remove_button = Button(window, text='Remove Item', font=('Arial', 16),
                       command=remove_items)
remove_button.place(x=710, y=275)




window.mainloop()
