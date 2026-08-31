import pandas as pd

vision_master = pd.read_csv(
    r"C:\Users\dougl\PycharmProjects\meyers_json\vision_inventory.csv")

#Removes Disco Items Because they are marked as Z* D/C
def remove_z():

    vision_df = vision_master[
        ~(
        (vision_master['Description'].str.startswith("Z*")) |
         (vision_master['Description'].str.startswith("Z *"))|
         (vision_master['Description'].str.startswith("Z "))|
         (vision_master['Description'].str.startswith("Z *"))|
         (vision_master['Description'].str.startswith("Z D"))
        )
          ]


    return vision_df

vision_remove_z = remove_z()

# Removes Entries that have been Deleted from inventory prefaced with [DEl]
def no_disco():
    vision_no_disco = vision_remove_z[~
    vision_remove_z['Description'].str.contains("[DEL]", regex=False, na=False)]

    return vision_no_disco
vision_disco_removed = no_disco()

# Removes Duplicated Item Numbers
def no_dups():

    vision_dups_removed = vision_disco_removed[~
        vision_disco_removed.duplicated('Item #', keep='first')]

    return vision_dups_removed

vision_no_dups = no_dups()

#Selects Only Rainbow Vendor Identified by Vendor Code 3
def remove_vendor():
    vision_rainbow = vision_no_dups[
        vision_no_dups['Vendor']=='3']

    return vision_rainbow
vision_vendor_rainbow = remove_vendor()

#Selects only Neccessary Columns
def remove_columns():
    column_list = ['Vintage', 'Unit Price', 'Pack Price', 'Bottle Size',
                   'Item Unit Cost', 'UPC data', 'Case Price', 'Current Inventory On Hand']
    vision_cleaned = vision_vendor_rainbow.drop(columns = column_list)

    vision_cleaned =  vision_cleaned.rename(columns = {'Item #':'item_num',
                                                       'Description':'item',

                                                       'Vendor':'vendor',
                                                       'Case Size':'case_size',
                                                       'Pack Qty':'pack_size',
                                                       'Item Case Cost':'case_cost'})
    vision_cleaned['weekly_sales'] = int(0)
    return vision_cleaned

rainbow_clean = remove_columns()

rainbow_clean['item_num'] = rainbow_clean['item_num'].astype(str).str.zfill(5)
rainbow_clean['case_size'] = rainbow_clean['case_size'].astype(int)
rainbow_clean['pack_size'] = rainbow_clean['pack_size'].astype(int)
rainbow_clean['case_cost'] = rainbow_clean['case_cost'].astype(int)


master_columns = ['item_num', 'item', 'vendor', 'case_size', 'pack_size', 'case_cost']

master_inventory = rainbow_clean[master_columns].copy()





