from lettuce import world, step
import time
from urllib import quote_plus
from selenium.common.exceptions import WebDriverException
from lettuce.django import django_url


@world.absorb
def wait(seconds):
    time.sleep(float(seconds))


@world.absorb
def visit(url):
    world.browser.visit(django_url(url))


@world.absorb
def url_equals(url):
    return world.browser.url == django_url(url)


@world.absorb
def is_css_present(css_selector):
    return world.browser.is_element_present_by_css(css_selector, wait_time=4)


@world.absorb
def css_click(css_selector):
    try:
        world.browser.find_by_css(css_selector).click()

    except WebDriverException:
        # Occassionally, MathJax or other JavaScript can cover up
        # an element  temporarily.
        # If this happens, wait a second, then try again
        time.sleep(1)
        world.browser.find_by_css(css_selector).click()


@world.absorb
def css_fill(css_selector, text):
    world.browser.find_by_css(css_selector).first.fill(text)


@world.absorb
def click_link(partial_text):
    world.browser.find_link_by_partial_text(partial_text).first.click()


@world.absorb
def css_text(css_selector):
    return world.browser.find_by_css(css_selector).first.text


@world.absorb
def css_visible(css_selector):
    return world.browser.find_by_css(css_selector).visible


@world.absorb
def save_the_html(path='/tmp'):
    u = world.browser.url
    html = world.browser.html.encode('ascii', 'ignore')
    filename = '%s.html' % quote_plus(u)
    f = open('%s/%s' % (path, filename), 'w')
    f.write(html)
    f.close
