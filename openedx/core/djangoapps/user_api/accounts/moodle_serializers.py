from openedx.core.djangoapps.user_api.serializers import ReadOnlyFieldsSerializerMixin
from rest_framework import serializers
from certificates.models import MdlCertificateIssued

class MoodleCertificateSerializer(serializers.HyperlinkedModelSerializer, ReadOnlyFieldsSerializerMixin):
    """
    Class that serializes the portion of MoodleCertificateIssued model needed for account information.
    """
    course_title = serializers.CharField(source='classname')
    class Meta(object):
        model = MdlCertificateIssued
        fields = ("certificateid", "mdl_userid", "timecreated", "studentname", "course_title", "certdate", "code", "download_url")
