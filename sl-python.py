import requests
import csv
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from colorama import Fore, Style, init
import os
def fetch_email_accounts(api_key, max_accounts=9999):
    base_url = "https://server.smartlead.ai/api/v1/email-accounts/"
    accounts = []
    offset = 0
    limit = 100  # Fetch 100 accounts at a time

    while True:
        api_url = f"{base_url}?api_key={api_key}&offset={offset}&limit={limit}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if offset == 0:  # Display friendly message for the first batch
                    sample_email = data[0]['from_email'] if data else 'No data'
                    print(f"{Fore.GREEN}Successfully connected to API. Sample account fetched: {sample_email}{Style.RESET_ALL}")

                accounts.extend(data)
                if len(data) < limit or len(accounts) >= max_accounts:
                    break
                offset += limit  # Increase offset to fetch the next set of accounts
            else:
                print(f"{Fore.RED}Error: Received status code {response.status_code}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Response Content: {response.text}{Style.RESET_ALL}")
                break
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
            break

    return [account['from_email'] for account in accounts]

init()

api_key = os.getenv("SMARTLEAD_API_KEY")
csv_path =  os.getenv("CSV_PATH")
custom_login_url = os.getenv("LOGIN_URL")

existing_emails = fetch_email_accounts(api_key)

emails_passwords = []
with open(csv_path, newline='', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        emails_passwords.append({'email': row['EmailAddress'], 'password': row['Password']})

print(f"{Fore.GREEN}Number of email addresses in the CSV: {len(emails_passwords)}{Style.RESET_ALL}")

response = input("Do you want to continue with the process? (y/n): ").lower()
if response != 'y':
    exit()

max_retries = 99
processed_count = 0

for record in emails_passwords:
    email = record['email']
    password = record['password']
    attempts = 0

    if email in existing_emails:
        print(f"{Fore.YELLOW}{email} already exists, skipping...{Style.RESET_ALL}")
        processed_count += 1
        print(f"Processed address {processed_count} out of {len(emails_passwords)}")
        continue

    while attempts < max_retries:
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)

            print(f"{Fore.BLUE}Accessing login page for {email}...{Style.RESET_ALL}")
            driver.get(custom_login_url)

            time.sleep(5)

            oauth_username_field = driver.find_element(By.NAME, 'loginfmt')
            oauth_username_field.send_keys(email)
            username_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            username_button.click()

            time.sleep(5)

            oauth_password_field = driver.find_element(By.NAME, 'passwd')
            oauth_password_field.send_keys(password)
            password_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            password_button.click()

            time.sleep(5)

            try:
                wait = WebDriverWait(driver, 5)
                no_button = wait.until(EC.element_to_be_clickable((By.ID, 'KmsiCheckboxField')))
                no_button.click()
                no_button = wait.until(EC.element_to_be_clickable((By.ID, 'idBtn_Back')))
                no_button.click()
            except TimeoutException:
                print(f"{Fore.YELLOW}New popup did not appear; proceeding without clicking 'No'.{Style.RESET_ALL}")

            time.sleep(5)

            try:
                wait = WebDriverWait(driver, 5)
                ask_later_button = wait.until(EC.element_to_be_clickable((By.ID, 'btnAskLater')))
                ask_later_button.click()
            except TimeoutException:
                print(f"{Fore.YELLOW}Popup did not appear; proceeding without clicking 'Ask later'.{Style.RESET_ALL}")

            time.sleep(5)

            try:
                wait = WebDriverWait(driver, 5)
                accept_submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"]')))
                accept_submit.click()
            except TimeoutException:
                print(f"{Fore.YELLOW}Final Submit button did not appear; proceeding with the next steps.{Style.RESET_ALL}")

            print(f"{Fore.GREEN}Login process completed for {email}.{Style.RESET_ALL}")
            processed_count += 1
            print(f"Processed address {processed_count} out of {len(emails_passwords)}")
            break

        except Exception as exception:
            attempts += 1
            print(f"{Fore.RED}Error occurred for {email}. Attempt {attempts} of {max_retries}. Retrying... Error: {exception}{Style.RESET_ALL}")
            time.sleep(2)
        finally:
            try:
                driver.quit()
            except:
                pass

        if attempts == max_retries:
            print(f"{Fore.RED}Max retries reached for {email}. Moving to next email.{Style.RESET_ALL}")
            processed_count += 1
            print(f"Processed address {processed_count} out of {len(emails_passwords)}")
