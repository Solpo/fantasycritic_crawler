import gspread

gc = gspread.oauth()

sh = gc.open_by_key("1GnBiI_bkm2dT5CY4XmPbN7rIQDRotL96P_3i-cAOF2c")


print(sh.sheet1.get('A1'))