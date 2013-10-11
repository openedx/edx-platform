require(["domReady", "jquery", "underscore", "gettext", "js/views/feedback_notification", "js/views/feedback_prompt",
         "js/utils/cancel_on_escape", "jquery.ui", "jquery.timepicker", "jquery.leanModal", "jquery.form", "jquery.smoothScroll"],
    function(domReady, $, _, gettext, NotificationView, PromptView, CancelOnEscape) {

var $body;
var $modal;
var $modalCover;
var $newComponentItem;
var $changedInput;
var $spinner;
var $newComponentTypePicker;
var $newComponentTemplatePickers;
var $newComponentButton;

domReady(function() {
    $body = $('body');
    $modal = $('.history-modal');
    $modalCover = $('.modal-cover');

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
    $('a.show-tender').bind('click', smoothScrollTop);

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

function hideModal(e) {
    if (e) {
        e.preventDefault();
    }
    // Unit editors do not want the modal cover to hide when users click outside
    // of the editor. Users must press Cancel or Save to exit the editor.
    // module_edit adds and removes the "is-fixed" class.
    if (!$modalCover.hasClass("is-fixed")) {
        $(".modal, .edit-subsection-publish-settings").hide();
        $modalCover.hide();
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

function addNewSection(e) {
    e.preventDefault();

    $(e.target).addClass('disabled');

    var $newSection = $($('#new-section-template').html());
    var $cancelButton = $newSection.find('.new-section-name-cancel');
    $('.courseware-overview').prepend($newSection);
    $newSection.find('.new-section-name').focus().select();
    $newSection.find('.section-name-form').bind('submit', saveNewSection);
    $cancelButton.bind('click', cancelNewSection);
    CancelOnEscape($cancelButton);
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
        'display_name': display_name
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
    CancelOnEscape($cancelButton);
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

    var saving = new NotificationView.Mini({
        title: gettext("Saving&hellip;")
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
    // Add to window object for unit test (overview_spec).
    window.saveSetSectionScheduleDate = saveSetSectionScheduleDate;
    window.deleteSection = deleteSection;

}); // end require()
