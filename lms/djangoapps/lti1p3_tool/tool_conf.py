from pylti1p3.tool_config import ToolConfDict
from .models import LtiTool


class ToolConfDb(ToolConfDict):
    _lti_tools = None

    def __init__(self):
        super(ToolConfDb, self).__init__({})
        self._lti_tools = {}

    def find_registration_by_issuer(self, iss):
        try:
            lti_tool = LtiTool.objects.get(issuer=iss)
            self._lti_tools[iss] = lti_tool
            self._config[lti_tool.issuer] = lti_tool.to_dict()
            self.set_private_key(iss, lti_tool.tool_key.private_key)
        except LtiTool.DoesNotExist:
            pass
        return super(ToolConfDb, self).find_registration_by_issuer(iss)

    def get_lti_tool(self, iss):
        return self._lti_tools[iss]
