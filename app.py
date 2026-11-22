import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import zipfile
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Actuarial Hurricane Risk Analyzer", page_icon="🌀", layout="centered"
)

st.title("🌀 Actuarial Hurricane Risk Analyzer")
st.markdown("""
This web application processes NOAA meteorological records, builds a spatial SQLite database for Texas landfalls, integrates FEMA emergency shelters, maps U.S. Census Bureau Texas ZIP codes, and executes an **actuarial risk-scoring model**.
""")

# Create Tabs for All 5 Phases
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Phase 1: Ingestion",
    "Phase 2: Database",
    "Phase 3: FEMA Shelters",
    "Phase 4: Census ZIPs",
    "Phase 5: Risk Engine",
])

# ----------------------------------------------------
# TAB 1: Phase 1 Logic
# ----------------------------------------------------
with tab1:
  st.subheader("Phase 1: Ingestion & Total Storm Count")
  URL = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt"
  DATA_FILE = "data/atlantic_hurricane_data-(raw).txt"

  if st.button("Run Phase 1 Pipeline", type="primary"):
    with st.spinner("Downloading and parsing NOAA records..."):
      if not os.path.exists(DATA_FILE):
        try:
          urllib.request.urlretrieve(URL, DATA_FILE)
        except Exception as e:
          st.error(f"Could not download file: {e}")
          st.stop()

      storm_count = 0
      line_count = 0
      with open(DATA_FILE, "r") as fh:
        for line in fh:
          line = line.strip()
          pieces = line.split(",")
          if len(pieces) < 2:
            continue
          line_count += 1
          if pieces[0].strip().startswith("AL"):
            storm_count += 1

      st.success("Phase 1 Complete!")
      col1, col2 = st.columns(2)
      col1.metric("Total Rows", f"{line_count:,}")
      col2.metric("Atlantic Storms", f"{storm_count:,}")

# ----------------------------------------------------
# TAB 2: Phase 2 Logic
# ----------------------------------------------------
with tab2:
  st.subheader("Phase 2: Texas Landfall Database Builder")
  st.markdown("""
    Parses the raw text file, applies a geographic bounding box for **Texas** (`25.5°N–30.5°N`, `-98.0°W–-93.0°W`), and stores historical landfalls in `texas_hurricanes.sqlite`.
    """)

  if st.button("Build SQLite Database", type="primary"):
    with st.spinner("Filtering Texas landfalls and building SQLite database..."):
      raw_path = "data/atlantic_hurricane_data-(raw).txt"
      sql_path = "texas_hurricanes.sqlite"

      if not os.path.exists(raw_path):
        st.error(
            "Raw data file not found! Please run Phase 1 or check your file"
            " path."
        )
        st.stop()

      LatMin, LatMax = 25.5, 30.5
      LonMin, LonMax = -98.0, -93.0

      conn = sqlite3.connect(sql_path)
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

      handle = open(raw_path, "r")
      storm_code = ""
      storm_name = ""
      land_falls = 0

      for line in handle:
        line = line.strip()
        pieces = line.split(",")
        if len(pieces) < 2:
          continue

        x = pieces[0].strip()
        if x.startswith("AL"):
          storm_code = x
          storm_name = pieces[1].strip()
          continue

        if len(pieces) >= 8:
          land_fallm = pieces[2].strip()
          Latx = pieces[4].strip()
          Lonx = pieces[5].strip()
          wind = pieces[6].strip()
          pressure = pieces[7].strip()

          if land_fallm == "L" and wind != "-999":
            lat = float(Latx[:-1])
            if Latx[-1] == "S":
              lat = -lat
            lon = float(Lonx[:-1])
            if Lonx[-1] == "W":
              lon = -lon

            if LatMin <= lat <= LatMax and LonMin <= lon <= LonMax:
              k = int(wind)
              mb = int(pressure) if pressure != "-999" else None

              cursor.execute(
                  """
                                INSERT INTO TX_Storms
                                (noaa_storm_code, storm_name, landfall_date, latitude, longitude, wind_knots, barometric_pressure)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                  (
                      storm_code,
                      storm_name,
                      pieces[0].strip(),
                      lat,
                      lon,
                      k,
                      mb,
                  ),
              )
              land_falls += 1

      conn.commit()
      conn.close()
      handle.close()

      st.success("Database Built Successfully!")
      st.metric("Total Texas Landfall Records Inserted", land_falls)
      st.info(f"Saved locally to `{sql_path}`")

# ----------------------------------------------------
# TAB 3: Phase 3 Logic
# ----------------------------------------------------
with tab3:
  st.subheader("Phase 3: FEMA Emergency Shelter Integration")
  st.markdown("""
    Queries **FEMA's OpenShelters ArcGIS REST API** for active Texas emergency infrastructure and appends the records into your SQLite database.
    """)

  if st.button("Fetch FEMA Shelter Data", type="primary"):
    with st.spinner("Contacting FEMA API and updating SQL database..."):
      sql_path = "texas_hurricanes.sqlite"

      filters = {
          "where": "state='TX'",
          "outFields": (
              "shelter_name,city,zip,shelter_status,evacuation_capacity,latitude,longitude"
          ),
          "returnGeometry": "false",
          "f": "json",
      }
      api = (
          "https://gis.fema.gov/arcgis/rest/services/NSS/OpenShelters/FeatureServer/0/query?"
          + urllib.parse.urlencode(filters)
      )

      try:
        conn = sqlite3.connect(sql_path)
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

        time.sleep(1)
        request = urllib.request.Request(
            api, headers={"User-Agent": "TexasHurricaneRiskProject/1.0"}
        )
        with urllib.request.urlopen(request) as response:
          data = response.read().decode("utf-8")

        jdata = json.loads(data)
        records = jdata.get("features", [])

        shelters = 0
        for record in records:
          info = record.get("attributes", {})
          name = info.get("shelter_name")
          city = info.get("city")
          zip_code = info.get("zip")
          status = info.get("shelter_status")
          capacity = info.get("evacuation_capacity")
          lat = info.get("latitude")
          lon = info.get("longitude")

          if lat is None or lon is None:
            continue

          cursor.execute(
              """
                            INSERT INTO Emergency_Shelters
                            (name, city, zip_code, status, evacuation_capacity, latitude, longitude)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
              (name, city, zip_code, status, capacity, lat, lon),
          )
          shelters += 1

        conn.commit()
        conn.close()

        st.success("FEMA Shelter Data Loaded Successfully!")
        st.metric("Retrieved Shelter Records", shelters)

        if shelters == 0:
          st.info(
              "Note: FEMA's Open Shelters feed only lists actively open"
              " shelters during an emergency. 0 records is normal when no"
              " storms are active!"
          )

      except Exception as error:
        st.error(f"Could not pull the shelter data: {error}")

# ----------------------------------------------------
# TAB 4: Phase 4 Logic
# ----------------------------------------------------
with tab4:
  st.subheader("Phase 4: U.S. Census Bureau ZIP Code Ingestion")
  st.markdown("""
    Downloads the **2025 U.S. Census Gazetteer ZCTA archive**, unzips and decodes the geographic dataset, and filters for Texas ZIP codes (`75xxx–79xxx`) to populate `TX_ZipCodes`.
    """)

  if st.button("Process Census ZIP Codes", type="primary"):
    with st.spinner(
        "Downloading Census zip data and updating SQLite database..."
    ):
      sql_path = "texas_hurricanes.sqlite"
      zip_file_path = "data/2025_Gaz_zcta_national.zip"
      census_url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip"

      if not os.path.exists(zip_file_path):
        try:
          urllib.request.urlretrieve(census_url, zip_file_path)
        except Exception as error:
          st.error(f"Could not download Census file: {error}")
          st.stop()

      try:
        with zipfile.ZipFile(zip_file_path) as archive:
          inside_name = archive.namelist()[0]
          raw_bytes = archive.read(inside_name)

        text_data = raw_bytes.decode("latin-1")
        lines = text_data.splitlines()

        conn = sqlite3.connect(sql_path)
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

        saved_count = 0
        for line in lines:
          pieces = line.split("|")
          if len(pieces) < 8:
            continue

          geoid = pieces[0].strip()
          if not geoid.isdigit():
            continue

          if geoid[:2] not in ("75", "76", "77", "78", "79"):
            continue

          lat = float(pieces[6].strip())
          lon = float(pieces[7].strip())

          cursor.execute(
              """
                            INSERT INTO TX_ZipCodes (zip_code, latitude, longitude)
                            VALUES (?, ?, ?)
                        """,
              (geoid, lat, lon),
          )
          saved_count += 1

        conn.commit()
        conn.close()

        st.success("Census ZIP Code Table Completed Successfully!")
        st.metric("Texas ZIP Codes Added", f"{saved_count:,}")
        st.info(f"Saved to `{sql_path}`")

      except Exception as e:
        st.error(f"Error processing ZIP file: {e}")

# ----------------------------------------------------
# TAB 5: Phase 5 Logic (Actuarial Risk Engine)
# ----------------------------------------------------
with tab5:
  st.subheader("Phase 5: Actuarial Risk Engine & Reporting")
  st.markdown("""
    Calculates great-circle distances via the **Haversine formula**, evaluates storm frequency, wind velocity, and atmospheric pressure drops, and computes an actuarial risk score (1–100) for Texas postal zones.
    """)

  sql_path = "texas_hurricanes.sqlite"
  radius = 75  # search radius in miles


  # Helper Functions for Scoring
  def calc_miles(lat1, lon1, lat2, lon2):
    earth = 3958.8
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    x = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return earth * (2 * math.asin(math.sqrt(x)))


  def compute_risk_score(lat, lon, astorms, ashelters):
    landfalls, maxwind, lowpressure = 0, 0, 1013
    for slat, slon, swind, spressure in astorms:
      if calc_miles(lat, lon, slat, slon) <= radius:
        landfalls += 1
        if swind is not None and swind > maxwind:
          maxwind = swind
        if spressure is not None and spressure < lowpressure:
          lowpressure = spressure

    clshelter, cldistance = None, None
    for shname, shcity, shzip, shlat, shlon in ashelters:
      if shlat is None or shlon is None:
        continue
      dist = calc_miles(lat, lon, shlat, shlon)
      if cldistance is None or dist < cldistance:
        cldistance = dist
        clshelter = (shname, shcity, shzip)

    frequency = math.sqrt(landfalls) * 5
    wind_score = (maxwind / 150) * 40
    pressure_score = ((1013 - lowpressure) / 100) * 20
    risk_score = min(max(int(frequency + wind_score + pressure_score), 5), 100)

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
        "risk_score": risk_score,
        "category": category,
        "closest_shelter": clshelter,
        "closest_distance": cldistance,
    }


  # UI Options for Risk Assessment
  assessment_mode = st.radio(
      "Select Assessment Mode:",
      ["Single ZIP Code Lookup", "Statewide Risk Report (All TX ZIPs)"],
  )

  if not os.path.exists(sql_path):
    st.warning(
        "Database not found! Please run Phases 1–4 first to populate the tables."
    )
  else:
    try:
      conn = sqlite3.connect(sql_path)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT latitude, longitude, wind_knots, barometric_pressure FROM"
          " TX_Storms"
      )
      astorms = cursor.fetchall()
      cursor.execute(
          "SELECT name, city, zip_code, latitude, longitude FROM"
          " Emergency_Shelters"
      )
      ashelters = cursor.fetchall()
      conn.close()
    except Exception as e:
      st.error(f"Error connecting to database: {e}")
      astorms, ashelters = [], []

    if assessment_mode == "Single ZIP Code Lookup":
      user_zip = st.text_input(
          "Enter Texas ZIP Code (e.g. 77433 or 77002):", "77433"
      )

      if st.button("Calculate Actuarial Risk", type="primary"):
        if not astorms:
          st.error("No storm records found. Please run Phase 2 first.")
        else:
          with st.spinner(f"Analyzing historical risk profile for {user_zip}..."):
            conn = sqlite3.connect(sql_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT latitude, longitude FROM TX_ZipCodes WHERE zip_code = ?",
                (user_zip,),
            )
            row = cursor.fetchone()
            conn.close()

            if row is None:
              st.error(
                  f"ZIP code '{user_zip}' was not found in the database. Ensure"
                  " Phase 4 has been executed."
              )
            else:
              lat, lon = row
              info = compute_risk_score(lat, lon, astorms, ashelters)

              st.success("Actuarial Assessment Complete!")
              st.metric(
                  label=f"Risk Score for ZIP {user_zip}",
                  value=f"{info['risk_score']} / 100",
                  delta=info["category"],
                  delta_color="inverse",
              )

              col1, col2, col3 = st.columns(3)
              col1.metric("Nearby Landfalls", f"{info['landfalls']} storms")
              col2.metric("Max Wind Velocity", f"{info['max_wind']} knots")
              col3.metric("Min Pressure", f"{info['min_pressure']} mb")

              st.markdown("### 🏥 Closest Emergency Shelter")
              if info["closest_shelter"] is not None:
                shelter = info["closest_shelter"]
                st.write(f"**Facility Name:** {shelter[0]}")
                st.write(
                    f"**Location:** {shelter[1]}, TX {shelter[2]} (Distance:"
                    f" {round(info['closest_distance'], 1)} miles)"
                )
              else:
                st.info(
                    "No active Federal emergency shelters currently reported in"
                    " FEMA feed."
                )

    else:  # Statewide Mode
      if st.button("Run Statewide Scoring Engine", type="primary"):
        if not astorms:
          st.error("No storm records found. Please run Phase 2 first.")
        else:
          with st.spinner(
              "Scoring thousands of Texas ZIP codes... please wait."
          ):
            conn = sqlite3.connect(sql_path)
            cursor = conn.cursor()
            cursor.execute("SELECT zip_code, latitude, longitude FROM TX_ZipCodes")
            allzip = cursor.fetchall()
            conn.close()

            results = []
            for zip_code, lat, lon in allzip:
              info = compute_risk_score(lat, lon, astorms, ashelters)
              results.append((zip_code, info))

            results.sort(key=lambda item: item[1]["risk_score"], reverse=True)

            # Generate CSV report payload
            csv_data = "zip_code,risk_score,category,landfalls,max_wind_knots,min_pressure_mb\n"
            for zip_code, info in results:
              csv_data += (
                  f"{zip_code},{info['risk_score']},{info['category']},{info['landfalls']},{info['max_wind']},{info['min_pressure']}\n"
              )

            st.success(
                f"Statewide analysis completed across {len(results):,} ZIP"
                " codes!"
            )

            st.download_button(
                label="Download Full Statewide CSV Report",
                data=csv_data,
                file_name="texas_statewide_risk_report.csv",
                mime="text/csv",
            )

            st.markdown("### 🏆 Top 10 Highest-Risk Texas ZIP Codes")
            top_ten_data = []
            for rank, (zip_code, info) in enumerate(results[:10], 1):
              top_ten_data.append({
                  "Rank": rank,
                  "ZIP Code": zip_code,
                  "Risk Score": f"{info['risk_score']}/100",
                  "Category": info["category"],
                  "Landfalls": info["landfalls"],
              })
            st.table(top_ten_data)