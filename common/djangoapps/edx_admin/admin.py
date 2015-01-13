from ratelimitbackend.admin import RateLimitAdminSite
from sudo.admin import SudoAdminSite


class RatelimitSudoAdminSite(RateLimitAdminSite, SudoAdminSite):
    """
    A class that includes the features of both RateLimitAdminSite and SudoAdminSite
    """
    pass
