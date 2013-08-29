.. raw:: latex
  
      \newpage %
      

======================
APPENDIX D: Time Zones
======================

    **Overview**
    Released course materials become visible to all students at once, and assignments with a due date will be due for all students at once, at the time specified by the setting. However, a number of places on edX and Studio present a time setting without specifying a time zone. Unless specified otherwise, most dates and times in Studio and edX are in UTC, not in your local time zone! When you specify date and time settings that do not have a time zone label, you need to convert values to UTC.  You should also ensure that students and instructors know how to interpret time settings for your course.

    **Details**
    Time is stored in a specific time zone. However, this time zone may not be visible in the interface. Unlabeled time values are specified, stored, and viewed in UTC.

    EdX and Studio handle time zones as follows.

    •	All times, labeled and unlabeled, are saved to the server in UTC (a.k.a. UTC or Z).
    •	Unlabeled times are displayed both in Studio and on edX/Edge in UTC.
    •	Times labeled with a particular time zone in Studio are specified in that time zone, and are converted to UTC. (This is rare.)

    For settings in Studio that are labeled with a time zone, such as the course start and end dates, enter the setting in the time zone specified (usually your local time zone).

    For time settings that are not labeled with a time zone, such as release dates and due dates for course content, convert from your local time zone, and set the dates and time settings in UTC. You can use an online time zone converter to convert from your local time zone.  

    *Note When you use an online converter, enter both the day and the time to account for daylight saving time.*

    Example US Eastern Standard Time is "UTC-5", so a New York winter due date of 5:00pm (17:00) should be entered as 10:00pm (or 22:00) in Studio. US Daylight Saving Time, however, is UTC-4, so a New York summer due date of 5:00pm would be entered as 9:00pm in Studio.

    Most of these time settings are also not labeled in the Student view on edX/Edge. When you set due dates for an assignment, make sure to tell students how to interpret the due date. You can choose one of the following options.

    •	Notify students in advance that all times, unless otherwise labeled, are displayed in UTC, and point them to a time zone converter to convert to their local time zone.
    •	Allow students to assume that all due dates are specified in their local time zone, and specify an unadvertised grace period to invisibly extend all the due dates in your course. For example, some courses set a grace period of "1 day, 6 hours, and 1 minute" to accommodate differences in time zones and any potential system issues.

    *Note Setting a grace period is generally not recommended. It can lead to problems not closing "when they should", and may be misleading to your students.*

    If you have further questions about specifying times and time zones, or are experiencing inconsistencies in due date or release date behavior, please contact us from the edX Studio Help page.

    **References**

    http://help.edge.edx.org/discussions/questions/61-time-zones

    http://help.edge.edx.org/discussions/questions/23-grace-periods
