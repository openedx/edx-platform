define(["domReady", "jquery", "underscore", "js/utils/cancel_on_escape", "js/views/utils/create_course_utils",
    "js/views/utils/view_utils"],
    function (domReady, $, _, CancelOnEscape, CreateCourseUtilsFactory, ViewUtils) {
        var CreateCourseUtils = CreateCourseUtilsFactory({
            name: '.new-course-name',
            org: '.new-course-org',
            number: '.new-course-number',
            run: '.new-course-run',
            save: '.new-course-save',
            errorWrapper: '.wrap-error',
            errorMessage: '#course_creation_error',
            tipError: 'span.tip-error',
            error: '.error',
            allowUnicode: '.allow-unicode-course-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var saveNewCourse = function (e) {
            e.preventDefault();

            if (CreateCourseUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newCourseForm = $(this).closest('#create-course-form');
            var display_name = $newCourseForm.find('.new-course-name').val();
            var org = $newCourseForm.find('.new-course-org').val();
            var number = $newCourseForm.find('.new-course-number').val();
            var run = $newCourseForm.find('.new-course-run').val();
            var license = $newCourseForm.find('.license').val();

            course_info = {
                org: org,
                number: number,
                display_name: display_name,
                run: run,
                license: license
            };

            analytics.track('Created a Course', course_info);
            CreateCourseUtils.createCourse(course_info, function (errorMessage) {
                $('.wrap-error').addClass('is-shown');
                $('#course_creation_error').html('<p>' + errorMessage + '</p>');
                $('.new-course-save').addClass('is-disabled');
            });
        };

        var cancelNewCourse = function (e) {
            e.preventDefault();
            $('.new-course-button').removeClass('is-disabled');
            $('.wrapper-create-course').removeClass('is-shown');
            // Clear out existing fields and errors
            _.each(
                ['.new-course-name', '.new-course-org', '.new-course-number', '.new-course-run', '#create-course-form .license'],
                function (field) {
                    $(field).val('');
                }
            );
            $('#course_creation_error').html('');
            $('.wrap-error').removeClass('is-shown');
            $('.new-course-save').off('click');
        };

        var toggleLicenseForm = function(e) {
            var button = $(e.srcElement);
            var selector = button.closest('.course-item').find('.license-selector');

            selector.toggleClass('is-shown');

            if (selector.hasClass('is-shown')) {
                // Toggle button text
                button.text('Save')
            }
            else {
                // Toggle button text
                button.text('Change Course License')

                // Update course here

            }
        }

        var setCourseLicense = function(e) {
            e.preventDefault();
            var button = $(e.srcElement);
            var container = button.closest('.license-selector');
            var allornothing = container.children('.license-allornothing');
            var cc = container.children('.license-cc');

            var license;
            if(cc.has(button).length==0) {
                allornothing.children('.license-button').removeClass('selected');
                button.addClass('selected');
                license = button.attr("data");
            }
            else {
                button.toggleClass("selected");

                

                if (button.attr("data") == "ND" && button.hasClass("selected")) {
                    cc.children(".license-button[data='SA']").first().removeClass("selected");
                }
                else if(button.attr("data") == "SA"&& button.hasClass("selected")) {
                    cc.children(".license-button[data='ND']").first().removeClass("selected");
                }

                if (button.attr("data") == "BY" && !button.hasClass("selected")) {
                    license = "CC0";
                    allornothing.children(".license-button[data='CC0']").first().addClass("selected");
                }
                else {
                    license = "CC";
                    cc.children(".license-button[data='BY']").first().addClass("selected");
                    var selected = cc.children(".selected");
                    selected.each( function() {
                        license = license + "-" + $(this).attr("data");
                    })
                }

                
            }

            // Toggle between custom license and allornothing
            if (license=="ARR" || license=="CC0") {
                allornothing.addClass('selected');
                cc.removeClass('selected');
            }
            else {
                cc.addClass('selected');
                allornothing.removeClass('selected');
                allornothing.children().removeClass("selected");
            }

            // Set chosen license
            container.find('.selected-license').html(license_to_img(license));
            container.find('.license').val(license);
        }

        var addNewCourse = function (e) {
            e.preventDefault();
            $('.new-course-button').addClass('is-disabled');
            $('.new-course-save').addClass('is-disabled');
            var $newCourse = $('.wrapper-create-course').addClass('is-shown');
            var $cancelButton = $newCourse.find('.new-course-cancel');
            var $courseName = $('.new-course-name');
            $courseName.focus().select();
            $('.new-course-save').on('click', saveNewCourse);
            $cancelButton.bind('click', cancelNewCourse);
            CancelOnEscape($cancelButton);

            CreateCourseUtils.configureHandlers();
        };

        var onReady = function () {
            $('.new-course-button').bind('click', addNewCourse);
            $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function () {
                ViewUtils.reload();
            }));
            $('.action-reload').bind('click', ViewUtils.reload);

            // Licencing in new course form
            $('.license-button').bind('click', setCourseLicense);
            // Change license button
            var licenseSelector = new LicenseSelector();
            $('#field-course-license').html(licenseSelector.render().$el);
        };

        domReady(onReady);

        return {
            onReady: onReady
        };
    });
