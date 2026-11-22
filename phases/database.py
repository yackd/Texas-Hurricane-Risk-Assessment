# Python Passion Project - Hurricane Data Analysis + Actuarial Risk Assessment
# Phase 2 of 5
# PY4E, - Python for Everybody by Dr. Charles Severance - Capstone/Personal Project

# Imports
import sqlite3

# Setting up file names for the data and sql database
raw = "data/atlantic_hurricane_data-(raw).txt"
sql = "texas_hurricanes.sqlite"

print("Starting Phase 2: Building the Actuarial Database...")

# Filtering for Texas landfalls only, with the coastal values between 25.5N and 30.5N, and -98.0W and -93.0W:
LatMin = 25.5
LatMax = 30.5
LonMin = -98.0
LonMax = -93.0

# Connecting to SQLite and building the TX_Storms Table
conn = sqlite3.connect(sql)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS TX_Storms")

cursor.execute("""
CREATE TABLE TX_Storms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    noaa_storm_code TEXT,
    storm_name TEXT,
    landfall_date TEXT,
    latitude REAL,
    longitude REAL,
    wind_knots INTEGER,
    barometric_pressure INTEGER
)
""")

# Processing the raw weather data
handle = open(raw, "r")
storm_code = ""
storm_name = ""
land_falls = 0

for line in handle:
    line = line.strip()
    pieces = line.split(",")

    if len(pieces) < 2:
        continue

    x = pieces[0].strip()

    # Parsing the storm header row to get the storm code and name
    if x.startswith("AL"):
        storm_code = x
        storm_name = pieces[1].strip()
        continue

    # Ensuring that the line has enough pieces to extract the necessary data
    if len(pieces) >= 8:
        # L in column 3 (index 2)
        land_fallm = pieces[2].strip()   
        Latx = pieces[4].strip()
        Lonx = pieces[5].strip()
        wind = pieces[6].strip()
        pressure = pieces[7].strip()

        if land_fallm == "L" and wind != "-999":
            # Updating north/east positive, and south/west negative
            lat = float(Latx[:-1])
            if Latx[-1] == "S":
                lat = -lat
            lon = float(Lonx[:-1])
            if Lonx[-1] == "W":
                lon = -lon

            # Filtering for Texas landfalls only, with coastal values between 25.5N and 30.5N, and -98.0W and -93.0W:
            if LatMin <= lat <= LatMax and LonMin <= lon <= LonMax:
                k = int(wind)
                # Storing the barometric pressure as an integer, or None if the value is -999
                mb = int(pressure) if pressure != "-999" else None

                cursor.execute("""
                    INSERT INTO TX_Storms
                    (noaa_storm_code, storm_name, landfall_date, latitude, longitude, wind_knots, barometric_pressure)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (storm_code, storm_name, pieces[0].strip(), lat, lon, k, mb))

                land_falls = land_falls + 1

# Saving the database and closing the connections
conn.commit()
conn.close()
handle.close()

print("DATABASE COMPLETED SUCCESSFULLY")
print("Inputted " + str(land_falls) + " historical Texas landfall records.")
print("The database is saved as: '" + sql + "'")
print("Phase 2 officially completed! Open the folder to see the new database file.")