define(['js/models/xblock_validation'],
    function(XBlockValidationModel) {
        var verifyModel;

        verifyModel = function(model, expected_empty, expected_summary, expected_messages, expected_xblock_id) {
            expect(model.get('empty')).toBe(expected_empty);
            expect(model.get('summary')).toEqual(expected_summary);
            expect(model.get('messages')).toEqual(expected_messages);
            expect(model.get('xblock_id')).toBe(expected_xblock_id);
        };

        describe('XBlockValidationModel', function() {
            it('handles empty variable', function() {
                verifyModel(new XBlockValidationModel({parse: true}), true, {}, [], null);
                verifyModel(new XBlockValidationModel({'empty': true}, {parse: true}), true, {}, [], null);

                // It is assumed that the "empty" state on the JSON object passed in is correct
                // (no attempt is made to correct other variables based on empty==true).
                verifyModel(
                    new XBlockValidationModel(
                        {'empty': true, 'messages': [{'text': 'Bad JSON case'}], 'xblock_id': 'id'},
                        {parse: true}
                    ),
                    true,
                    {},
                    [{'text': 'Bad JSON case'}], 'id'
                );
            });

            it('creates a summary if not defined', function() {
                // Single warning message.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'xblock_id': 'id'
                    }, {parse: true}),
                    false,
                    {'text': 'This component has validation issues.', 'type': 'warning'},
                    [],
                    'id'
                );
                // Two messages that compute to a "warning" state in the summary.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'messages': [{'text': 'one', 'type': 'not-configured'}, {'text': 'two', 'type': 'warning'}],
                        'xblock_id': 'id'
                    }, {parse: true}),
                    false,
                    {'text': 'This component has validation issues.', 'type': 'warning'},
                    [{'text': 'one', 'type': 'not-configured'}, {'text': 'two', 'type': 'warning'}],
                    'id'
                );
                // Two messages, with one of them "error", resulting in an "error" state in the summary.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'messages': [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                        'xblock_id': 'id'
                    }, {parse: true}),
                    false,
                    {'text': 'This component has validation issues.', 'type': 'error'},
                    [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                    'id'
                );
            });

            it('respects summary properties that are defined', function() {
                // Summary already present (both text and type), no messages.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'xblock_id': 'id',
                        'summary': {'text': 'my summary', 'type': 'custom type'}
                    }, {parse: true}),
                    false,
                    {'text': 'my summary', 'type': 'custom type'},
                    [],
                    'id'
                );
                // Summary text present, but not type (will get default value of warning).
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'xblock_id': 'id',
                        'summary': {'text': 'my summary'}
                    }, {parse: true}),
                    false,
                    {'text': 'my summary', 'type': 'warning'},
                    [],
                    'id'
                );
                // Summary type present, but not text.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'summary': {'type': 'custom type'},
                        'messages': [{'text': 'one', 'type': 'not-configured'}, {'text': 'two', 'type': 'warning'}],
                        'xblock_id': 'id'
                    }, {parse: true}),
                    false,
                    {'text': 'This component has validation issues.', 'type': 'custom type'},
                    [{'text': 'one', 'type': 'not-configured'}, {'text': 'two', 'type': 'warning'}],
                    'id'
                );
                // Summary text present, type will be computed as error.
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'summary': {'text': 'my summary'},
                        'messages': [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                        'xblock_id': 'id'
                    }, {parse: true}),
                    false,
                    {'text': 'my summary', 'type': 'error'},
                    [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                    'id'
                );
            });

            it('clears messages if showSummaryOnly is true', function() {
                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'xblock_id': 'id',
                        'summary': {'text': 'my summary'},
                        'messages': [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                        'showSummaryOnly': true
                    }, {parse: true}),
                    false,
                    {'text': 'my summary', 'type': 'error'},
                    [],
                    'id'
                );

                verifyModel(
                    new XBlockValidationModel({
                        'empty': false,
                        'xblock_id': 'id',
                        'summary': {'text': 'my summary'},
                        'messages': [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                        'showSummaryOnly': false
                    }, {parse: true}),
                    false,
                    {'text': 'my summary', 'type': 'error'},
                    [{'text': 'one', 'type': 'warning'}, {'text': 'two', 'type': 'error'}],
                    'id'
                );
            });
        });
    }
);
