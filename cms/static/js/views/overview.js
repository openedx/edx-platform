define(["domReady", "jquery", "jquery.ui", "underscore", "gettext", "js/views/feedback_notification", "draggabilly",
    "js/utils/modal", "js/utils/cancel_on_escape", "js/utils/get_date", "js/utils/module"],
    function (domReady, $, ui, _, gettext, NotificationView, Draggabilly, ModalUtils, CancelOnEscape,
              DateUtils, ModuleUtils) {

        var modalSelector = '.edit-subsection-publish-settings';

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
                $section.find('header .expand-collapse-icon').removeClass('collapse').addClass('expand');
            } else {
                $section.removeClass('collapsed');
                // first child in order to avoid the icons on the subsection lists which are not in the first child
                $section.find('header .expand-collapse-icon').removeClass('expand').addClass('collapse');
            }
        };

        var toggleSubmodules = function(e) {
            e.preventDefault();
            $(this).toggleClass('expand').toggleClass('collapse');
            $(this).closest('.branch, .window').toggleClass('collapsed');
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
            ModalUtils.showModal();
        };

        var saveSetSectionScheduleDate = function (e) {
            e.preventDefault();

            var datetime = DateUtils(
                $('.edit-subsection-publish-settings .start-date'),
                $('.edit-subsection-publish-settings .start-time')
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
                            '<strong>' + gettext("Will Release:") + '&nbsp;</strong>' +
                            gettext("{month}/{day}/{year} at {hour}:{minute} UTC") +
                            '</span>' +
                            '<a href="#" class="edit-button" data-date="{month}/{day}/{year}" data-time="{hour}:{minute}" data-locator="{locator}">' +
                            gettext("Edit") +
                            '</a>',
                        {year: datetime.getUTCFullYear(), month: pad2(datetime.getUTCMonth() + 1), day: pad2(datetime.getUTCDate()),
                            hour: pad2(datetime.getUTCHours()), minute: pad2(datetime.getUTCMinutes()),
                            locator: locator},
                        {interpolate: /\{(.+?)\}/g});
                    $thisSection.find('.section-published-date').html(html);
                    ModalUtils.hideModal();
                    saving.hide();
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

            var parent = $(this).parents("section.branch").data("locator");

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
            $(this).parents('li.branch').remove();
        };

        var overviewDragger = {
            droppableClasses: 'drop-target drop-target-prepend drop-target-before drop-target-after',
            validDropClass: "valid-drop",
            expandOnDropClass: "expand-on-drop",

            /*
             * Determine information about where to drop the currently dragged
             * element. Returns the element to attach to and the method of
             * attachment ('before', 'after', or 'prepend').
             */
            findDestination: function (ele, yChange) {
                var eleY = ele.offset().top;
                var containers = $(ele.data('droppable-class'));

                for (var i = 0; i < containers.length; i++) {
                    var container = $(containers[i]);
                    // Exclude the 'new unit' buttons, and make sure we don't
                    // prepend an element to itself
                    var siblings = container.children().filter(function () {
                        return $(this).data('locator') !== undefined && !$(this).is(ele);
                    });
                    // If the container is collapsed, check to see if the
                    // element is on top of its parent list -- don't check the
                    // position of the container
                    var parentList = container.parents(ele.data('parent-location-selector')).first();
                    if (parentList.hasClass('collapsed')) {
                        if (Math.abs(eleY - parentList.offset().top) < 10) {
                            return {
                                ele: container,
                                attachMethod: 'prepend',
                                parentList: parentList
                            };
                        }
                    }
                    // Otherwise, do check the container
                    else {
                        // If the list is empty, we should prepend to it,
                        // unless both elements are at the same location --
                        // this prevents the user from being unable to expand
                        // a section
                        var containerY = container.offset().top;
                        if (siblings.length == 0 &&
                            containerY != eleY &&
                            Math.abs(eleY - containerY) < 50) {
                            return {
                                ele: container,
                                attachMethod: 'prepend'
                            };
                        }
                        // Otherwise the list is populated, and we should attach before/after a sibling
                        else {
                            for (var j = 0; j < siblings.length; j++) {
                                var $sibling = $(siblings[j]);
                                var siblingY = $sibling.offset().top;
                                var siblingHeight = $sibling.height();
                                var siblingYEnd = siblingY + siblingHeight;

                                // Facilitate dropping into the beginning or end of a list
                                // (coming from opposite direction) via a "fudge factor". Math.min is for Jasmine test.
                                var fudge = Math.min(Math.ceil(siblingHeight / 2), 20);
                                // Dragging up into end of list.
                                if (j == siblings.length - 1 && yChange < 0 && Math.abs(eleY - siblingYEnd) <= fudge) {
                                    return {
                                        ele: $sibling,
                                        attachMethod: 'after'
                                    };
                                }
                                // Dragging down into beginning of list.
                                else if (j == 0 && yChange > 0 && Math.abs(eleY - siblingY) <= fudge) {
                                    return {
                                        ele: $sibling,
                                        attachMethod: 'before'
                                    };
                                }
                                else if (eleY >= siblingY && eleY <= siblingYEnd) {
                                    return {
                                        ele: $sibling,
                                        attachMethod: eleY - siblingY <= siblingHeight / 2 ? 'before' : 'after'
                                    };
                                }
                            }
                        }
                    }
                }
                // Failed drag
                return {
                    ele: null,
                    attachMethod: ''
                }
            },

            // Information about the current drag.
            dragState: {},

            onDragStart: function (draggie, event, pointer) {
                var ele = $(draggie.element);
                this.dragState = {
                    // Which element will be dropped into/onto on success
                    dropDestination: null,
                    // How we attach to the destination: 'before', 'after', 'prepend'
                    attachMethod: '',
                    // If dragging to an empty section, the parent section
                    parentList: null,
                    // The y location of the last dragMove event (to determine direction).
                    lastY: 0,
                    // The direction the drag is moving in (negative means up, positive down).
                    dragDirection: 0
                };
                if (!ele.hasClass('collapsed')) {
                    ele.addClass('collapsed');
                    ele.find('.expand-collapse-icon').first().addClass('expand').removeClass('collapse');
                    // onDragStart gets called again after the collapse, so we can't just store a variable in the dragState.
                    ele.addClass(this.expandOnDropClass);
                }
            },

            onDragMove: function (draggie, event, pointer) {
                // Handle scrolling of the browser.
                var scrollAmount = 0;
                var dragBuffer = 10;
                if (window.innerHeight - dragBuffer < pointer.clientY) {
                    scrollAmount = dragBuffer;
                }
                else if (dragBuffer > pointer.clientY) {
                    scrollAmount = -(dragBuffer);
                }
                if (scrollAmount !== 0) {
                    window.scrollBy(0, scrollAmount);
                    return;
                }

                var yChange = draggie.dragPoint.y - this.dragState.lastY;
                if (yChange !== 0) {
                    this.dragState.direction = yChange;
                }
                this.dragState.lastY = draggie.dragPoint.y;

                var ele = $(draggie.element);
                var destinationInfo = this.findDestination(ele, this.dragState.direction);
                var destinationEle = destinationInfo.ele;
                this.dragState.parentList = destinationInfo.parentList;

                // Clear out the old destination
                if (this.dragState.dropDestination) {
                    this.dragState.dropDestination.removeClass(this.droppableClasses);
                }
                // Mark the new destination
                if (destinationEle && this.pointerInBounds(pointer, ele)) {
                    ele.addClass(this.validDropClass);
                    destinationEle.addClass('drop-target drop-target-' + destinationInfo.attachMethod);
                    this.dragState.attachMethod = destinationInfo.attachMethod;
                    this.dragState.dropDestination = destinationEle;
                }
                else {
                    ele.removeClass(this.validDropClass);
                    this.dragState.attachMethod = '';
                    this.dragState.dropDestination = null;
                }
            },

            onDragEnd: function (draggie, event, pointer) {
                var ele = $(draggie.element);
                var destination = this.dragState.dropDestination;

                // Clear dragging state in preparation for the next event.
                if (destination) {
                    destination.removeClass(this.droppableClasses);
                }
                ele.removeClass(this.validDropClass);

                // If the drag succeeded, rearrange the DOM and send the result.
                if (destination && this.pointerInBounds(pointer, ele)) {
                    // Make sure we don't drop into a collapsed element
                    if (this.dragState.parentList) {
                        this.expandElement(this.dragState.parentList);
                    }
                    var method = this.dragState.attachMethod;
                    destination[method](ele);
                    this.handleReorder(ele);
                }
                // If the drag failed, send it back
                else {
                    $('.was-dragging').removeClass('was-dragging');
                    ele.addClass('was-dragging');
                }

                if (ele.hasClass(this.expandOnDropClass)) {
                    this.expandElement(ele);
                    ele.removeClass(this.expandOnDropClass);
                }

                // Everything in its right place
                ele.css({
                    top: 'auto',
                    left: 'auto'
                });

                this.dragState = {};
            },

            pointerInBounds: function (pointer, ele) {
                return pointer.clientX >= ele.offset().left && pointer.clientX < ele.offset().left + ele.width();
            },

            expandElement: function (ele) {
                ele.removeClass('collapsed');
                ele.find('.expand-collapse-icon').first().removeClass('expand').addClass('collapse');
            },

            /*
             * Find all parent-child changes and save them.
             */
            handleReorder: function (ele) {
                var parentSelector = ele.data('parent-location-selector');
                var childrenSelector = ele.data('child-selector');
                var newParentEle = ele.parents(parentSelector).first();
                var newParentLocator = newParentEle.data('locator');
                var oldParentLocator = ele.data('parent');
                // If the parent has changed, update the children of the old parent.
                if (newParentLocator !== oldParentLocator) {
                    // Find the old parent element.
                    var oldParentEle = $(parentSelector).filter(function () {
                        return $(this).data('locator') === oldParentLocator;
                    });
                    this.saveItem(oldParentEle, childrenSelector, function () {
                        ele.data('parent', newParentLocator);
                    });
                }
                var saving = new NotificationView.Mini({
                    title: gettext('Saving&hellip;')
                });
                saving.show();
                ele.addClass('was-dropped');
                // Timeout interval has to match what is in the CSS.
                setTimeout(function () {
                    ele.removeClass('was-dropped');
                }, 1000);
                this.saveItem(newParentEle, childrenSelector, function () {
                    saving.hide();
                });
            },

            /*
             * Actually save the update to the server. Takes the element
             * representing the parent item to save, a CSS selector to find
             * its children, and a success callback.
             */
            saveItem: function (ele, childrenSelector, success) {
                // Find all current child IDs.
                var children = _.map(
                    ele.find(childrenSelector),
                    function (child) {
                        return $(child).data('locator');
                    }
                );
                $.ajax({
                    url: ModuleUtils.getUpdateUrl(ele.data('locator')),
                    type: 'PUT',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        children: children
                    }),
                    success: success
                });
            },

            /*
             * Make `type` draggable using `handleClass`, able to be dropped
             * into `droppableClass`, and with parent type
             * `parentLocationSelector`.
             */
            makeDraggable: function (type, handleClass, droppableClass, parentLocationSelector) {
                _.each(
                    $(type),
                    function (ele) {
                        // Remember data necessary to reconstruct the parent-child relationships
                        $(ele).data('droppable-class', droppableClass);
                        $(ele).data('parent-location-selector', parentLocationSelector);
                        $(ele).data('child-selector', type);
                        var draggable = new Draggabilly(ele, {
                            handle: handleClass,
                            containment: '.wrapper-dnd'
                        });
                        draggable.on('dragStart', _.bind(overviewDragger.onDragStart, overviewDragger));
                        draggable.on('dragMove', _.bind(overviewDragger.onDragMove, overviewDragger));
                        draggable.on('dragEnd', _.bind(overviewDragger.onDragEnd, overviewDragger));
                    }
                );
            }
        };

        domReady(function() {
            // toggling overview section details
            $(function() {
                if ($('.courseware-section').length > 0) {
                    $('.toggle-button-sections').addClass('is-shown');
                }
            });
            $('.toggle-button-sections').bind('click', toggleSections);
            $('.expand-collapse-icon').bind('click', toggleSubmodules);

            var $body = $('body');
            $body.on('click', '.section-published-date .edit-button', editSectionPublishDate);
            $body.on('click', '.section-published-date .schedule-button', editSectionPublishDate);
            $body.on('click', '.edit-subsection-publish-settings .save-button', saveSetSectionScheduleDate);
            $body.on('click', '.edit-subsection-publish-settings .cancel-button', ModalUtils.hideModal);

            $('.new-courseware-section-button').bind('click', addNewSection);
            $('.new-subsection-item').bind('click', addNewSubsection);

            // Section
            overviewDragger.makeDraggable(
                '.courseware-section',
                '.section-drag-handle',
                '.courseware-overview',
                'article.courseware-overview'
            );
            // Subsection
            overviewDragger.makeDraggable(
                '.id-holder',
                '.subsection-drag-handle',
                '.subsection-list > ol',
                '.courseware-section'
            );
            // Unit
            overviewDragger.makeDraggable(
                '.unit',
                '.unit-drag-handle',
                'ol.sortable-unit-list',
                'li.branch, article.subsection-body'
            );
        });

        return {
            overviewDragger: overviewDragger,
            saveSetSectionScheduleDate: saveSetSectionScheduleDate
        };
    });
