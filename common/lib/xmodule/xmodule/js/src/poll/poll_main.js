(function (requirejs, require, define) {
define('PollMain', ['logme'], function (logme) {

PollMain.prototype = {

// class @PollModule
//   constructor: (element) ->
//     @el = element
//     @ajaxUrl = @$('.container').data('url')
//     @$('.upvote').on('click', () => $.postWithPrefix(@url('upvote'), @handleVote))
//     @$('.downvote').on('click', () => $.postWithPrefix(@url('downvote'), @handleVote))

//   $: (selector) -> $(selector, @el)

//   url: (target) -> "#{@ajaxUrl}/#{target}"

//   handleVote: (response) =>
//     @$('.container').replaceWith(response.results)

'submitAnswer': function (answer, answerEl) {
    var _this;

    // Make sure that the user can answer a question only once.
    if (this.questionAnswered === true) {
        return;
    }
    this.questionAnswered = true;

    _this = this;

    answerEl.addClass('answered');

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        _this.ajax_url + '/' + answer,  {},
        function (response) {
            var dataSeries, tickSets, c1;

            logme('The following response was received: ' + JSON.stringify(response));

            // Show the answer from server.
            _this.graphAnswerEl.show();

            dataSeries = [];
            tickSets = {};
            c1 = 0;

            response.sum = 0;
            // To be taken out when we actually have the 'response.sum' parameter.
            $.each(response.poll_answers, function (index, value) {
                var numValue;

                numValue = parseFloat(value);
                if (isFinite(numValue) === false) {
                    return;
                }

                response.sum += numValue;
            });

            $.each(response.poll_answers, function (index, value) {
                var numValue;

                numValue = parseFloat(value);
                if (isFinite(numValue) === false) {
                    return;
                }

                c1 += 1;

                tickSets[c1.toFixed(1)] = _this.jsonConfig.answers[index]

                dataSeries.push({
                    'legend': _this.jsonConfig.answers[index],
                    'data': [[c1, (numValue / response.sum) * 100.0]]
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
                        'max': 100,
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
                    }
                }
            );

            /*
            _this.vertModEl.find('.xmodule_ConditionalModule').each(
                function (index, value) {
                    (new window[response.className]($(value)));
                }
            );
            */
        }
    );
} // End-of: 'submitAnswer': function (answer, answerEl) {
}; // End-of: PollMain.prototype = {

return PollMain;

function PollMain(el) {
    var _this;

    this.vertModEl = $(el).parent().parent();
    if (this.vertModEl.length !== 1) {
        // We will work with a single DOM element that contains one question, and zero or more conditionals.
        return;
    }

    this.questionEl = $(el).find('.poll_question');
    if (this.questionEl.length !== 1) {
        // We require one question DOM element.
        logme('ERROR: PollMain constructor ');

        return;
    }

    // Just a safety precussion. If we run this code more than once, multiple 'click' callback handlers will be
    // attached to the same DOM elements. We don't want this to happen.
    if (this.vertModEl.attr('poll_main_processed') === 'true') {
        logme(
            'ERROR: PolMain JS constructor was called on a DOM element that has already been processed once.'
        );

        return;
    }

    // This element was not processed earlier.
    // Make sure that next time we will not process this element a second time.
    this.vertModEl.attr('poll_main_processed', 'true');

    try {
        this.jsonConfig = JSON.parse(this.questionEl.children('.poll_question_div').html());
    } catch (err) {
        logme(
            'ERROR: Invalid JSON config for poll ID "' + this.id + '".',
            'Error messsage: "' + err.message + '".'
        );

        return;
    }

    // Get the DOM id of the question.
    this.id = this.questionEl.attr('id');

    // Get the URL to which we will post the users answer to the question.
    this.ajax_url = this.questionEl.data('ajax-url');

    // Access this object inside inner functions.
    _this = this;

    this.questionHtmlMarkup = $('<div />').html(this.jsonConfig.question).text();
    this.questionEl.append(this.questionHtmlMarkup);

    $.each(this.jsonConfig.answers, function (index, value) {
        var answerEl;

        answerEl = $('<div class="poll_answer">' + value + '</li>');
        answerEl.on('click', function () {
            _this.submitAnswer(index, answerEl);
        });
        answerEl.appendTo(_this.questionEl);
    });

    // When the user selects and answer, we will set this flag to true.
    this.questionAnswered = false;

    this.graphAnswerEl = $('<div class="graph_answer"></div>');
    this.graphAnswerEl.hide();
    this.graphAnswerEl.appendTo(this.questionEl);

    logme('PollMain object: ', this);
} // End-of: function PollMain(el) {

}); // End-of: define('PollMain', ['logme'], function (logme) {

// End-of: (function (requirejs, require, define) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
