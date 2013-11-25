@shard_2
Feature: LMS.Instructor Dash Data Download
    As an instructor or course staff,
    In order to manage my class
    I want to view and download data information about my students.

    ### todos when more time can be spent on instructor dashboard
    #Scenario: Download profile information as a CSV
    #Scenario: Download student anonymized IDs as a CSV

    Scenario: List enrolled students' profile information
       Given I am "<Role>" for a course
       When I click "List enrolled students' profile information"
       Then I see a table of student profiles
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: View the grading configuration
       Given I am "<Role>" for a course
       When I click "Grading Configuration"
       Then I see the grading configuration for the course
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: Generate & download a grade report
       Given I am "<Role>" for a course
       When I click "Generate Grade Report"
       Then I see a csv file in the grade reports table
       Examples:
       | Role          |
       | instructor    |
       | staff         |
