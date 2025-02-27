import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from time import sleep
import pandas as pd
import requests
import json
import random
import os
import certifi
import ssl
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

df = pd.read_csv('trending_games.csv')

# Initialize the UserAgent object with cache server disabled for local generation
ua = UserAgent()
os.environ['SSL_CERT_FILE'] = certifi.where()


def create_driver():
    # Retrieve proxy credentials from environment variables
    username = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")

    # Construct the HTTP proxy string
    http_proxy = f"http://{username}:{password}@{proxy_host}:{proxy_port}"

    # Initialize the undetected Chrome driver with proxy settings
    options = uc.ChromeOptions()
    options.headless = False  # Change to True if you want to run headlessly
    options.add_argument(f'--proxy-server={http_proxy}')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)

    return driver


# Function to perform random scrolling dynamically
def random_scroll(driver, pause_time=0.5, scroll_amount=200):
    page_height = driver.execute_script("return document.body.scrollHeight")
    quarter_page = page_height / 20

    # Scroll down a quarter of the way
    current_position = driver.execute_script("return window.pageYOffset")
    target_position = current_position + quarter_page

    while current_position < target_position:
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(pause_time)
        current_position = driver.execute_script("return window.pageYOffset")

    # Scroll back up a quarter of the way
    target_position = current_position - quarter_page

    while current_position > target_position:
        driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
        time.sleep(pause_time)
        current_position = driver.execute_script("return window.pageYOffset")


# Function to gradually scroll to the bottom of the page
def scroll_slowly_to_element(driver, xpath, scroll_pause_time=0.1, scroll_amount=200):
    element = driver.find_element(By.XPATH, xpath)
    y_position = element.location['y']
    current_position = driver.execute_script("return window.pageYOffset")

    while current_position < y_position:
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_pause_time)
        current_position = driver.execute_script("return window.pageYOffset")
        if current_position >= y_position:
            break

    # Ensure final position is at the element
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(scroll_pause_time)
    print("Final scroll complete")


def get_description(url):
    driver = create_driver()
    driver.get(url)
    time.sleep(5)
    random_scroll(driver)
    time.sleep(2)
    scroll_slowly_to_element(driver, xpath='//*[@id="report-this-project-button"]')

    timeout = 5
    # Wait until the element is located or the timeout is reached
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'story-content'))
    )
    # Find the div with class 'story-content'
    story_content_div = driver.find_element(By.CLASS_NAME, 'story-content')
    # Find all paragraphs within this div
    p_elements = story_content_div.find_elements(By.TAG_NAME, 'p')
    # Extract and concatenate the text from each paragraph
    description_text = " ".join([p.text for p in p_elements])
    print("Description:", description_text)

    driver.quit()
    return description_text


df['description'] = df['project_link'].apply(get_description)
df.to_csv("trending_games_with_descriptions.csv", index=False)
