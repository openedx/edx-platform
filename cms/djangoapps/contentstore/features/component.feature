@shard_1
Feature: CMS.Component Adding
    As a course author, I want to be able to add a wide variety of components

    Scenario: I can add single step components
       Given I am in Studio editing a new unit
       When I add this type of single step component:
           | Component    |
           | Discussion   |
           | Video        |
       Then I see this type of single step component:
           | Component    |
           | Discussion   |
           | Video        |

    Scenario: I can add HTML components
       Given I am in Studio editing a new unit
       When I add this type of HTML component:
           | Component               |
           | Text                    |
           | Announcement            |
           | Zooming Image Tool      |
           | Raw HTML                |
       Then I see HTML components in this order:
           | Component               |
           | Text                    |
           | Announcement            |
           | Zooming Image Tool      |
           | Raw HTML                |

    Scenario: I can add Latex HTML components
       Given I am in Studio editing a new unit
       Given I have enabled latex compiler
       When I add this type of HTML component:
           | Component               |
           | E-text Written in LaTeX |
       Then I see HTML components in this order:
           | Component               |
           | E-text Written in LaTeX |

    Scenario: I can add Common Problem components
       Given I am in Studio editing a new unit
       When I add this type of Problem component:
           | Component            |
           | Blank Common Problem |
           | Checkboxes           |
           | Dropdown             |
           | Multiple Choice      |
           | Numerical Input      |
           | Text Input           |
       Then I see Problem components in this order:
           | Component            |
           | Blank Common Problem |
           | Checkboxes           |
           | Dropdown             |
           | Multiple Choice      |
           | Numerical Input      |
           | Text Input           |

    Scenario Outline: I can add Advanced Problem components
       Given I am in Studio editing a new unit
       When I add a "<Component>" "Advanced Problem" component
       Then I see a "<Component>" Problem component
       # Flush out the database before the next example executes
       And I reset the database

    Examples:
           | Component                     |
           | Blank Advanced Problem        |
           | Circuit Schematic Builder     |
           | Custom Python-Evaluated Input |
           | Drag and Drop                 |
           | Image Mapped Input            |
           | Math Expression Input         |
           | Problem with Adaptive Hint    |


# Disabled 1/21/14 due to flakiness seen in master
#    Scenario: I can add Advanced Latex Problem components
#       Given I am in Studio editing a new unit
#       Given I have enabled latex compiler
#       When I add a "<Component>" "Advanced Problem" component
#       Then I see a "<Component>" Problem component
#       # Flush out the database before the next example executes
#       And I reset the database

#    Examples:
#           | Component                     |
#           | Problem Written in LaTeX      |
#           | Problem with Adaptive Hint in Latex  |

    Scenario: I see a prompt on delete
        Given I am in Studio editing a new unit
        And I add a "Discussion" "single step" component
        And I delete a component
        Then I am shown a prompt

    Scenario: I can delete Components
        Given I am in Studio editing a new unit
        And I add a "Discussion" "single step" component
        And I add a "Text" "HTML" component
        And I add a "Blank Common Problem" "Problem" component
        And I add a "Blank Advanced Problem" "Advanced Problem" component
        And I delete all components
        Then I see no components

    Scenario: I can duplicate a component
        Given I am in Studio editing a new unit
        And I add a "Blank Common Problem" "Problem" component
        And I add a "Multiple Choice" "Problem" component
        And I duplicate the first component
        Then I see a Problem component with display name "Duplicate of 'Blank Common Problem'" in position "1"
        And I reload the page
        Then I see a Problem component with display name "Blank Common Problem" in position "0"
        And I see a Problem component with display name "Duplicate of 'Blank Common Problem'" in position "1"
        And I see a Problem component with display name "Multiple Choice" in position "2"

    Scenario: I can set the display name of a component
        Given I am in Studio editing a new unit
        When I add a "Text" "HTML" component
        Then I see the display name is "Text"
        When I change the display name to "I'm the Cuddliest!"
        Then I see the display name is "I'm the Cuddliest!"

    Scenario: If a component has no display name, the category is displayed
        Given I am in Studio editing a new unit
        When I add a "Blank Advanced Problem" "Advanced Problem" component
        Then I see the display name is "Blank Advanced Problem"
        When I change the display name to ""
        Then I see the display name is "problem"
        When I unset the display name
        Then I see the display name is "Blank Advanced Problem"
