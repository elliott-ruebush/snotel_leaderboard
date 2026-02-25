from snotel_lib import SnotelClient

client = SnotelClient()
# get metadata to find DDM / Deadman Creek
metadata = client.get_stations_metadata()
ddm = metadata[metadata["name"].str.contains("Deadman", case=False, na=False)]
print("Found Deadman Creek:")
print(ddm)

if not ddm.empty:
    station_id = "DDM"
    print(f"Fetching data for {station_id}...")
    try:
        df = client.get_station_data(station_id)
        print("Describe:")
        print(df.describe())
        print("\nHead:")
        print(df.head())
    except Exception as e:
        print(f"Error fetching data: {e}")
