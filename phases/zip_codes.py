# Python Passion Project - Hurricane Data Analysis + Actuarial Risk Assessment
# Phase 4 of 5
# PY4E, - Python for Everybody by Dr. Charles Severance - Capstone/Personal Project

# Imports
import sqlite3
import urllib.request
import zipfile
import os

# Setting up the sql database and the Census Gazetteer zip file
sql = "texas_hurricanes.sqlite"
url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip"
file = "2025_Gaz_zcta_national.zip"

print("Starting Phase 4: Building the Zip Code Table...")

# Downloading the Census Gazetteer file
if not os.path.exists(file):
    print("Downloading zip code data from the U.S. Census Bureau...")
    try:
        urllib.request.urlretrieve(url, file)
    except Exception as error:
        print("Could not download the file. Check your internet connection.")
        print(str(error))
        quit()
else:
    print("File already exists on your computer.")

# Opening the zip archive and reading the text file
x = zipfile.ZipFile(file)
inside = x.namelist()[0]
print("Reading " + inside + "...")

download = x.read(inside)

# Census files use Latin-1, not UTF-8; (as taught in PY4E).
text = download.decode("latin-1")  
lines = text.splitlines()

# Setting up the database table
conn = sqlite3.connect(sql)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS TX_ZipCodes")
cursor.execute("""
CREATE TABLE TX_ZipCodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zip_code TEXT,
    latitude REAL,
    longitude REAL
)
""")

# Processing the lines and inserting only Texas zip codes into the database
saved = 0

for line in lines:
    pieces = line.split("|")

    # Skipping the header row and blank lines
    if len(pieces) < 8:
        continue  

    geoid = pieces[0].strip()

    if not geoid.isdigit():
        continue  

    # Zip codes starting with 75, 76, 77, 78, or 79 are in Texas
    if geoid[:2] not in ("75", "76", "77", "78", "79"):
        continue  

    lat = float(pieces[6].strip())
    lon = float(pieces[7].strip())

    cursor.execute("""
        INSERT INTO TX_ZipCodes (zip_code, latitude, longitude)
        VALUES (?, ?, ?)
    """, (geoid, lat, lon))

    saved = saved + 1

conn.commit()
conn.close()

print("ZIP CODE TABLE COMPLETED SUCCESSFULLY.")
print("Inputted " + str(saved) + " Texas zip codes into '" + sql + "'")
print("Phase 4 officially completed! Every Texas zip code is now ready for Phase 5.")