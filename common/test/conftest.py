"""Code run by pylint before running any tests."""
from safe_lxml import defuse_xml_libs

defuse_xml_libs()
