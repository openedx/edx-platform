from lettuce import before, after, world
from selenium import webdriver
import lettuce_webdriver.webdriver
from os import getenv

@before.all
def setup_browser():
  world.browser = webdriver.Firefox()

#@after.all
#def teardown_browser(total):
#  world.browser.quit()