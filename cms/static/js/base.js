if (!window.CmsUtils) window.CmsUtils = {};

var $body;
var $modal;
var $modalCover;
var $newComponentItem;
var $changedInput;
var $spinner;
var $newComponentTypePicker;
var $newComponentTemplatePickers;
var $newComponentButton;

$(document).ready(function() {
    $body = $('body');
    $modal = $('.history-modal');
    $modalCover = $('<div class="modal-cover">');
    // cdodge: this looks funny, but on AWS instances, this base.js get's wrapped in a separate scope as part of Django static
    // pipelining (note, this doesn't happen on local runtimes). So if we set it on window, when we can access it from other
    // scopes (namely the course-info tab)
    window.$modalCover = $modalCover;

    $body.append($modalCover);
    $newComponentItem = $('.new-component-item');
    $newComponentTypePicker = $('.new-component');
    $newComponentTemplatePickers = $('.new-component-templates');
    $newComponentButton = $('.new-component-button');
    $spinner = $('<span class="spinner-in-field-icon"></span>');

    $('.expand-collapse-icon').bind('click', toggleSubmodules);
    $('.visibility-options').bind('change', setVisibility);

    $modal.bind('click', hideModal);
    $modalCover.bind('click', hideModal);

    $body.on('click', '.embeddable-xml-input', function() {
        $(this).select();
    });

    $('body').addClass('js');

    $('.unit .item-actions .delete-button').bind('click', deleteUnit);
    $('.new-unit-item').bind('click', createNewUnit);

    // lean/simple modal
    $('a[rel*=modal]').leanModal({
        overlay: 0.80,
        closeButton: '.action-modal-close'
    });
    $('a.action-modal-close').click(function(e) {
        (e).preventDefault();
    });

    // alerts/notifications - manual close
    $('.action-alert-close, .alert.has-actions .nav-actions a').bind('click', hideAlert);
    $('.action-notification-close').bind('click', hideNotification);

    // nav - dropdown related
    $body.click(function(e) {
        $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
        $('.nav-dd .nav-item .title').removeClass('is-selected');
    });

    $('.nav-dd .nav-item').click(function(e) {

        $subnav = $(this).find('.wrapper-nav-sub');
        $title = $(this).find('.title');

        if ($subnav.hasClass('is-shown')) {
            $subnav.removeClass('is-shown');
            $title.removeClass('is-selected');
        } else {
            $('.nav-dd .nav-item .title').removeClass('is-selected');
            $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
            $title.addClass('is-selected');
            $subnav.addClass('is-shown');
            // if propogation is not stopped, the event will bubble up to the
            // body element, which will close the dropdown.
            e.stopPropagation();
        }
    });

    // general link management - new window/tab
    $('a[rel="external"]').attr('title', gettext('This link will open in a new browser window/tab')).bind('click', linkNewWindow);

    // general link management - lean modal window
    $('a[rel="modal"]').attr('title', gettext('This link will open in a modal window')).leanModal({
        overlay: 0.50,
        closeButton: '.action-modal-close'
    });
    $('.action-modal-close').click(function(e) {
        (e).preventDefault();
    });

    // general link management - smooth scrolling page links
    $('a[rel*="view"][href^="#"]').bind('click', smoothScrollLink);

    // tender feedback window scrolling
    $('a.show-tender').bind('click', window.CmsUtils.smoothScrollTop);

    // toggling footer additional support
    $('.cta-show-sock').bind('click', toggleSock);

    // toggling overview section details
    $(function() {
        if ($('.courseware-section').length > 0) {
            $('.toggle-button-sections').addClass('is-shown');
        }
    });
    $('.toggle-button-sections').bind('click', toggleSections);

    // autosave when leaving input field
    $body.on('change', '.subsection-display-name-input', saveSubsection);
    $('.subsection-display-name-input').each(function() {
        this.val = $(this).val();
    });
    $("#start_date, #start_time, #due_date, #due_time").bind('change', autosaveInput);
    $('.sync-date, .remove-date').bind('click', autosaveInput);

    // expand/collapse methods for optional date setters
    $('.set-date').bind('click', showDateSetter);
    $('.remove-date').bind('click', removeDateSetter);
    // add new/delete section
    $('.new-courseware-section-button').bind('click', addNewSection);
    $('.delete-section-button').bind('click', deleteSection);

    // add new/delete subsection
    $('.new-subsection-item').bind('click', addNewSubsection);
    $('.delete-subsection-button').bind('click', deleteSubsection);

    $('.sync-date').bind('click', syncReleaseDate);

    // import form setup
    $('.import .file-input').bind('change', showImportSubmit);
    $('.import .choose-file-button, .import .choose-file-button-inline').bind('click', function(e) {
        e.preventDefault();
        $('.import .file-input').click();
    });

    $('.new-course-button').bind('click', addNewCourse);

    // section date setting
    $('.set-publish-date').bind('click', setSectionScheduleDate);
    $('.edit-section-start-cancel').bind('click', cancelSetSectionScheduleDate);
    $('.edit-section-start-save').bind('click', saveSetSectionScheduleDate);

    $body.on('click', '.section-published-date .edit-button', editSectionPublishDate);
    $body.on('click', '.section-published-date .schedule-button', editSectionPublishDate);
    $body.on('click', '.edit-subsection-publish-settings .save-button', saveSetSectionScheduleDate);
    $body.on('click', '.edit-subsection-publish-settings .cancel-button', hideModal);
    $body.on('change', '.edit-subsection-publish-settings .start-date', function() {
        if ($('.edit-subsection-publish-settings').find('.start-time').val() == '') {
            $('.edit-subsection-publish-settings').find('.start-time').val('12:00am');
        }
    });
    $('.edit-subsection-publish-settings').on('change', '.start-date, .start-time', function() {
        $('.edit-subsection-publish-settings').find('.save-button').show();
    });
});

function smoothScrollLink(e) {
    (e).preventDefault();

    $.smoothScroll({
        offset: -200,
        easing: 'swing',
        speed: 1000,
        scrollElement: null,
        scrollTarget: $(this).attr('href')
    });
}

// On AWS instances, this base.js gets wrapped in a separate scope as part of Django static
// pipelining (note, this doesn't happen on local runtimes). So if we set it on window,
//  when we can access it from other scopes (namely Course Advanced Settings).
window.CmsUtils.smoothScrollTop = function(e) {
    (e).preventDefault();

    $.smoothScroll({
        offset: -200,
        easing: 'swing',
        speed: 1000,
        scrollElement: null,
        scrollTarget: $('#view-top')
    });
}

function linkNewWindow(e) {
    window.open($(e.target).attr('href'));
    e.preventDefault();
}

// On AWS instances, base.js gets wrapped in a separate scope as part of Django static
// pipelining (note, this doesn't happen on local runtimes). So if we set it on window,
// when we can access it from other scopes (namely the checklists)
window.cmsLinkNewWindow = linkNewWindow;

function toggleSections(e) {
    e.preventDefault();

    $section = $('.courseware-section');
    sectionCount = $section.length;
    $button = $(this);
    $labelCollapsed = $('<i class="icon-arrow-up"></i> <span class="label">' +
        gettext('Collapse All Sections') + '</span>');
    $labelExpanded = $('<i class="icon-arrow-down"></i> <span class="label">' +
        gettext('Expand All Sections') + '</span>');

    var buttonLabel = $button.hasClass('is-activated') ? $labelCollapsed : $labelExpanded;
    $button.toggleClass('is-activated').html(buttonLabel);

    if ($button.hasClass('is-activated')) {
        $section.addClass('collapsed');
        // first child in order to avoid the icons on the subsection lists which are not in the first child
        $section.find('header .expand-collapse-icon').removeClass('collapse').addClass('expand');
    } else {
        $section.removeClass('collapsed');
        // first child in order to avoid the icons on the subsection lists which are not in the first child
        $section.find('header .expand-collapse-icon').removeClass('expand').addClass('collapse');
    }
}

function editSectionPublishDate(e) {
    e.preventDefault();
    $modal = $('.edit-subsection-publish-settings').show();
    $modal.attr('data-id', $(this).attr('data-id'));
    $modal.find('.start-date').val($(this).attr('data-date'));
    $modal.find('.start-time').val($(this).attr('data-time'));
    if ($modal.find('.start-date').val() == '' && $modal.find('.start-time').val() == '') {
        $modal.find('.save-button').hide();
    }
    $modal.find('.section-name').html('"' + $(this).closest('.courseware-section').find('.section-name-span').text() + '"');
    $modalCover.show();
}

function showImportSubmit(e) {
    var filepath = $(this).val();
    if (filepath.substr(filepath.length - 6, 6) == 'tar.gz') {
        $('.error-block').hide();
        $('.file-name').html($(this).val().replace('C:\\fakepath\\', ''));
        $('.file-name-block').show();
        $('.import .choose-file-button').hide();
        $('.submit-button').show();
        $('.progress').show();
    } else {
        $('.error-block').html(gettext('File format not supported. Please upload a file with a <code>tar.gz</code> extension.')).show();
    }
}

function syncReleaseDate(e) {
    e.preventDefault();
    $(this).closest('.notice').hide();
    $("#start_date").val("");
    $("#start_time").val("");
}

function getDatetime(datepickerInput, timepickerInput) {
    // given a pair of inputs (datepicker and timepicker), return a JS Date
    // object that corresponds to the datetime that they represent. Assume
    // UTC timezone, NOT the timezone of the user's browser.
    var date = $(datepickerInput).datepicker("getDate");
    var time = $(timepickerInput).timepicker("getTime");
    if(date && time) {
        return new Date(Date.UTC(
            date.getFullYear(), date.getMonth(), date.getDate(),
            time.getHours(), time.getMinutes()
        ));
    } else {
        return null;
    }
}

function autosaveInput(e) {
    var self = this;
    if (this.saveTimer) {
        clearTimeout(this.saveTimer);
    }

    this.saveTimer = setTimeout(function() {
        $changedInput = $(e.target);
        saveSubsection();
        self.saveTimer = null;
    }, 500);
}

function saveSubsection() {
    // Spinner is no longer used by subsection name, but is still used by date and time pickers on the right.
    if ($changedInput && !$changedInput.hasClass('no-spinner')) {
        $spinner.css({
            'position': 'absolute',
            'top': Math.floor($changedInput.position().top + ($changedInput.outerHeight() / 2) + 3),
            'left': $changedInput.position().left + $changedInput.outerWidth() - 24,
            'margin-top': '-10px'
        });
        $changedInput.after($spinner);
        $spinner.show();
    }

    var id = $('.subsection-body').data('id');

    // pull all 'normalized' metadata editable fields on page
    var metadata_fields = $('input[data-metadata-name]');

    var metadata = {};
    for (var i = 0; i < metadata_fields.length; i++) {
        var el = metadata_fields[i];
        metadata[$(el).data("metadata-name")] = el.value;
    }

    // get datetimes for start and due, stick into metadata
    _(["start", "due"]).each(function(name) {

        var datetime = getDatetime(
            document.getElementById(name+"_date"),
            document.getElementById(name+"_time")
        );
        // if datetime is null, we want to set that in metadata anyway;
        // its an indication to the server to clear the datetime in the DB
        metadata[name] = datetime;
    });

    $.ajax({
        url: "/save_item",
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify({
            'id': id,
            'metadata': metadata
        }),
        success: function() {
            $spinner.delay(500).fadeOut(150);
            $changedInput = null;
        },
        error: function() {
            showToastMessage(gettext('There has been an error while saving your changes.'));
        }
    });
}


function createNewUnit(e) {
    e.preventDefault();

    var parent = $(this).data('parent');
    var category = $(this).data('category');

    analytics.track('Created a Unit', {
        'course': course_location_analytics,
        'parent_location': parent
    });


    $.post('/create_item', {
        'parent_location': parent,
        'category': category,
        'display_name': 'New Unit'
    },

    function(data) {
        // redirect to the edit page
        window.location = "/edit/" + data['id'];
    });
}

function deleteUnit(e) {
    e.preventDefault();
    _deleteItem($(this).parents('li.leaf'), 'Unit');
}

function deleteSubsection(e) {
    e.preventDefault();
    _deleteItem($(this).parents('li.branch'), 'Subsection');
}

function deleteSection(e) {
    e.preventDefault();
    _deleteItem($(this).parents('section.branch'), 'Section');
}

function _deleteItem($el, type) {
    var confirm = new CMS.Views.Prompt.Warning({
        title: gettext('Delete this ' + type + '?'),
        message: gettext('Deleting this ' + type + ' is permanent and cannot be undone.'),
        actions: {
            primary: {
                text: gettext('Yes, delete this ' + type),
                click: function(view) {
                    view.hide();

                    var id = $el.data('id');

                    analytics.track('Deleted an Item', {
                        'course': course_location_analytics,
                        'id': id
                    });

                    var deleting = new CMS.Views.Notification.Mini({
                        title: gettext('Deleting') + '&hellip;'
                    });
                    deleting.show();

                    $.post('/delete_item',
                           {'id': id,
                            'delete_children': true,
                            'delete_all_versions': true},
                           function(data) {
                               $el.remove();
                               deleting.hide();
                           }
                          );
                }
            },
            secondary: {
                text: gettext('Cancel'),
                click: function(view) {
                    view.hide();
                }
            }
        }
    });
    confirm.show();
}

function markAsLoaded() {
    $('.upload-modal .copy-button').css('display', 'inline-block');
    $('.upload-modal .progress-bar').addClass('loaded');
}

function hideModal(e) {
    if (e) {
        e.preventDefault();
    }
    // Unit editors do not want the modal cover to hide when users click outside
    // of the editor. Users must press Cancel or Save to exit the editor.
    // module_edit adds and removes the "is-fixed" class.
    if (!$modalCover.hasClass("is-fixed")) {
        $('.file-input').unbind('change', startUpload);
        $modal.hide();
        $modalCover.hide();
    }
}

function toggleSock(e) {
    e.preventDefault();

    var $btnLabel = $(this).find('.copy');
    var $sock = $('.wrapper-sock');
    var $sockContent = $sock.find('.wrapper-inner');

    $sock.toggleClass('is-shown');
    $sockContent.toggle('fast');

    $.smoothScroll({
        offset: -200,
        easing: 'swing',
        speed: 1000,
        scrollElement: null,
        scrollTarget: $sock
    });

    if ($sock.hasClass('is-shown')) {
        $btnLabel.text(gettext('Hide Studio Help'));
    } else {
        $btnLabel.text(gettext('Looking for Help with Studio?'));
    }
}

function toggleSubmodules(e) {
    e.preventDefault();
    $(this).toggleClass('expand').toggleClass('collapse');
    $(this).closest('.branch, .window').toggleClass('collapsed');
}

function setVisibility(e) {
    $(this).find('.checked').removeClass('checked');
    $(e.target).closest('.option').addClass('checked');
}

function editComponent(e) {
    e.preventDefault();
    $(this).closest('.xmodule_edit').addClass('editing').find('.component-editor').slideDown(150);
}

function closeComponentEditor(e) {
    e.preventDefault();
    $(this).closest('.xmodule_edit').removeClass('editing').find('.component-editor').slideUp(150);
}

function showDateSetter(e) {
    e.preventDefault();
    var $block = $(this).closest('.due-date-input');
    $(this).hide();
    $block.find('.date-setter').show();
}

function removeDateSetter(e) {
    e.preventDefault();
    var $block = $(this).closest('.due-date-input');
    $block.find('.date-setter').hide();
    $block.find('.set-date').show();
    // clear out the values
    $block.find('.date').val('');
    $block.find('.time').val('');
}


function hideNotification(e) {
    (e).preventDefault();
    $(this).closest('.wrapper-notification').removeClass('is-shown').addClass('is-hiding').attr('aria-hidden', 'true');
}

function hideAlert(e) {
    (e).preventDefault();
    $(this).closest('.wrapper-alert').removeClass('is-shown');
}

function showToastMessage(message, $button, lifespan) {
    var $toast = $('<div class="toast-notification"></div>');
    var $closeBtn = $('<a href="#" class="close-button">×</a>');
    $toast.append($closeBtn);
    var $content = $('<div class="notification-content"></div>');
    $content.html(message);
    $toast.append($content);
    if ($button) {
        $button.addClass('action-button');
        $button.bind('click', hideToastMessage);
        $content.append($button);
    }
    $closeBtn.bind('click', hideToastMessage);

    if ($('.toast-notification')[0]) {
        var targetY = $('.toast-notification').offset().top + $('.toast-notification').outerHeight();
        $toast.css('top', (targetY + 10) + 'px');
    }

    $body.prepend($toast);
    $toast.fadeIn(200);

    if (lifespan) {
        $toast.timer = setTimeout(function() {
            $toast.fadeOut(300);
        }, lifespan * 1000);
    }
}

function hideToastMessage(e) {
    e.preventDefault();
    $(this).closest('.toast-notification').remove();
}

function addNewSection(e, isTemplate) {
    e.preventDefault();

    $(e.target).addClass('disabled');

    var $newSection = $($('#new-section-template').html());
    var $cancelButton = $newSection.find('.new-section-name-cancel');
    $('.courseware-overview').prepend($newSection);
    $newSection.find('.new-section-name').focus().select();
    $newSection.find('.section-name-form').bind('submit', saveNewSection);
    $cancelButton.bind('click', cancelNewSection);
    $body.bind('keyup', {
        $cancelButton: $cancelButton
    }, checkForCancel);
}

function checkForCancel(e) {
    if (e.which == 27) {
        $body.unbind('keyup', checkForCancel);
        e.data.$cancelButton.click();
    }
}


function saveNewSection(e) {
    e.preventDefault();

    var $saveButton = $(this).find('.new-section-name-save');
    var parent = $saveButton.data('parent');
    var category = $saveButton.data('category');
    var display_name = $(this).find('.new-section-name').val();

    analytics.track('Created a Section', {
        'course': course_location_analytics,
        'display_name': display_name
    });

    $.post('/create_item', {
        'parent_location': parent,
        'category': category,
        'display_name': display_name,
    },

    function(data) {
        if (data.id != undefined) location.reload();
    });
}

function cancelNewSection(e) {
    e.preventDefault();
    $('.new-courseware-section-button').removeClass('disabled');
    $(this).parents('section.new-section').remove();
}

function addNewCourse(e) {
    e.preventDefault();
    $('.new-course-button').addClass('is-disabled');
    $('.new-course-save').addClass('is-disabled');
    var $newCourse = $('.wrapper-create-course').addClass('is-shown');
    var $cancelButton = $newCourse.find('.new-course-cancel');
    var $courseName = $('.new-course-name');
    $courseName.focus().select();
    $('.new-course-save').on('click', saveNewCourse);
    $cancelButton.bind('click', cancelNewCourse);
    $body.bind('keyup', {
        $cancelButton: $cancelButton
    }, checkForCancel);

    // Check that a course (org, number, run) doesn't use any special characters
    var validateCourseItemEncoding = function(item) {
        var required = validateRequiredField(item);
        if(required) {
            return required;
        }
        if(item !== encodeURIComponent(item)) {
            return gettext('Please do not use any spaces or special characters in this field.');
        }
        return '';
    }

    // Ensure that all items are less than 80 characters.
    var validateTotalCourseItemsLength = function() {
        var totalLength = _.reduce(
            ['.new-course-name', '.new-course-org', '.new-course-number', '.new-course-run'],
            function(sum, ele) {
                return sum + $(ele).val().length;
        }, 0
        );
        if(totalLength > 80) {
            $('.wrap-error').addClass('is-shown');
            $('#course_creation_error').html('<p>' + gettext('Course fields must have a combined length of no more than 80 characters.') + '</p>');
            $('.new-course-save').addClass('is-disabled');
        }
        else {
            $('.wrap-error').removeClass('is-shown');
        }
    }

    // Handle validation asynchronously
    _.each(
        ['.new-course-org', '.new-course-number', '.new-course-run'],
        function(ele) {
            var $ele = $(ele);
            $ele.on('keyup', function(event) {
                // Don't bother showing "required field" error when
                // the user tabs into a new field; this is distracting
                // and unnecessary
                if(event.keyCode === 9) {
                    return;
                }
                var error = validateCourseItemEncoding($ele.val());
                setNewCourseFieldInErr($ele.parent('li'), error);
                validateTotalCourseItemsLength();
            });
        }
    );
    var $name = $('.new-course-name');
    $name.on('keyup', function() {
        var error = validateRequiredField($name.val());
        setNewCourseFieldInErr($name.parent('li'), error);
        validateTotalCourseItemsLength();
    });
}

function validateRequiredField(msg) {
    return msg.length === 0 ? gettext('Required field.') : '';
}

function setNewCourseFieldInErr(el, msg) {
    if(msg) {
        el.addClass('error');
        el.children('span.tip-error').addClass('is-showing').removeClass('is-hiding').text(msg);
        $('.new-course-save').addClass('is-disabled');
    }
    else {
        el.removeClass('error');
        el.children('span.tip-error').addClass('is-hiding').removeClass('is-showing');
        // One "error" div is always present, but hidden or shown
        if($('.error').length === 1) {
            $('.new-course-save').removeClass('is-disabled');
        }
    }
};

function saveNewCourse(e) {
    e.preventDefault();

    // One final check for empty values
    var errors = _.reduce(
        ['.new-course-name', '.new-course-org', '.new-course-number', '.new-course-run'],
        function(acc, ele) {
            var $ele = $(ele);
            var error = validateRequiredField($ele.val());
            setNewCourseFieldInErr($ele.parent('li'), error);
            return error ? true : acc;
        },
        false
    );

    if(errors) {
        return;
    }

    var $newCourseForm = $(this).closest('#create-course-form');
    var display_name = $newCourseForm.find('.new-course-name').val();
    var org = $newCourseForm.find('.new-course-org').val();
    var number = $newCourseForm.find('.new-course-number').val();
    var run = $newCourseForm.find('.new-course-run').val();

    analytics.track('Created a Course', {
        'org': org,
        'number': number,
        'display_name': display_name,
        'run': run
    });

    $.post('/create_new_course', {
            'org': org,
            'number': number,
            'display_name': display_name,
            'run': run
        },
        function(data) {
            if (data.id !== undefined) {
                window.location = '/' + data.id.replace(/.*:\/\//, '');
            } else if (data.ErrMsg !== undefined) {
                $('.wrap-error').addClass('is-shown');
                $('#course_creation_error').html('<p>' + data.ErrMsg + '</p>');
                $('.new-course-save').addClass('is-disabled');
            }
        }
    );
}

function cancelNewCourse(e) {
    e.preventDefault();
    $('.new-course-button').removeClass('is-disabled');
    $('.wrapper-create-course').removeClass('is-shown');
    // Clear out existing fields and errors
    _.each(
        ['.new-course-name', '.new-course-org', '.new-course-number', '.new-course-run'],
        function(field) {
            $(field).val('');
        }
    );
    $('#course_creation_error').html('');
    $('.wrap-error').removeClass('is-shown');
    $('.new-course-save').off('click');
}

function addNewSubsection(e) {
    e.preventDefault();
    var $section = $(this).closest('.courseware-section');
    var $newSubsection = $($('#new-subsection-template').html());
    $section.find('.subsection-list > ol').append($newSubsection);
    $section.find('.new-subsection-name-input').focus().select();

    var $saveButton = $newSubsection.find('.new-subsection-name-save');
    var $cancelButton = $newSubsection.find('.new-subsection-name-cancel');

    var parent = $(this).parents("section.branch").data("id");

    $saveButton.data('parent', parent);
    $saveButton.data('category', $(this).data('category'));

    $newSubsection.find('.new-subsection-form').bind('submit', saveNewSubsection);
    $cancelButton.bind('click', cancelNewSubsection);
    $body.bind('keyup', {
        $cancelButton: $cancelButton
    }, checkForCancel);
}

function saveNewSubsection(e) {
    e.preventDefault();

    var parent = $(this).find('.new-subsection-name-save').data('parent');
    var category = $(this).find('.new-subsection-name-save').data('category');
    var display_name = $(this).find('.new-subsection-name-input').val();

    analytics.track('Created a Subsection', {
        'course': course_location_analytics,
        'display_name': display_name
    });


    $.post('/create_item', {
        'parent_location': parent,
        'category': category,
        'display_name': display_name
    },

    function(data) {
        if (data.id != undefined) {
            location.reload();
        }
    });
}

function cancelNewSubsection(e) {
    e.preventDefault();
    $(this).parents('li.branch').remove();
}

function setSectionScheduleDate(e) {
    e.preventDefault();
    $(this).closest("h4").hide();
    $(this).parent().siblings(".datepair").show();
}

function cancelSetSectionScheduleDate(e) {
    e.preventDefault();
    $(this).closest(".datepair").hide();
    $(this).parent().siblings("h4").show();
}

function saveSetSectionScheduleDate(e) {
    e.preventDefault();

    var datetime = getDatetime(
        $('.edit-subsection-publish-settings .start-date'),
        $('.edit-subsection-publish-settings .start-time')
    );

    var id = $modal.attr('data-id');

    analytics.track('Edited Section Release Date', {
        'course': course_location_analytics,
        'id': id,
        'start': datetime
    });

    var saving = new CMS.Views.Notification.Mini({
        title: gettext("Saving") + "&hellip;"
    });
    saving.show();
    // call into server to commit the new order
    $.ajax({
        url: "/save_item",
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify({
            'id': id,
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

        var $thisSection = $('.courseware-section[data-id="' + id + '"]');
        var html = _.template(
            '<span class="published-status">' +
                '<strong>' + gettext("Will Release:") + '&nbsp;</strong>' +
                gettext("{month}/{day}/{year} at {hour}:{minute} UTC") +
            '</span>' +
            '<a href="#" class="edit-button" data-date="{month}/{day}/{year}" data-time="{hour}:{minute}" data-id="{id}">' +
                gettext("Edit") +
            '</a>',
            {year: datetime.getUTCFullYear(), month: pad2(datetime.getUTCMonth() + 1), day: pad2(datetime.getUTCDate()),
             hour: pad2(datetime.getUTCHours()), minute: pad2(datetime.getUTCMinutes()),
             id: id},
            {interpolate: /\{(.+?)\}/g});
        $thisSection.find('.section-published-date').html(html);
        hideModal();
        saving.hide();
    });
}
