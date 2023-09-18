import attr


@attr.s(frozen=True, auto_attribs=True)
class LTIToolsReceivingPIIData:
    """
    Class that stores data about the list of LTI tools sharing PII
    """
    lii_tools_receiving_pii: dict()


@attr.s(frozen=True, auto_attribs=True)
class LTIPIISignatureData:
    """
    Class that stores an lti pii signature
    """
    user: str
    course_id: str
    lti_tools: str
    lti_tools_hash: str
