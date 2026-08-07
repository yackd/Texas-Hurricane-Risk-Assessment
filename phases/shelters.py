# Python Passion Project - Hurricane Data Analysis + Actuarial Risk Assessment
# Phase 3 of 5
# PY4E, - Python for Everybody by Dr. Charles Severance - Capstone/Personal Project

# Imports
import sqlite3
import urllib.request
import urllib.parse
import json
import time

# Setting up the sql database
sql = "texas_hurricanes.sqlite"

# Connecting to FEMA's official registry of emergency shelters
filters = {
    "where": "state='TX'",
    "outFields": "shelter_name,city,zip,shelter_status,evacuation_capacity,latitude,longitude",
    "returnGeometry": "false",
    "f": "json",
}
api = ("https://gis.fema.gov/arcgis/rest/services/NSS/OpenShelters"
                  "/FeatureServer/0/query?" + urllib.parse.urlencode(filters))

print("Starting Phase 3: Retrieving regional data...")

# Opening the Phase 2 (sql) database and creating a new table for the FEMA emergency shelter data
conn = sqlite3.connect(sql)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS Emergency_Shelters")

cursor.execute("""
CREATE TABLE Emergency_Shelters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    city TEXT,
    zip_code TEXT,
    status TEXT,
    evacuation_capacity INTEGER,
    latitude REAL,
    longitude REAL
)
""")

print("API contacting FEMA's shelter database...")

# Creating a one second delay to avoid overwhelming the API with requests
time.sleep(1)

shelters = 0

try:
    request = urllib.request.Request(
        api, headers={"User-Agent": "TexasHurricaneRiskProject/1.0"}
        )
    with urllib.request.urlopen(request) as response:
        data = response.read().decode("utf-8")

    jdata = json.loads(data)
    records = jdata.get("features", [])

    print("API data downloaded successfully. Now extracting shelter records...")

    # Looping and filtering the FEMA shelter data (TX only)
    # Storing the correct data in the Emergency_Shelters table 
    for record in records:
        info = record.get("attributes", {})
        name = info.get("shelter_name")
        city = info.get("city")
        zip_code = info.get("zip")
        status = info.get("shelter_status")
        capacity = info.get("evacuation_capacity")
        lat = info.get("latitude")
        lon = info.get("longitude")

        # Skipping any records that are missing latitude or longitude values
        if lat is None or lon is None:
            continue

        cursor.execute("""
            INSERT INTO Emergency_Shelters
            (name, city, zip_code, status, evacuation_capacity, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, city, zip_code, status, capacity, lat, lon))

        shelters = shelters + 1

    conn.commit()
    print("EMERGENCY SHELTER DATA SAVED SUCCESSFULLY.")
    print("Retrieved " + str(shelters) + " emergency shelter records.")
    print("All locations are linked into '" + sql + "'")

    if shelters == 0:
        print("A result of 0 shelters found.")
        print("FEMA's Open Shelters feed only lists shelters currently activated,")
        print("meaning your area has no ongoing shelter activations at this time.")

except Exception as error:
    print("Error: Could not pull the shelter data - " + str(error))

finally:
    conn.close()
    print("Phase 3 officially completed! Open the folder to see the new database file.")