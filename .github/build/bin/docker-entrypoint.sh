#!/bin/bash -e
export DJANGO_SETTINGS_MODULE=$SERVICE_VARIANT.envs.$SETTINGS
USERID=${USERID:=0}

## Configure user with a different USERID if requested.
if [ "$USERID" -ne 0 ]
    then
        echo "creating new user 'openedx' with UID $USERID"
        useradd --home-dir /openedx -u $USERID openedx

        # Change file permissions
        chown --no-dereference -R openedx /openedx

        # Run CMD as different user
        exec chroot --userspec="$USERID" --skip-chdir / env HOME=/openedx "$@"
else 
        # Run CMD as root (business as usual)
        exec "$@"
fi
