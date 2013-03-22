from lettuce import world, step
import time
from urllib import quote_plus

@world.absorb
def wait(seconds):
    time.sleep(float(seconds))


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
def save_the_html(path='/tmp'):
    u = world.browser.url
    html = world.browser.html.encode('ascii', 'ignore')
    filename = '%s.html' % quote_plus(u)
    f = open('%s/%s' % (path, filename), 'w')
    f.write(html)
    f.close

