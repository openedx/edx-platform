Migrating Apple users while switching teams on Apple
-----------------------------------------------

This document explains how to migrate apple signed-in users in the event of
switching teams on the Apple Developer console. When a user uses Apple to sign in,
LMS receives an `id_token from apple containing user information`_, including
user's unique identifier with key `sub`. This unique identifier is unique to
Apple team this user belongs to. Upon switching teams on Apple, developers need
to migrate users from one team to another i.e. migrate users' unique
identifiers. In the LMS, users' unique apple identifiers are stored in
social_django.models.UserSocialAuth.uid. Following is an outline specifying the
migration process.

1. `Create transfer_identifiers for all apple users`_ using the current respective apple unique id.

   i. Run management command generate_and_store_apple_transfer_ids to generate and store apple transfer ids.

   ii. Transfer ids are stored in third_party_auth.models.AppleMigrationUserIdInfo to be used later on.

2. Transfer/Migrate teams on Apple account.

   i. After the migration, `Apple continues to send the transfer identifier`_ with key `transfer_sub` in information sent after login.

   ii. These transfer identifiers are available in the login information for 60 days after team transfer.

   ii. The method get_user_id() in third_party_auth.appleid.AppleIdAuth enables existing users to sign in by matching the transfer_sub sent in the login information with stored records of old Apple unique identifiers in third_party_auth.models.AppleMigrationUserIdInfo.

3. Update Apple Backend credentials in third_party_auth.models.OAuth2ProviderConfig for the Apple backend.

4. Create new team-scoped apple unique ids' for users after the migration using transfer ids created in Step 1.

   i. Run management command generate_and_store_new_apple_ids to generate and store new team-scoped apple ids.

5. Update apple unique identifiers in the Database with new team-scoped apple ids retrieved in step 3.

   i. Run management command update_new_apple_ids_in_social_auth.

6. Apple user migration is complete!


.. _id_token from apple containing user information: https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api/authenticating_users_with_sign_in_with_apple
.. _Create transfer_identifiers for all apple users: https://developer.apple.com/documentation/sign_in_with_apple/transferring_your_apps_and_users_to_another_team
.. _Apple continues to send the transfer identifier: https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api/authenticating_users_with_sign_in_with_apple
