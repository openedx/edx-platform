ADR 0004: Service Layer for Contentstore Views
=============================================================

Status
------
Proposed

Context
-------
- The recent introduction of the public authoring API, which shares business logic with existing APIs for Micro-Frontends (MFEs), has led to redundant API implementations across various folders.
- Previously, business logic was embedded within lengthy view files, hindering reusability.
- To enhance maintainability and development efficiency, it's architecturally prudent to separate business logic from view-related code.

Decision
--------
- View files within ``cms/djangoapps/contentstore`` will exclusively handle API-layer operations. These responsibilities include, but are not limited to:
    - Endpoint definitions
    - Authorization processes
    - Data validation
    - Serialization tasks
- Business logic will be extracted and relocated to a distinct service layer, accountable for:
    - Interactions with the modulestore
    - All Create, Read, Update, Delete (CRUD) operations
    - Data mapping and transformation
    - Query-related logic
    - Business domain-specific logic
    - Functions not directly associated with API-layer tasks
- Given potential naming conflicts (e.g., with "Xblock Services"), meticulous consideration is required when naming service layer entities to avoid confusion.

Consequences
------------
- Future view methods should confine business logic to the service layer. This ADR mandates the extraction of business logic from view files into separate entities, without prescribing specific file structures or naming conventions.

Examples
--------

**Before:**::

    # cms/djangoapps/contentstore/views/videos.py

    @view_auth_classes(is_authenticated=True)
    class VideoUsageView(DeveloperErrorViewMixin, APIView):
        @verify_course_exists()
        def get(self, request: Request, course_id: str, edx_video_id: str):
            course_key = CourseKey.from_string(course_id)

            if not has_studio_read_access(request.user, course_key):
                self.permission_denied(request)

            store = modulestore()
            usage_locations = []
            videos = store.get_items(
            course_key,
            qualifiers={
                    'category': 'video'
            },
            )
            for video in videos:
            video_id = getattr(video, 'edx_video_id', '')
            if video_id == edx_video_id:
                    unit = video.get_parent()
                    subsection = unit.get_parent()
                    subsection_display_name = getattr(subsection, 'display_name', '')
                    unit_display_name = getattr(unit, 'display_name', '')
                    xblock_display_name = getattr(video, 'display_name', '')
                    usage_locations.append(f'{subsection_display_name} - {unit_display_name} / {xblock_display_name}')

            formatted_usage_locations = {'usage_locations': usage_locations}
            serializer = VideoUsageSerializer(formatted_usage_locations)
            return Response(serializer.data)

**After:**::

    # cms/djangoapps/contentstore/views/videos.py

    @view_auth_classes(is_authenticated=True)
    class VideoUsageView(DeveloperErrorViewMixin, APIView):
        @verify_course_exists()
        def get(self, request: Request, course_id: str, edx_video_id: str):
            course_key = CourseKey.from_string(course_id)

            if not has_studio_read_access(request.user, course_key):
                self.permission_denied(request)

            usage_locations = get_video_usage_path(course_key, edx_video_id)
            serializer = VideoUsageSerializer(usage_locations)
            return Response(serializer.data)

    # cms/djangoapps/contentstore/videos_provider.py

    def get_video_usage_path(course_key, edx_video_id):
        """
        API for fetching the locations a specific video is used in a course.
        Returns a list of paths to a video.
        """
        store = modulestore()
        usage_locations = []
        videos = store.get_items(
            course_key,
            qualifiers={
                'category': 'video'
            },
        )
        for video in videos:
            video_id = getattr(video, 'edx_video_id', '')
            if video_id == edx_video_id:
                unit = video.get_parent()
                subsection = unit.get_parent()
                subsection_display_name = getattr(subsection, 'display_name', '')
                unit_display_name = getattr(unit, 'display_name', '')
                xblock_display_name = getattr(video, 'display_name', '')
                usage_locations.append(f'{subsection_display_name} - {unit_display_name} / {xblock_display_name}')
        return {'usage_locations': usage_locations}

Notes
-----
- Identifying suitable names for service layer files is challenging due to existing naming conventions within the ecosystem (as discussed in `this forum post <https://discuss.openedx.org/t/contentstore-views-refactoring/11801>`_).
- The service layer is distinct from "Xblock Services" and should not be conflated with them.
- For a deeper understanding of service layer concepts, refer to `Cosmic Python, Chapter 4: Service Layer <https://www.cosmicpython.com/book/chapter_04_service_layer.html>`_.
