@shard_1
Feature: CMS.Help
    As a course author, I am able to access online help

    Scenario: Users can access online help on course listing page
        Given There are no courses
        And I am logged into Studio
        Then I should see online help for "get_started"


    Scenario: Users can access online help within a course
        Given I have opened a new course in Studio

        And I click the course link in Studio Home
        Then I should see online help for "outline"

        And I go to the course updates page
        Then I should see online help for "updates"

        And I go to the pages page
        Then I should see online help for "pages"

        And I go to the files and uploads page
        Then I should see online help for "files"

        And I go to the textbooks page
        Then I should see online help for "textbooks"

        And I select Schedule and Details
        Then I should see online help for "setting_up"

        And I am viewing the grading settings
        Then I should see online help for "grading"

        And I am viewing the course team settings
        Then I should see online help for "course-team"

        And I select the Advanced Settings
        Then I should see online help for "index"

        And I select Checklists from the Tools menu
        Then I should see online help for "checklist"

        And I go to the import page
        Then I should see online help for "import"

        And I go to the export page
        Then I should see online help for "export"


    Scenario: Users can access online help on the unit page
        Given I am in Studio editing a new unit
        Then I should see online help for "units"
