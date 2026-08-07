# Python Passion Project - Hurricane Data Analysis + Actuarial Risk Assessment
# Phase 1 of 5
# PY4E, - Python for Everybody by Dr. Charles Severance - Capstone/Personal Project

# Imports
import urllib.request
import os

# Setting up the URL and file names for the hurricane data
url = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt"
data = "atlantic_hurricane_data-(raw).txt"
report = "hurricane_report.txt"
print("Starting Phase 1...")

# Downloading the hurricane data file 
if not os.path.exists(data):
    print("Downloading data from NOAA...")
    try:
        urllib.request.urlretrieve(url, data)
    except:
        print("Could not download the file. Please retry later or check your internet connection.")
        quit()
else:
    print("File already exists on your computer.")

# Reading and processing the hurricane data file
fh = open(data, "r")
storm_count = 0
line_count = 0
for line in fh:
    line = line.strip()
    pieces = line.split(",")

    if len(pieces) < 2:
        continue

    line_count = line_count + 1

    x = pieces[0].strip()
    if x.startswith("AL"):
        storm_count = storm_count + 1
fh.close()

# Writing the report file 
print("Writing the hurricane data report...")

outputHandle = open(report, "w")
outputHandle.write("TEXAS HURRICANE DATA REPORT:\n")
outputHandle.write("Total rows looked at: " + str(line_count) + "\n")
outputHandle.write("Total storms found: " + str(storm_count) + "\n")
outputHandle.write("Status: Completed and ready for Phase 2.\n")

outputHandle.close()

# Completed!
print("Phase 1 officially completed! Open the folder to see the new report file.")