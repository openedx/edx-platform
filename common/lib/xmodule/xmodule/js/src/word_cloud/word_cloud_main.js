/**
 * @file The main module definition for Word Cloud XModule.
 *
 *  Defines a constructor function which operates on a DOM element. Either show the user text inputs so
 *  he can enter words, or render his selected words along with the word cloud representing the top words.
 *
 *  @module WordCloudMain
 *
 *  @exports WordCloudMain
 *
 *  @external d3, $, RequireJS
 */

(function (requirejs, require, define) {
define('WordCloudMain', [], function () {

    /**
     * @function WordCloudMain
     *
     * This function will process all the attributes from the DOM element passed, taking all of
     * the configuration attributes. It will either then attach a callback handler for the click
     * event on the button in the case when the user needs to enter words, or it will call the
     * appropriate mehtod to generate and render a word cloud from user's enetered words along with
     * all of the other words.
     *
     * @constructor
     *
     * @param {jQuery} el DOM element where the word cloud will be processed and created.
     */
    var WordCloudMain = function (el) {
        var _this = this;

        this.wordCloudEl = $(el).find('.word_cloud');

        // Get the URL to which we will post the users words.
        this.ajax_url = this.wordCloudEl.data('ajax-url');

        // Dimensions of the box where the word cloud will be drawn.
        this.width = 635;
        this.height = 635;

        // Hide WordCloud container before Ajax request done
        this.wordCloudEl.hide();

        // Retriveing response from the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + 'get_state', null,
            function (response) {
                if (response.status !== 'success') {
                    console.log('ERROR: ' + response.error);

                    return;
                }

                _this.configJson = response;
            }
        )
        .done(function () {
            // Show WordCloud container after Ajax request done
            _this.wordCloudEl.show();

            if (_this.configJson && _this.configJson.submitted) {
                _this.showWordCloud(_this.configJson);

                return;
            }
        });

        $(el).find('input.save').on('click', function () {
            _this.submitAnswer();
        });
    }; // End-of: var WordCloudMain = function (el) {

    /**
     * @function submitAnswer
     *
     * Callback to be executed when the user eneter his words. It will send user entries to the
     * server, and upon receiving correct response, will call the function to generate the
     * word cloud.
     */
    WordCloudMain.prototype.submitAnswer = function () {
        var _this = this,
            data = {'student_words': []};

        // Populate the data to be sent to the server with user's words.
        this.wordCloudEl.find('input.input-cloud').each(function (index, value) {
            data.student_words.push($(value).val());
        });

        // Send the data to the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + 'submit', $.param(data),
            function (response) {
                if (response.status !== 'success') {
                    console.log('ERROR: ' + response.error);

                    return;
                }

                _this.showWordCloud(response);
            }
        );

    }; // End-of: WordCloudMain.prototype.submitAnswer = function () {

    /**
     * @function showWordCloud
     *
     * @param {object} response The response from the server that contains the user's entered words
     * along with all of the top words.
     *
     * This function will set up everything for d3 and launch the draw method. Among other things,
     * iw will determine maximum word size.
     */
    WordCloudMain.prototype.showWordCloud = function (response) {
        var words,
            _this = this,
            maxSize, minSize, scaleFactor, maxFontSize, minFontSize;

        this.wordCloudEl.find('.input_cloud_section').hide();

        words = response.top_words;
        maxSize = 0;
        minSize = 10000;
        scaleFactor = 1;
        maxFontSize = 200;
        minFontSize = 15;

        // Find the word with the maximum percentage. I.e. the most popular word.
        $.each(words, function (index, word) {
            if (word.size > maxSize) {
                maxSize = word.size;
            }
            if (word.size < minSize) {
                minSize = word.size;
            }
        });

        // Find the longest word, and calculate the scale appropriately. This is
        // required so that even long words fit into the drawing area.
        //
        // This is a fix for: if the word is very long and/or big, it is discarded by
        // for unknown reason.
        $.each(words, function (index, word) {
            var tempScaleFactor = 1.0,
                size = ((word.size / maxSize) * maxFontSize);

            if (size * 0.7 * word.text.length > _this.width) {
                tempScaleFactor = ((_this.width / word.text.length) / 0.7) / size;
            }

            if (scaleFactor > tempScaleFactor) {
                scaleFactor = tempScaleFactor;
            }
        });

        // Update the maximum font size based on the longest word.
        maxFontSize *= scaleFactor;

        // Generate the word cloud.
        d3.layout.cloud().size([this.width, this.height])
            .words(words)
            .rotate(function () {
                return Math.floor((Math.random() * 2)) * 90;
            })
            .font('Impact')
            .fontSize(function (d) {
                var size = (d.size / maxSize) * maxFontSize;

                size = size >= minFontSize ? size : minFontSize;

                return size;
            })
            .on('end', function (words, bounds) {
                // Draw the word cloud.
                _this.drawWordCloud(response, words, bounds);
            })
            .start();
    }; // End-of: WordCloudMain.prototype.showWordCloud = function (response) {

    /**
     * @function drawWordCloud
     *
     * This function will be called when d3 has finished initing the state for our word cloud,
     * and it is ready to hand off the process to the drawing routine. Basically set up everything
     * necessary for the actual drwing of the words.
     *
     * @param {object} response The response from the server that contains the user's entered words
     * along with all of the top words.
     *
     * @param {array} words An array of objects. Each object must have two properties. One property
     * is 'text' (the actual word), and the other property is 'size' which represents the number that the
     * word was enetered by the students.
     *
     * @param {array} bounds An array of two objects. First object is the top-left coordinates of the bounding
     * box where all of the words fir, second object is the bottom-right coordinates of the bounding box. Each
     * coordinate object contains two properties: 'x', and 'y'.
     */
    WordCloudMain.prototype.drawWordCloud = function (response, words, bounds) {
            // Color words in different colors.
        var fill = d3.scale.category20(),

            // Will be populated by words the user enetered.
            studentWordsKeys = [],

            // Comma separated string of user enetered words.
            studentWordsStr,

            // By default we do not scale.
            scale = 1,

            // Caсhing of DOM element
            cloudSectionEl = this.wordCloudEl.find('.result_cloud_section'),

            // Needed for caсhing of d3 group elements
            groupEl;

        // If bounding rectangle is given, scale based on the bounding box of all the words.
        if (bounds) {
            scale = 0.5 * Math.min(
                this.width / Math.abs(bounds[1].x - this.width / 2),
                this.width / Math.abs(bounds[0].x - this.width / 2),
                this.height / Math.abs(bounds[1].y - this.height / 2),
                this.height / Math.abs(bounds[0].y - this.height / 2)
            );
        }

        $.each(response.student_words, function (word, stat) {
            var percent = (response.display_student_percents) ? ' ' + (Math.round(100 * (stat / response.total_count))) + '%' : '';

            studentWordsKeys.push('<strong>' + word + '</strong>' + percent);
        });
        studentWordsStr = '' + studentWordsKeys.join(', ');

        cloudSectionEl
            .addClass('active')
            .find('.your_words').html(studentWordsStr)
            .end()
            .find('.total_num_words').html(response.total_count);

        $(cloudSectionEl.attr('id') + ' .word_cloud').empty();

        // Actual drawing of word cloud.
        groupEl = d3.select('#' + cloudSectionEl.attr('id') + ' .word_cloud').append('svg')
                .attr('width', this.width)
                .attr('height', this.height)
                .append('g')
                .attr('transform', 'translate(' + (0.5 * this.width) + ',' + (0.5 * this.height) + ')')
                .selectAll('text')
                .data(words)
                .enter().append('g');

        groupEl
            .append('title')
            .text(function (d) {
                var res = '';

                $.each(response.top_words, function(index, value){
                    if (value.text === d.text) {
                        res = value.percent + '%';

                        return;
                    }
                });

                return res;
            });

        groupEl
            .append('text')
            .style('font-size', function (d) {
                return d.size + 'px';
            })
            .style('font-family', 'Impact')
            .style('fill', function (d, i) {
                return fill(i);
            })
            .attr('text-anchor', 'middle')
            .attr('transform', function (d) {
                return 'translate(' + [d.x, d.y] + ')rotate(' + d.rotate + ')scale(' + scale + ')';
            })
            .text(function (d) {
                return d.text;
            });
    }; // End-of: WordCloudMain.prototype.drawWordCloud = function (words, bounds) {

    return WordCloudMain;

}); // End-of: define('WordCloudMain', [], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
