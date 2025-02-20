from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the BASE_URL from the environment variables
BASE_URL = os.getenv("BASE_URL")

global_section_index = 1
constitutionUrl = "/akn/ke/act/2010/constitution/eng@2010-09-03";