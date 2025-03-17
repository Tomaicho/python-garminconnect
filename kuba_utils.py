import datetime
from datetime import timezone
import json
import logging
import os
import sys
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

menu_options = {
    "1": f"Get activity data",
    "2": f"Get activity data (compatible with garminconnect-ha)",
    "3": f"Get daily steps data",
    "4": f"Get heart rate data",
    "5": f"Get blood pressure data of onw week",
    "6": f"Get floors data",
    "7": f"Get sleep data",
    "8": f"Get stress data",
    "9": f"Get respiration data",
    "0": f"Get SpO2 data",
    "a": f"Get Heart Rate Variability data (HRV)",
    "b": f"Get all day stress data",
    "c": f"Get daily steps data of one week",
    "q": "Exit",
}

api = None

format = '%d-%m-%Y'

def get_credentials():
    """Get user credentials."""
    try:
        import credentials
        email = credentials.email
        password = credentials.password
    except:
        email = input("Login e-mail: ")
        password = getpass("Enter password: ")

    return email, password

def print_menu():
    """Print examples menu."""
    for key in menu_options.keys():
        print(f"{key} -- {menu_options[key]}")
    print("Make your selection: ", end="", flush=True)

def switch(api, i, startdate):
    """Run selected API call."""

    # Exit example program
    if i == "q":
        print("Be active, generate some data to fetch next time ;-) Bye!")
        sys.exit()

    # Skip requests if login failed
    if api:
        try:
            print(f"\n\nExecuting: {menu_options[i]}\n")

            # USER STATISTIC SUMMARIES
            if i == "1":
                # Get activity data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_stats('{startdate.isoformat()}')",
                    api.get_stats(startdate.isoformat()),
                )
            elif i == "2":
                # Get activity data (to be compatible with garminconnect-ha)
                save_json(
                    f"api.get_user_summary('{startdate.isoformat()}')",
                    api.get_user_summary(startdate.isoformat()),
                )

            # USER STATISTICS LOGGED
            elif i == "3":
                # Get steps data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_steps_data('{startdate.isoformat()}')",
                    api.get_steps_data(startdate.isoformat()),
                )

            elif i == "4":
                # Get heart rate data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_heart_rates('{startdate.isoformat()}')",
                    api.get_heart_rates(startdate.isoformat()),
                )

            elif i == "5":
                # Get daily blood pressure data for 'YYYY-MM-DD' to 'YYYY-MM-DD'
                save_json(
                    f"api.get_blood_pressure('{startdate.isoformat()}, {enddate.isoformat()}')",
                    api.get_blood_pressure(startdate.isoformat(), enddate.isoformat()),
                )

            elif i == "6":
                # Get daily floors data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_floors('{startdate.isoformat()}')",
                    api.get_floors(startdate.isoformat()),
                )

            elif i == "7":
                # Get sleep data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_sleep_data('{startdate.isoformat()}')",
                    api.get_sleep_data(startdate.isoformat()),
                )
            elif i == "8":
                # Get stress data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_stress_data('{startdate.isoformat()}')",
                    api.get_stress_data(startdate.isoformat()),
                )
            elif i == "9":
                # Get respiration data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_respiration_data('{startdate.isoformat()}')",
                    api.get_respiration_data(startdate.isoformat()),
                )
            elif i == "0":
                # Get SpO2 data for 'YYYY-MM-DD'
                save_json(
                    f"api.get_spo2_data('{startdate.isoformat()}')",
                    api.get_spo2_data(startdate.isoformat()),
                )

            elif i == "a":
                # Get Heart Rate Variability (hrv) data
                save_json(
                    f"api.get_hrv_data('{startdate.isoformat()}')",
                    api.get_hrv_data(startdate.isoformat()),
                )

            elif i == "b":
                # Get all day stress data for date
                save_json(
                    f"api.get_all_day_stress('{startdate.isoformat()}')",
                    api.get_all_day_stress(startdate.isoformat()),
                )

            elif i == "c":
                # Get daily step data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_daily_steps('{startdate.isoformat()}, {enddate.isoformat()}')",
                    api.get_daily_steps(startdate.isoformat(), enddate.isoformat()),
                )


        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
            GarthHTTPError,
        ) as err:
            logger.error(err)
        except KeyError:
            # Invalid menu option chosen
            pass
    else:
        print("Could not login to Garmin Connect, try again later.")

# Define function to save retrieved jsons from GarminConnect
def save_json(api_call, output):
    """Save API output to file."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    print(header)

    if isinstance(output, (int, str, dict, list)):
        with open(f"{api_call}.json", "w") as file:
            file.write(json.dumps(output, indent=4))
    else:
        print(output)

    print(footer)

def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    if not email or not password:
        email, password = get_credentials()

    garmin = Garmin(
        email=email, password=password, is_cn=False, prompt_mfa=get_mfa
    )
    garmin.login()
    # Save Oauth1 and Oauth2 token files to directory for next login

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")

# Initialize variable to keep track if date that user want to get data from is set
valid_start_date = False
#valid_end_date = False

def main_menu_loop(api=None, valid_start_date=False):
    while True:
        # Display header and login
        print("\n*** Garmin Connect API ***\n")

        # Init API
        if not api:
            email, password = get_credentials()
            api = init_api(email, password)

        if api:
            while not valid_start_date:
                # Get start_date that user want to get data from
                try:
                    startdate = datetime.datetime.strptime(input("Enter the date to get data from (DD-MM-YYYY): "), format).date()
                    #startdate = datetime.datetime.strptime("07-02-2025", format)
                    enddate = startdate - datetime.timedelta(days=7)
                    valid_start_date = True
                except ValueError as e:
                    print("Invalid date format, please try again.")
                    continue
            '''        
            while not valid_end_date:
                # Get end_date that user want to get data from
                try:
                    #enddate = datetime.datetime.strptime(input("Enter the end date to get data from (DD-MM-YYYY): "), format)
                    enddate = datetime.datetime.strptime("09-02-2025", format)
                    valid_end_date = True
                except ValueError as e:
                    print("Invalid date format, please try again.")
                    continue
            '''
            # Display menu
            print_menu()
            option = readchar.readkey()
            switch(api, option, startdate)
            valid_start_date = False
        else:
            email, password = get_credentials()
            api = init_api(email, password)
