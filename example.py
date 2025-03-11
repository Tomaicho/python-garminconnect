#!/usr/bin/env python3
"""
pip3 install garth requests readchar

export EMAIL=<your garmin email>
export PASSWORD=<your garmin password>

"""
import datetime
from datetime import timezone
import json
import logging
import os
import sys
import credentials
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

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
email = credentials.email
password = credentials.password
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
api = None

# Example selections and settings

# Let's say we want to scrape all activities using switch menu_option "p". We change the values of the below variables, IE startdate days, limit,...
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)  # Select past week
start = 0
limit = 100
start_badge = 1  # Badge related calls calls start counting at 1
activitytype = ""  # Possible values are: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
activityfile = "MY_ACTIVITY.fit"  # Supported file types are: .fit .gpx .tcx
weight = 89.6
weightunit = "kg"
# workout_example = """
# {
#     'workoutId': "random_id",
#     'ownerId': "random",
#     'workoutName': 'Any workout name',
#     'description': 'FTP 200, TSS 1, NP 114, IF 0.57',
#     'sportType': {'sportTypeId': 2, 'sportTypeKey': 'cycling'},
#     'workoutSegments': [
#         {
#             'segmentOrder': 1,
#             'sportType': {'sportTypeId': 2, 'sportTypeKey': 'cycling'},
#             'workoutSteps': [
#                 {'type': 'ExecutableStepDTO', 'stepOrder': 1,
#                     'stepType': {'stepTypeId': 3, 'stepTypeKey': 'interval'}, 'childStepId': None,
#                     'endCondition': {'conditionTypeId': 2, 'conditionTypeKey': 'time'}, 'endConditionValue': 60,
#                     'targetType': {'workoutTargetTypeId': 2, 'workoutTargetTypeKey': 'power.zone'},
#                     'targetValueOne': 95, 'targetValueTwo': 105},
#                 {'type': 'ExecutableStepDTO', 'stepOrder': 2,
#                     'stepType': {'stepTypeId': 3, 'stepTypeKey': 'interval'}, 'childStepId': None,
#                     'endCondition': {'conditionTypeId': 2, 'conditionTypeKey': 'time'}, 'endConditionValue': 120,
#                     'targetType': {'workoutTargetTypeId': 2, 'workoutTargetTypeKey': 'power.zone'},
#                     'targetValueOne': 114, 'targetValueTwo': 126}
#             ]
#         }
#     ]
# }
# """

menu_options = {
    "1": "Get full name",
    "3": f"Get activity data for '{today.isoformat()}'",
    "4": f"Get activity data for '{today.isoformat()}' (compatible with garminconnect-ha)",
    "8": f"Get steps data for '{today.isoformat()}'",
    "9": f"Get heart rate data for '{today.isoformat()}'",
    "-": f"Get daily step data for '{startdate.isoformat()}' to '{today.isoformat()}'",
    "!": f"Get floors data for '{startdate.isoformat()}'",
    "?": f"Get blood pressure data for '{startdate.isoformat()}' to '{today.isoformat()}'",
    "c": f"Get sleep data for '{today.isoformat()}'",
    "d": f"Get stress data for '{today.isoformat()}'",
    "e": f"Get respiration data for '{today.isoformat()}'",
    "f": f"Get SpO2 data for '{today.isoformat()}'",
    "x": f"Get Heart Rate Variability data (HRV) for '{today.isoformat()}'",
    "K": f"Get all day stress data for '{today.isoformat()}'",
    "q": "Exit",
}


def display_json(api_call, output):
    """Format API output for better readability."""

    dashed = "-" * 20
    header = f"{dashed} {api_call} {dashed}"
    footer = "-" * len(header)

    print(header)

    if isinstance(output, (int, str, dict, list)):
        print(json.dumps(output, indent=4))
    else:
        print(output)

    print(footer)

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


def display_text(output):
    """Format API output for better readability."""

    dashed = "-" * 60
    header = f"{dashed}"
    footer = "-" * len(header)

    print(header)
    print(json.dumps(output, indent=4))
    print(footer)


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, prompt_mfa=get_mfa
            )
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def print_menu():
    """Print examples menu."""
    for key in menu_options.keys():
        print(f"{key} -- {menu_options[key]}")
    print("Make your selection: ", end="", flush=True)


def switch(api, i):
    """Run selected API call."""

    # Exit example program
    if i == "q":
        print("Be active, generate some data to fetch next time ;-) Bye!")
        sys.exit()

    # Skip requests if login failed
    if api:
        try:
            print(f"\n\nExecuting: {menu_options[i]}\n")

            # USER BASICS
            if i == "1":
                # Get full name from profile
                display_json("api.get_full_name()", api.get_full_name())

            # USER STATISTIC SUMMARIES
            elif i == "3":
                # Get activity data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_stats('{today.isoformat()}')",
                    api.get_stats(today.isoformat()),
                )
            elif i == "4":
                # Get activity data (to be compatible with garminconnect-ha)
                display_json(
                    f"api.get_user_summary('{today.isoformat()}')",
                    api.get_user_summary(today.isoformat()),
                )
                save_json(
                    f"api.get_user_summary('{today.isoformat()}')",
                    api.get_user_summary(today.isoformat()),
                )

            # USER STATISTICS LOGGED
            elif i == "8":
                # Get steps data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_steps_data('{today.isoformat()}')",
                    api.get_steps_data(today.isoformat()),
                )
                save_json(
                    f"api.get_steps_data('{today.isoformat()}')",
                    api.get_steps_data(today.isoformat()),
                )

            elif i == "9":
                # Get heart rate data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_heart_rates('{today.isoformat()}')",
                    api.get_heart_rates(today.isoformat()),
                )
                save_json(
                    f"api.get_heart_rates('{today.isoformat()}')",
                    api.get_heart_rates(today.isoformat()),
                )

            elif i == "?":
                # Get daily blood pressure data for 'YYYY-MM-DD' to 'YYYY-MM-DD'
                display_json(
                    f"api.get_blood_pressure('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_blood_pressure(startdate.isoformat(), today.isoformat()),
                )
            elif i == "-":
                # Get daily step data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_daily_steps('{startdate.isoformat()}, {today.isoformat()}')",
                    api.get_daily_steps(startdate.isoformat(), today.isoformat()),
                )
            elif i == "!":
                # Get daily floors data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_floors('{today.isoformat()}')",
                    api.get_floors(today.isoformat()),
                )

            elif i == "c":
                # Get sleep data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_sleep_data('{today.isoformat()}')",
                    api.get_sleep_data(today.isoformat()),
                )
                save_json(
                    f"api.get_sleep_data('{today.isoformat()}')",
                    api.get_sleep_data(today.isoformat()),
                )
            elif i == "d":
                # Get stress data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_stress_data('{today.isoformat()}')",
                    api.get_stress_data(today.isoformat()),
                )
            elif i == "e":
                # Get respiration data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_respiration_data('{today.isoformat()}')",
                    api.get_respiration_data(today.isoformat()),
                )
            elif i == "f":
                # Get SpO2 data for 'YYYY-MM-DD'
                display_json(
                    f"api.get_spo2_data('{today.isoformat()}')",
                    api.get_spo2_data(today.isoformat()),
                )

            elif i == "x":
                # Get Heart Rate Variability (hrv) data
                display_json(
                    f"api.get_hrv_data({today.isoformat()})",
                    api.get_hrv_data(today.isoformat()),
                )

            elif i == "K":
                # Get all day stress data for date
                display_json(
                    f"api.get_all_day_stress({today.isoformat()})",
                    api.get_all_day_stress(today.isoformat()),
                )
                save_json(
                    f"api.get_all_day_stress('{today.isoformat()}')",
                    api.get_all_day_stress(today.isoformat()),
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


# Main program loop
while True:
    # Display header and login
    print("\n*** Garmin Connect API Demo by cyberjunky ***\n")

    # Init API
    if not api:
        api = init_api(email, password)

    if api:
        # Display menu
        print_menu()
        option = readchar.readkey()
        switch(api, option)
    else:
        api = init_api(email, password)
