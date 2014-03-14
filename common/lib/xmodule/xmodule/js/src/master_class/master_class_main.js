/**
 * @file The main module definition for Word Cloud XModule.
 *
 *  Defines a constructor function which operates on a DOM element. Either show the user text inputs so
 *  he can enter words, or render his selected words along with the word cloud representing the top words.
 *
 *  @module MasterClassMain
 *
 *  @exports MasterClassMain
 *
 *  @requires logme
 *
 *  @external $, RequireJS
 */

(function (requirejs, require, define) {
define('MasterClassMain', ['logme'], function (logme) {

    /**
     * @function MasterClassMain
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
    var MasterClassMain = function (el) {
        var _this = this;

        this.masterClassEl = $(el).find('.master_class');

        // Get the URL to which we will post the users words.
        this.ajax_url = this.masterClassEl.data('ajax-url');

        // Dimensions of the box where the word cloud will be drawn.
        this.width = 635;
        this.height = 635;

        // Hide MasterClass container before Ajax request done
        this.masterClassEl.hide();

        // Retriveing response from the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + 'get_state', null,
            function (response) {
                if (response.status !== 'success') {
                    logme('ERROR: ' + response.error);

                    return;
                }

                _this.configJson = response;
            }
        )
        .done(function () {
            // Show MasterClass container after Ajax request done
            _this.masterClassEl.show();

            if (_this.configJson) {
                _this.showMasterClass(_this.configJson);

                return;
            }
        });

        $(el).find('input.save').on('click', function () {
            _this.submitAnswer();
        });
        $(el).find('input.email-send').on('click', function () {
            _this.submitEmail();
        });
    }; // End-of: var MasterClassMain = function (el) {

    /**
     * @function submitAnswer
     *
     * Callback to be executed when the user eneter his words. It will send user entries to the
     * server, and upon receiving correct response, will call the function to generate the
     * word cloud.
     */
    MasterClassMain.prototype.submitAnswer = function () {
        var _this = this,
            data = {'master_class': '0'};

        // Populate the data to be sent to the server with user's words.
        this.masterClassEl.find('input.input-class').each(function (index, value) {
            data.master_class = $(value).val();
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

                _this.showMasterClass(response);
            }
        );

    }; // End-of: MasterClassMain.prototype.submitAnswer = function () {


    MasterClassMain.prototype.submitEmail = function () {
        var _this = this,
            data = {'master_class': '0'};

        // Populate the data to be sent to the server with user's words.
        


        // Send the data to the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + 'csv', $.param(data),
            function (response) {
                if (response.status !== 'success') {
                    logme('ERROR: ' + response.error);

                    return;
                }
            var csv = ConvertToCSV([response.data.header]) + ConvertToCSV(response.data.data);
            a=document.createElement('a');
            a.textContent='download';
            a.download="emails.csv";
            a.href='data:text/csv;charset=utf-8,'+escape(csv);
            a.click();
             }
        );

    }; // End-of: MasterClassMain.prototype.submitAnswer = function () {


     MasterClassMain.prototype.submitRegister = function (caller) {
        var _this = this,
            data = {'emails': []};

        // Populate the data to be sent to the server with user's words.
        data.emails.push($(caller).val());

        // Send the data to the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            _this.ajax_url + '/' + 'register', $.param(data),
            function (response) {
                if (response.status !== 'success') {
                    logme('ERROR: ' + response.error);

                    return;
                }

                _this.showMasterClass(response);
            }
        );
    };

    function ConvertToCSV(objArray) {
            var array = typeof objArray != 'object' ? JSON.parse(objArray) : objArray;
            var str = '';

            for (var i = 0; i < array.length; i++) {
                var line = '';
            for (var index in array[i]) {
                if (line != '') line += ','

                line += array[i][index];
            }

            str += line + '\r\n';
        }

        return str;
    }

    /**
     * @function showMasterClass
     *
     * @param {object} response The response from the server that contains the user's entered words
     * along with all of the top words.
     *
     * This function will set up everything for d3 and launch the draw method. Among other things,
     * iw will determine maximum word size.
     */
    MasterClassMain.prototype.showMasterClass = function (response) {
        var _this = this;

        if (response.submitted) {
            this.masterClassEl.find('.input_class_section').hide();
        }
        _this.drawMasterClass(response);
    }; // End-of: MasterClassMain.prototype.showMasterClass = function (response) {

    /**
     * @function drawMasterClass
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
    MasterClassMain.prototype.drawMasterClass = function (response) {
            // Color words in different colors.
        var fill = 
            // Caсhing of DOM element
            cloudSectionEl = this.masterClassEl.find('.result_class_section'),
            staffSectionEl = this.masterClassEl.find('.staff_information_section');

        gettext("You have been registered for this master class. We will provide addition information soon.")
        gettext("You are pending for registration for this master class. Please visit this page later for result.")
        cloudSectionEl
            .addClass('active');
        cloudSectionEl.find('.message').html(gettext(response.message));
        cloudSectionEl
            .find('.total_places').html(response.total_places);
        cloudSectionEl
            .find('.total_register').html(response.total_register);

        $(cloudSectionEl.attr('id') + ' .master_class').empty();

        if (response.is_staff) {
            staffSectionEl.removeClass('sr')
            var all_registrations = staffSectionEl.find('#all_registrations'),
                passed_registrations = staffSectionEl.find('#passed_registrations');
            $(all_registrations).empty()
            $(passed_registrations).empty()
            $.each(response.all_registrations, function(key, value)
                {
                    var li = $('<li/>')
                        .addClass('ui-menu-item')
                        .appendTo(all_registrations);
                    $('<input/>').addClass('add-button').attr('type', 'checkbox').attr('id', 'email_' + key).attr('value', value).appendTo(li);
                    $('<label/>').attr('for', 'email_' + key).html("<span></span>").appendTo(li);
                    $('<a/>')
                        .addClass('ui-all')
                        .text(value)
                        .appendTo(li);
                });
            $.each(response.passed_registrations, function(key, value)
                {
                    var li = $('<li/>')
                        .addClass('ui-menu-item')
                        .appendTo(passed_registrations);
                    $('<a/>')
                        .addClass('ui-all')
                        .text(value)
                        .appendTo(li);
                });
            var _this = this
            $(all_registrations).find('input.add-button').each( function(index, elem) {
            $(elem).on('click', function () {
                _this.submitRegister(this);
                });
            });
        }

    }; // End-of: MasterClassMain.prototype.drawMasterClass = function (words, bounds) {

    return MasterClassMain;

}); // End-of: define('MasterClassMain', ['logme'], function (logme) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
