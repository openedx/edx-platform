Transitional for moving to new settings scheme. 

To use: 
  django-admin.py runserver --settings=envs.dev --pythonpath=.

NOTE: Using manage.py will automatically run mitx/settings.py first, regardless
of what you send it for an explicit --settings flag. It still works, but might
have odd side effects. Using django-admin.py avoids that problem. 
django-admin.py is installed by default when you install Django.

