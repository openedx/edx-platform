Feature: There are courses on the homepage
  In order to compared rendered content to the database
  As an acceptance test
  I want to count all the chapters, sections, and tabs for each course

  Scenario: Navigate through course MITx/6.002x/2012_Fall
    Given I am registered for course "MITx/6.002x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  # Scenario: Navigate through course edX/edx101/edX_Studio_Reference
  #   Given I am registered for course "edX/edx101/edX_Studio_Reference"
  #   And I log in
  #   Then I verify all the content of each course

  # Scenario: Navigate through course BerkeleyX/CS169.1x/2012_Fall
  #   Given I am registered for course "BerkeleyX/CS169.1x/2012_Fall"
  #   And I log in
  #   Then I verify all the content of each course