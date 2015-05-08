"""
The Course Metadata API is responsible for aggregating descriptive course information into
a single logical representation.

The api.py module is the programmatic integration point of the Course Metadata API application.
This module currently contains both the interface and the implementation of the app.  It also
acts as the bridge between the application's RESTful interface and its data access logic

Other platform applications should bind to the classes and methods exposed in this module, versus
binding directly to the views.py or data.py modules.
"""
