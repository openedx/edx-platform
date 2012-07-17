Problem format
==============



course.xml format
=================

Structure of xml document:

<course>
  <chapter>
    <section>
      <sequential>
        <problem />
        <video youtube="" />
      </sequential>
      <vertical>
        <problem />
        <video youtube="" />
      </vertical>
    </section>
  </chapter>
</course>

<course name="">
  name: String representing the name of course.
  graceperiod: A default length of time that the problem is still accessible after the due date in the format "2 days 3 hours" or "1 day 15 minutes". S


<chapter name="">
  name: String that will appear at the top level in accordion.

<section name="" [format=""]>
  name: String that will appear in first sub-level in accordion.
  format: String that will appear under the previous name, in disabled
  style. Usual values: Topic, Lab, Homework, Tutorial, Lecture
  etc. Optional.
  due: Due date. Values: valid date. Default: none. Optional.
  subtitle: Optional. Shown as subtitle in courseware accordion or profile page. Defaults to use value in format field.
  graceperiod: A length of time that the problem is still accessible after the due date in the format "2 days 3 hours" or "1 day 15 minutes"
  graded: Whether this section will count towards the students grade or not. "true" or "false". Defaults to "false".
  

<sequential>
Content will be accessed sequentially, under a navigational bar, on
the right part of the page.

<vertical>
Content will be accessed all at once, on the right part of the
page. No navigational bar. May have to use browser scroll
bars. Content split with separators.

<problem name="" filename="" [type="" explain="" explain_available="" due="" attemps="" showanswer="" rerandomnize=""]>
  name: String that will appear above the text of problem. 
  filename: Name of file that will load under the previous title. Should be placed in /problem directory.
  type: Type of page. Optional.
  attemps: Number of allowed attempts. Values: integer. Default: 0. Optional.
  rerandomnize: Randomize question on each attempts. Values: true or false. Default: true. Optional.
  showanswer: When to show answer. For attempted, will show answer after first attempt. Values: never, attempted, answered, closed. Default: closed. Optional.
  explain: ???
  explain_available: ???

<video youtube="" [name=""] />
  youtube: Name of video file stored on YouTube.
  name: Name of video. Optional.
