(function (requirejs, require, define) {
define('WordCloudMain', ['logme'], function (logme) {

WordCloudMain.prototype = {

'submitAnswer': function () {
    var _this, sendData;

    sendData = {
        'data': []
    };

    _this = this;

    console.log('submit answer');
    this.wordCloudEl.find('input.input-cloud').each(function(index, value){
        sendData.data.push($(value).val());
    });

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        _this.ajax_url + '/' + 'submit', JSON.stringify(sendData),
        function (response) {
            if (
                (response.hasOwnProperty('status') !== true) ||
                (typeof response.status !== 'string') ||
                (response.status.toLowerCase() !== 'success')) {
                    console.log('Bad response!');
                    return;
            }
            console.log('success! response = ');
            console.log(response);
            _this.showWordCloud();
        }
    );

}, // End-of: 'submitAnswer': function (answer, answerEl) {

'showWordCloud': function(){
    console.log('Show word cloud.');
    
    inputSection = this.wordCloudEl.find('#input-cloud-section');
    resultSection = this.wordCloudEl.find('#result-cloud-section');
    
    resultSection.text('TODO: Word cloud canvas');
    inputSection.hide();
    resultSection.show();
},

}; // End-of: WordCloudMain.prototype = {

return WordCloudMain;

function WordCloudMain(el) {
    var _this;
    this.wordCloudEl = $(el).find('.word_cloud');
    if (this.wordCloudEl.length !== 1) {
        // We require one question DOM element.
        logme('ERROR: WordCloudMain constructor requires one word cloud DOM element.');

        return;
    }

    this.inputSaveEl = $(el).find('input.save');

    // Get the URL to which we will post the users words.
    this.ajax_url = this.wordCloudEl.data('ajax-url');

    _this = this;
    this.inputSaveEl.on('click', function () {
        _this.submitAnswer();
    });

} // End-of: function WordCloudMain(el) {

}); // End-of: define('WordCloudMain', ['logme'], function (logme) {

// End-of: (function (requirejs, require, define) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
