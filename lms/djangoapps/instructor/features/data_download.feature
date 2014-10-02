@shard_2
Feature: LMS.Instructor Dash Data Download
    As an instructor or course staff,
    In order to manage my class
    I want to view and download data information about my students.

    ### todos when more time can be spent on instructor dashboard
    #Scenario: Download profile information as a CSV
    #Scenario: Download student anonymized IDs as a CSV
    ## Need to figure out how to assert csvs will download without actually downloading them

    Scenario: List enrolled students' profile information
       Given I am "<Role>" for a course
       When I click "List enrolled students' profile information"
       Then I see a table of student profiles
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: List enrolled students' profile information for a large course
       Given I am "<Role>" for a very large course
       When I visit the "Data Download" tab
       Then I do not see a button to 'List enrolled students' profile information'
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
       Then I see a grade report csv file in the reports table
       Examples:
       | Role          |
       | instructor    |
       | staff         |

    Scenario: Generate & download a student profile report
       Given I am "<Role>" for a course
       When I click "Download profile information as a CSV"
       Then I see a student profile csv file in the reports table
       Examples:
       | Role          |
       | instructor    |
       | staff         |
