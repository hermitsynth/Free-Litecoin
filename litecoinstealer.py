# TESSERACT OCR
import ddddocr
import random
import os
import sys
import pathlib
from typing import Union, Dict, Any
from selenium import webdriver
import selenium.webdriver
import selenium.webdriver.common.by as By
import selenium.webdriver.support.ui as WebDriverWait
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
# add to path

def ocr_core(filename):
    ocr = ddddocr.DdddOcr()
    with open(filename, 'rb') as f:
        img_bytes = f.read()
    text = ocr.classification(img_bytes, True)
    return text

import time

def random_email():
    import random
    import string
    domains = ["example.com", "test.com", "demo.com"]
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{name}@{domain}"

while True:
    with open("proxylist.txt", "r") as f:
        proxies = f.read().splitlines()
    proxy = random.choice(proxies)


    webdriver.DesiredCapabilities.CHROME['proxy'] = {
    "httpProxy": proxy,
    "proxyType": "manual",
    }
    driver = webdriver.Chrome()
    print(f"Using proxy: {proxy}")
    driver.set_window_size(1920, 1080)
    driver.get("https://free-litecoin.com/login")
    driver.find_element("id", "register").click()
    captcha_element = driver.find_element("id", "captchaimgregister")
    captcha_element.screenshot("captcha.png")
    captcha_text = ocr_core("captcha.png")
    print("Captcha text:", captcha_text)
    email = random_email()
    driver.find_element("name", "emailreg").send_keys(email)
    driver.find_element("name", "hesloreg").send_keys("password123!672")
    driver.find_element("name", "referer").clear()
    driver.find_element("name", "referer").send_keys("7228808")
    driver.find_element("name", "adresa").send_keys("ltc1qpfyd2q4awsec5m7jxxapx5uznldwrxacttz37c")
    driver.find_element("name", "captcha_register").send_keys(captcha_text.upper())
    driver.find_element("id", "signupbutton").click()
    time.sleep(2)  # wait for the registration to process
    try:
        messegereg = driver.find_element("id", "messegereg").text
        if messegereg.lower().startswith("in"):
            print("Captcha failed, retrying...")
            driver.quit()
            continue
    except:
        pass
    time.sleep(8)
    if driver.current_url == "https://free-litecoin.com/":
        print("Registration successful!")

        with open("accounts.txt", "a") as f:
            f.write(f"{captcha_text.upper()} - {email} - password123!672\n")

    else:
        print("Registration failed, retrying...")
        driver.quit()
        continue

    money = driver.find_element("id", "money").text
    print(f"Current balance: {money}")
    moneyfloat = float(money.replace(" LTC", ""))
    while True:
        # roll
        driver.find_element("id", "captchaimg").screenshot("captcha_roll.png")
        captcha_text_roll = ocr_core("captcha_roll.png")
        print("Captcha text for roll:", captcha_text_roll)  
        driver.find_element("id", "captchainput").clear()
        driver.find_element("id", "captchainput").send_keys(captcha_text_roll.upper())
        driver.find_element("id", "roll").click()

        time.sleep(5)  # wait for the roll to complete
        result = driver.find_element("id", "numberroll").text
        if not result.isdigit():
            print(f"Failed to read roll result: '{result}'. Retrying...")
            time.sleep(2)
            continue
        if int(result) >= 9998:
            print(f"Rolled {result}!")
            with open("high_rolls.txt", "a") as f:
                f.write(f"{email} rolled {result}\n")
        else:
            print(f"Rolled {result}, not high enough.")
        
        # check if we gained money
        new_money = driver.find_element("id", "money").text
        new_moneyfloat = float(new_money.replace(" LTC", ""))
        if new_moneyfloat > moneyfloat:
            print(f"Gained money! New balance: {new_money}")
            with open("gains.txt", "a") as f:
                f.write(f"{email} gained money! New balance: {new_money}\n")
            moneyfloat = new_moneyfloat
            break
        else:
            print(f"No gain. Current balance: {new_money}")
        time.sleep(1)

    driver.quit()