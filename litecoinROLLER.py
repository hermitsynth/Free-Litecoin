import subprocess
import sys
import base64
import os
import string
import random
import traceback
import time
import datetime
import threading
import math

def pip_install(*packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import ddddocr
except ImportError:
    print("📦  Installing ddddocr...")
    pip_install("ddddocr")
    import ddddocr

try:
    from PIL import Image
except ImportError:
    print("📦  Installing Pillow...")
    pip_install("Pillow")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load sensitive/config from environment
PROXY_LIST_FILE = os.getenv("PROXY_LIST_FILE", "proxylist.txt")
ACCOUNTS_FILE   = os.getenv("ACCOUNTS_FILE", os.path.join(os.path.dirname(__file__), "accounts.txt"))
WINS_FILE       = os.getenv("HIGH_ROLLS_FILE", os.path.join(os.path.dirname(__file__), "high_rolls.txt"))
WIN_THRESHOLD   = int(os.getenv("WIN_THRESHOLD", "9998"))
SITE_URL        = os.getenv("TARGET_URL", "https://free-litecoin.com/login")
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", "10"))
ROLL_INTERVAL   = int(os.getenv("ROLL_INTERVAL", str(70 * 60)))  # seconds

print_lock          = threading.Lock()
wins_lock           = threading.Lock()
first_roll_lock     = threading.Lock()
first_roll_time_ref = [None]

def tprint(thread_id, *args):
    with print_lock:
        print(f"[T{thread_id}]", *args)

_ocr_local = threading.local()
def get_ocr():
    if not hasattr(_ocr_local, "ocr"):
        _ocr_local.ocr = ddddocr.DdddOcr(show_ad=False)
    return _ocr_local.ocr

def solve_captcha_from_id(driver, element_id: str, thread_id: int) -> str:
    el        = driver.find_element(By.ID, element_id)
    src       = el.get_attribute("src")
    img_bytes = base64.b64decode(src.split(",", 1)[1])
    save_path = os.path.join(os.path.dirname(__file__), f"captcha{thread_id}.png")
    with open(save_path, "wb") as f:
        f.write(img_bytes)
    result = get_ocr().classification(img_bytes)
    return "".join(c for c in result.strip() if c.isalnum()).upper()

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"❌  {ACCOUNTS_FILE} not found!")
        return []
    accounts = []
    with open(ACCOUNTS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(" - ")]
            if len(parts) == 3:
                _, email, password = parts
                accounts.append((email, password))
            else:
                print(f"  ⚠️  Skipping unrecognised line: {line}")
    print(f"📋  Loaded {len(accounts)} accounts from {ACCOUNTS_FILE}")
    return accounts

def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)

def do_login(driver, wait, email, password, thread_id):
    attempt = 0
    while True:
        attempt += 1
        tprint(thread_id, f"🔁  Login captcha attempt {attempt}")

        for field_id, value in [("usr", email), ("usr2", password)]:
            el = driver.find_element(By.ID, field_id)
            driver.execute_script(
                "arguments[0].value = arguments[1]; "
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true})); "
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el, value
            )

        answer = solve_captcha_from_id(driver, "captchaimglogin", thread_id)
        tprint(thread_id, f"  🔍  OCR: '{answer}'")

        captcha_input = driver.find_element(By.CSS_SELECTOR, "input[name='captcha_login']")
        driver.execute_script(
            "arguments[0].value = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
            captcha_input, answer
        )

        driver.find_element(By.ID, "loginbutton").click()

        try:
            WebDriverWait(driver, 5).until(
                lambda d: "/login" not in d.current_url and "free-litecoin.com" in d.current_url
            )
            tprint(thread_id, "✅  Login successful!")
            return True
        except TimeoutException:
            try:
                body = driver.find_element(By.TAG_NAME, "body").text.lower()
                if "incorrect" in body or "invalid" in body or "wrong" in body:
                    tprint(thread_id, "❌  Wrong captcha or bad credentials, retrying...")
                else:
                    tprint(thread_id, "❌  No redirect yet, retrying...")
            except Exception:
                tprint(thread_id, "❌  No redirect yet, retrying...")
            driver.get(SITE_URL)
            try:
                wait.until(EC.presence_of_element_located((By.ID, "captchaimglogin")))
            except TimeoutException:
                pass

def do_roll(driver, wait, thread_id):
    time.sleep(3)
    tprint(thread_id, "✅  Proceeding to roll.")
    attempt = 0
    while True:
        attempt += 1
        tprint(thread_id, f"🔁  Roll captcha attempt {attempt}")
        answer = solve_captcha_from_id(driver, "captchaimg", thread_id)
        tprint(thread_id, f"  🔍  OCR: '{answer}'")
        captcha_input = driver.find_element(By.ID, "captchainput")
        captcha_input.clear()
        captcha_input.send_keys(answer)
        driver.find_element(By.ID, "roll").click()
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.find_element(By.ID, "numberroll").text.strip().isdigit()
            )
            result_text = driver.find_element(By.ID, "numberroll").text.strip()
            tprint(thread_id, f"🎲  Rolled: {result_text}")
            return int(result_text)
        except TimeoutException:
            tprint(thread_id, "❌  No result — captcha likely wrong, retrying...")

def save_win(email, password, number):
    with wins_lock:
        with open(WINS_FILE, "a") as f:
            f.write(f"{email} : {password}  (rolled {number})\n")

def run_chunk(chunk, thread_id):
    total = len(chunk)
    for i, (email, password) in enumerate(chunk, 1):
        tprint(thread_id, f"{'='*45}")
        tprint(thread_id, f"👤  Account {i}/{total}: {email}")
        tprint(thread_id, f"{'='*45}")
        driver = make_driver()
        wait   = WebDriverWait(driver, 15)
        try:
            driver.get(SITE_URL)
            wait.until(EC.presence_of_element_located((By.ID, "captchaimglogin")))
            if do_login(driver, wait, email, password, thread_id):
                result = do_roll(driver, wait, thread_id)
                if result is not None:
                    with first_roll_lock:
                        if first_roll_time_ref[0] is None:
                            first_roll_time_ref[0] = datetime.datetime.now()
                            tprint(thread_id, f"🕐  First roll recorded at {first_roll_time_ref[0].strftime('%H:%M:%S')}")
                    if result >= WIN_THRESHOLD:
                        save_win(email, password, result)
                        tprint(thread_id, f"🏆  WIN saved! Rolled {result}")
                    else:
                        tprint(thread_id, f"(rolled {result} — below threshold {WIN_THRESHOLD})")
        except Exception as e:
            tprint(thread_id, f"⚠️  Error: {str(e)[:120]}")
            traceback.print_exc()
        finally:
            driver.quit()
            tprint(thread_id, "🔒  Browser closed.")
    tprint(thread_id, f"✅  Chunk done ({total} accounts).")

def run_once(accounts):
    with first_roll_lock:
        first_roll_time_ref[0] = None
    chunks = [accounts[i:i + CHUNK_SIZE] for i in range(0, len(accounts), CHUNK_SIZE)]
    n      = len(chunks)
    print(f"\n🧵  Spawning {n} thread(s) — {CHUNK_SIZE} accounts per chunk ({len(accounts)} accounts total)")
    threads = []
    for thread_id, chunk in enumerate(chunks):
        t = threading.Thread(target=run_chunk, args=(chunk, thread_id), daemon=True)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    print("\n✅  All threads finished.")
    return first_roll_time_ref[0]

def main():
    accounts = load_accounts()
    if not accounts:
        print("No accounts to process. Exiting.")
        return
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'#'*55}")
        print(f"🔄  Starting cycle #{cycle}  —  {datetime.datetime.now().strftime('%H:%M:%S')}")
        print(f"{'#'*55}")
        first_roll_time = run_once(accounts)
        if first_roll_time is None:
            print("⚠️  No rolls completed this cycle — retrying in 60 seconds.")
            time.sleep(60)
            continue
        elapsed   = (datetime.datetime.now() - first_roll_time).total_seconds()
        wait_secs = ROLL_INTERVAL - elapsed
        if wait_secs > 0:
            resume_at = datetime.datetime.now() + datetime.timedelta(seconds=wait_secs)
            print(f"\n⏳  Cycle #{cycle} done. Waiting {wait_secs/60:.1f} min before next cycle.")
            print(f"    ▶  Next cycle starts at {resume_at.strftime('%H:%M:%S')}")
            time.sleep(wait_secs)
        else:
            print(f"\n⚡  Cycle #{cycle} took longer than {ROLL_INTERVAL/60:.0f} min — starting next cycle immediately.")

if __name__ == "__main__":
    main()
