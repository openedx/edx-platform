define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/inline_analytics'],
    function(Backbone, $, AjaxHelpers, InlineAnalytics) {

        describe('InlineAnalyticsActions', function() {

            var radioFixture = ('<table cellspacing="2px" id="i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1_table" class="analytics-table"><tr><td width="65px">Choice</td><td width="50px"></td><td width="125px" colspan="2">Last Attempt</td></tr></table>');
            var checkboxFixture = ('<table cellspacing="2px" id="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_table" class="analytics-table"><tr class="checkbox_header_row"><td width="65px">Choice</td></tr></table>');
            var messageFixture = ('<div id="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics" class="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics_div" data-question-type="numerical">');
            var numericalFixture = ('<div id="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics" data-question-type="numerical"><section aria-hidden="true"><div class="grid-wrapper"><p><strong class="num-students"></strong>students answered this question:<br><strong class="num-students-extra"></strong></p><p>Last updated:<strong class="last-update"></strong></p></div></section></div>');
            var buttonFixture = ('<div class="wrap-instructor-info" aria-hidden="true"><a id="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics_button" class="instructor-info-action instructor-analytics-action" data-course-id="A/B/Fall2013" data-answer-dist-url="/get_analytics_answer_dist/" data-location="i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1">Staff Analytics Info</a></div>');
            var checkboxProblemFixture = ('<form id="inputtype_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1" class="choicegroup capa_inputtype"><div class="indicator_container"><span id="status_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1" class="status unanswered" aria-describedby="inputtype_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1"><span class="sr"> - unanswered </span></span></div><fieldset aria-label="" role="checkboxgroup"><label for="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_0"><input id="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_0" type="checkbox" aria-multiselectable="true" value="choice_0" aria-describedby="answer_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1" aria-role="radio" name="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1[]">The ordering of the rows</label><label for="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_1"><input id="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_1" type="checkbox" aria-multiselectable="true" value="choice_1" aria-describedby="answer_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1" aria-role="radio" name="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1[]">The ordering of the columns</label><label for="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_2"><input id="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1_choice_2" type="checkbox" aria-multiselectable="true" value="choice_2" aria-describedby="answer_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1" aria-role="radio" name="input_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1[]">The coloring of the cells as red or green</label><span id="answer_i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1"></span></fieldset></form>');

            var ajaxDataString = 'data=%7B%22module_id%22%3A%22i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1%22%2C%22question_types_by_part%22%3A%7B%22i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1%22%3A%22numerical%22%7D%2C%22num_options_by_part%22%3A%7B%22i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1%22%3A0%7D%2C%22course_id%22%3A%22A%2FB%2FFall2013%22%7D';

            response = {
                'radio': {
                    'count_by_part': {
                        'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': {
                            'totalIncorrectCount': 68,
                            'totalAttemptCount': 268,
                            'totalCorrectCount': 200,
                        },
                    },
                    'message_by_part': {},
                    'data_by_part': {
                        'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': [{
                            'count': 200,
                            'value_id': 'choice_0',
                            'correct': true,
                        }, {
                            'count': 30,
                            'value_id': 'choice_1',
                            'correct': false,
                        }, {
                            'count': 27,
                            'value_id': 'choice_2',
                            'correct': false,
                        }, ],
                    },
                    'last_update_date': 'May 13, 2015 at 07:24 UTC',
                },
                'checkbox': {
                    count_by_part: {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': {
                            'totalIncorrectCount': 398,
                            'totalAttemptCount': 3459,
                            'totalCorrectCount': 3061,
                        },
                    },
                    'message_by_part': {},
                    data_by_part: {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': [{
                            count: 65,
                            value_id: '[choice_2]',
                            correct: false
                        }, {
                            count: 65,
                            value_id: '[choice_0|choice_2]',
                            correct: false
                        }, {
                            count: 58,
                            value_id: '[choice_0]',
                            correct: false
                        }, {
                            count: 83,
                            value_id: '[choice_1|choice_2]',
                            correct: false
                        }, {
                            count: 3061,
                            value_id: '[choice_0|choice_1]',
                            correct: true
                        }, {
                            count: 56,
                            value_id: '[choice_1]',
                            correct: false
                        }, {
                            count: 71,
                            value_id: '[choice_0|choice_1|choice_2]',
                            correct: false
                        }, {
                            count: 2,
                            value_id: '[choice_3',
                            correct: false
                        }, {
                            count: 3,
                            value_id: '[choice_0|choice_3',
                            correct: false
                        }, {
                            count: 4,
                            value_id: 'choice_1|choice_3',
                            correct: false
                        }, {
                            count: 5,
                            value_id: 'choice_2|choice_3',
                            correct: false
                        }, ],
                    },
                    'last_update_date': 'May 14, 2015 at 07:24 UTC',
                },
                'message': {
                    'message_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1': 'The analytics cannot be displayed for this question as randomization was set at one time.'
                    },
                },
                'radio_no_results': {
                    'count_by_part': {},
                    'message_by_part': {},
                    'data_by_part': {},
                },
                'numerical': {
                    'count_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1': {
                            'totalIncorrectCount': 10,
                            'totalAttemptCount': 30,
                            'totalCorrectCount': 20,
                        },
                    },
                    'message_by_part': {},
                    'data_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1': [{
                            'count': 200,
                            'value_id': 'choice_0',
                            'correct': true,
                        }, {
                            'count': 30,
                            'value_id': 'choice_1',
                            'correct': false,
                        }, ]
                    },
                    'last_update_date': 'May 14, 2015 at 07:24 UTC',
                },
            }

            radioData = {
                partsToGet: [
                    'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1'
                ],
                questionTypesByPart: {
                    'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 'radio'
                },
                correctResponses: {
                    'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': '["choice_0"]'
                },
                choiceNameListByPart: {
                    'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': '["choice_0", "choice_1", "choice_2", "choice_3"]'
                },
            }
            checkboxData = {
                partsToGet: [
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1'
                ],
                questionTypesByPart: {
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': 'checkbox'
                },
                correctResponses: {
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': '["choice_0", "choice_1"]'
                },
            }
            messageData = {
                partsToGet: [
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1'
                ],
            }
            numericalData = {
                partsToGet: [
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1'
                ],
                questionTypesByPart: {
                    'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1': 'numerical'
                },
            }

            it('ensures radio type table is rendered correctly', function() {

                $('body').append(radioFixture);
                window.InlineAnalytics.processResponse(
                    response['radio'],
                    radioData['partsToGet'],
                    radioData['questionTypesByPart'],
                    radioData['correctResponses'],
                    radioData['choiceNameListByPart']
                )

                expect($('table')).toHaveHtml('<tbody><tr><td width="65px">Choice</td><td width="50px"></td><td colspan="2" width="125px">Last Attempt</td></tr><tr><td class="answer-box">1</td><td class="answer-box inline-analytics-correct"><span class="dot"></span></td><td class="answer-box">200</td><td class="answer-box">75%</td></tr><tr><td class="answer-box">2</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">30</td><td class="answer-box">11%</td></tr><tr><td class="answer-box">3</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">27</td><td class="answer-box">10%</td></tr><tr><td class="answer-box">4</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">0</td><td class="answer-box">0%</td></tr></tbody>');
                $('table').remove();

            });

            it('ensures checkbox type table is rendered correctly', function() {

                $('body').append(checkboxFixture);
                $('body').append(checkboxProblemFixture);
                window.InlineAnalytics.processResponse(
                    response['checkbox'],
                    checkboxData['partsToGet'],
                    checkboxData['questionTypesByPart'],
                    checkboxData['correctResponses'],
                    checkboxData['choiceNameListByPart']
                )

                expect($('table')).toHaveHtml('<tbody><tr class="checkbox_header_row"><td width="65px">Choice</td><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="not-displayed"> 1 columns not displayed.</th></tr><tr><td id="column0:row1" class="answer-box" title="The ordering of the rows">1</td><td id="column0:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column1:row1" class="answer-box inline-analytics-incorrect"></td><td id="column2:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column3:row1" class="answer-box inline-analytics-incorrect"></td><td id="column4:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column5:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column6:row1" class="answer-box inline-analytics-incorrect"></td><td id="column7:row1" class="answer-box inline-analytics-incorrect"></td><td id="column8:row1" class="answer-box inline-analytics-incorrect"></td><td id="column9:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td></tr><tr><td id="column0:row2" class="answer-box" title="The ordering of the columns">2</td><td id="column0:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column1:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column2:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column3:row2" class="answer-box inline-analytics-incorrect"></td><td id="column4:row2" class="answer-box inline-analytics-incorrect"></td><td id="column5:row2" class="answer-box inline-analytics-incorrect"></td><td id="column6:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column7:row2" class="answer-box inline-analytics-incorrect"></td><td id="column8:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column9:row2" class="answer-box inline-analytics-incorrect"></td></tr><tr><td id="column0:row3" class="answer-box" title="The coloring of the cells as red or green">3</td><td id="column0:row3" class="answer-box inline-analytics-correct"></td><td id="column1:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column2:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column3:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column4:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column5:row3" class="answer-box inline-analytics-correct"></td><td id="column6:row3" class="answer-box inline-analytics-correct"></td><td id="column7:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column8:row3" class="answer-box inline-analytics-correct"></td><td id="column9:row3" class="answer-box inline-analytics-correct"></td></tr><tr><td id="last_attempt" class="answer-box checkbox-last-attempt">Last Attempt</td><td class="answer-box">3061<br>88%</td><td class="answer-box">83<br>2%</td><td class="answer-box">71<br>2%</td><td class="answer-box">65<br>2%</td><td class="answer-box">65<br>2%</td><td class="answer-box">58<br>2%</td><td class="answer-box">56<br>2%</td><td class="answer-box">5<br>0%</td><td class="answer-box">4<br>0%</td><td class="answer-box">3<br>0%</td></tr></tbody>');
                $('table').remove();
                $('form').remove();
            });

            it('ensures message is correctly rendered', function() {
                $('body').append(messageFixture);
                window.InlineAnalytics.processResponse(
                    response['message'],
                    messageData['partsToGet'],
                    null,
                    null,
                    null
                )

                expect($('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics')).toHaveText('The analytics cannot be displayed for this question as randomization was set at one time.');
                $('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics').remove();
            });

            it('ensures radio type is rendered correctly with no results', function() {
                $('body').append(radioFixture);
                window.InlineAnalytics.processResponse(
                    response['radio_no_results'],
                    radioData['partsToGet'],
                    radioData['questionTypesByPart'],
                    radioData['correctResponses'],
                    radioData['choiceNameListByPart']
                )

                expect($('table')).toHaveHtml('<tbody><tr><td width="65px">Choice</td><td width="50px"></td><td colspan="2" width="125px">Last Attempt</td></tr><tr><td class="answer-box">1</td><td class="answer-box inline-analytics-correct"><span class="dot"></span></td><td class="answer-box">0</td><td class="answer-box">0%</td></tr><tr><td class="answer-box">2</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">0</td><td class="answer-box">0%</td></tr><tr><td class="answer-box">3</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">0</td><td class="answer-box">0%</td></tr><tr><td class="answer-box">4</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="answer-box">0</td><td class="answer-box">0%</td></tr></tbody>');
                $('table').remove();
            });

            it('ensures numerical type is rendered correctly', function() {
                $('body').append(numericalFixture);
                window.InlineAnalytics.processResponse(
                    response['numerical'],
                    numericalData['partsToGet'],
                    numericalData['questionTypesByPart'],
                    numericalData['correctResponses'],
                    null
                )
                expect($('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics')).toHaveHtml('<section aria-hidden="true"><div class="grid-wrapper"><p><strong class="num-students">30</strong>students answered this question:<br><strong class="num-students-extra">20 (67%) correct and 10 (33%) incorrect.</strong></p><p>Last updated:<strong class="last-update">May 14, 2015 at 07:24 UTC</strong></p></div></section>');
                $('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics').remove();
            });


            it('ensures ajax call to server', function() {

                $('body').append(messageFixture);
                $('body').append(buttonFixture);

                window.InlineAnalytics.runDocReady('i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1');

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(this);

                $('#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics_button').click();

                // Verify that the client contacts the server with correct params.
                AjaxHelpers.expectRequest(
                    requests, "POST", "/get_analytics_answer_dist/", ajaxDataString
                );
                $('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics').remove();
                $('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics_button').remove();
            });

        });
    });
