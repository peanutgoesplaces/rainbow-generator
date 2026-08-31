from vision_master_filter import master_inventory
from datetime import date
from database import conn
from tkinter import messagebox

today = date.today()

#Uploads Full Inventory Downloaded from Work Computer
def insert_dataframe(df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO vision_master_list
            (item_num, item, vendor, case_size, pack_size, case_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (item_num) DO NOTHING
            """, (
            #IF item_num already in dataframe it wont upload

            row['item_num'],
            row['item'],
            row['vendor'],
            row['case_size'],
            row['pack_size'],
            row['case_cost']
        ))

    conn.commit()
    cursor.close()


#insert_dataframe(master_inventory)

#Uploads Current Inventory on Hand to Database
def insert_current_dataframe(df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO current_inventory
            (item_num, item, qoh, current_date)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (item_num)
            DO UPDATE SET
                item = EXCLUDED.item,
                qoh = EXCLUDED.qoh,
                current_date = EXCLUDED.current_date
            """, (

            row['item_num'],
            row['item'],
            row['qoh'],
            today
        ))

    conn.commit()
    cursor.close()

# insert_current_dataframe(rainbow_full_current)

#Uploads Current Weeks Sales to Database
def insert_weekly_dataframe(df):
    cursor = conn.cursor()
    week_end = df['week_end'].iloc[0]
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM weekly_sales
            WHERE week_end = %s
        )
    """, (week_end,))
    week_exists = cursor.fetchone()[0]

    if week_exists:
        messagebox.showinfo("Week's Sales Already Exist")
    else:
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO weekly_sales
                (item_num, item, weekly_sales, case_size, case_cost,
                pack_size, week_start, week_end, week_num)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_num, week_end) DO NOTHING
                """, (
                row['item_num'],
                row['item'],
                row['weekly_sales'],
                row['case_size'],
                row['case_cost'],
                row['pack_size'],
                row['week_start'],
                row['week_end'],
                row['week_num']

            ))

        conn.commit()
        cursor.close()

#insert_weekly_dataframe(weekly_df)

