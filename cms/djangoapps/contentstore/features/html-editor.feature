@shard_2
Feature: CMS.HTML Editor
  As a course author, I want to be able to create HTML blocks.

  Scenario: User can view metadata
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I see only the HTML display name setting

  # Safari doesn't save the name properly
  @skip_safari
  Scenario: User can modify display name
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I can modify the display name
    And my display name change is persisted on save

  Scenario: Edit High Level source is available for LaTeX html
    Given I have created an E-text Written in LaTeX
    When I edit and select Settings
    Then Edit High Level Source is visible

  Scenario: TinyMCE image plugin sets urls correctly
    Given I have created a Blank HTML Page
    When I edit the page
    And I add an image with static link "/static/image.jpg" via the Image Plugin Icon
    Then the src link is rewritten to "c4x/MITx/999/asset/image.jpg"
    And the link is shown as "/static/image.jpg" in the Image Plugin

  Scenario: TinyMCE link plugin sets urls correctly
    Given I have created a Blank HTML Page
    When I edit the page
    And I add a link with static link "/static/image.jpg" via the Link Plugin Icon
    Then the href link is rewritten to "c4x/MITx/999/asset/image.jpg"


  Scenario: TinyMCE and CodeMirror preserve style tags
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<p class='title'>pages</p><style><!-- .title { color: red; } --></style>" in the code editor and press OK
    And I save the page
    Then the page text is:
      """
      <p>&nbsp;</p>
      <p class="title">pages</p>
      <style><!--
      .title { color: red; }
      --></style>
      """

  Scenario: TinyMCE toolbar buttons are as expected
    Given I have created a Blank HTML Page
    When I edit the page
    Then the expected toolbar buttons are displayed

  Scenario: Static links are converted when switching between code editor and WYSIWYG views
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<img src="/static/image.jpg">" in the code editor and press OK
    Then the src link is rewritten to "c4x/MITx/999/asset/image.jpg"
    And the code editor displays "<p><img src="/static/image.jpg" alt="" /></p>"

  Scenario: Code format toolbar button wraps text with code tags
    Given I have created a Blank HTML Page
    When I edit the page
    And I set the text to "display as code" and I select the text
    And I select the code toolbar button
    And I save the page
    Then the page text is:
      """
      <p><code>display as code</code></p>
      """
