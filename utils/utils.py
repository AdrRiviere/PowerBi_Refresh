import os
import platform
import time

import boto3
import prefect as pf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@pf.task(name="[Selenium] Get drivers paths")
def get_paths():
    if platform.system() == "Windows":
        path_driver = (
                os.path.dirname(os.path.realpath(__file__))
                + "/../drivers/chromedriver.exe"
        )
        path_chrome = (
                os.path.dirname(os.path.realpath(__file__))
                + "7../drivers/chrome-win64/chrome.exe"
        )
    else:
        path_driver = (
                os.path.dirname(os.path.realpath(__file__))
                + "/../drivers/chromedriver-linux64/chromedriver"
        )
        path_chrome = (
                os.path.dirname(os.path.realpath(__file__))
                + "/../drivers/chrome-linux64/chrome"
        )
    path_downloads = "./"
    print("path_driver : ", path_driver)
    print("path_chrome : ", path_chrome)
    print("path_downloads : ", path_downloads)
    return path_driver, path_chrome, path_downloads


@pf.task(name="[Selenium] Create drivers")
def get_driver(url, path_driver, path_chrome, path_downloads, headless=True):
    options = Options()
    options.binary_location = path_chrome
    width = 1920
    height = 1080
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--no-sandbox")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("download.default_directory=./data")
    options.add_argument("--log-level=3")
    options.add_argument("enable-automation")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("disable-quic")
    options.add_argument('--disable-blink-features="BlockCredentialedSubresources"')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")

    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    prefs = {"download.default_directory": path_downloads}

    capabilities = DesiredCapabilities().CHROME
    options.add_experimental_option("prefs", prefs)
    capabilities.update(options.to_capabilities())
    service = webdriver.ChromeService(executable_path=path_driver)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    time.sleep(5)
    return driver


@pf.task(name="[Power BI] Connection")
def connect(driver, user, passwd):
    # connection :
    # find email area using xpath
    email = driver.find_element(By.XPATH, "/html/body/div/div[2]/div[2]/div/div[1]/div[2]/input")
    # send power bi login user
    email.send_keys(user)
    # driver.save_screenshot("screenshot_user.png")
    # find submit button
    submit = driver.find_element(By.ID, "submitBtn")
    # click for submit button
    submit.click()
    time.sleep(5)
    # find element for password :
    pwd = driver.find_element(
        By.XPATH,
        """/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div/
        div[3]/div/div[2]/div/div[3]/div/div[2]/input""",
    )
    # send power bi login user
    pwd.send_keys(passwd)
    # driver.save_screenshot("screenshot_pwd.png")
    # find submit button
    pwd_submit = driver.find_element(
        By.XPATH,
        """/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div/div[3]/
        div/div[2]/div/div[5]/div/div/div/div/input""",
    )
    # click for submit button
    pwd_submit.click()
    time.sleep(5)
    try:
        stay_signed = driver.find_element(
            By.XPATH,
            """/html/body/div/form/div/div/div[2]/div[1]/div/div/div/div/div/div[3]/div/div[2]/div/
            div[3]/div[2]/div/div/div[2]/input""",
        )
        # click for submit button
        stay_signed.click()
        time.sleep(5)
    except ValueError:
        print("no stay signed")
    time.sleep(10)
    # driver.save_screenshot("screenshot_signed_in.png")
    return driver


@pf.task(name="[Power BI] Create Embed Report")
def create_embed_report(driver, name_screenshot):
    # Click File
    time.sleep(10)
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located((By.CLASS_NAME, "dropDownIcon"))
    )
    element[0].click()

    # Click Embed
    time.sleep(10)
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located((By.CLASS_NAME, "chevronRightIcon"))
    )
    element[0].click()

    time.sleep(10)
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "[data-testid='appbar-embed-report-website-or-portal-btn']")
        )
    )
    element[0].click()

    time.sleep(10)
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "[data-testid='secure-embed-link-input']")
        )
    )
    value = element[0].get_attribute("value")
    embed_report_url = value + "&navContentPaneEnabled=false"

    driver.get(embed_report_url)
    time.sleep(30)

    # Full Screen + Screenshot
    action = ActionChains(driver)
    action.key_down(Keys.CONTROL).send_keys("F").key_up(Keys.CONTROL).perform()
    time.sleep(30)

    driver.save_screenshot(name_screenshot + ".png")

    return driver


@pf.task(name="[Selenium] Close driver")
def close(driver):
    driver.stop_client()
    driver.close()
    driver.quit()


@pf.task(name="[AWS] Export Screenshot on AWS")
def export_screenshot_aws(region_name, aws_access_key_id, aws_secret_access_key, name_screenshot):
    s3 = boto3.client(
        "s3",
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    bucket_name = "flowbank-dashboard"
    object_key = name_screenshot + ".png"

    with open(name_screenshot + ".png", "rb") as f:
        screenshot_data = f.read()

    s3.put_object(Bucket=bucket_name, Key=object_key, Body=screenshot_data, ContentType="image/png")
    os.remove(name_screenshot + ".png")
