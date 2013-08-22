Feature: Video component
  As a student, I want to view course videos in LMS.


  Scenario: Video component is fully rendered in the LMS in HTML5 mode
  Given the course has a Video component in HTML5 mode
  Then when I view the video it has rendered in HTML5 mode
  And all sources are correct

  Scenario: Video component is fully rendered in the LMS in Youtube mode
  Given the course has a Video component in Youtube mode
  Then when I view the video it has rendered in Youtube mode

  # Firefox doesn't have HTML5
  @skip_firefox
  Scenario: Autoplay is enabled in LMS for a Video component
  Given the course has a Video component in HTML5 mode
  Then when I view the video it has autoplay enabled
