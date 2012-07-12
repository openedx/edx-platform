// maintain compatibility with other CS50 libraries
var CS50 = CS50 || {};
CS50.Video.Render = CS50.Video.Render || {};

// question types
CS50.Video.QuestionMode = CS50.Video.Mode || {};
CS50.Video.QuestionMode.FLIP = 'flip';
CS50.Video.QuestionMode.PANEL = 'panel';

/**
 * Renderer for a multiple choice question
 *
 * @param container Container for question to be rendered within
 * @param data Question data
 * @param callback Response callback
 * @return Input element user types into
 *
 */
CS50.Video.Render.FreeResponse = function(container, data, callback) {
    // render question and input area placeholder
    var $container = $(container);
    $container.append('<h2>' + data.question + '</h2>');
    var $placeholder = $('<input type="text" class="txt-answer-location" />');
    $container.append($placeholder);

    // create input area that is absolutely positioned to avoid transform weirdness
    var $input = $('<input type="text" class="video50-txt-answer" />');
    setTimeout(function() {
        var offset = $placeholder.offset();
        $input.css({ position: 'absolute', 'top': offset.top + 'px', 'left': offset.left + 'px', 'z-index': 999 });
        $('body').append($input);
        $placeholder.css({ visibility: 'hidden' });
    }, 1000);

    // create submit button, hidden by default
    var $submit = $('<button class="btn btn-submit">Submit Response</button>').hide();
    $container.append($submit);

    // when submit button is pressed, check the answer
    $container.on('click', '.btn-submit', function(e) {
        // remove previous messages from the container
        var $container = $(this).parents('.question-content');
        $container.find('.alert').remove();

        // a correct answer matches the supplied regex
        if ($input.val().match(data.answer))
            var $message = $('<div class="alert alert-success"><strong>Correct!</strong></div>');       
        else
            var $message = $('<div class="alert alert-error">That\'s not the right answer, <strong>try again!</strong></div>');
    
        // display message
        $message.hide().appendTo($container).fadeIn('fast');

        e.preventDefault();
        return false;
    });

    // when answer is selected, make sure submit button is shown
    $('body').on('keyup', '.video50-txt-answer', function() {
        var $submit = $container.find('.btn-submit');

        // toggle submit button based on input state
        if ($input.val().match(/^\s*$/) && $submit.is(':visible'))
            $submit.fadeOut('fast');
        else if (!$submit.is(':visible'))
            $submit.fadeIn('fast');
    });

    return $input;
};

/**
 * Renderer for a multiple choice question
 *
 * @param container Container for question to be rendered within
 * @param data Question data
 * @param callback Response callback
 *
 */
CS50.Video.Render.MultipleChoice = function(container, data, callback) {
    // render question title
    var $container = $(container);
    $container.append('<h2>' + data.question + '</h2>');

    // display each choice
    $choices = $('<div class="question-choices">');
    _.each(data.choices, function(e, i) {
        $choices.append('<input id="' + i + '" type="radio" name="question" value="' + i + '" />' + 
            '<label for="' + i + '">' + e + '</label><br />');
    });

    // create submit button, hidden by default
    var $submit = $('<button class="btn btn-submit">Submit Response</button>').hide();

    // add display questions
    $container.append($choices);
    $container.append($submit);

    // when submit button is pressed, check the answer
    $container.on('click', '.btn-submit', function(e) {
        // remove previous messages from the container
        var $container = $(this).parents('.question-content');
        $container.find('.alert').remove();

        // the index of the selected answer must match the correct answer
        if (data.answer == $container.find('input[type=radio]:checked').val())
            var $message = $('<div class="alert alert-success"><strong>Correct!</strong></div>');       
        else
            var $message = $('<div class="alert alert-error">That\'s not the right answer, <strong>try again!</strong></div>');
    
        // display message
        $message.hide().appendTo($container).fadeIn('fast');

        e.preventDefault();
        return false;
    });

    // when answer is selected, make sure submit button is show
    $container.on('click', '.question-choices input[type=radio]', function() {
        $submit = $container.find('.btn-submit');
        if (!$submit.is(':visible')) {
            $submit.fadeIn('fast');
        }
    });
};

/**
 * Renderer for a question with a numeric answer
 *
 * @param container Container for question to be rendered within
 * @param data Question data
 * @param callback Response callback 
 *
 */
CS50.Video.Render.Numeric = function(container, data, callback) {
    // if no tolerance given, then assume exact answer
    data.tolerance = (data.tolerance === undefined) ? 1 : data.tolerance;

    // render free response
    var $input = CS50.Video.Render.FreeResponse(container, data, callback);

    // swap out event handler
    var $container = $(container);
    $container.off('click', '.btn-submit');

    // when submit is pressed, check answer
    $container.on('click', '.btn-submit', function(e) {
        var val = parseFloat($input.val());

        // a correct answer is within the bounds established by the tolerance
        if (isNaN(val))
            var $message = $('<div class="alert alert-error">The answer must be a number, <strong>try again!</strong></div>');
        else if (val <= data.answer + data.answer * data.tolerance && val >= data.answer - data.answer * data.tolerance)
            var $message = $('<div class="alert alert-success"><strong>Correct!</strong></div>');       
        else
            var $message = $('<div class="alert alert-error">That\'s not the right answer, <strong>try again!</strong></div>');

        // display message
        $container.find('.alert').remove();
        $message.hide().appendTo($container).fadeIn('fast');

        e.preventDefault();
        return false;
    });
};

/**
 * Renderer for a true/false question
 *
 * @param container Container for question to be rendered within
 * @param data Question data
 * @param callback Response callback
 *
 */
CS50.Video.Render.TrueFalse = function(container, data, callback) {
    // true/false is really just multiple choice
    CS50.Video.Render.MultipleChoice(container, {
        answer: !data.answer,
        choices: ['True', 'False'],
        id: data.id,
        mode: data.mode,
        question: data.question,
        tags: data.tags,
    }, callback);
};
