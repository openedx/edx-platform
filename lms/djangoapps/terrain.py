from lettuce import before, after, world
from selenium import webdriver
import lettuce_webdriver.webdriver
from os import getenv

@before.all
def setup_browser():
  world.browser = webdriver.Firefox()
  world.dev_url = getenv("EDX_DEV_URL")
  world.sandbox_url = getenv("EDX_SANDBOX_URL")
  world.stage_url = getenv("EDX_STAGE_URL")
  world.production_url = getenv("EDX_PRODUCTION_URL")

@after.all
def teardown_browser(total):
  world.browser.quit()