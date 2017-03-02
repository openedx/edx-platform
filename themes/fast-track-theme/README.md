# Kauffman FastTrack theme for EDX

This is custom EDX theme for Kauffman project. 

## How to use theme

Create folder named *fast-track-theme* in:
```
edx-platfom/themes/
```

Clone repository in folder:

```
edx-platfom/themes/fast-track-theme
```

### Setup environment variables

Change your *lms.env.json* file located in */edx/app/edxapp* folder.

```
"DEFAULT_SITE_THEME": "fast-track-theme",

...

"ENABLE_COMPREHENSIVE_THEMING": true

...

"COMPREHENSIVE_THEME_DIRS": [
        "/edx/app/edxapp/edx-platform/themes"
    ],
```
### Update assets (local server)

Restart LMS with following command:
```
paver devstack lms
```

If you don't want to stop the server, from *edx-platform/* run:
```
paver update_assets lms
```
and hard refresh the page. You should now be able to see changes in LMS.
Restarting local server with compiling assets is a long process. If you are interested in making your local servers run faster, see [Developing on the edX / Making the local servers run faster](https://github.com/edx/edx-platform/wiki/Developing-on-the-edX-Developer-Stack#making-the-local-servers-run-faster).

## EDX comprehensive theme

See also [Comprehensive Theming on Open edX](https://dehamzah.com/openedx/comprehensive-theming-on-openedx/) for more details on creating and using comprehensive theme on EDX.
