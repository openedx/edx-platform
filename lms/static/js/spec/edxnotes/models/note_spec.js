define(['js/edxnotes/models/note'],
    function(NoteModel) {
        'use strict';

        describe('NoteModel', function() {
            var model,
                timezoneOffset = (new Date()).getTimezoneOffset(),
                dates = [
                    new Date(2014, 11, 11, 11, 10),
                    new Date(2014, 11, 11, 11, 11)
                ],
                options = {
                    id: 'dummy-id',
                    created: dates[0],
                    updated: dates[1],
                    user: 'dummy-user-id',
                    usage_id: 'dummy-usage-id',
                    course_id: 'dummy-course-id',
                    text: 'dummy-text',
                    quote: 'dummy-quote',
                    ranges: [
                        {
                            start: '/p[1]',
                            end: '/p[1]',
                            startOffset: 0,
                            endOffset: 10,
                        }
                    ],
                };

            beforeEach(function() {
                model = new NoteModel(options);
            });

            describe('Initialization', function() {
                it('Will set passed attributes on the model instance', function() {
                    var ranges = model.get('ranges');
                    expect(model.get('id')).toEqual('dummy-id');
                    expect(model.get('created')).toEqual(dates[0]);
                    expect(model.get('updated')).toEqual(dates[1]);
                    expect(model.get('user')).toEqual('dummy-user-id');
                    expect(model.get('usage_id')).toEqual('dummy-usage-id');
                    expect(model.get('course_id')).toEqual('dummy-course-id');
                    expect(model.get('text')).toEqual('dummy-text');
                    expect(model.get('quote')).toEqual('dummy-quote');
                    expect(ranges[0].start).toEqual('/p[1]');
                    expect(ranges[0].end).toEqual('/p[1]');
                    expect(ranges[0].startOffset).toEqual(0);
                    expect(ranges[0].endOffset).toEqual(10);
                });

                it('Parses dates correctly', function() {
                    expect(model.getDateTime(dates[0])).toEqual('December 11, 2014 at 11:10AM');
                });
            });
        });
    }
);
