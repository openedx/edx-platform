import django.dispatch

# Custom Signal to save data of Interests on NodeBB
save_interests = django.dispatch.Signal(providing_args=["instance"])
