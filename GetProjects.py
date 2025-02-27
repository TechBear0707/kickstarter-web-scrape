import ssl
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
import json
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase credentials using the file path from the .env file
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
cred = credentials.Certificate(firebase_cred_path)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# HELPER METHODS
def extract_project_link(json_str):
    try:
        print(json_str['web']['project'])
        return json_str['web']['project']
    except (json.JSONDecodeError, KeyError):
        return None

def extract_category(json_str):
    # Since our JSON is already parsed, we simply extract the parent name.
    parent_name = json_str.get('parent_name')
    return parent_name

#######################
# CREATING THE DRIVER #
#######################

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

# Retrieve proxy credentials from environment variables
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")
proxy_host = os.getenv("PROXY_HOST", "gate.smartproxy.com")
proxy_port = os.getenv("PROXY_PORT", "7000")
proxy = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"

# Initialize the undetected Chrome driver with proxy settings
options = uc.ChromeOptions()
options.headless = False  # Change to True if you want to run headlessly
options.add_argument(f'--proxy-server={proxy}')
driver = uc.Chrome(options=options)

########################
# LOGIN TO KICKSTARTER #
########################

driver.get("https://www.kickstarter.com/login")
time.sleep(3)

# Retrieve Kickstarter login credentials from environment variables
ks_email = os.getenv("KICKSTARTER_EMAIL")
ks_password = os.getenv("KICKSTARTER_PASSWORD")

driver.find_element(By.XPATH, '//*[@id="user_session_email"]').send_keys(ks_email)
time.sleep(1)
driver.find_element(By.XPATH, '//*[@id="user_session_password"]').send_keys(ks_password)
time.sleep(1)
driver.find_element(By.XPATH, '//*[@id="new_user_session"]/fieldset/ol/li[3]/input').click()
time.sleep(1)

##############################################
# LOAD MORE BUTTON INTERACTION AND SCROLLING #
##############################################

driver.get("https://www.kickstarter.com/discover/advanced?category_id=12&sort=magic&staff_picks=1")
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.bttn.bttn-primary.theme--create.bttn-medium")))
load_more_button = driver.find_element(By.CSS_SELECTOR, "a.bttn.bttn-primary.theme--create.bttn-medium")
actions = ActionChains(driver)
actions.move_to_element(load_more_button).perform()
load_more_button.click()

def scroll_to_bottom(driver, max_scrolls):
    count = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True and count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        count += 1

scroll_to_bottom(driver, 5)

##################################
# COLLECT AND STORE PROJECT DATA #
##################################

# Locate div elements with the "data-project" attribute
project_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-project]")
print("Number of projects:", len(project_elements))

# Convert project elements into a pandas DataFrame by parsing the JSON strings
df = pd.DataFrame([json.loads(project.get_attribute("data-project")) for project in project_elements])
df['project_link'] = df['urls'].apply(extract_project_link)
df['category'] = df['category'].apply(extract_category)
driver.quit()

# Store the data in the Firestore database
for i in range(len(df)):
    doc_ref = db.collection("medium_demo").add({
        "Title": df['name'][i],
        "URL": df['project_link'][i],
        "Category": df['category'][i],
        "blurb": df['blurb'][i],
        "state": df['state'][i],
        "country": df['country'][i],
        "goal": df['goal'][i],
        "pledged": df['usd_pledged'][i],
        "percentage_funded": df['percent_funded'][i],
        "project_link": df['project_link'][i]
    })
