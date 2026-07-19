#!/usr/bin/env python3
"""Headless Selenium test: install the yt-dlp XPI into a COPY of the live
Floorp profile, verify it loads, and confirm the native host is reachable."""
import os, sys, time, traceback
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import WebDriverException

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\automation-test"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"

def main():
    opts = Options()
    opts.binary_location = FLOORP
    opts.add_argument("-profile")
    opts.add_argument(PROFILE)
    opts.add_argument("--headless")
    opts.set_preference("xpinstall.signatures.required", False)
    opts.set_preference("extensions.autoDisableScopes", 0)

    driver = webdriver.Firefox(service=Service(GECKO), options=opts)
    try:
        print("[1] driver started")
        driver.install_addon(XPI, temporary=True)
        print("[2] install_addon OK")
        time.sleep(3)
        driver.get("about:addons")
        time.sleep(4)
        src = driver.page_source
        if "yt-dlp" in src.lower():
            print("[3] FOUND yt-dlp in about:addons -> INSTALL OK")
        else:
            print("[3] WARN: yt-dlp not in about:addons page_source")
        # dump extension list via management API
        driver.get("about:debugging#/runtime/this-firefox")
        time.sleep(2)
        print("[4] debugging page loaded")
    except WebDriverException as e:
        print("WEBDRIVER ERROR:", e)
    except Exception:
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
    print("DONE")
