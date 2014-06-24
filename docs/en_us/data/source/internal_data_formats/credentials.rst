.. _Getting_Credentials_Data_Czar:

####################################################
Data Transfers
####################################################

EdX transfers course data to the data czars at our partner institutions in
regularly generated data packages. Data packages are delivered to a single
contact at each university, referred to as the "data czar".

When a data czar is selected at each institution, he or she works with an edX
Program Manager to set up credentials for securely transferring course data
from edX to the partner institution. When this initial step is complete, the
data czar can download data packages when they are available.

****************************************************************
Credentials Created By Data Czars for Encryption and Decryption
****************************************************************

To assure the security of data packages, edX encrypts course data before
transferring it to a partner institution. As a result, when you receive a data
package you must decrypt the data before it can be added to a database,
queried, or used in any other way.

To set up the credentials needed for this encryption and decryption process,
edX has selected GNU Privacy Guard (GnuPG). Each data czar sets up the
credentials that will be used for their institution's data packages. This
entails the creation of a public/private key pair. Essentially, you install an
application on your local computer and then supply your email address and a
secret passphrase (a password). The application uses this information to create
a private key for *decrypting* your data packages and also the unique public
key that you send to edX to use in *encrypting* your data packages.

.. note:: The domain in the email address you supply when you create your credentials must be for your official email address for your edX partner institution. 

Creating these credentials is a one-time process that you coordinate with your
edX Program Manager. Instructions for creating the credentials on Windows and
Macintosh follow.

For more information about the key pairs, see `chapter 3 in the Gpg4win
Compendium`_.

.. _chapter 3 in the Gpg4win Compendium: http://www.gpg4win.org/doc/en/gpg4win-compendium_8.html

Create Credentials: Windows
-----------------------------------------

#. Go to the Gpg4win_ website and download the most recent version of Gpg4win.

   For detailed installation instructions, see `chapter 6 in the Gpg4win Compendium`_.

2. Install Gpg4win and then open the Kleopatra Gpg4win application. A wizard
   presents a series of dialog boxes to collect information from you and 
   generate your public key (called a certificate in Kleopatra).
    
   * When you are prompted to specify the type of key pair you want, click
     **Create personal OpenPGP key pair**.

   * When you are prompted for your email address, be sure to enter your
     official university or institution email address. EdX cannot use public
     keys that are based on personal or other non-official email addresses to
     encrypt data.

   * When you are prompted for a passphrase, enter a strong passphrase. For
     information about passphrases, see `chapter 4 in the Gpg4win
     Compendium`_. Be sure to remember your secret passphrase: you will use it
     to decrypt your data packages.

   For detailed instructions, see `chapter 7 of the Gpg4win Compendium`_.  

3. When Kleopatra presents the "Key Pair Successfully Created" dialog box,
   click **Send Certificate by EMail** to send the public key (and only the
   public key) to your edX Program Manager.

#. You can also click **Make a Backup Copy of Your Key Pair** to store both of
   the keys on a removable data storage device. Do not reveal your secret
   passphrase, or share your private key, with anyone else.

.. _Gpg4win: http://gpg4win.org/
.. _chapter 4 in the Gpg4win Compendium: http://www.gpg4win.org/doc/en/gpg4win-compendium_9.html
.. _chapter 6 in the Gpg4win Compendium: http://www.gpg4win.org/doc/en/gpg4win-compendium_11.html
.. _chapter 7 in the Gpg4win Compendium: http://www.gpg4win.org/doc/en/gpg4win-compendium_12.html

Create Credentials: Macintosh
--------------------------------------------

#. Go to the `GPG Tools`_ website. Scroll down to the **GPG Suite** section of
   the page and click **Download GPG Suite**.

#. When the download is complete, click the .dmg file to begin the
   installation.

#. When installation is complete, GPG Keychain Access opens both a web page of
   `First Steps`_ and a dialog box.

#. Enter your name and email address. Be sure to enter your official university
   or institution email address. EdX cannot use public keys that are based on
   personal or other non-official email addresses to encrypt data.

#. Click **Generate key**. A dialog box opens to prompt you for a passphrase.

#. Enter a strong passphrase. For information about passphrases, see `chapter 4
   in the Gpg4win Compendium`_. Be sure to remember your secret passphrase: you
   will use it to decrypt your data packages. 

#. To send only your public key to your edX Program Manager, click the key and
   then click **Export**. A dialog box opens.

#. Specify a name and a place to save the file. Accept the default value in the
   **Format** of ASCII and leave **Allow secret key export** cleared.

#. Compose a new e-mail message to your edX program manager. Attach the .asc
   file that you saved in the previous step to the message, and then send the
   message.

.. _GPG Tools: https://gpgtools.org/
.. _First Steps: http://support.gpgtools.org/kb/how-to/first-steps-where-do-i-start-where-do-i-begin#setupkey










* The edX Analytics team creates an account on the Amazon Web Service (AWS)
  Simple Storage Service (S3), and provides the Program Manager with the
  public key for account access.

* When a data package is available, the data czar downloads it from S3 and
  decrypts it using the private key.

.. xref to this chapter from the How Do I Get My Research Data Package? article on the Open edX Analytics wiki.





EdX stores the data packages in a secure bucket on the Amazon Web Services (AWS) Simple Storage Service (Amazon S3). Only the data czar is given access credentials (a user name and password) to the AWS S3 account.

To gain access to the AWS S3 account, the data czar must complete these steps:

    Create the encryption keys.
    Receive an email message from edX.




Then, to retrieve the first (and each subsequent) data package, the data czar must complete these steps:

    Access the AWS S3 account.
    Download the data package.
    Decrypt the data package.

Details for each of these tasks follow for the data czar at your institution. For more information about the responsibilities of a data czar, see the edX Data Documentation.