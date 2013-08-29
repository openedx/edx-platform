Feature: Component Adding
    As a course author, I want to be able to add a wide variety of components

    @skip
    Scenario: I can add components
        Given I have opened a new course in studio
        And I am editing a new unit
        When I add the following components:
            | Component    |
            | Discussion   |
            | Blank HTML   |
            | LaTex        |
            | Blank Problem|
            | Dropdown     |
            | Multi Choice |
            | Numerical    |
            | Text Input   |
            | Advanced     |
            | Circuit      |
            | Custom Python|
            | Image Mapped |
            | Math Input   |
            | Problem LaTex|
            | Adaptive Hint|
            | Video        |
        Then I see the following components:
            | Component    |
            | Discussion   |
            | Blank HTML   |
            | LaTex        |
            | Blank Problem|
            | Dropdown     |
            | Multi Choice |
            | Numerical    |
            | Text Input   |
            | Advanced     |
            | Circuit      |
            | Custom Python|
            | Image Mapped |
            | Math Input   |
            | Problem LaTex|
            | Adaptive Hint|
            | Video        |

    @skip
    Scenario: I can delete Components
        Given I have opened a new course in studio
        And I am editing a new unit
        And I add the following components:
            | Component    |
            | Discussion   |
            | Blank HTML   |
            | LaTex        |
            | Blank Problem|
            | Dropdown     |
            | Multi Choice |
            | Numerical    |
            | Text Input   |
            | Advanced     |
            | Circuit      |
            | Custom Python|
            | Image Mapped |
            | Math Input   |
            | Problem LaTex|
            | Adaptive Hint|
            | Video        |
        When I will confirm all alerts
        And I delete all components
        Then I see no components

    Scenario: I see a prompt on delete
        Given I have opened a new course in studio
        And I am editing a new unit
        And I add the following components:
            | Component    |
            | Discussion   |
       And I delete a component
       Then I am shown a prompt

   Scenario: I see a notification on save
        Given I have opened a new course in studio
        And I am editing a new unit
        And I add the following components:
            | Component    |
            | Discussion   |
        And I edit and save a component
        Then I am shown a notification
