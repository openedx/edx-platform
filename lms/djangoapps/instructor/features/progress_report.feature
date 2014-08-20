@shard_2
Feature: LMS.Instructor Dash Progress Report
    As an instructor or course staff,
    In order to manage my class
    I want to view and download data information about progress.

    Scenario: View modules progress
       Given I am "<Role>" for a course
       When I visit the "Progress Report" tab
       Then I see a tables of modules progress
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: Generate students progress
       Given I am "<Role>" for a course
       When I click "Generate Progress Report"
       Then I generate CSV to mongodb
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: Download students progress
       Given I am "<Role>" for a course
       When I click "Download Progress Report"
       Then I download CSV from mongodb
       Examples:
       | Role          |
       | instructor    |
       | staff         |
