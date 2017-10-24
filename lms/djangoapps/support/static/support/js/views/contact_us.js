(function (define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'support/js/models/file',
        'text!support/templates/upload_file.underscore',
        'text!support/templates/form_errors.underscore'

    ], function (Backbone, _, FileModel, FileTemplate, ErrorsTemplate) {
        return Backbone.View.extend({
            //TODO remove hard coded url token and keys https://openedx.atlassian.net/browse/LEARNER-2736
            accessToken: 'd6ed06821334b6584dd9607d04007c281007324ed07e087879c9c44835c684da',

            events: {
                'change #attachment': 'selectFile',
                'click .remove-upload': 'removeFile',
                'click .btn-submit': 'submitForm'
            },

            selectFile: function (e) {
                var url = 'https://arbisoft.zendesk.com/api/v2/uploads.json?filename=',
                    file = e.target.files[0],
                    request = new XMLHttpRequest(),
                    $fileContainer = this.$el.find('.files-container'),
                    $progressContainer = this.$el.find('.progress-container'),
                    fileReader = new FileReader(),
                    maxFileSize = 5000000,  //5mb is max limit
                    allowedFileTypes = ['gif', 'png', 'jpg', 'jpeg', 'pdf'],
                    fileModel,
                    responseData;

                // remove file from input and upload it to zendesk after validation
                $(e.target).val("");

                if (file.size > maxFileSize) {
                    this.showErrors([gettext('File must be smaller than 5 MB in size.')]);
                    return
                } else if ($.inArray(file.name.split('.').pop().toLowerCase(), allowedFileTypes) === -1) {
                    this.showErrors([gettext('Please select image or pdf file!')]);
                    return
                }

                request.open('POST', (url + file.name), true);
                request.setRequestHeader("Authorization", "Bearer " + this.accessToken);
                request.setRequestHeader("Content-Type", "image/jpeg");

                fileReader.readAsArrayBuffer(file);

                fileReader.onloadend = function () {
                    // show progress container
                    $progressContainer.removeClass('hidden');
                    $progressContainer.find('.file-name').html(file.name);
                    request.send(fileReader.result);

                };

                request.upload.addEventListener("progress", function (e) {
                    if (e.lengthComputable) {
                        var percentComplete = (e.loaded / e.total) * 100;
                        $progressContainer.find('.progress-bar').css({"width": percentComplete + "%"});
                    }
                });

                request.onreadystatechange = function () {
                    if (request.readyState === 4 && request.status === 201) {
                        responseData = JSON.parse(request.response);
                        fileModel = new FileModel({
                            'fileName': file.name,
                            'fileToken': responseData['upload'].token
                        });
                        $fileContainer.append(_.template(FileTemplate)(fileModel.toJSON()));
                        resetProgressBar();
                    }
                };

                this.$el.find(".abort-upload").click(function (e) {
                    e.preventDefault();
                    request.abort();
                });

                request.addEventListener("abort", function (e) {
                    resetProgressBar();
                });

                function resetProgressBar() {
                    $progressContainer.addClass('hidden');
                    $progressContainer.find('.progress-bar').addClass('zero-width');
                }
            },

            removeFile: function (e) {
                e.preventDefault();
                var fileToken = e.target.id,
                    fileRow = $(e.target).closest('.row'),
                    url = 'https://arbisoft.zendesk.com/api/v2/uploads/' + fileToken + '.json',
                    request = new XMLHttpRequest();

                request.open('DELETE', url, true);
                request.setRequestHeader("Authorization", "Bearer " + this.accessToken);
                request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

                request.send();

                request.onreadystatechange = function () {
                    if (request.readyState === 4 && request.status === 204) {
                        fileRow.fadeOut();
                    }
                };
            },

            submitForm: function (e) {
                var url = 'https://arbisoft.zendesk.com/api/v2/tickets.json',
                    $userInfo = $('.user-info'),
                    request = new XMLHttpRequest(),
                    data,
                    course;

                data = {
                    "subject": $('#subject').val(),
                    "comment": {
                        "body": $('#message').val(),
                        "uploads": $.map($(".files-container a"), function (n, i) {
                            return n.id;
                        })
                    }
                };

                if ($userInfo.length) {
                    data['requester'] = $userInfo.data('email');
                    course = $('#course').find(":selected").text();

                } else {
                    data['requester'] = $('#email').val();
                    course = $('#course').val();
                }

                //TODO remove hard coded id of custom field
                data['custom_fields'] = [{
                    'id': '114099484092',
                    'value': course
                }];

                //before submit validate data
                if (this.validateData(data)) {

                    request.open('POST', url, true);
                    request.setRequestHeader("Authorization", "Bearer " + this.accessToken);
                    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

                    request.send(JSON.stringify({
                        "ticket": data
                    }));

                    request.onreadystatechange = function () {
                        if (request.readyState === 4 && request.status === 201) {
                            //TODO https://openedx.atlassian.net/browse/LEARNER-2735
                            alert("request submited successfully.");
                        }
                    };
                }
            },

            validateData: function (data) {
                var errors = [],
                    regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;

                if (!data['subject']) {
                    errors.push(gettext('You must enter a subject before submitting.'));
                    $('#subject').closest('.form-group').addClass('has-error');
                }
                if (!data['comment']['body']) {
                    errors.push(gettext('You must enter a message before submitting.'));
                    $('#message').closest('.form-group').addClass('has-error');
                }
                if (!data['requester']) {
                    errors.push(gettext('You must enter email before submitting.'));
                    $('#email').closest('.form-group').addClass('has-error');
                } else if (!regex.test(data['requester'])) {
                    errors.push(gettext('You must enter a valid email before submitting.'));
                    $('#email').closest('.form-group').addClass('has-error');
                }

                if (!errors.length) {
                    return true;
                }

                this.showErrors(errors);
                return false;
            },

            showErrors: function (errors) {
                var $errorContainer = this.$el.find('.form-errors');
                $errorContainer.html(_.template(ErrorsTemplate)({'errors': errors}));

                $('body').animate({
                    scrollTop: $errorContainer.offset().top
                }, 1000);
            }
        });
    });
}).call(this, define || RequireJS.define);
