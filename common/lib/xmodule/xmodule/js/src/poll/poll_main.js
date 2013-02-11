(function (requirejs, require, define) {
define('PollMain', ['logme'], function (logme) {
    var debugMode;

    debugMode = false;
    if (debugMode === true) {
        logme('We are in debug mode.');
    }

PollMain.prototype = {

'showAnswerGraph': function (poll_answers, total) {
    var dataSeries, tickSets, c1, _this, totalValue;

    totalValue = parseFloat(total);
    if (isFinite(totalValue) === false) {
        return;
    }

    _this = this;

    // Show the graph answer DOM elementfrom.
    this.graphAnswerEl.show();

    dataSeries = [];
    tickSets = {};
    c1 = 0;

    logme('poll_answers: ', poll_answers, '_this.jsonConfig.answers: ', _this.jsonConfig.answers);

    $.each(poll_answers, function (index, value) {
        var numValue, text;

        numValue = parseFloat(value);
        if (isFinite(numValue) === false) {
            return;
        }

        c1 += 1;

        text = _this.jsonConfig.answers[index].substring(0, 10);

        tickSets[c1.toFixed(1)] = text;

        dataSeries.push({
            'label': '' + value + '/' + total,
            'data': [[c1, (numValue / totalValue) * 100.0]]
        });
    });

    jQuery.plot(
        _this.graphAnswerEl,
        dataSeries,
        {
            'xaxis': {
                'min': 0,
                'max': c1 + 1,
                'tickFormatter': function formatter(val, axis) {
                    var valStr;

                    valStr = val.toFixed(axis.tickDecimals);

                    if (tickSets.hasOwnProperty(valStr)) {
                        return tickSets[valStr];
                    } else {
                        return '';
                    }
                }
            },
            'yaxis': {
                'min': 0,
                'max': 105,
                'tickFormatter': function formatter(val, axis) {
                    return val.toFixed(axis.tickDecimals) + ' %';
                }
            },
            'lines':  {  'show': false  },
            'points': {  'show': false  },
            'bars': {
                'show': true,
                'align': 'center',
                'barWidth': 0.5
            },
            'legend': {
                'show': true,
                'backgroundOpacity': 0
            }
        }
    );
},

'submitAnswer': function (answer, answerEl) {
    var _this;

    // Make sure that the user can answer a question only once.
    if (this.questionAnswered === true) {
        return;
    }
    this.questionAnswered = true;

    _this = this;

    answerEl.addClass('answered');

    if (debugMode === true) {
        (function () {
            var response;

            response = {
                'poll_answers': {
                    'Yes': '1',
                    'No': '1',
                    'Dont_know': '8'
                },
                'total': '10'
            };

            logme('One.');
            _this.showAnswerGraph(response.poll_answers, response.total);
        }());
    } else {
        // Send the data to the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + answer,  {},
            function (response) {
                logme('response:', response);

                logme('Two.');
                _this.showAnswerGraph(response.poll_answers, response.total);

                if (_this.verticalSectionEl !== null) {
                    _this.verticalSectionEl.find('xmodule_ConditionalModule', function (index, value) {
                        console.log('Found conditional element. index = ');
                        console.log(index);
                        console.log('value = ');
                        console.log(value);
                    });
                }

                /*
                _this.vertModEl.find('.xmodule_ConditionalModule').each(
                    function (index, value) {
                        (new window[response.className]($(value)));
                    }
                );
                */
            }
        );
    }
}, // End-of: 'submitAnswer': function (answer, answerEl) {

'postInit': function () {
    var _this;

    // Access this object inside inner functions.
    _this = this;

    if (
        (this.jsonConfig.poll_answer.length > 0) &&
        (this.jsonConfig.answers.hasOwnProperty(this.jsonConfig.poll_answer) === false)
    ) {
        this.questionEl.append(
            '<h3>Error!</h3>' +
            '<p>XML data format changed. List of answers was modified, but poll data was not updated.</p>'
        );

        return;
    }

    // Get the DOM id of the question.
    this.id = this.questionEl.attr('id');

    // Get the URL to which we will post the users answer to the question.
    this.ajax_url = this.questionEl.data('ajax-url');

    this.questionHtmlMarkup = $('<div />').html(this.jsonConfig.question).text();
    this.questionEl.append(this.questionHtmlMarkup);

    // When the user selects and answer, we will set this flag to true.
    this.questionAnswered = false;

    logme('this.jsonConfig.answers: ', this.jsonConfig.answers);
    logme('this.jsonConfig.poll_answer: ', this.jsonConfig.poll_answer);

    $.each(this.jsonConfig.answers, function (index, value) {
        var answerEl;

        answerEl = $('<div class="poll_answer">' + value + '</li>');
        answerEl.on('click', function () {
            _this.submitAnswer(index, answerEl);
        });

        if (index === _this.jsonConfig.poll_answer) {
            answerEl.addClass('answered');
            _this.questionAnswered = true;
        }

        answerEl.appendTo(_this.questionEl);
    });

    this.graphAnswerEl = $('<div class="graph_answer"></div>');
    this.graphAnswerEl.hide();
    this.graphAnswerEl.appendTo(this.questionEl);

    logme('PollMain object: ', this);

    // If it turns out that the user already answered the question, show the answers graph.
    if (this.questionAnswered === true) {
        logme('Three');
        this.showAnswerGraph(this.jsonConfig.poll_answers, this.jsonConfig.total);
    }
} // End-of: 'postInit': function () {
}; // End-of: PollMain.prototype = {

return PollMain;

function PollMain(el) {
    var _this;

    var tel, c1;

    tel = $(el)[0];
    c1 = 0;

    console.log(tel);

    this.verticalSectionEl = null;

    while (tel.tagName.toLowerCase() !== 'body') {
        tel = $(tel).parent()[0];
        c1 += 1;

        console.log('' + c1 + ': parent = ');
        console.log(tel);

        if ((tel.tagName.toLowerCase() === 'section') && ($(tel).hasClass('xmodule_VerticalModule') === true)) {
            console.log('Found vertical section. Saving element for future use.');
            this.verticalSectionEl = tel;

            break;
        } else if (c1 > 50) {
            console.log('ERROR: HTML hierarchy is very large.');

            break;
        }
    }

    console.log('this.verticalSectionEl = ');
    console.log(this.verticalSectionEl);

    this.vertModEl = $(el).parent().parent();
    if (this.vertModEl.length !== 1) {
        // We will work with a single DOM element that contains one question, and zero or more conditionals.
        return;
    }

    this.questionEl = $(el).find('.poll_question');
    if (this.questionEl.length !== 1) {
        // We require one question DOM element.
        logme('ERROR: PollMain constructor requires one question DOM element.');

        return;
    }

    // Just a safety precussion. If we run this code more than once, multiple 'click' callback handlers will be
    // attached to the same DOM elements. We don't want this to happen.
    if (this.questionEl.attr('poll_main_processed') === 'true') {
        logme(
            'ERROR: PolMain JS constructor was called on a DOM element that has already been processed once.'
        );

        return;
    }

    // This element was not processed earlier.
    // Make sure that next time we will not process this element a second time.
    this.questionEl.attr('poll_main_processed', 'true');

    // Access this object inside inner functions.
    _this = this;

    // Test case for when the server part is still not ready. Change to 'false' so you can test actual server
    // generated JSON config.
    if (debugMode === true) {
        (function () {
            var testNum;

            // Test for when the user has already answered.
            // testNum = 1;

            // Test for when the user did not answer yet.
            testNum = 2;

            if (testNum === 1) {
                _this.jsonConfig = {
                    'poll_answers': {
                        'Dont_know': '2',
                        'No': '1',
                        'Yes': '4'
                    },
                    'total': '7',
                    'poll_answer': 'No',
                    'answers': {
                        'Dont_know':
                            'Don\'t know. What does it mean to not know? Well, the student must be able to ' +
                            'answer this question for himself. In the case when difficulties arise, he should' +
                            'consult a TA.',
                        'No': 'No',
                        'Yes': 'Yes'
                    },
                    'question':
                        "&lt;h3&gt;What's the Right Thing to Do?&lt;/h3&gt;&lt;p&gt;Suppose four shipwrecked " +
                        "sailors are stranded at sea in a lifeboat, without food or water. Would it be wrong for " +
                        "three of them to kill and eat the cabin boy, in order to save their own lives?&lt;/p&gt;"
                };
            } else if (testNum === 2) {
                _this.jsonConfig = {
                    'poll_answers': {},
                    'total': '',
                    'poll_answer': '',
                    'answers': {
                        'Dont_know':
                            'Don\'t know. What does it mean to not know? Well, the student must be able to ' +
                            'answer this question for himself. In the case when difficulties arise, he should' +
                            'consult a TA.',
                        'No': 'No',
                        'Yes': 'Yes'
                    },
                    'question':
                        "&lt;h3&gt;What's the Right Thing to Do?&lt;/h3&gt;&lt;p&gt;Suppose four shipwrecked " +
                        "sailors are stranded at sea in a lifeboat, without food or water. Would it be wrong for " +
                        "three of them to kill and eat the cabin boy, in order to save their own lives?&lt;/p&gt;"
                };
            }

            _this.postInit();
        }());

        return;
    } else {
        try {
            this.jsonConfig = JSON.parse(this.questionEl.children('.poll_question_div').html());

            $.postWithPrefix(
                '' + this.questionEl.data('ajax-url') + '/' + 'get_state',  {},
                function (response) {
                    logme('Get pre init state.');
                    logme('response:', response);

                    _this.jsonConfig.poll_answer = response.poll_answer;
                    _this.jsonConfig.total = response.total;

                    $.each(response.poll_answers, function (index, value) {
                        _this.jsonConfig.poll_answers[index] = value;
                    });

                    logme('Current "jsonConfig": ');
                    logme(_this.jsonConfig);

                    _this.questionEl.children('.poll_question_div').html(JSON.stringify(_this.jsonConfig));

                    _this.postInit();
                }
            );

            return;
        } catch (err) {
            logme(
                'ERROR: Invalid JSON config for poll ID "' + this.id + '".',
                'Error messsage: "' + err.message + '".'
            );

            return;
        }
    }
} // End-of: function PollMain(el) {

}); // End-of: define('PollMain', ['logme'], function (logme) {

// End-of: (function (requirejs, require, define) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
