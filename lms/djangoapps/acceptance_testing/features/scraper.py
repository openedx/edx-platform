from lettuce import * #before, world
from selenium import *
import lettuce_webdriver.webdriver
import logging
import nose.tools
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import re

## imported from lms/djangoapps/courseware/courses.py
from collections import defaultdict
from fs.errors import ResourceNotFoundError
from functools import wraps
import logging

from path import path
from django.conf import settings
from django.http import Http404

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from static_replace import replace_urls, try_staticfiles_lookup
from courseware.access import has_access
## end import

from django.core.urlresolvers import reverse
from courseware.courses import course_image_url, get_course_about_section, get_course_by_id
from courses import *
import os.path
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
if not path in sys.path:
    sys.path.insert(1, path)
del path
from helpers import *
import codecs

@step(u'I scrape the page')
def i_scrape_the_page(step):
	sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
	articles = world.browser.find_elements_by_css_selector("li[class^='article']")
	world.browser.find_element_by_link_text("I'm a Student").click()
	try:
		WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~='active']"))
	except:
		pass

#	world.browser.find_element_by_id("averill-chab").find_element_by_tag_name("a").click()
#	try:
#		WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~='averill-chab']"))
#	except:
#		assert False, "%s failed to render" % (class_name)
#	element = world.browser.find_element_by_id("book-content")
#	contents = world.browser.execute_script("return arguments[0].innerHTML;", element)

#	f = open('averill-chab.html', 'w')
#	f.write(contents.encode('utf-8'))
#	f.close()

#	world.browser.find_element_by_id("averill-chac").find_element_by_tag_name("a").click()

#	try:
#		WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~='averill-chac']"))
#	except:
#		assert False, "%s failed to render" % (class_name)
#	element = world.browser.find_element_by_id("book-content")
#	contents = world.browser.execute_script("return arguments[0].innerHTML;", element)

#	f = open('averill-chac.html', 'w')
#	f.write(contents.encode('utf-8'))
#	f.close()
	
#	world.browser.find_element_by_id("averill-chde").find_element_by_tag_name("a").click()
#	try:
#		WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~='averill-chde']"))
#	except:
#		assert False, "%s failed to render" % (class_name)
#	element = world.browser.find_element_by_id("book-content")
#	contents = world.browser.execute_script("return arguments[0].innerHTML;", element)

#	f = open('averill-chde.html', 'w')
#	f.write(contents.encode('utf-8'))
#	f.close()

#	world.browser.find_element_by_id("averill_1.0-ch00pref").find_element_by_tag_name("a").click()
#	try:
#		WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~='averill_1.0-ch00pref']"))
#	except:
#		assert False, "%s failed to render" % (class_name)
#	element = world.browser.find_element_by_id("book-content")
#	contents = world.browser.execute_script("return arguments[0].innerHTML;", element)
		
#	f = open('averill_1.0-ch00pref.html', 'w')
#	f.write(contents.encode('utf-8'))
#	f.close()	

	chapters = world.browser.find_elements_by_css_selector("li[class^='chapter']")

	#i = 0
	j = 3
	l = 1
	
	while j <= len(chapters):
		if j < 10:
			world.browser.find_element_by_id("averill_1.0-ch0"+str(j)).find_element_by_tag_name("a").click()
		
		elif j >= 10:
			world.browser.find_element_by_id("averill_1.0-ch"+str(j)).find_element_by_tag_name("a").click()
		
		try:
			WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id^='averill_1.0-ch0'] > foo"))
		except:
			pass

		element = world.browser.find_element_by_id("book-content")
		contents = world.browser.execute_script("return arguments[0].innerHTML;", element)
		f = open("averill_1.0-ch0"+str(j)+'.html', 'w')
		f.write(contents.encode('utf-8'))
		f.close()
		
		sections = world.browser.find_elements_by_css_selector("li[class='chapter active'] > ul > li")
		j+=1
		k = 1
		while k <= len(sections):
			if k < 10:
				if j < 10:
					world.browser.find_element_by_id("averill_1.0-ch0"+str(j-1)+"_s0"+str(k)).find_element_by_tag_name("a").click()
				if j > 10:
					world.browser.find_element_by_id("averill_1.0-ch"+str(j-1)+"_s0"+str(k)).find_element_by_tag_name("a").click()
			elif k >= 10:
				if j < 10:
					world.browser.find_element_by_id("averill_1.0-ch0"+str(j-1)+"_s"+str(k)).find_element_by_tag_name("a").click()
				if j > 10:
					world.browser.find_element_by_id("averill_1.0-ch"+str(j-1)+"_s"+str(k)).find_element_by_tag_name("a").click()
			try:
				WebDriverWait(world.browser, 8).until(lambda driver : driver.find_element_by_css_selector("div[id^='averill_1.0-ch'] > foo"))
			except:
				pass
			element = world.browser.find_element_by_id("book-content")
			contents = world.browser.execute_script("return arguments[0].innerHTML;", element)
			f = open("averill_1.0-ch0"+str(j-1)+"_s0"+str(k)+'.html', 'w')
			f.write(contents.encode('utf-8'))
			f.close()
			k += 1
		
		

	appendixes = world.browser.find_elements_by_css_selector("li[class^='appendix']")
	
	while l <= len(appendixes):
		#world.browser.find_element_by_css_selector("li[class^='appendix']:nth-of-type("+str(k+1)+")").click()
		
		world.browser.find_element_by_css_selector("li[class~='appendix']:nth-of-type("+str(k)+")").find_element_by_tag_name("a").click()
		named_element = world.browser.find_element_by_css_selector("div[class~='active']")
		
		try:
			WebDriverWait(world.browser, 3).until(lambda driver : driver.find_element_by_css_selector("div[id~=''"+named_element.get_attribute("id")+"'']"))
		except:
			assert False, "%s failed to render" % (class_name)
		named_element = world.browser.find_element_by_css_selector("div[class~='active']")
		
		element = world.browser.find_element_by_id("book-content")
		contents = world.browser.execute_script("return arguments[0].innerHTML;", element)
		f = open(named_element.get_attribute("id")+'.html', 'w')
		f.write(contents.encode('utf-8'))
		f.close()

		l += 1
		

