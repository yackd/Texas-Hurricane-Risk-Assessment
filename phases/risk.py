# Python Passion Project - Hurricane Data Analysis + Actuarial Risk Assessment
# Phase 5 of 5
# PY4E, - Python for Everybody by Dr. Charles Severance - Capstone/Personal Project

# Imports
import sqlite3
import math

# Setting up file names for the sql database, the search radius, and the report file
sql = "texas_hurricanes.sqlite"
file = "texas_statewide_risk_report.csv"
radius = 75

# Actuarial Risk Assessment for Texas Hurricanes
print("TEXAS HURRICANE RISK ASSESSMENT")

user = input(
    "Enter a Texas zip code, or type ALL, for a statewide risk report : "
).strip()

# The Haversine Formula
# Calculates the great-circle distance between two points given their coordinates
def miles(lat1, lon1, lat2, lon2):
    earth = 3958.8
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    x = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    y = 2 * math.asin(math.sqrt(x))
    return earth * y


# The scoring function
# Returns the risk profile after analyzing the hurricane data and FEMA shelter data
def score(lat, lon, astorms, ashelters):
    landfalls = 0
    maxwind = 0
    lowpressure = 1013

    for slat, slon, swind, spressure in astorms:
        distance = miles(lat, lon, slat, slon)
        if distance <= radius:
            landfalls = landfalls + 1
            if swind is not None and swind > maxwind:
                maxwind = swind
            if spressure is not None and spressure < lowpressure:
                lowpressure = spressure
    # sh = shelter, cl = closest
    clshelter = None
    cldistance = None
    for shname, shcity, shzip, shlat, shlon in ashelters:
        if shlat is None or shlon is None:
            continue
        distance = miles(lat, lon, shlat, shlon)
        if cldistance is None or distance < cldistance:
            cldistance = distance
            clshelter = (shname, shcity, shzip)

    frequency = math.sqrt(landfalls) * 5
    wind = (maxwind / 150) * 40
    pressure = ((1013 - lowpressure) / 100) * 20
    risk_score = frequency + wind + pressure

    if risk_score > 100:
        risk_score = 100
    if risk_score < 5:
        risk_score = 5

    if risk_score >= 75:
        category = "CRITICAL RISK ZONE"
    elif risk_score >= 40:
        category = "MODERATE RISK ZONE"
    else:
        category = "LOW RISK ZONE"

    return {
        "landfalls": landfalls,
        "max_wind": maxwind,
        "min_pressure": lowpressure,
        "risk_score": int(risk_score),
        "category": category,
        "closest_shelter": clshelter,
        "closest_distance": cldistance,
    }

# The actuarial risk assessment process
try:
    conn = sqlite3.connect(sql)
    cursor = conn.cursor()

    cursor.execute("SELECT latitude, longitude, wind_knots, barometric_pressure FROM TX_Storms")
    astorms = cursor.fetchall()

    cursor.execute("SELECT name, city, zip_code, latitude, longitude FROM Emergency_Shelters")
    ashelters = cursor.fetchall()

    # Option 2 - The statewide report for all Texas zip codes
    if user.upper() == "ALL":
        cursor.execute("SELECT zip_code, latitude, longitude FROM TX_ZipCodes")
        allzip = cursor.fetchall()
        conn.close()

        print("\nScoring " + str(len(allzip)) + " Texas zip codes... please wait.")

        results = []
        for zip_code, lat, lon in allzip:
            info = score(lat, lon, astorms, ashelters)
            results.append((zip_code, info))

        # Highest risk first
        results.sort(key=lambda item: item[1]["risk_score"], reverse=True)

        # Write the full report to a CSV file
        output_handle = open(file, "w")
        output_handle.write("zip_code,risk_score,category,landfalls,max_wind_knots,min_pressure_mb\n")
        for zip_code, info in results:
            output_handle.write(
                zip_code + ","
                + str(info["risk_score"]) + ","
                + info["category"] + ","
                + str(info["landfalls"]) + ","
                + str(info["max_wind"]) + ","
                + str(info["min_pressure"]) + "\n"
            )
        output_handle.close()

        # Printing the top-10 highest-risk summary
        print("\n")
        print("TOP 10 HIGHEST-RISK TEXAS ZIP CODES")
        for zip_code, info in results[:10]:
            print(zip_code + " - " + str(info["risk_score"]) + "/100 (" + info["category"] + ")")
        print("Statewide report for all " + str(len(results)) + " zip codes have been saved to '" + file + "'")

    else:
        # Option 1 - The single Zip Code option
        zip_code = user
        cursor.execute("SELECT latitude, longitude FROM TX_ZipCodes WHERE zip_code = ?", (zip_code,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            print("\n'" + zip_code + "' was not found in the Texas zip code table.")
            print("Make sure all previous phases have been run.")
        else:
            lat, lon = row
            info = score(lat, lon, astorms, ashelters)

            print("\n")
            print("PERSONAL ACTUARIAL ASSESSMENT (TEXAS)")  
            print("Estimated Postal Zone: " + zip_code)
            print("Risk Level: " + str(info["risk_score"]) + "/100 (" + info["category"] + ")")
            print("\n")
            print("Regional Data Summary (within " + str(radius) + " miles):")
            print("Documented Nearby Landfalls : " + str(info["landfalls"]) + " storms")
            print("Maximum Wind Velocity : " + str(info["max_wind"]) + " knots")
            print("Minimum Atmospheric Pressure : " + str(info["min_pressure"]) + " mb")
            print("\n")
            print("EMERGENCY SHELTER INFORMATION :")
            if info["closest_shelter"] is not None:
                shelter = info["closest_shelter"]
                print("Active Evacuation Destination Found :")
                print("Facility Name : " + str(shelter[0]))
                print("Location : " + str(shelter[1]) + ", TX " + str(shelter[2]))
                print("Distance from you : " + str(round(info["closest_distance"], 1)) + " miles")
            else:
                print("No active Federal emergency shelters are currently open.")
                print("Monitor local NOAA and Red Cross alerts for shelter activations.")

# In case of an error
except sqlite3.OperationalError as error:
    print("\nError : Could not read the database - " + str(error))
    print("All previous phases need to be run first.")