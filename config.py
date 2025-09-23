# config.py

# --- Login Details ---
# IMPORTANT: Use environment variables in a real production scenario
LOGIN_URL = "https://dashboard.thehousekraft.com/login" # The page where you enter the phone number
PHONE_NUMBER = "1231231231" # Your actual phone number
STATIC_OTP = "111111" # The simplified, static OTP you are using

# --- Target Application ---
START_URL_AFTER_LOGIN = "https://dashboard.thehousekraft.com/dashboard" # The first page to crawl after logging in
LOGIN_SUCCESS_INDICATOR_TEXT = "Welcome"
# --- CSS Selectors for the OTP Login Flow ---
# You MUST find these using your browser's "Inspect Element" tool.
# These are examples and will NOT work on your site without being changed.

# 1. Phone Number Input Field
PHONE_NUMBER_SELECTOR = 'input[name="phone"]' # e.g., '#phone-input', 'input[type="tel"]'

# 2. Button to click AFTER entering the phone number (e.g., "Send OTP", "Continue")
SEND_OTP_BUTTON_SELECTOR = 'button#send-otp-button' # e.g., 'button:contains("Send OTP")'

# 3. OTP Input Field (this might only appear AFTER you click the button above)
OTP_INPUT_SELECTOR = 'input[name="otp"]' # e.g., '#otp-field', 'input[aria-label="One-Time Password"]'

# 4. Final button to submit the OTP (e.g., "Verify", "Login")
VERIFY_OTP_BUTTON_SELECTOR = 'button[type="submit"]' # e.g., 'button:contains("Verify")'

# 5. An element that ONLY appears after a successful login to confirm it worked.
LOGIN_SUCCESS_INDICATOR_SELECTOR = "#user-avatar" # e.g., 'a[href="/logout"]', '.dashboard'

# --- Crawler Settings ---
IMAGE_UPLOAD_FOLDER = "images"
STRUCTURED_DATA_FILE = "structured_data_with_flow.json"
GRAPH_FILE = "site_graph_with_flow.gpickle"
