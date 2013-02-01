(function (requirejs, require, define) { define('PollMain', ['logme'], function (logme) { return {


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

'submitAnswer': function (event, pollObj, vote_type) {
    var answer, _this;

    _this = this;

    answer = {
        'vote_type': vote_type,
        'id': pollObj.id
    };
    logme('We are sending the following answer: ', answer);

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        pollObj.ajax_url + '/submit_answer',  answer,
        function (response) {
            logme('The following response was received: ' + JSON.stringify(response));

            // Show the answer from server.
            pollObj.graph_answer.show();

            // Show the next poll in series, and disable the current poll's submit and radio buttons.
            if (pollObj[vote_type + 'Id'] !== '') {
                _this.pollObjects[pollObj[vote_type + 'Id']].el.appendTo(_this.element);
                _this.pollObjects[pollObj[vote_type + 'Id']].el.show();
            }

            // function disableClick (event) {
            //     event.preventDefault();
            //     return false;
            // }
            // pollObj.upvote.click(disableClick);
            // pollObj.downvote.click(disableClick);

            jQuery.plot(
                pollObj.graph_answer,
                [
                    [[1, response.upvotes / (response.upvotes + response.downvotes)   ]],
                    [[2, response.downvotes / (response.upvotes + response.downvotes) ]]
                ],
                {
                    'xaxis': {
                        'min': 0,
                        'max': 3,
                        'tickFormatter': function formatter(val, axis) {
                            var valStr;

                            valStr = val.toFixed(axis.tickDecimals);

                            if (valStr === '1.0') {
                                return 'Yes / Upvote';
                            } else if (valStr === '2.0') {
                                return 'No / Downvote';
                            } else { return ''; }
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
        }
    );
},

'initialize': function (element) {
    var _this, jsonConfig, c1, obj, strQuestion;

    if (element.attr('poll_main_processed') === 'true') {
        // This element was already processed once.
        return;
    }
    // Make sure that next time we will not process this element a second time.
    element.attr('poll_main_processed', 'true');

    // Access PollMain instance inside inner functions created by $.each() iterator.
    _this = this;

    if (this.hasOwnProperty('pollObjects') === false) {
        this.pollObjects = {};
    }

    this.element = element;

    try {
        jsonConfig = JSON.parse(element.children('.poll_div').html());
    } catch (err) {
        logme(
            'ERROR: Invalid JSON config for poll ID "' + element.id + '".',
            'Error messsage: "' + err.message + '".'
        );

        return;
    }

    logme('JSON config:', jsonConfig);
    logme('jsonConfig.poll_chain.length = ' + jsonConfig.poll_chain.length);

    for (c1 = 0; c1 < jsonConfig.poll_chain.length; c1 += 1) {
        obj = {};

        this.pollObjects[obj.id] = obj;

        obj.id = jsonConfig.poll_chain[c1].id;
        obj.upvoteId = jsonConfig.poll_chain[c1].upvote_id;
        obj.downvoteId = jsonConfig.poll_chain[c1].downvote_id;
        obj.showStats = jsonConfig.poll_chain[c1].show_stats === 'yes';
        obj.ajax_url = element.data('ajax-url');

        strQuestion = $('<div />').html(jsonConfig.poll_chain[c1].question).text();

        obj.el = $(
            '<div id="poll-' + c1 + '" class="polls" style="' + ((c1 === 0) ? '' : 'display: none;') + '">' +
                strQuestion +
                '<div style="width: 500px; height: 150px; margin-left: auto; margin-right: auto;">' +
                    '<div id="vote_block-' + c1 + '" class="vote_blocks" style="display: inline; float: left; clear: none;">' +
                        '<ul>' +
                            '<li>' +
                                '<input type="radio" id="poll-vote-' + c1 + '-1" name="vote_' + c1 + '-1" value="1" />' +
                                '<label for="poll-vote-' + c1 + '-1">Yes</label>' +
                            '</li>' +
                            '<li>' +
                                '<input type="radio" id="poll-vote-' + c1 + '-2" name="vote_' + c1 + '-2" value="2" />' +
                                '<label for="poll-vote-' + c1 + '-2">No</label>' +
                            '</li>' +
                        '</ul>' +
                    '</div>' +
                    '<div class="submit-button" style="display: inline; float: left; clear: none; margin: 2.5rem;">' +
                        '<input type="button" value="Cast Your vote" class=".submit-button" name="vote" />' +
                    '</div>' +
                '</div>' +
                '<div class="graph_answer" style="display: none; clear: both;"></div>' +
            '</div>'
        );

        obj.el.find('input').each(function (index, value) {
            var val, type;

            val = $(value).val();
            if (val == '1') {
                type = 'upvote';
            } else if (val == '2') {
                type = 'downvote';
            } else {
                logme('ERROR: Not a valid input value.');

                return;
            }

            $(value).on('click', function (event) {
                _this.submitAnswer(event, obj, type);
            });
        });

        obj.el.appendTo(element);
    }
}

}; }); }(RequireJS.requirejs, RequireJS.require, RequireJS.define));
