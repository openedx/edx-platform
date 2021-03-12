"""
Discounts are determined by a combination of user and course, and have a one to one relationship with the enrollment
(if already enrolled) or a join table of user and course. They are determined in LMS, because all of the data for
the business rules exists here. Discount rules are meant to be permanent.
"""
