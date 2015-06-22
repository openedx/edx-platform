define(['URI', 'common/js/spec_helpers/ajax_helpers', 'teams/js/collections/topic'], function (URI, AjaxHelpers, TopicCollection) {
    describe('TopicCollection', function () {
        var topicCollection;
        beforeEach(function () {
            topicCollection = new TopicCollection(
                {
                    "count": 6,
                    "num_pages": 6,
                    "current_page": 1,
                    "start": 0,
                    "results": [
                        {
                            "description": "asdf description",
                            "name": "asdf",
                            "id": "_asdf"
                        },
                        {
                            "description": "bar description",
                            "name": "bar",
                            "id": "_bar"
                        },
                        {
                            "description": "baz description",
                            "name": "baz",
                            "id": "_baz"
                        },
                        {
                            "description": "foo description",
                            "name": "foo",
                            "id": "_foo"
                        },
                        {
                            "description": "qwerty description",
                            "name": "qwerty",
                            "id": "_qwerty"
                        }
                    ]
                },
                {course_id: 'my/course/id'});
        });

        it('sets its perPage based on initial page size', function () {
            expect(topicCollection.perPage).toBe(5);
        });

        it('sorts by name', function () {
            var requests = AjaxHelpers.requests(this),
                url,
                params;
            topicCollection.fetch();
            expect(requests.length).toBe(1);
            url = new URI(requests[0].url);
            params = url.query(true);
            expect(params.order_by).toBe('name');
        });

        it('passes a course_id to the server', function () {
            var requests = AjaxHelpers.requests(this),
                url,
                params;
            topicCollection.fetch();
            expect(requests.length).toBe(1);
            url = new URI(requests[0].url);
            params = url.query(true);
            expect(params.course_id).toBe('my/course/id');
        });
    });
});
