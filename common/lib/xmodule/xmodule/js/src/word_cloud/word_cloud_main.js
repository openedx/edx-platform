(function (requirejs, require, define) {
define('WordCloudMain', ['logme'], function (logme) {

    var hash = 0;

WordCloudMain.prototype = {

'submitAnswer': function () {
    var _this = this,
        data = {
            'student_words': []
        };

    this.wordCloudEl.find('input.input-cloud').each(function(index, value){
        data.student_words.push($(value).val());
    });

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        _this.ajax_url + '/' + 'submit', $.param(data),
        function (response) {
            if (response.status !== 'success') {
                logme('ERROR: ' + response.error);

                return;
            }

            _this.showWordCloud(response);
        }
    );

}, // End-of: 'submitAnswer': function (answer, answerEl) {

'showWordCloud': function(response){
    var words,
        _this = this,
        fill = d3.scale.category20(),
        maxSize, minSize;

    this.wordCloudEl.find('#input-cloud-section').hide();

    console.log('response: ', response);

    words = response.top_words;

    maxSize = 0;
    minSize = 10000;

    $.each(words, function (index, word) {
        if (word.size > maxSize) {
            maxSize = word.size;
        }
        if (word.size < minSize) {
            minSize = word.size;
        }
    });

    d3.layout.cloud().size([500, 500])
        .words(words)
        .rotate(function () {
            return ~~(Math.random() * 2) * 90;
        })
        .font('Impact')
        .fontSize(function (d) {
            var size;

            size = (d.size / maxSize) * 100;

            if (size < 20) {
                return 0;
            }

            return size;
        })
        .on('end', draw)
        .start();

    // End of executable code.
    return;

    function draw(words) {
        var el, firstWord = false;

        $('#word_cloud_d3_' + _this.hash).remove();

        el = $(
            '<div ' +
                'id="' + 'word_cloud_d3_' + _this.hash + '" ' +
                'style="display: block; width: 500px; height: auto; margin-left: auto; margin-right: auto;" ' +
            '></div>'
        );
        el.append('<h3>Your words:</h3>');
        $.each(response.student_words, function (index, value) {
            if (firstWord === false) {
                firstWord = true;
            } else {
                el.append(', ');
            }

            el.append(index + ': ' + (100.0 * (value / response.total_count)) + ' %');
        });
        el.append('<br /><br /><h3>Overall number of words: ' + response.total_count + '</h3><br />');
        _this.wordCloudEl.append(el);

        d3.select('#word_cloud_d3_' + _this.hash).append('svg')
            .attr('width', 500)
            .attr('height', 500)
            .append('g')
            .attr('transform', 'translate(190,250)')
            .selectAll('text')
            .data(words)
            .enter().append('text')
            .style('font-size', function (d) {
                return d.size + 'px';
            })
            .style('font-family', 'Impact')
            .style('fill', function (d, i) {
                return fill(i);
            })
            .attr('text-anchor', 'middle')
            .attr('transform', function (d) {
                return 'translate(' + [d.x, d.y] + ')rotate(' + d.rotate + ')';
            })
            .text(function (d) {
                return d.text;
            });
    }
}

}; // End-of: WordCloudMain.prototype = {

return WordCloudMain;

function WordCloudMain(el) {
    var _this = this;

    this.wordCloudEl = $(el).find('.word_cloud');
    if (this.wordCloudEl.length !== 1) {
        // We require one question DOM element.
        logme('ERROR: WordCloudMain constructor requires one word cloud DOM element.');

        return;
    }

    // Later on used to create a unique DOM element.
    hash += 1;
    this.hash = hash;

    this.configJson = null;
    try {
        this.configJson = JSON.parse(this.wordCloudEl.find('.word_cloud_div').html());
    } catch (err) {
        logme('ERROR: Incorrect JSON config was given.');
        logme(err.message);

        return;
    }

    if (this.configJson.submitted) {
        this.showWordCloud(this.configJson);

        return;
    }

    this.inputSaveEl = $(el).find('input.save');

    // Get the URL to which we will post the users words.
    this.ajax_url = this.wordCloudEl.data('ajax-url');

    this.inputSaveEl.on('click', function () {
        _this.submitAnswer();
    });

} // End-of: function WordCloudMain(el) {

}); // End-of: define('WordCloudMain', ['logme'], function (logme) {

// End-of: (function (requirejs, require, define) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
