class Queries:
    @staticmethod
    def all_volcanoes():
        return "SELECT * FROM volcanoes"

    @staticmethod
    def select_table():
        return "SELECT name FROM sqlite_master WHERE type='table' AND name='volcanoes'"

    @staticmethod
    def create_table(table: str):
        return f"CREATE TABLE {table} (Date TEXT, Precipitation TEXT, Latitude REAL, Longitude REAL)"

    @staticmethod
    def check_table(table: str):
        return f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"""

    @staticmethod
    def extract_position(lat, lon, date_list):
        return f"SELECT Date, Precipitation FROM volcanoes WHERE Latitude = '{lat}' AND Longitude = '{lon}' and DATE between '{date_list[0]}' and '{date_list[-1]}'"

    @staticmethod
    def insert_precipitation(date, precipitation, lat, lon):
        return "INSERT INTO volcanoes (Date, Precipitation, Latitude, Longitude) VALUES (?, ?, ?, ?)", date, precipitation, lat, lon