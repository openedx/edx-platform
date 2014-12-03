@shard_2
Feature: LMS.Verified certificates
    As a student,
    In order to earn a verified certificate
    I want to sign up for a verified certificate course.

    Scenario: I can audit a verified certificate course
        Given I am logged in
        When I select the audit track
        Then I should see the course on my dashboard
        And a "edx.course.enrollment.activated" server event is emitted

    Scenario: I can submit photos to verify my identity
        Given I am logged in
        When I select the verified track
        And I go to step "1"
        And I capture my "face" photo
        And I approve my "face" photo
        And I go to step "2"
        And I capture my "photo_id" photo
        And I approve my "photo_id" photo
        And I go to step "3"
        And I select a contribution amount
        And I confirm that the details match
        And I go to step "4"
        Then I am at the payment page

    Scenario: I can pay for a verified certificate
        Given I have submitted photos to verify my identity
        When I submit valid payment information
        Then I see that my payment was successful

    Scenario: Verified courses display correctly on dashboard
        Given I have submitted photos to verify my identity
        When I submit valid payment information
        And I navigate to my dashboard
        Then I see the course on my dashboard
        And I see that I am on the verified track
        And I do not see the upsell link on my dashboard
        And a "edx.course.enrollment.activated" server event is emitted

    # Not easily automated
#    Scenario: I can re-take photos
#        Given I have submitted my "<PhotoType>" photo
#        When I retake my "<PhotoType>" photo
#        Then I see the new photo on the confirmation page.
#
#        Examples:
#        | PhotoType     |
#        | face          |
#        | ID            |

#    # TODO: automate
#    Scenario: I can edit identity information
#        Given I have submitted face and ID photos
#        When I edit my name
#        Then I see the new name on the confirmation page.

    Scenario: I can return to the verify flow
        Given I have submitted photos to verify my identity
        When I leave the flow and return
        Then I am at the verified page

    # TODO: automate
#    Scenario: I can pay from the return flow
#        Given I have submitted photos to verify my identity
#        When I leave the flow and return
#        And I press the payment button
#        Then I am at the payment page

    Scenario: The upsell offer is on the dashboard if I am auditing
        Given I am logged in
        When I select the audit track
        And I navigate to my dashboard
        Then I see the upsell link on my dashboard

    Scenario: I can take the upsell offer and pay for it
        Given I am logged in
        And I select the audit track
        And I navigate to my dashboard
        When I see the upsell link on my dashboard
        And I select the upsell link on my dashboard
        And I select the verified track for upgrade
        And I submit my photos and confirm
        And I am at the payment page
        And I submit valid payment information
        And I navigate to my dashboard
        Then I see the course on my dashboard
        And I see that I am on the verified track
        And a "edx.course.enrollment.activated" server event is emitted
        And a "edx.course.enrollment.upgrade.succeeded" server event is emitted
