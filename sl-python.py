import requests
import csv
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from colorama import Fore, Style, init
import tempfile
import os
import random

init()

api_key = os.getenv("SMARTLEAD_API_KEY")
csv_folder = os.getenv("CSV_FOLDER", "bulk1").strip()
custom_login_url = os.getenv("LOGIN_URL")
log_dir = os.getenv("LOG_DIR", "logs")
os.makedirs(log_dir, exist_ok=True)

def fetch_email_accounts(api_key, max_accounts=9999):
    base_url = "https://server.smartlead.ai/api/v1/email-accounts/"
    accounts = []
    offset = 0
    limit = 100

    while True:
        api_url = f"{base_url}?api_key={api_key}&offset={offset}&limit={limit}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if offset == 0 and data:
                    sample_email = data[0]['from_email']
                    print(f"{Fore.GREEN}Connected to API. Sample: {sample_email}{Style.RESET_ALL}")

                accounts.extend(data)
                if len(data) < limit or len(accounts) >= max_accounts:
                    break
                offset += limit
            else:
                print(f"{Fore.RED}API error: {response.status_code}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Response: {response.text}{Style.RESET_ALL}")
                break
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Request error: {e}{Style.RESET_ALL}")
            break

    return [account['from_email'] for account in accounts]


def load_csv_emails(csv_path):
    with open(csv_path, newline='', mode='r') as file:
        reader = csv.DictReader(file)
        return [{'email': row['EmailAddress'], 'password': row['Password']} for row in reader]


def get_remaining_emails(csv_emails, existing_emails):
    return [record for record in csv_emails if record['email'] not in existing_emails]


def process_emails(remaining_emails, custom_login_url, log_file, max_retries=3):
    processed = 0

    for record in remaining_emails:
        email = record['email']
        password = record['password']
        attempts = 0

        while attempts < max_retries:
            try:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

                driver = webdriver.Chrome(options=chrome_options)
                print(f"{Fore.BLUE}Logging in: {email}{Style.RESET_ALL}")
                log_file.write(f"Logging in: {email}\n")
                driver.get(custom_login_url)
                time.sleep(5)

                driver.find_element(By.NAME, 'loginfmt').send_keys(email)
                driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
                time.sleep(5)

                driver.find_element(By.NAME, 'passwd').send_keys(password)
                driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
                time.sleep(5)

                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'KmsiCheckboxField'))).click()
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'idBtn_Back'))).click()
                except TimeoutException:
                    print(f"{Fore.YELLOW}Skipping 'No' popup.{Style.RESET_ALL}")
                    log_file.write("Skipping 'No' popup.\n")

                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'btnAskLater'))).click()
                except TimeoutException:
                    print(f"{Fore.YELLOW}Skipping 'Ask Later' popup.{Style.RESET_ALL}")
                    log_file.write("Skipping 'Ask Later' popup.\n")

                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"]'))).click()
                except TimeoutException:
                    print(f"{Fore.YELLOW}Skipping final submit.{Style.RESET_ALL}")
                    log_file.write("Skipping final submit.\n")

                print(f"{Fore.GREEN}Login success: {email}{Style.RESET_ALL}")
                log_file.write(f"Login success: {email}\n")
                processed += 1
                time.sleep(random.uniform(3, 6))  # Human-like delay
                break

            except Exception as e:
                attempts += 1
                print(f"{Fore.RED}Error ({email}) Attempt {attempts}: {e}{Style.RESET_ALL}")
                log_file.write(f"Error ({email}) Attempt {attempts}: {e}\n")
                time.sleep(2)
            finally:
                try:
                    driver.quit()
                except:
                    pass

    return processed


for filename in sorted(os.listdir(csv_folder)):
    if not filename.lower().endswith('.csv'):
        continue

    csv_path = os.path.join(csv_folder, filename)
    log_path = os.path.join(log_dir, f"{os.path.splitext(filename)[0]}_log.txt")

    print(f"{Fore.CYAN}\nProcessing file: {filename}{Style.RESET_ALL}")

    with open(log_path, 'w') as log_file:
        csv_emails = load_csv_emails(csv_path)
        print(f"{Fore.GREEN}CSV loaded. {len(csv_emails)} emails found.{Style.RESET_ALL}")
        log_file.write(f"CSV loaded. {len(csv_emails)} emails found.\n")

        max_cycles = 5
        cycle = 0

        while cycle < max_cycles:
            print(f"{Fore.CYAN}Cycle {cycle + 1}: checking Smartlead...{Style.RESET_ALL}")
            log_file.write(f"Cycle {cycle + 1}: checking Smartlead...\n")
            existing_emails = fetch_email_accounts(api_key)
            remaining = get_remaining_emails(csv_emails, existing_emails)

            if not remaining:
                print(f"{Fore.GREEN}All emails in {filename} uploaded successfully!{Style.RESET_ALL}")
                log_file.write("All emails uploaded successfully!\n")
                break

            print(f"{Fore.YELLOW}Remaining to process: {len(remaining)}{Style.RESET_ALL}")
            log_file.write(f"Remaining to process: {len(remaining)}\n")
            process_emails(remaining, custom_login_url, log_file)
            cycle += 1
            time.sleep(3)

        if cycle == max_cycles:
            print(f"{Fore.RED}Max retry cycles reached for {filename}. Some emails may still be unprocessed.{Style.RESET_ALL}")
            log_file.write("Max retry cycles reached. Some emails may still be unprocessed.\n")
