# Configure mobile push notifications in edx-platform


### 1. Create a new Firebase project

All push notifications in Open edX are sent via FCM service to start with it you need to create
a new Firebase project in Firebase console https://console.firebase.google.com/

### 2. Provide service account credentials to initialize an FCM admin application in edx-platform

To configure sending push notifications via FCM from edx-platform, you need to generate private
key for Firebase admin SDK in Project settings > Service accounts section.

After downloading .json key, you should mount it to LMS/CMS containers and specify a path to
the mounted file using FIREBASE_CREDENTIALS_PATH settings
[variable](https://github.com/openedx/edx-platform/pull/34971/files#diff-f694c479e5c9b133241a799e1ddf33d5d5133bfdec91e3f7d371e094c9999e74R31). There is also an alternative option,
which is to add the value from the .json key to the FIREBASE_CREDENTIALS environment
[variable](https://github.com/openedx/edx-platform/pull/34971/files#diff-f694c479e5c9b133241a799e1ddf33d5d5133bfdec91e3f7d371e094c9999e74R34),
like a python dictionary.

https://github.com/openedx/edx-ace/blob/master/docs/decisions/0002-push-notifications.rst?plain=1#L108


### 3. Configure and build mobile applications

Use the supported Open edX  mobile applications:

https://github.com/openedx/openedx-app-android/

https://github.com/openedx/openedx-app-ios

#### 3.1 Configure oauth2

First you need to configure Oauth applications for each mobile client in edx-platform. You should create separate
entries for Android and IOS applications in the Django OAuth Toolkit > Applications.

Fill in all required fields in the form:
  - Client ID: <your_client_id>.
  - Client type: Public
  - Authorization grant type: Resource owner password-based
  - Public Client secret: <your_client_secret
  - Name: <your_app_name>

Specify generated Client ID in mobile config.yaml file

https://github.com/openedx/openedx-app-android/blob/main/Documentation/ConfigurationManagement.md#configuration-files

https://github.com/openedx/openedx-app-ios/blob/main/Documentation/CONFIGURATION_MANAGEMENT.md#examples-of-config-files

#### 3.2 Provide FCM credentials to the app

Create new apps in Firebase Console for Android and IOS in Project settings > General section.

Download credentials file, google-services.json for Android, or GoogleService-Info.plist for IOS.

Copy/paste values from configuration file into config.yaml as shown in example configurations.

https://github.com/openedx/openedx-app-android/blob/main/Documentation/ConfigurationManagement.md#configuration-files

https://github.com/openedx/openedx-app-ios/blob/main/Documentation/CONFIGURATION_MANAGEMENT.md#examples-of-config-files

Build applications and you’re ready to go!

