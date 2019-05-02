Feature: One-click unsubscribe
  As a user with notifications enabled
  I want to be able to unsubscribe from notifications

    Scenario: Unsubscribe when not logged in
      Given I am an edX user
      And I am not logged in
      And I have notifications enabled
      When I access my unsubscribe url
      Then my notifications should be disabled
      And I should see "Unsubscribe Successful!" somewhere on the page
      And I should see "Click here to return to your dashboard" somewhere on the page
      And I should see a link to "/dashboard" with the text "here"

    Scenario: Unsubscribe when logged in
      Given I am a logged in user
      And I have notifications enabled
      When I access my unsubscribe url
      Then my notifications should be disabled
      And I should see "Unsubscribe Successful!" somewhere on the page
      And I should see "Click here to return to your dashboard" somewhere on the page
      And I should see a link to "/dashboard" with the text "here"
