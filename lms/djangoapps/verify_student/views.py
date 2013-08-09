"""


"""

@login_required
def start(request):
    """
    If they've already started a PhotoVerificationAttempt, we move to wherever
    they are in that process. If they've completed one, then we skip straight
    to payment.
    """
    