import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from time import sleep
import pandas as pd
import requests
import json
import random
from openai import OpenAI
import os
import certifi
import ssl
import shutil
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase credentials using the file path from the .env file
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
cred = credentials.Certificate(firebase_cred_path)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

def find_and_update_document(collection_name, title_value, comments, comment_analysis):
    # Search for the document
    docs = db.collection(collection_name).where('Title', '==', title_value).stream()
    for doc in docs:
        # Update the document with new fields
        doc_ref = db.collection(collection_name).document(doc.id)
        doc_ref.update({
            'comments': comments,
            'comment_analysis': comment_analysis
        })
        print(f'Document {doc.id} updated with comments and comment_analysis.')

def create_driver():
    # Retrieve proxy credentials from environment variables
    username = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    proxy_host = os.getenv("PROXY_HOST", "us.smartproxy.com")
    proxy_port = os.getenv("PROXY_PORT", "10000")
    http_proxy = f"http://{username}:{password}@{proxy_host}:{proxy_port}"

    # Initialize the undetected Chrome driver with proxy settings
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument(f'--proxy-server={http_proxy}')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)
    return driver

def extract_project_link(json_str):
    try:
        print(json_str['web']['project'])
        return json_str['web']['project']
    except (json.JSONDecodeError, KeyError):
        return None

def get_comments():
    driver = create_driver()

    # Open the Kickstarter login page
    driver.get("https://www.kickstarter.com/login")
    time.sleep(2)

    # Retrieve Kickstarter login credentials from environment variables
    ks_email = os.getenv("KICKSTARTER_EMAIL")
    ks_password = os.getenv("KICKSTARTER_PASSWORD")

    # Enter login credentials
    driver.find_element(By.XPATH, '//*[@id="user_session_email"]').send_keys(ks_email)
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="user_session_password"]').send_keys(ks_password)
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="new_user_session"]/fieldset/ol/li[3]/input').click()
    # Handle 2FA or CAPTCHA manually (pause the script to allow manual input)
    time.sleep(2)

    driver.get('https://www.kickstarter.com/projects/mysteriouspackage/no-escape-1')
    time.sleep(2)

    try:
        comments_button = driver.find_element(By.XPATH, '//*[@id="comments-emoji"]')
        # Optionally, scroll to the button if it's not in view
        actions = ActionChains(driver)
        actions.move_to_element(comments_button).perform()
        # Click the comments button
        comments_button.click()
        time.sleep(10)
        # Locate comments using XPath
        comments = driver.find_elements(By.XPATH, '//*[@class="data-comment-text type-14 mb0"]')
        # Convert comments to text
        comments = [comment.text for comment in comments]
        return comments
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the browser
        driver.quit()

# Initialize the OpenAI API client using the key from the .env file
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def chat_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Retrieve comments to pass to the model
proj_comments = get_comments()

# Create prompt for the model by joining the comments
prompt = ("Here are the comments on a product that I just launched. What is going right and what is going wrong? ").join(proj_comments)

# Get response from the model
response = chat_gpt(prompt)
print(response)
