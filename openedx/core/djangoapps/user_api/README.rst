Status: Active

Responsibilities
================
The user_api app is currently a catch all that is used to provide various apis that are related to the user and also to features within the platform.

Intended responsibility: To manage user profile and general account information and to provide APIs to do so easily. This includes the following features: user preference, user profile, user retirement, and account activation/deactivation.

Direction: Decompose
===============
Currently this app is a catch all for many user related information even when that information should really belong in a different app.  If you are building a feature and need to provide information about a user within the context of your feature, you should localize that API to your feature and make your assumptions about what user information you need clear.

For example authentication related APIs have already been moved to the user_authn django app.

Glossary
========

More Documentation
==================
