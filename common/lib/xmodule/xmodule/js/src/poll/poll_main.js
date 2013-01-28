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

    logme('We are sending the following data: ' + vote_type);

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        pollObj.ajax_url + '/submit_answer',  vote_type,
        function (response) {
            var color;

            logme('The following response was received: ' + JSON.stringify(response));

            // Show the answer from server.
            pollObj.graph_answer.show();

            // Show the next poll in series, and disable the current poll's submit and radio buttons.
            if (pollObj.nextPollObj !== null) {
                pollObj.nextPollObj.element.show();
            }

            function disableClick (event) {
                event.preventDefault();
                return false;
            }
            pollObj.upvote.click(disableClick);
            pollObj.downvote.click(disableClick);

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
    var _this, prevPollObj;

    console.log('four');

    if (element.attr('poll_main_processed') === 'true') {
        // This element was already processed once.
        return;
    }

    // Make sure that next time we will not process this element a second time.
    element.attr('poll_main_processed', 'true');

    // Access PollMain instance inside inner functions created by $.each() iterator.
    _this = this;

    // Helper object which will help create a chain of poll objects.
    // Initially there is no previous poll object, so we initialize this reference to null.
    prevPollObj = null;

    element.children('.polls').each(function (index, value) {
        var pollObj;

        // Poll object with poll configuration and properties.
        pollObj = {
            'element': $(value), // Current poll DOM element (jQuery object).
            'id': $(value).prop('id'), // ID of DOM element with current poll.
            'pollId': element.prop('id'), // ID of DOM element which contains all polls.
            'ajax_url': element.data('ajax-url'),
            'upvote': $(value).find('.upvote'),
            'downvote': $(value).find('.downvote'),
            'vote_blocks': $(value).find('.vote_blocks'),
            'graph_answer': $(value).find('.graph_answer')
        };

        pollObj.graph_answer.css({
                'width': 400,
                'height': 400,
                'margin-left': 'auto',
                'margin-right': 'auto',
                'margin-bottom': 15
            });

        // Set up a reference to current poll object in previous poll object.
        // Reference to next poll object is initialized to null.
        if (prevPollObj !== null) {
            prevPollObj.nextPollObj = pollObj;
        }
        prevPollObj = pollObj;
        pollObj.nextPollObj = null;

        // Attach a handler to the submit button, which will pass the current poll object.
        pollObj.upvote.click(function (event) {
            _this.submitAnswer(event, pollObj, 'upvote');
        });
        pollObj.downvote.click(function (event) {
            _this.submitAnswer(event, pollObj,'downvote');
        });
    });
}

}; }); }(RequireJS.requirejs, RequireJS.require, RequireJS.define));
