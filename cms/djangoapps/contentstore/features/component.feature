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
           | E-text Written in LaTeX |
       Then I see HTML components in this order:
           | Component               |
           | Text                    |
           | Announcement            |
           | E-text Written in LaTeX |

    Scenario: I can add Common Problem components
       Given I am in Studio editing a new unit
       When I add this type of Problem component:
           | Component            |
           | Blank Common Problem |
           | Dropdown             |
           | Multiple Choice      |
           | Numerical Input      |
           | Text Input           |
       Then I see Problem components in this order:
           | Component            |
           | Blank Common Problem |
           | Dropdown             |
           | Multiple Choice      |
           | Numerical Input      |
           | Text Input           |

    Scenario: I can add Advanced Problem components
       Given I am in Studio editing a new unit
       When I add this type of Advanced Problem component:
           | Component                     |
           | Blank Advanced Problem        |
           | Circuit Schematic Builder     |
           | Custom Python-Evaluated Input |
           | Drag and Drop                 |
           | Image Mapped Input            |
           | Math Expression Input         |
           | Problem Written in LaTeX      |
           | Problem with Adaptive Hint    |
       Then I see Problem components in this order:
           | Component                     |
           | Blank Advanced Problem        |
           | Circuit Schematic Builder     |
           | Custom Python-Evaluated Input |
           | Drag and Drop                 |
           | Image Mapped Input            |
           | Math Expression Input         |
           | Problem Written in LaTeX      |
           | Problem with Adaptive Hint    |

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
