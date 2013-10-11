require(["domReady", "jquery", "underscore", "gettext", "js/views/feedback_notification", "js/views/feedback_prompt",
    "js/utils/get_date", "jquery.ui", "jquery.timepicker", "jquery.leanModal", "jquery.form", "jquery.smoothScroll"],
    function(domReady, $, _, gettext, NotificationView, PromptView, DateUtils) {

var $body;
var $newComponentItem;
var $changedInput;
var $spinner;
var $newComponentTypePicker;
var $newComponentTemplatePickers;
var $newComponentButton;

domReady(function() {
    $body = $('body');

    $newComponentItem = $('.new-component-item');
    $newComponentTypePicker = $('.new-component');
    $newComponentTemplatePickers = $('.new-component-templates');
    $newComponentButton = $('.new-component-button');
    $spinner = $('<span class="spinner-in-field-icon"></span>');

    $('.expand-collapse-icon').bind('click', toggleSubmodules);
    $('.visibility-options').bind('change', setVisibility);


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
    $('a.show-tender').bind('click', smoothScrollTop);

    // toggling footer additional support
    $('.cta-show-sock').bind('click', toggleSock);

    // toggling overview section details
    $(function() {
        if ($('.courseware-section').length > 0) {
            $('.toggle-button-sections').addClass('is-shown');
        }
    });

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
    $('.view-import .file-input').bind('change', showImportSubmit);
    $('.view-import .choose-file-button, .view-import .choose-file-button-inline').bind('click', function(e) {
        e.preventDefault();
        $('.view-import .file-input').click();
    });

    $('.new-course-button').bind('click', addNewCourse);

    // section date setting
    $('.set-publish-date').bind('click', setSectionScheduleDate);
    $('.edit-section-start-cancel').bind('click', cancelSetSectionScheduleDate);

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

function smoothScrollTop(e) {
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


function showImportSubmit(e) {
    var filepath = $(this).val();
    if (filepath.substr(filepath.length - 6, 6) == 'tar.gz') {
        $('.error-block').hide();
        $('.file-name').html($(this).val().replace('C:\\fakepath\\', ''));
        $('.file-name-block').show();
        $('.view-import .choose-file-button').hide();
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

        var datetime = DateUtils(
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
    var confirm = new PromptView.Warning({
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

                    var deleting = new NotificationView.Mini({
                        title: gettext('Deleting&hellip;')
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
    };

    // Ensure that org/course_num/run < 65 chars.
    var validateTotalCourseItemsLength = function() {
        var totalLength = _.reduce(
            ['.new-course-org', '.new-course-number', '.new-course-run'],
            function(sum, ele) {
                return sum + $(ele).val().length;
        }, 0
        );
        if(totalLength > 65) {
            $('.wrap-error').addClass('is-shown');
            $('#course_creation_error').html('<p>' + gettext('The combined length of the organization, course number, and course run fields cannot be more than 65 characters.') + '</p>');
            $('.new-course-save').addClass('is-disabled');
        }
        else {
            $('.wrap-error').removeClass('is-shown');
        }
    };

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


    window.deleteSection = deleteSection;

}); // end require()
