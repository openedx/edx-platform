
from user_tasks.models import UserTaskStatus
from user_tasks.views import StatusViewSet
from rest_framework.response import Response

from .serializers import StatusWithImportSerializer
from ...models import COMPOSITION_LEVEL_COMPONENT
from ...tasks import import_legacy_content


class ImportViewSet(StatusViewSet):

    # TODO: it would be more robust to instead filter the UserTaskStatuses by whether
    # they have a related Import object, but I'm not sure how to write that query.
    queryset = StatusViewSet.queryset.filter(
        task_class="cms.djangoapps.import_from_modulestore.tasks.import_legacy_content"
    )

    serializer_class = StatusWithImportSerializer

    def create(self, request, *args, **kwargs):
        task = import_legacy_content.delay(
            user_id=request.user.id,
            # TODO: Need to validate these parameters.
            #       I think the serializer can be used to do this.
            source_key=request.data['source_key'],
            target_key=request.data['target_key'],
            override=request.data.get('override', False),
            composition_level=request.data.get('composition_level', COMPOSITION_LEVEL_COMPONENT),
        )
        return UserTaskStatus.objects.get(uuid=task.id)
