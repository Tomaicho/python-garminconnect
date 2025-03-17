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

from kuba_utils import *

main_menu_loop()