Feature: Change Enrollment Events
As a registered user
I want to change my enrollment mode


Scenario: I can change my enrollment
Given The course "6.002x" exists
And the course "6.002x" has all enrollment modes
And I am logged in
And I visit the courses page
When I register to audit the course
And a "edx.course.enrollment.activated" server event is emitted
And a "edx.course.enrollment.mode_changed" server events is emitted

And I visit the dashboard
And I click on Challenge Yourself
And I choose an honor code upgrade
Then I should be on the dashboard page
Then 2 "edx.course.enrollment.mode_changed" server event is emitted

# don't emit another mode_changed event upon unenrollment
When I unregister for the course numbered "6.002x"
Then 2 "edx.course.enrollment.mode_changed" server events is emitted
