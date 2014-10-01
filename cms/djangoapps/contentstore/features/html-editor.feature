@shard_2
Feature: CMS.HTML Editor
  As a course author, I want to be able to create HTML blocks.

  Scenario: User can view metadata
    Given I have created a Blank HTML Page
    And I edit and select Settings
    Then I see the HTML component settings

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
    Then the src link is rewritten to the asset link "image.jpg"
    And the link is shown as "/static/image.jpg" in the Image Plugin

  Scenario: TinyMCE link plugin sets urls correctly
    Given I have created a Blank HTML Page
    When I edit the page
    And I add a link with static link "/static/image.jpg" via the Link Plugin Icon
    Then the href link is rewritten to the asset link "image.jpg"
    And the link is shown as "/static/image.jpg" in the Link Plugin

  Scenario: TinyMCE and CodeMirror preserve style tags
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<p class='title'>pages</p><style><!-- .title { color: red; } --></style>" in the code editor and press OK
    And I save the page
    Then the page text contains:
      """
      <p class="title">pages</p>
      <style><!--
      .title { color: red; }
      --></style>
      """

  Scenario: TinyMCE and CodeMirror preserve span tags
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<span>Test</span>" in the code editor and press OK
    And I save the page
    Then the page text contains:
      """
      <span>Test</span>
      """

  Scenario: TinyMCE and CodeMirror preserve math tags
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<math><msup><mi>x</mi><mn>2</mn></msup></math>" in the code editor and press OK
    And I save the page
    Then the page text contains:
      """
      <math><msup><mi>x</mi><mn>2</mn></msup></math>
      """

  Scenario: TinyMCE toolbar buttons are as expected
    Given I have created a Blank HTML Page
    When I edit the page
    Then the expected toolbar buttons are displayed

  Scenario: Static links are converted when switching between code editor and WYSIWYG views
    Given I have created a Blank HTML Page
    When I edit the page
    And type "<img src="/static/image.jpg">" in the code editor and press OK
    Then the src link is rewritten to the asset link "image.jpg"
    And the code editor displays "<p><img src="/static/image.jpg" /></p>"

  Scenario: Code format toolbar button wraps text with code tags
    Given I have created a Blank HTML Page
    When I edit the page
    And I set the text to "display as code" and I select the text
    And I select the code toolbar button
    And I save the page
    Then the page text contains:
      """
      <p><code>display as code</code></p>
      """

  Scenario: Raw HTML component does not change text
    Given I have created a raw HTML component
    When I edit the page
    And type "<li>zzzz<ol>" into the Raw Editor
    And I save the page
    Then the page text contains:
      """
      <li>zzzz<ol>
      """
    And I edit the page
    Then the Raw Editor contains exactly:
      """
      <li>zzzz<ol>
      """

  Scenario: Font selection dropdown contains Default font and tinyMCE builtin fonts
    Given I have created a Blank HTML Page
    When I edit the page
    And I click font selection dropdown
    Then I should see a list of available fonts
    And "Default" option sets "'Open Sans', Verdana, Arial, Helvetica, sans-serif" font family
    And all standard tinyMCE fonts should be available

# Skipping in master due to brittleness JZ 05/22/2014
#  Scenario: Can switch from Visual Editor to Raw
#    Given I have created a Blank HTML Page
#    When I edit the component and select the Raw Editor
#    And I save the page
#    When I edit the page
#    And type "fancy html" into the Raw Editor
#    And I save the page
#    Then the page text contains:
#      """
#      fancy html
#      """

# Skipping in master due to brittleness JZ 05/22/2014
#  Scenario: Can switch from Raw Editor to Visual
#    Given I have created a raw HTML component
#    And I edit the component and select the Visual Editor
#    And I save the page
#    When I edit the page
#    And type "less fancy html" in the code editor and press OK
#    And I save the page
#    Then the page text contains:
#      """
#      less fancy html
#      """
