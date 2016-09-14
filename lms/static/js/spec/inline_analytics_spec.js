define(['backbone', 'jquery', 'common/js/spec_helpers/ajax_helpers', 'js/inline_analytics'],
    function(Backbone, $, AjaxHelpers, InlineAnalytics) {

        describe('InlineAnalyticsActions', function() {

            var radioFixture = ('<table cellspacing="2px" id="i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1_table" class="analytics-table"><tr><td width="65px">Choice</td><td width="50px"><td width="125px" colspan="2">First Attempt</td></td><td width="125px" colspan="2">Last Attempt</td></tr></table>');
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
                            'totalFirstIncorrectCount': 68,
                            'totalFirstAttemptCount': 268,
                            'totalFirstCorrectCount': 200,
                            'totalLastIncorrectCount': 70,
                            'totalLastAttemptCount': 268,
                            'totalLastCorrectCount': 198,
                        },
                    },
                    'message_by_part': {},
                    'data_by_part': {
                        'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': [{
                            'first_count': 200,
                            'last_count': 100,
                            'value_id': 'choice_0',
                            'correct': true,
                        }, {
                            'first_count': 30,
                            'last_count': 50,
                            'value_id': 'choice_1',
                            'correct': false,
                        }, {
                            'first_count': 27,
                            'last_count': 57,
                            'value_id': 'choice_2',
                            'correct': false,
                        }, ],
                    },
                    'last_update_date': 'May 13, 2015 at 07:24 UTC',
                },
                'checkbox': {
                    'count_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': {
                            'totalFirstIncorrectCount': 398,
                            'totalFirstAttemptCount': 3459,
                            'totalFirstCorrectCount': 3061,
                            'totalLastIncorrectCount': 400,
                            'totalLastAttemptCount': 3459,
                            'totalLastCorrectCount': 3059,
                        },
                    },
                    'message_by_part': {},
                    'data_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_2_1': [{
                            'first_count': 65,
                            'last_count': 70,
                            'value_id': '[choice_2]',
                            'correct': false
                        }, {
                            'first_count': 65,
                            'last_count': 70,
                            'value_id': '[choice_0|choice_2]',
                            'correct': false
                        }, {
                            'first_count': 58,
                            'last_count': 53,
                            'value_id': '[choice_0]',
                            'correct': false
                        }, {
                            'first_count': 83,
                            'last_count': 78,
                            'value_id': '[choice_1|choice_2]',
                            'correct': false
                        }, {
                            'first_count': 3061,
                            'last_count': 3001,
                            'value_id': '[choice_0|choice_1]',
                            'correct': true
                        }, {
                            'first_count': 56,
                            'last_count': 66,
                            'value_id': '[choice_1]',
                            'correct': false
                        }, {
                            'first_count': 71,
                            'last_count': 81,
                            'value_id': '[choice_0|choice_1|choice_2]',
                            'correct': false
                        }, {
                            'first_count': 2,
                            'last_count': 12,
                            'value_id': '[choice_3',
                            'correct': false
                        }, {
                            'first_count': 3,
                            'last_count': 13,
                            'value_id': '[choice_0|choice_3',
                            'correct': false
                        }, {
                            'first_count': 4,
                            'last_count': 14,
                            'value_id': 'choice_1|choice_3',
                            'correct': false
                        }, {
                            'first_count': 5,
                            'last_count': 15,
                            'value_id': 'choice_2|choice_3',
                            'correct': false
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
                            'totalFirstIncorrectCount': 10,
                            'totalFirstAttemptCount': 30,
                            'totalFirstCorrectCount': 20,
                            'totalLastIncorrectCount': 2,
                            'totalLastAttemptCount': 30,
                            'totalLastCorrectCount': 28,
                        },
                    },
                    'message_by_part': {},
                    'data_by_part': {
                        'i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1': [{
                            'first_count': 200,
                            'last_count': 100,
                            'value_id': 'choice_0',
                            'correct': true,
                        }, {
                            'first_count': 30,
                            'last_count': 130,
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

                expect($('table')).toHaveHtml('<tbody><tr><td width="65px">Choice</td><td width="50px"></td><td colspan="2" width="125px">First Attempt</td><td colspan="2" width="125px">Last Attempt</td></tr><tr><td class="answer-box">1</td><td class="answer-box inline-analytics-correct"><span class="dot"></span></td><td class="checkbox-first-attempt">200</td><td class="checkbox-first-attempt">75%</td><td class="checkbox-last-attempt">100</td><td class="checkbox-last-attempt">37%</td></tr><tr><td class="answer-box">2</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">30</td><td class="checkbox-first-attempt">11%</td><td class="checkbox-last-attempt">50</td><td class="checkbox-last-attempt">19%</td></tr><tr><td class="answer-box">3</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">27</td><td class="checkbox-first-attempt">10%</td><td class="checkbox-last-attempt">57</td><td class="checkbox-last-attempt">21%</td></tr><tr><td class="answer-box">4</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">0</td><td class="checkbox-first-attempt">0%</td><td class="checkbox-last-attempt">0</td><td class="checkbox-last-attempt">0%</td></tr></tbody>');
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

                expect($('table')).toHaveHtml('<tbody><tr class="checkbox_header_row"><td width="65px">Choice</td><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="header"></th><th class="not-displayed"> 1 columns not displayed.</th></tr><tr><td id="column0:row1" class="answer-box" title="The ordering of the rows">1</td><td id="column0:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column1:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column2:row1" class="answer-box inline-analytics-incorrect"></td><td id="column3:row1" class="answer-box inline-analytics-incorrect"></td><td id="column4:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column5:row1" class="answer-box inline-analytics-incorrect"></td><td id="column6:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column7:row1" class="answer-box inline-analytics-incorrect"></td><td id="column8:row1" class="answer-box inline-analytics-incorrect"></td><td id="column9:row1" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td></tr><tr><td id="column0:row2" class="answer-box" title="The ordering of the columns">2</td><td id="column0:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column1:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column2:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column3:row2" class="answer-box inline-analytics-incorrect"></td><td id="column4:row2" class="answer-box inline-analytics-incorrect"></td><td id="column5:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column6:row2" class="answer-box inline-analytics-incorrect"></td><td id="column7:row2" class="answer-box inline-analytics-incorrect"></td><td id="column8:row2" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column9:row2" class="answer-box inline-analytics-incorrect"></td></tr><tr><td id="column0:row3" class="answer-box" title="The coloring of the cells as red or green">3</td><td id="column0:row3" class="answer-box inline-analytics-correct"></td><td id="column1:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column2:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column3:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column4:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column5:row3" class="answer-box inline-analytics-correct"></td><td id="column6:row3" class="answer-box inline-analytics-correct"></td><td id="column7:row3" class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td id="column8:row3" class="answer-box inline-analytics-correct"></td><td id="column9:row3" class="answer-box inline-analytics-correct"></td></tr><tr><td id="first_attempt" class="answer-box checkbox-first-attempt">First Attempt</td><td class="answer-box checkbox-first-attempt">3061<br>88%</td><td class="answer-box checkbox-first-attempt">71<br>2%</td><td class="answer-box checkbox-first-attempt">83<br>2%</td><td class="answer-box checkbox-first-attempt">65<br>2%</td><td class="answer-box checkbox-first-attempt">65<br>2%</td><td class="answer-box checkbox-first-attempt">56<br>2%</td><td class="answer-box checkbox-first-attempt">58<br>2%</td><td class="answer-box checkbox-first-attempt">5<br>0%</td><td class="answer-box checkbox-first-attempt">4<br>0%</td><td class="answer-box checkbox-first-attempt">3<br>0%</td></tr><tr><td id="last_attempt" class="answer-box checkbox-last-attempt">Last Attempt</td><td class="answer-box checkbox-last-attempt">3001<br>87%</td><td class="answer-box checkbox-last-attempt">81<br>2%</td><td class="answer-box checkbox-last-attempt">78<br>2%</td><td class="answer-box checkbox-last-attempt">70<br>2%</td><td class="answer-box checkbox-last-attempt">70<br>2%</td><td class="answer-box checkbox-last-attempt">66<br>2%</td><td class="answer-box checkbox-last-attempt">53<br>2%</td><td class="answer-box checkbox-last-attempt">15<br>0%</td><td class="answer-box checkbox-last-attempt">14<br>0%</td><td class="answer-box checkbox-last-attempt">13<br>0%</td></tr></tbody>');
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

                expect($('table')).toHaveHtml('<tbody><tr><td width="65px">Choice</td><td width="50px"></td><td colspan="2" width="125px">First Attempt</td><td colspan="2" width="125px">Last Attempt</td></tr><tr><td class="answer-box">1</td><td class="answer-box inline-analytics-correct"><span class="dot"></span></td><td class="checkbox-first-attempt">0</td><td class="checkbox-first-attempt">0%</td><td class="checkbox-last-attempt">0</td><td class="checkbox-last-attempt">0%</td></tr><tr><td class="answer-box">2</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">0</td><td class="checkbox-first-attempt">0%</td><td class="checkbox-last-attempt">0</td><td class="checkbox-last-attempt">0%</td></tr><tr><td class="answer-box">3</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">0</td><td class="checkbox-first-attempt">0%</td><td class="checkbox-last-attempt">0</td><td class="checkbox-last-attempt">0%</td></tr><tr><td class="answer-box">4</td><td class="answer-box inline-analytics-incorrect"><span class="dot"></span></td><td class="checkbox-first-attempt">0</td><td class="checkbox-first-attempt">0%</td><td class="checkbox-last-attempt">0</td><td class="checkbox-last-attempt">0%</td></tr></tbody>');
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
                expect($('div#i4x-C-D-problem-d9330c956fa2445fa6ea0c09391e020f_3_1_analytics')).toHaveHtml('<section aria-hidden="true"><div class="grid-wrapper"><p><strong class="num-students">30</strong>students answered this question:<br><strong class="num-students-extra"></strong></p><p>Last updated:<strong class="last-update">May 14, 2015 at 07:24 UTC</strong></p></div></section>');
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
