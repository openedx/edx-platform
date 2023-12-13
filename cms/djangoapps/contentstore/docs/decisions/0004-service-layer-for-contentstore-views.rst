ADR 0004: Service Layer for Contentstore Views
=============================================================

Status
------
Accepted

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
- Business logic will be extracted and relocated as a distinct service layer to a folder called `edx-platform/cms/djangoapps/contentstore/core`, accountable for:
    - Interactions with the modulestore
    - All Create, Read, Update, Delete (CRUD) operations
    - Data mapping and transformation
    - Query-related logic
    - Business domain-specific logic
    - Functions not directly associated with API-layer tasks
- Given naming conflicts (e.g., with "Xblock Services"), we should generally avoid the term "service" where it could lead to confusion.

Consequences
------------
- Future view methods should confine business logic to the service layer (the `/core` folder). This ADR mandates the extraction of business logic from view files into the `/core` folder. There are no specific rules to how things in this folder should be named for now.

Example
-------

The following example shows a refactoring to this service layer pattern.

Before refactoring, the view method implements some view-related logic like
authorization via `if not has_studio_read_access: ...` and serialization,
but also business logic: instantiating modulestore, fetching videos from it,
and then transforming the data to generate a new data structure `usage_locations`.

After refactoring, the view method only implements logic related to the view / API layer,
and the business logic is extracted to a service file called `videos_provider.py` outside
the `views` folder. Now the videos provider is responsible for fetching and transforming
the data, while the view is responsible for authorization and serialization.

Note that the file name `videos_provider.py` is a made-up example and is not a recommendation, since
we haven't determined any naming conventions at the time of writing this ADR
`(Discuss forum thread) <https://discuss.openedx.org/t/contentstore-views-refactoring/11801>`_.


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

    # cms/djangoapps/contentstore/core/videos_provider.py

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

Rejected Alternatives
---------------------
Contentstore may be becoming too big and may warrant being split up into multiple djangoapps. However, that would be a much larger and different refactoring effort and is not considered necessary at this point. By implementing this ADR we are not preventing this from happening later, so we decided to follow the patterns described in this ADR for now.

Community Feedback
------------------
The following feedback about this ADR is considered out of scope here, but consists of relevant recommendations from the community. (`Source <https://discuss.openedx.org/t/contentstore-views-refactoring/11801/5>`_)

1. Code in `contentstore/api` should be for Python API that can be consumed by other edx-platform apps, as per `OEP-49 <https://open-edx-proposals.readthedocs.io/en/latest/best-practices/oep-0049-django-app-patterns.html>`_.
2. "One recommendation I’d add is the use of a `data.py module <https://docs.openedx.org/projects/openedx-proposals/en/latest/best-practices/oep-0049-django-app-patterns.html#data-py>`_ for immutable domain-layer attrs classes (dataclasses are good too, they just weren’t available when that OEP was written) which can be passed around in place of models or entire xblocks. (`Example <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/content/learning_sequences/data.py>`_) If there are data classes that you’d rather not expose in the public API, maybe you could have two data modules:
    - cms/djangoapps/contentstore/data.py – domain objects exposed by the public python API
    - cms/djangoapps/contentstore/core/data.py – domain objects for internal business logic"
3. "Another recommendation is to be wary of deep nesting and long names. There’s a non-trivial cognitive load that is added when we have modules paths like openedx/core/djangoapps/content/foo/bar/bar_providers.py instead of, e.g., common/core/foo/bar.py. I know you’re working within the existing framework of edx-platform’s folder structure, so there’s only so much you can do here"
4. "once the refactoring is done, if we like how the end result looks and think it’d generalize well to other apps, I suggest that we update OEP-49 with the structure."


Notes
-----
- Identifying a good way to structure file and folder naming and architecture around this is
  discussed in `this forum post <https://discuss.openedx.org/t/contentstore-views-refactoring/11801>`_.
- The terms "service" / "service layer" are distinct from "Xblock Services" and should not be conflated with them.
- For a deeper understanding of service layer concepts, refer to `Cosmic Python, Chapter 4: Service Layer <https://www.cosmicpython.com/book/chapter_04_service_layer.html>`_.
