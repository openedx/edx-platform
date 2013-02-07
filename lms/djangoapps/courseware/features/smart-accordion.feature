# Here are all the courses for Fall 2012
#  MITx/3.091x/2012_Fall
#  MITx/6.002x/2012_Fall
#  MITx/6.00x/2012_Fall
#  HarvardX/CS50x/2012 (we will not be testing this, as it is anomolistic)
#  HarvardX/PH207x/2012_Fall
#  BerkeleyX/CS169.1x/2012_Fall
#  BerkeleyX/CS169.2x/2012_Fall
#  BerkeleyX/CS184.1x/2012_Fall

#You can load the courses into your data directory with these cmds:
#  git clone https://github.com/MITx/3.091x.git
#  git clone https://github.com/MITx/6.00x.git
#  git clone https://github.com/MITx/content-mit-6002x.git
#  git clone https://github.com/MITx/content-mit-6002x.git
#  git clone https://github.com/MITx/content-harvard-id270x.git
#  git clone https://github.com/MITx/content-berkeley-cs169x.git
#  git clone https://github.com/MITx/content-berkeley-cs169.2x.git
#  git clone https://github.com/MITx/content-berkeley-cs184x.git

Feature: There are courses on the homepage
  In order to compared rendered content to the database
  As an acceptance test
  I want to count all the chapters, sections, and tabs for each course

  Scenario: Navigate through course MITx/3.091x/2012_Fall
    Given I am registered for course "MITx/3.091x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course MITx/6.002x/2012_Fall
    Given I am registered for course "MITx/6.002x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course MITx/6.00x/2012_Fall
    Given I am registered for course "MITx/6.00x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course HarvardX/PH207x/2012_Fall
    Given I am registered for course "HarvardX/PH207x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course BerkeleyX/CS169.1x/2012_Fall
    Given I am registered for course "BerkeleyX/CS169.1x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course BerkeleyX/CS169.2x/2012_Fall
    Given I am registered for course "BerkeleyX/CS169.2x/2012_Fall"
    And I log in
    Then I verify all the content of each course

  Scenario: Navigate through course BerkeleyX/CS184.1x/2012_Fall
    Given I am registered for course "BerkeleyX/CS184.1x/2012_Fall"
    And I log in
    Then I verify all the content of each course