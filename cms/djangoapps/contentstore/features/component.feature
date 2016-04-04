@shard_1
Feature: CMS.Component Adding
    As a course author, I want to be able to add a wide variety of components

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
