// maintain compatibility with other CS50 libraries
var CS50 = CS50 || {};

/**
 * CS50 Video constructor
 *
 * @param options Player options
 *
 */
CS50.Video = function(options) {
    this.options = options;

    // make sure default options are defined
    if (!this.options.playerContainer)
        throw 'Error: You must define a container for the player!';
    if (!this.options.notificationsContainer)
        throw 'Error: You must define a container for the list of questions!';
    if (!this.options.video)
        throw 'Error: You must define a video to play!';

    // specify default values for optional parameters
    this.options.autostart = (options.autostart === undefined) ? true : options.autostart;
    this.options.defaultLanguage = (options.defaultLanguage === undefined) ? 'en' : options.defaultLanguage;
    this.options.height = (options.height === undefined) ? 360 : options.height;
    this.options.playbackRates = (options.playbackRates === undefined) ? [0.75, 1, 1.25, 1.5] : options.playbackRates;
    this.options.questions = (options.questions === undefined) ? [] : options.questions;
    this.options.srt = (options.srt === undefined) ? null : options.srt;
    this.options.swf = (options.swf === undefined) ? './flashmediaelement.swf' : options.swf;
    this.options.title = (options.title === undefined) ? '' : options.title;
    this.options.width = (options.width === undefined) ? 640 : options.width;

    // templates for plugin
    var templateHtml = {
        panelQuestion: ' \
            <div class="video50-question"> \
                <button type="button" class="panel-close close">&times;</button> \
                <div class="question-content"></div> \
            </div> \
        ',

        playbackControls: ' \
            <div class="video50-playback-controls"> \
                <ul class="nav nav-pills"> \
                    <% for (var i in rates) { %> \
                        <li data-rate="<%= rates[i] %>" class="btn-playback-rate"> \
                            <a href="#"><%= rates[i] %>x</a> \
                        </li> \
                    <% } %> \
                </ul> \
            </div> \
        ',

        player: ' \
            <div class="video50-player" style="width: <%= width %>px; height: <%= 38 + height %>px"> \
                <div class="player-navbar"> \
                    <button class="btn btn-back"><i class="icon-arrow-left"></i> Back</button> \
                    <div class="player-navbar-title"><%= title %></div> \
                </div> \
                <div class="flip-container"> \
                    <div class="video-container" style="width: <%= width %>px; height: <%= height %>px"> \
                        <video width="<%= width %>" height="<%= height %>" class="video-player" controls="controls"> \
                            <% if (srt) { %> \
                                <track kind="subtitles" src="<%= srt[defaultLanguage] %>" srclang="<%= defaultLanguage %>" /> \
                                <% for (var i in srt) { %> \
                                    <% if (i != defaultLanguage) { %> \
                                        <track kind="subtitles" src="<%= srt[i] %>" srclang="<%= i %>" /> \
                                    <% } %> \
                                <% } %> \
                            <% } %> \
                            <source type="video/mp4" src="<%= video %>" /> \
                            <object width="<%= width %>" height="<%= height %>" type="application/x-shockwave-flash" data="<%= swf %>"> \
                                <param name="movie" value="<%= swf %>" /> \
                                <param name="flashvars" value="controls=true&file=<%= video %>" /> \
                            </object> \
                        </video> \
                    </div> \
                    <div class="flip-question-container video50-question" style="width: <%= width %>px; height: <%= height %>px"> \
                        <div class="question-content"></div> \
                    </div> \
                </div> \
            </div> \
        ',

        notifications: ' \
            <div class="video50-notifications"> \
                <table class="table table-bordered table-striped"> \
                    <thead> \
                        <tr> \
                            <td class="video50-available-questions-td"> \
                                <strong class="video50-available-questions">Available Questions</strong> \
                                <button class="btn video50-notifications-btn"> \
                                    <input id="video50-notifications-auto" type="checkbox" /> \
                                    <label for="video50-notifications-auto">Automatically go to new questions</label> \
                                </button> \
                            </td> \
                        </tr> \
                    </thead> \
                    <tbody></tbody> \
                </table> \
            </div> \
        ',

        notification: ' \
            <tr data-question-id="<%= question.question.id %>"> \
                <td > \
                    <a href="#" rel="tooltip" title="<%= question.question.question %>"> \
                        <%= question.question.tags.join(", ") %> \
                    </a> \
                </td> \
            </tr> \
        ',

        transcript: ' \
            <div class="video50-transcript"> \
                <div class="video50-transcript-controls-wrapper"> \
                    <button class="btn"> \
                        <input id="video50-transcript-auto" type="checkbox" checked="checked" /> \
                        <label for="video50-transcript-auto">Automatically scroll transcript</label> \
                    </button> \
                    <div class="video50-transcript-lang btn-group"> \
                        <a class="btn dropdown-toggle" data-toggle="dropdown" href="#"> \
                            <%= language %> <span class="caret"></span> \
                        </a> \
                        <ul class="dropdown-menu"> \
                            <% for (var i in srt) { %> \
                                <% if (i != language) { %> \
                                    <li> \
                                        <a href="#" data-lang="<%= i %>"><%= i %></a> \
                                    </li> \
                                <% } %> \
                            <% } %> \
                        </ul> \
                    </div> \
                </div> \
                <div class="video50-transcript-container"> \
                    <div class="video50-transcript-text"> \
                    </div> \
                </div> \
            </div> \
        '
    };

    // compile templates
    this.templates = {};
    for (var template in templateHtml)
        this.templates[template] = _.template(templateHtml[template]);

    // instantiate video
    this.createPlayer();
    this.createNotifications();
    this.loadSrt(this.options.defaultLanguage);
};

/**
 * Check if a new question is available, adding it to the notifications container if so
 *
 */
CS50.Video.prototype.checkQuestionAvailable = function() {
    // make sure notifications container is given
    if (!this.options.notificationsContainer)
        return;

    var player = this.player;
    var $container = $(this.options.notificationsContainer).find('tbody');

    // check if any of the given questions should be displayed at this timecode
    var me = this;
    _.each(this.options.questions, function(e, i) {
        // question should be shown if timecodes match and it isn't already shown
        if (e.timecode == Math.floor(player.getCurrentTime()) && 
                !$container.find('tr[data-question-id="' + e.question.id + '"]').length) {

            // don't take both actions on the same question
            if (me.currentQuestion != e.question.id) {
                // automatically go to the new question if user checked that box
                if ($(me.options.notificationsContainer).find('#video50-notifications-auto').is(':checked'))
                    me.showQuestion(e.question.id)

                // put question at the top of the list of available questions
                else {
                    $container.prepend(me.templates.notification({
                        question: e
                    })).find('[rel=tooltip]').tooltip({
                        placement: 'right'
                    });
                }
            }
        }
    })
};

/**
 * Create a new instance of the video player at the specified container
 *
 */
CS50.Video.prototype.createPlayer = function() {
    // create html for video player
    var $container = $(this.options.playerContainer);
    $container.html(this.templates.player({
        defaultLanguage: this.options.defaultLanguage,
        height: this.options.height,
        srt: this.options.srt,
        swf: this.options.swf,
        title: this.options.title,
        video: this.options.video,
        width: this.options.width
    }));

    // create video player
    var me = this;
    this.player = new MediaElementPlayer(this.options.playerContainer + ' .video-player', {
        timerRate: 500,
        success: function (player, dom) {
            // event handler for video moving forward
            player.addEventListener('timeupdate', function(e) {
                // check if a new question is available
                me.checkQuestionAvailable();

                // update highlight on the transcript
                me.updateTranscriptHighlight();
            }, false);

            // start video immediately if autostart is enabled
            if (me.options.autostart)
                player.play();

            // determine if browser is capable of variable playback speeds
            var canAdjustPlayback = player.pluginType != 'flash';

            // if playback rates are given, then display controls
            if (me.options.playbackRates.length && canAdjustPlayback) {
                // use explicit container if given, else simply put controls below video
                if (me.options.playbackContainer)
                    $(me.options.playbackContainer).html(me.templates.playbackControls({ 
                        rates: me.options.playbackRates 
                    }));
                else {
                    me.options.playbackContainer = $(me.templates.playbackControls({ 
                        rates: me.options.playbackRates 
                    }));
                    $container.after(me.options.playbackContainer);
                }

                // 1 is the default playback rate
                var $playbackContainer = $(me.options.playbackContainer);
                $playbackContainer.find('[data-rate="1"]').addClass('active');

                // when playback button is changed, alter rate of video
                $playbackContainer.on('click', '.btn-playback-rate', function(e) {
                    // highlight the current control and remove highlight from others
                    $(this).siblings().removeClass('active');
                    $(this).addClass('active');

                    // adjust video rate
                    me.player.media.playbackRate = parseFloat($(this).attr('data-rate'));

                    e.preventDefault();
                    return false;
                });
            }
        }
    });

    // when back button is pressed, return to video
    $container.on('click', '.btn-back', function(e) {
        // hide button
        $(this).fadeOut('medium');

        // start video and flip back
        me.player.play();
        $container.find('.flip-container').removeClass('flipped');

        // remove input
        $('.video50-txt-answer').remove();

        // fade video back in while flip is occurring for smoothness
        setTimeout(function() {
            $container.find('.video-container').fadeIn('medium');
        }, 500);
    });
};

/**
 * Create a new instance of the notification area at the specified container
 *
 */
CS50.Video.prototype.createNotifications = function() {
    // build notifications container
    var $container = $(this.options.notificationsContainer);
    $container.html(this.templates.notifications());

    // event handler for selecting a question to view
    var me = this;
    $container.on('click', 'a', function() {
        // display question
        var id = $(this).parents('[data-question-id]').attr('data-question-id');
        me.showQuestion(id);

        // remove selected question from list
        $(this).tooltip('hide');
        $(this).parents('tr').remove();
    });
};

/**
 * Load the specified SRT file
 *
 * @param lang Language to load
 *
 */
CS50.Video.prototype.loadSrt = function(language) {
    this.srtData = {};
    var player = this.player;
    var me = this;

    if (this.options.srt[language]) {
        $.get(this.options.srt[language], function(response) {
            var timecodes = response.split(/\n\s*\n/);

            // if transcript container is given, then build transcript
            if (me.options.transcriptContainer) {
                // create transcript container
                $(me.options.transcriptContainer).html(me.templates.transcript({
                    srt: me.options.srt,
                    language: language
                }));

                // clear previous text
                var $container = $(me.options.transcriptContainer).find('.video50-transcript-text');
                $container.empty();

                // iterate over each timecode
                var n = timecodes.length;
                for (var i = 0; i < n; i++) {
                    // split the elements of the timecode
                    var timecode = timecodes[i].split("\n");
                    if (timecode.length > 1) {
                        // extract time and content from timecode
                        var timestamp = timecode[1].split(" --> ")[0];
                        timecode.splice(0, 2);
                        var content = timecode.join(" ");

                        // if line starts with >> or [, then start a new line
                        if (content.match(/^(>>|\[)/))
                            $container.append('<br /><br />');

                        // convert from hours:minutes:seconds to seconds
                        var time = timestamp.match(/(\d+):(\d+):(\d+)/);
                        var seconds = parseInt(time[1], 10) * 3600 + parseInt(time[2], 10) * 60 + parseInt(time[3], 10);

                        // add line to transcript
                        $container.append('<a href="#" data-time="' + seconds + '">' + content + '</a>');
                    }
                }

                // when transcript language is changed, refresh srt data and captioning
                $(me.options.transcriptContainer).on('click', '.video50-transcript-lang a[data-lang]', function() {
                    // refresh transcript
                    var lang = $(this).attr('data-lang');
                    me.loadSrt(lang);

                    // change language in player if captions have been turned on by user
                    if ($(me.options.playerContainer).find('.mejs-captions-selector input[type=radio]:checked').attr('value') != 'none')
                        $(me.options.playerContainer).find('.mejs-captions-selector input[value="' + lang + '"]').click();
                });

                // when captioning is changed, refresh srt data
                $(me.options.playerContainer).on('click', '.mejs-captions-selector input[type=radio]', function() {
                    var lang = $(this).attr('value');

                    if (lang != 'none')
                        me.loadSrt(lang);
                });

                // when a line is clicked, seek to that time in the video
                $container.on('click', 'a', function() {
                    // determine timecode associated with line
                    var time = $(this).attr('data-time');

                    if (time)   
                        player.setCurrentTime(time);
                });

                // keep track of scroll state so we don't auto-seek the transcript when the user scrolls
                me.disableTranscriptAutoSeek = false;
                $(me.options.transcriptContainer).find('.video50-transcript-container').on('scrollstart', function() {
                    me.disableTranscriptAutoSeek = true;
                });
                $(me.options.transcriptContainer).find('.video50-transcript-container').on('scrollstop', function() {
                    me.disableTranscriptAutoSeek = false;
                });
            }
        });
    }
};

/**
 * Callback for logging question data
 * 
 * @param correct Whether or not the question was answered correctly
 * @param data Additional data to be logged by server
 *
 */
CS50.Video.prototype.renderCallback = function(correct, data) {
    return true;
};

/**
 * Show the question with the given ID
 *
 */
CS50.Video.prototype.showQuestion = function(id) {
    // determine question to show
    var question = _.find(this.options.questions, function(e) { return e.question.id == id; });

    if (question) {
        // keep track of the current question
        this.currentQuestion = id;

        // flip video over to display question
        if (question.mode == CS50.Video.QuestionMode.FLIP) {
            // stop video so we can think, think, thiiiiiink
            this.player.pause();

            // remove existing panel questions
            $('.video50-question .panel-close').click();

            // clear previous question contents and events
            var player = $(this.options.playerContainer);
            var $container = $(this.options.playerContainer).find('.flip-question-container .question-content');
            $container.empty().off();

            // render question
            question.question.render($container, question.question, CS50.Video.renderCallback);

            // flip player to show question
            $(this.options.playerContainer).find('.video-container').fadeOut('medium');
            $(this.options.playerContainer).find('.flip-container').addClass('flipped');

            // display back button
            setTimeout(function() {
                player.find('.btn-back').show();
            }, 100);
        }

        // display question in the specified panel while video plays
        else if (question.mode == CS50.Video.QuestionMode.PANEL) {
            // remove existing flip questions
            $('.video50-player .btn-back').click();

            // clear previous question contents and events
            var $container = $(this.options.questionContainer);
            $container.empty().off();

            // render question
            $container.hide().html(this.templates.panelQuestion()).fadeIn('fast');
            question.question.render($container.find('.question-content'), question.question, CS50.Video.renderCallback);

            // when x in top-right corner is clicked, remove the question
            $container.on('click', '.panel-close', function() {
                $container.find('.video50-question').fadeOut('fast', function() {
                    // remove question controls
                    $('.video50-txt-answer').remove();
                    $(this).remove();
                });
            });
        }
    }
};

/**
 * Highlight the line corresponding to the current point in the video in the transcript
 *
 */
CS50.Video.prototype.updateTranscriptHighlight = function() {
    var time = Math.floor(this.player.getCurrentTime());
    var $container = $(this.options.transcriptContainer);
    var $active = $container.find('[data-time="' + time + '"]');

    // check if a new element should be highlighted
    if ($active && $active.length) {
        // remove all other highlights
        $container.find('a').removeClass('highlight');

        // add highlight to active element
        $active.addClass('highlight');

        // put the current element in the middle of the transcript if user is not scrolling
        if (!this.disableTranscriptAutoSeek && $container.find('#video50-transcript-auto').is(':checked')) {
            var top = $active.position().top - parseInt($container.height() / 2);
            $container.find('.video50-transcript-container').animate({ scrollTop: top });
        }
    }
};
