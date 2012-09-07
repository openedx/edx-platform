Feature: Homepage renders
  In order to get an idea of edX
  As anonymous web users
  We want to see lots of information about edX on the home page

  Scenario: We can see all the courses
    Given I visit "localhost:8000"
    #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "3.091x"
    I should see "CS50x"
    I should see "CS169.1x"
    I should see "6.002x"
    I should see "PH207x"
    I should see "CS188.1x"
    I should see "6.00x"

  Scenario: We can see the "Login" button
    Given I visit "localhost:8000"
    #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "Log In"

  Scenario: We can see the "Sign up" button
    Given I visit "localhost:8000"
    #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "Sign Up"

  Scenario: We can see the three partner institutions
    Given I visit "localhost:8000"
     #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "MITx"
    I should see "HarvardX"
    I should see "BerkeleyX"

  Scenario: We can see the static content pages
    Given I visit "localhost:8000"
    #"http://anant:agarwal@stage-edx-001.m.edx.org/"
    I should see "Find Courses"
    I should see "About"
    I should see "Blog"
    I should see "Jobs"
    I should see "Contact"
    When I click "Find Courses"
    I should be at "http://stage-edx-001.m.edx.org/courses"
    When I click "About"
    I should be at "http://stage-edx-001.m.edx.org/about"
    When I click "Jobs"
    I should be at "http://stage-edx-001.m.edx.org/jobs"
    When I click "Contact"
    I should be at "http://stage-edx-001.m.edx.org/contact"
    When I click "Blog"
    I should be at "http://blog.edx.org/"
    When I click "EDX HOME"
    I should be at "http://www.edx.org"