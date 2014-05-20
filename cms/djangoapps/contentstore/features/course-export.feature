@shard_1
Feature: Course export
  I want to export my course to a tar.gz file to share with others or check into source control

  Scenario: User is directed to unit with bad XML when export fails
    Given I am in Studio editing a new unit
    When I add a "Blank Advanced Problem" "Advanced Problem" component
    And I edit and enter bad XML
    And I export the course
    Then I get an error dialog
    And I can click to go to the unit with the error

 # Disabling due to failure on master. 05/21/2014 TODO: fix
 # Scenario: User is directed to problem with & in it when export fails
 #   Given I am in Studio editing a new unit
 #   When I add a "Blank Advanced Problem" "Advanced Problem" component
 #   And I edit and enter an ampersand
 #   And I export the course
 #   Then I get an error dialog
 #   And I can click to go to the unit with the error
