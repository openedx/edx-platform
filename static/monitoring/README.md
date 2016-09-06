This directory contains a custom package.json file that is only to be used by 
[Gemnasium](https://gemnasium.com/edx/edx-platform). It declares the versions
of the platform's JavaScript vendor libraries that are used without npm. This
is necessary because Gemnasium cannot find such JavaScript files, as it only
looks at dependencies declared in package.json files.

An important note is that .json files cannot contain comments, so libraries
that cannot be found must be removed from package.json. For this reason,
there is a package.txt with a full list of all the vendor libraries in
package.json format. This can be used to determine the scope of libraries
that are not being managed through npm.

As JavaScript dependencies are added to the true package.json file, they should
be removed from both files so that obsolete version dependencies aren't captured.

For more information, see the JIRA story [FEDX-2](https://openedx.atlassian.net/browse/FEDX-2).
