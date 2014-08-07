define(["domReady", "jquery", "jquery.ui", "underscore", "gettext", "js/views/feedback_notification",
    "js/utils/cancel_on_escape", "js/utils/date_utils", "js/utils/module"],
    function (domReady, $, ui, _, gettext, NotificationView, CancelOnEscape,
              DateUtils, ModuleUtils) {

        var modalSelector = '.edit-section-publish-settings';

        var toggleSections = function(e) {
            e.preventDefault();

            var $section = $('.courseware-section');
            var $button = $(this);
            var $labelCollapsed = $('<i class="icon-arrow-up"></i> <span class="label">' +
                gettext('Collapse All Sections') + '</span>');
            var $labelExpanded = $('<i class="icon-arrow-down"></i> <span class="label">' +
                gettext('Expand All Sections') + '</span>');

            var buttonLabel = $button.hasClass('is-activated') ? $labelCollapsed : $labelExpanded;
            $button.toggleClass('is-activated').html(buttonLabel);

            if ($button.hasClass('is-activated')) {
                $section.addClass('collapsed');
                // first child in order to avoid the icons on the subsection lists which are not in the first child
                $section.find('header .expand-collapse').removeClass('collapse').addClass('expand');
            } else {
                $section.removeClass('collapsed');
                // first child in order to avoid the icons on the subsection lists which are not in the first child
                $section.find('header .expand-collapse').removeClass('expand').addClass('collapse');
            }
        };

        var toggleSubmodules = function(e) {
            e.preventDefault();
            $(this).toggleClass('expand collapse');
            $(this).closest('.is-collapsible, .window').toggleClass('collapsed');
        };


        var closeModalNew = function (e) {
            if (e) {
                e.preventDefault();
            }
            $('body').removeClass('modal-window-is-shown');
            $('.edit-section-publish-settings').removeClass('is-shown');
        };

        var editSectionPublishDate = function (e) {
            e.preventDefault();
            var $modal = $(modalSelector);
            $modal.attr('data-locator', $(this).attr('data-locator'));
            $modal.find('.start-date').val($(this).attr('data-date'));
            $modal.find('.start-time').val($(this).attr('data-time'));
            if ($modal.find('.start-date').val() == '' && $modal.find('.start-time').val() == '') {
                $modal.find('.save-button').hide();
            }
            $modal.find('.section-name').html('"' + $(this).closest('.courseware-section').find('.section-name-span').text() + '"');
            $('body').addClass('modal-window-is-shown');
            $('.edit-section-publish-settings').addClass('is-shown');
        };

        var saveSetSectionScheduleDate = function (e) {
            e.preventDefault();

            var datetime = DateUtils.getDate(
                $('.edit-section-publish-settings .start-date'),
                $('.edit-section-publish-settings .start-time')
            );

            var locator = $(modalSelector).attr('data-locator');

            analytics.track('Edited Section Release Date', {
                'course': course_location_analytics,
                'id': locator,
                'start': datetime
            });

            var saving = new NotificationView.Mini({
                title: gettext("Saving&hellip;")
            });
            saving.show();
            // call into server to commit the new order
            $.ajax({
                url: ModuleUtils.getUpdateUrl(locator),
                type: "PUT",
                dataType: "json",
                contentType: "application/json",
                data: JSON.stringify({
                    'metadata': {
                        'start': datetime
                    }
                })
            }).success(function() {
                    var pad2 = function(number) {
                        // pad a number to two places: useful for formatting months, days, hours, etc
                        // when displaying a date/time
                        return (number < 10 ? '0' : '') + number;
                    };

                    var $thisSection = $('.courseware-section[data-locator="' + locator + '"]');
                    var html = _.template(
                        '<span class="published-status">' +
                            '<strong>' + gettext("Release date:") + '&nbsp;</strong>' +
                            gettext("{month}/{day}/{year} at {hour}:{minute} UTC") +
                            '</span>' +
                            '<a href="#" class="edit-release-date action" data-date="{month}/{day}/{year}" data-time="{hour}:{minute}" data-locator="{locator}"><i class="icon-time"></i> <span class="sr">' +
                            gettext("Edit section release date") +
                            '</span></a>',
                        {year: datetime.getUTCFullYear(), month: pad2(datetime.getUTCMonth() + 1), day: pad2(datetime.getUTCDate()),
                            hour: pad2(datetime.getUTCHours()), minute: pad2(datetime.getUTCMinutes()),
                            locator: locator},
                        {interpolate: /\{(.+?)\}/g});
                    $thisSection.find('.section-published-date').html(html);
                    saving.hide();
                    closeModalNew();
                });
        };

        var addNewSection = function (e) {
            e.preventDefault();

            $(e.target).addClass('disabled');

            var $newSection = $($('#new-section-template').html());
            var $cancelButton = $newSection.find('.new-section-name-cancel');
            $('.courseware-overview').prepend($newSection);
            $newSection.find('.new-section-name').focus().select();
            $newSection.find('.section-name-form').bind('submit', saveNewSection);
            $cancelButton.bind('click', cancelNewSection);
            CancelOnEscape($cancelButton);
        };

        var saveNewSection = function (e) {
            e.preventDefault();

            var $saveButton = $(this).find('.new-section-name-save');
            var parent = $saveButton.data('parent');
            var category = $saveButton.data('category');
            var display_name = $(this).find('.new-section-name').val();

            analytics.track('Created a Section', {
                'course': course_location_analytics,
                'display_name': display_name
            });

            $.postJSON(ModuleUtils.getUpdateUrl(), {
                    'parent_locator': parent,
                    'category': category,
                    'display_name': display_name
                },

                function(data) {
                    if (data.locator != undefined) location.reload();
                });
        };

        var cancelNewSection = function (e) {
            e.preventDefault();
            $('.new-courseware-section-button').removeClass('disabled');
            $(this).parents('section.new-section').remove();
        };

        var addNewSubsection = function (e) {
            e.preventDefault();
            var $section = $(this).closest('.courseware-section');
            var $newSubsection = $($('#new-subsection-template').html());
            $section.find('.subsection-list > ol').append($newSubsection);
            $section.find('.new-subsection-name-input').focus().select();

            var $saveButton = $newSubsection.find('.new-subsection-name-save');
            var $cancelButton = $newSubsection.find('.new-subsection-name-cancel');

            var parent = $(this).parents("section.courseware-section").data("locator");

            $saveButton.data('parent', parent);
            $saveButton.data('category', $(this).data('category'));

            $newSubsection.find('.new-subsection-form').bind('submit', saveNewSubsection);
            $cancelButton.bind('click', cancelNewSubsection);
            CancelOnEscape($cancelButton);
        };

        var saveNewSubsection = function (e) {
            e.preventDefault();

            var parent = $(this).find('.new-subsection-name-save').data('parent');
            var category = $(this).find('.new-subsection-name-save').data('category');
            var display_name = $(this).find('.new-subsection-name-input').val();

            analytics.track('Created a Subsection', {
                'course': course_location_analytics,
                'display_name': display_name
            });


            $.postJSON(ModuleUtils.getUpdateUrl(), {
                    'parent_locator': parent,
                    'category': category,
                    'display_name': display_name
                },

                function(data) {
                    if (data.locator != undefined) {
                        location.reload();
                    }
                });
        };

        var cancelNewSubsection = function (e) {
            e.preventDefault();
            $(this).parents('li.courseware-subsection').remove();
        };



        domReady(function() {
            // toggling overview section details
            $(function() {
                if ($('.courseware-section').length > 0) {
                    $('.toggle-button-sections').addClass('is-shown');
                }
            });
            $('.toggle-button-sections').bind('click', toggleSections);
            $('.expand-collapse').bind('click', toggleSubmodules);

            var $body = $('body');
            $body.on('click', '.section-published-date .edit-release-date', editSectionPublishDate);
            $body.on('click', '.edit-section-publish-settings .action-save', saveSetSectionScheduleDate);
            $body.on('click', '.edit-section-publish-settings .action-cancel', closeModalNew);

            $('.new-courseware-section-button').bind('click', addNewSection);
            $('.new-subsection-item').bind('click', addNewSubsection);

        });

        return {
            saveSetSectionScheduleDate: saveSetSectionScheduleDate
        };
    });
