import os
import time

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()  # Load environment variables from .env file


# Authenticate to Google Sheets API
def authenticate_google_sheets():
    """Handles authentication for Google Sheets API and returns a service object."""
    creds = None
    # Check if token.json exists to reuse credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials or the token is invalid, request user login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Automatically refresh token
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future runs
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the service for Google Sheets API
    service = build('sheets', 'v4', credentials=creds)
    return service


# Update sheet (overwrite data starting from first row)
def update_sheet(service, spreadsheet_id, data):
    """Updates the data starting from the first row."""
    # Define the range where the data will be updated (starting from A1)
    range_name = 'Sheet1!A1'  # Modify according to your sheet name

    # Prepare the body with the values
    body = {
        'values': data
    }

    # Update the sheet with the provided data
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"{result.get('updatedCells')} cells updated.")


# Selenium scraping for the data
def scrape_data():
    """Scrapes data from the website and returns it as a list of lists."""
    # Initialize WebDriver
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Navigate to the website and log in
        driver.get("https://ltp.investingdaddy.com/detailed-options-chain.php?symbol=BANKNIFTY")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="login"]/div[1]/div[2]/div/form'))
        )

        # Login details
        username_field = driver.find_element(By.XPATH, '//*[@id="username"]')
        password_field = driver.find_element(By.XPATH, '//*[@id="login"]/div[1]/div[2]/div/form/div[2]/div/input')
        terms_checkbox = driver.find_element(By.XPATH, '//*[@id="terms"]')
        login_button = driver.find_element(By.XPATH, '//*[@id="login"]/div[1]/div[2]/div/form/div[5]/center/button')

        # Fill login form
        username_field.send_keys('7046701695')  # Replace with your username
        password_field.send_keys('Amulkool11@')  # Replace with your password

        if not terms_checkbox.is_selected():
            terms_checkbox.click()

        login_button.click()

        time.sleep(2)

        # Extract table data after login
        table = driver.find_element(By.XPATH, '//*[@id="tech-companies-1"]')

        # Fetch table rows
        rows = []
        for row in table.find_elements(By.XPATH, './/tbody/tr'):
            cells = row.find_elements(By.XPATH, './td')
            row_data = [cell.text if cell else '' for cell in cells]
            rows.append(row_data)

        return rows

    except Exception as e:
        print("An error occurred:", e)
        return []

    finally:
        # Clean up and close WebDriver
        driver.quit()


def main():
    # Authenticate and create a service object for Google Sheets API
    service = authenticate_google_sheets()

    # Scrape data from the website using Selenium
    rows = scrape_data()

    # Update the Google Sheet with the scraped data (overwrites existing data from the first row)
    spreadsheet_id = '1QXuHMa_EfFnpgZFlbjxKugBY1ytkXmYfuYI1i-2nU0I'  # Your Google Sheet ID
    update_sheet(service, spreadsheet_id, rows)


if __name__ == "__main__":
    main()
