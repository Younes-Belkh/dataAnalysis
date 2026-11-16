# main.py
from python.fetch import fetch_agoda_data
from python.clean import clean_json_to_csv

if __name__ == "__main__":
    print("--- STAGE 1: FETCHING DATA ---")
    fetch_agoda_data()

    print("\n--- STAGE 2: CLEANING TO CSV ---")
    clean_json_to_csv()
    
    print("\nDone!")