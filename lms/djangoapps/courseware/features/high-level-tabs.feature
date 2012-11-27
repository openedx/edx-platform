Feature: All the high level tabs should work
  In order to preview the courseware
  As a student
  I want to navigate through the high level tabs

# Note this didn't work as a scenario outline because
# before each scenario was not flushing the database
# TODO: break this apart so that if one fails the others
# will still run
  Scenario: A student can see all tabs of the course
    Given I am registered for a course
    And I log in
    And I click on View Courseware
    When I click on the "Courseware" tab
    Then the page title should be "6.002x Courseware"
    When I click on the "Course Info" tab
    Then the page title should be "6.002x Course Info"
    When I click on the "Textbook" tab
    Then the page title should be "6.002x Textbook"
    When I click on the "Wiki" tab
    Then the page title should be "6.002x | edX Wiki"
    When I click on the "Progress" tab
    Then the page title should be "6.002x Progress"
