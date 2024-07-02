import pandas as pd
import os
from fuzzywuzzy import process
from precip.plotter_functions import volcanoes_list
from precip.config import workDir, jsonVolcano
import subprocess

dir = (os.getenv(workDir)) if workDir in os.environ else (os.getenv('HOME'))

other_volcanoes = volcanoes_list(dir + '/' + jsonVolcano)

# Invert the order of the list
other_volcanoes = other_volcanoes[::-1]

full_path = os.getenv('HOME') + '/Desktop/Holocene_Volcanoes.xlsx'

# Read the Excel file
df = pd.read_excel(full_path, skiprows=1)

# Iterate over each row
for index, row in df.iterrows():
    # Check if the first column value is "WEEKLY" or "MONTHLY"
    if row[0] in ["WEEKLY", "MONTHLY"]:
        volcano_name = row['Volcano Name']
        similar_volcano = process.extractOne(volcano_name, other_volcanoes)

        # Only print the similar volcano if the similarity score is 86 or higher
        if similar_volcano[1] >= 86:
            print(f"Original: {volcano_name}, Similar: {similar_volcano}")
            command = f'get_all.py "{similar_volcano[0]}" --period 20040101:20050101 --bins 3 --log'
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

        else:
            # TODO to be determined
            pass