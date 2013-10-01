/**
 * Course import-related js.
 */

"use strict";
/**
 * Entry point for server feedback. Makes status list visible and starts
 * sending requests to the server for status updates.
 * @param {string} url The url to send Ajax GET requests for updates.
 */
var startServerFeedback = function (url){
    $('div.wrapper-status').removeClass('is-hidden');
    $('.status-info').show();
    getStatus(url, 500);
};

/**
 * Toggle the spin on the progress cog.
 * @param {boolean} isSpinning Turns cog spin on if true, off otherwise.
 */
var updateCog = function (elem, isSpinning) {
    var cogI = elem.find('i.icon-cog');
    if (isSpinning) { cogI.addClass("icon-spin");}
    else { cogI.removeClass("icon-spin");}
};

/**
 * Manipulate the DOM to reflect current status of upload.
 * @param {int} stageNo Current stage.
 */
var updateStage = function (stageNo){
    var all = $('ol.status-progress').children();
    var prevList = all.slice(0, stageNo);
    _.map(prevList, function (elem){
        $(elem).removeClass("is-not-started").removeClass("is-started").addClass("is-complete");
        updateCog($(elem), false);
    });
    var curList = all.eq(stageNo);
    curList.removeClass("is-not-started").addClass("is-started");
    updateCog(curList, true);
};

/**
 * Give error message at the list element that corresponds to the stage where
 * the error occurred.
 * @param {int} stageNo Stage of import process at which error occured.
 * @param {string} msg Error message to display.
 */
var stageError = function (stageNo, msg) {
    var all = $('ol.status-progress').children();
    // Make all stages up to, and including, the error stage 'complete'.
    var prevList = all.slice(0, stageNo + 1);
    _.map(prevList, function (elem){
        $(elem).removeClass("is-not-started").removeClass("is-started").addClass("is-complete");
        updateCog($(elem), false);
    });
    var message = msg || "There was an error with the upload";
    var elem = $('ol.status-progress').children().eq(stageNo);
    elem.removeClass('is-started').addClass('has-error');
    elem.find('p.copy').hide().after("<p class='copy error'>" + message + "</p>");
};

/**
 * Check for import status updates every `timemout` milliseconds, and update
 * the page accordingly.
 * @param {string} url Url to call for status updates.
 * @param {int} timeout Number of milliseconds to wait in between ajax calls
 *     for new updates.
 * @param {int} stage Starting stage.
 */
var getStatus = function (url, timeout, stage) {
    if (currentStage == 3 ) { return ;}
    if (window.stopGetStatus) { return ;}
    var currentStage = stage || 0;
    updateStage(currentStage);
    var time = timeout || 1000;
    $.getJSON(url,
        function (data) {
            setTimeout(function () {
                getStatus(url, time, data["ImportStatus"]);
            }, time);
        }
    );
};

/**
 * Update DOM to set all stages as complete, and stop asking for status
 * updates.
 */
var displayFinishedImport = function () {
    window.stopGetStatus = true;
    var all = $('ol.status-progress').children();
    _.map(all, function (elem){
        $(elem).removeClass("is-not-started").removeClass("is-started").addClass("is-complete");
        updateCog($(elem), false);
    });
};

/**
 * Update DOM to set all stages as not-started (for retrying an upload that
 * failed).
 */
var clearImportDisplay = function () {
    var all = $('ol.status-progress').children();
    _.map(all, function (elem){
        $(elem).removeClass("is-complete").
            removeClass("is-started").
            removeClass("has-error").
            addClass("is-not-started");
        $(elem).find('p.error').remove(); // remove error messages
        $(elem).find('p.copy').show();
        updateCog($(elem), false);
    });
    window.stopGetStatus = false;
};
