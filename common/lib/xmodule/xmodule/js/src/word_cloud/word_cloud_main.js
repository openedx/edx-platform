(function (requirejs, require, define) {
define('WordCloudMain', ['logme'], function (logme) {

WordCloudMain.prototype = {

'submitAnswer': function (answer, answerObj) {
    var _this;

    _this = this;

    console.log('submit answer');

    answerObj.buttonEl.addClass('answered');

    // Send the data to the server as an AJAX request. Attach a callback that will
    // be fired on server's response.
    $.postWithPrefix(
        _this.ajax_url + '/' + answer,  {},
        function (response) {
            console.log('success! response = ');
            console.log(response);


            _this.showWordCloud(response.poll_answers, response.total);

        }
    );

}, // End-of: 'submitAnswer': function (answer, answerEl) {

'showWordCloud': function(){
    console.log('TADAM!!!')
},

}; // End-of: WordCloudMain.prototype = {

return WordCloudMain;

function WordCloudMain(el) {
    var _this;

    this.questionEl = $(el).find('.poll_question');
    if (this.questionEl.length !== 1) {
        // We require one question DOM element.
        logme('ERROR: WordCloudMain constructor requires one question DOM element.');

        return;
    }

    // Access this object inside inner functions.
    _this = this;

    this.submitAnswer(this.questionEl)
} // End-of: function WordCloudMain(el) {

}); // End-of: define('WordCloudMain', ['logme'], function (logme) {

// End-of: (function (requirejs, require, define) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
