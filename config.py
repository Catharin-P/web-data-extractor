# config.py

# --- Login Credentials ---
# IMPORTANT: Use environment variables in a real production scenario
LOGIN_URL = "https://your-app.com/login"
USERNAME = "your_username"
PASSWORD = "your_password"

# --- Target Application ---
START_URL_AFTER_LOGIN = "https://your-app.com/dashboard" # The first page to crawl after logging in

# --- Selectors for Login ---
# These are CSS selectors. You MUST inspect your app's login page to find the correct ones.
USERNAME_SELECTOR = "#username" # e.g., 'input[name="email"]'
PASSWORD_SELECTOR = "#password" # e.g., 'input[name="password"]'
SUBMIT_BUTTON_SELECTOR = 'button[type="submit"]' # e.g., '#login-button'

# A selector for an element that ONLY appears after a successful login
# This is crucial for verifying that the login worked.
LOGIN_SUCCESS_INDICATOR_SELECTOR = "#dashboard-title" # e.g., 'a[href="/logout"]'

# --- Crawler Settings ---
# Path to a folder containing files to be used for upload forms
IMAGE_UPLOAD_FOLDER = "images"
# File for the final structured data
STRUCTURED_DATA_FILE = "structured_data_with_flow.json"
# File for the site graph
GRAPH_FILE = "site_graph_with_flow.gpickle"