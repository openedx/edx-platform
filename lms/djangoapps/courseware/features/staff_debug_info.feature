@shard_1
Feature: LMS.Debug staff info links
    As a course staff in an edX course
    In order to test my understanding of the material
    I want to click on staff debug info links

    Scenario: I can reset student attempts
        When i am staff member for the course "model_course"
        And I am viewing a "multiple choice" problem
        And I can view staff debug info
        Then I can reset student attempts
        Then I cannot see delete student state link
        Then I cannot see rescore student submission link
