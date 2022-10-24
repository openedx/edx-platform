Course + User Discounts
-----------------------------

Status
======

Accepted

Context
=======

We are implementing platform-wide discounts that are determined using a combination of course and user. The
data used in this determination lives in the LMS. The discount will be messaged in the LMS, and then autoapplied
on the basket page of Ecommerce. See the table below for information on how this new discount differs from our
current discounting schemes.

+-------------------------------------+-------------------------------------+------------------------------------+ 
| Discounts                           | Coupons                             | Enterprise Offers                  | 
+=====================================+=====================================+====================================+ 
| Permanent                           | Temporary                           | Permanent                          | 
+-------------------------------------+-------------------------------------+------------------------------------+ 
| Applies to all -- certain combos of | Applies to a specific subset of     | Applies to enterprise users        |
| of user and course exempted         | users and/or courses                |                                    |
+-------------------------------------+-------------------------------------+------------------------------------+ 
| Messaged in specific places in the  | Sometimes messaged on the marketing | Messaged in integration            |
| LMS                                 | site (specific promotions)          |                                    |
+-------------------------------------+-------------------------------------+------------------------------------+
| Currently calculated in the LMS     | Calculated in Ecommerce             | Calculated in Ecommerce            |
+-------------------------------------+-------------------------------------+------------------------------------+
 

Decisions
=========

#. **The location of the calculation of discount applicability/eligibility**

   a. We want *one* service to contain the logic for whether a discount can be applied/can be communicated to the 
      user. This way, upkeep is much simpler: if/when the logic changes, it only needs to change in one place.
      Additionally, if we duplicated the logic, we would either need to duplicate the data, ask for the data, or
      have slightly different logic (which would present cases in which the outcome is different depending on the
      service). We are unhappy with all of those implementations.

   b. We will calculate applicability/eligibility in the LMS. All of the data that we need currently resides in 
      the LMS. In order to get the information to make the determination in Ecommerce, we would need to ask LMS
      for the data. If the ultimate destination of that data was the LMS (to decide whether to message the 
      discount), we would have excess communication and more failure points. See below for a diagram of what we
      don't want:

::

      LMS -asks for discount applicability------------------> Ecommerce
      LMS <-----------asks for data to dermine applicability- Ecommerce
      LMS -sends back data----------------------------------> Ecommerce
      LMS <-------------------------sends back applicability- Ecommerce

#. **Communication of discount applicability**

   a. Within the LMS, when we need to get the applicability of a discount for a user and course, we can just
      import the function and call it.

   b. Outside of the LMS, we need a way to get this information in a validated fashion. We have added a rest 
      endpoint for that communication. Because we want to be able to use the information both on the front-end
      and back-end without risk of the user creating their own discounts, we are sending it as a jwt, which is
      signed. See C for more information on how specifically it will be used on the Ecommerce front-end.

   c. We do not want to make a synchronous call from the Ecommerce backend to the LMS every time the basket 
      page is loaded. See this decision record link for more information: 
      https://github.com/openedx/Ecommerce/blob/master/docs/decisions/0002-no-synchronous-calls.rst  However, 
      we are happy to make an ajax call from the front-end.
      The basket page needs this information for two reasons: 1) So that the correct price is shown to the user,
      and the user is informed that they are recieving a discount. 2) So that the correct price is charged to 
      the user during payment.  We will handle both by making the ajax call, updating the ui on the page, and
      also updating the data that is sent to the server during the payment step. Because we are using a JWT, we
      can verify that the discount is correct. Right now, another team is working on adding a MFE to Ecommerce. 
      Rather than have to implement the front-end code in Ecommerce to do this twice, we will write the code
      to make the ajax call, and if there is a discount, reload the page passing the JWT as a parameter. See
      diagram below for current (interum) state of the communication of the discount:

::

      LMS <--asks about discount applicability- Ecom Frontend                                      Ecom Backend
      LMS -sends applicability as JWT---------> Ecom Frontend
      -----IF APPLICABLE----
      LMS                                       Ecom Frontend -Reloads the page w/ JWT as param--> Ecom Backend