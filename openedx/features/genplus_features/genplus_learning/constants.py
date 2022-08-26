class ProgramEnrollmentStatuses:
    """
    Status that a user may have enrolled in a program.
    """
    ENROLLED = 'enrolled'
    PENDING = 'pending'
    SUSPENDED = 'suspended'
    CANCELED = 'canceled'
    ENDED = 'ended'
    __ACTIVE__ = (ENROLLED, PENDING)
    __ALL__ = (ENROLLED, PENDING, SUSPENDED, CANCELED, ENDED)
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )


class ProgramStatuses:
    """
    Status of a program.
    """
    UNPUBLISHED = 'unpublished'
    ACTIVE = 'active'
    RETIRED = 'retired'

    __ALL__ = (UNPUBLISHED, ACTIVE, RETIRED)
    __MODEL_CHOICES__ = (
        (status, status) for status in __ALL__
    )
