# Custom Features Migration

## SSO Logout Feature

### Overview
The SSO Logout feature adds an extension point to integrate the Pearson Core Single Sign-On (SSO) logout functionality into the system.

### Test Cases

To test the SSO Logout feature, follow these steps:

1. Configure the site configurations:
   - Set the value of `IES_SESSION_COOKIE_NAME` to the appropriate session cookie name.
   - Set the value of `IES_LOGOUT_ENDPOINT_URL` to the URL of the logout endpoint.

2. Perform a logout from the LMS:
   - Ensure that the `ies_sso_logout` function from Pearson Core is being called during the logout process.

3. Verify the expected behavior:
   - Confirm that the Pearson Core SSO logout feature is triggered.

## Full Name Construction

The Full Name Construction feature enhances the user_details_force_sync pipeline to construct the full name attribute from the first name and last name attributes, compensating for the lack of a full name attribute sent by IES.

### Test Cases

Follow these steps to configure and test the Full Name Construction feature:

1. Configure a SAML IdP and SP in the edx-platform:
   - Refer to the [EDX documentation](https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/tpa/tpa_integrate_open/tpa_SAML_IdP.html) for instructions on configuring a SAML IdP and SP.

2. Configure the SAML IdP in the Django admin page:
   - Leave the "Full Name Attribute" field blank.
   - Set an arbitrary value for the "Full Name Default Value" attribute.
   - Enable the Sync learner profile data field.

3. Ensure the SAML IdP passes the first name and last name attributes:
   - During the account creation process with SAML, make sure that the SAML IdP passes both the first name and last name attributes.

4. Add the SAML IdP entity ID to the list in the code:
   - Update the code to include the entity ID of your SAML IdP in the entity_id list.

5. Create an account with SAML:
   - When creating an account using SAML authentication, ensure that the first name and last name attributes are passed correctly.

6. Verify the Full Name attribute:
   - After the account is created, navigate to your profile page.
   - Confirm that the Full Name attribute is constructed by combining the first name and last name values.

If the first and last name attributes are not passed, the full name should contain the default value
