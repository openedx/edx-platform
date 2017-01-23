define(['jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/spec_helpers/template_helpers', 'js/views/move_xblock_list',
        'js/views/move_xblock_breadcrumb', 'js/models/xblock_info'],
    function($, _, AjaxHelpers, TemplateHelpers, MoveXBlockListView, MoveXBlockBreadcrumbView,
             XBlockInfoModel) {
        'use strict';
        describe('MoveXBlock', function() {
            var renderViews, createXBlockInfo, createCourseOutline, moveXBlockBreadcrumbView,
                moveXBlockListView, parentChildMap, categoryMap, createChildXBlockInfo,
                verifyBreadcrumbViewInfo, verifyListViewInfo, getDisplayedInfo, clickForwardButton,
                clickBreadcrumbButton, verifyXBlockInfo, nextCategory;

            parentChildMap = {
                course: 'section',
                section: 'subsection',
                subsection: 'unit',
                unit: 'component'
            };

            categoryMap = {
                section: 'chapter',
                subsection: 'sequential',
                unit: 'vertical',
                component: 'component'
            };

            beforeEach(function() {
                setFixtures(
                    "<div class='breadcrumb-container'></div><div class='xblock-list-container'></div>"
                );
                TemplateHelpers.installTemplates([
                    'move-xblock-list',
                    'move-xblock-breadcrumb'
                ]);
            });

            afterEach(function() {
                moveXBlockBreadcrumbView.remove();
                moveXBlockListView.remove();
            });

            /**
             * Create child XBlock info.
             *
             * @param {String} category         XBlock category
             * @param {Object} outlineOptions   options according to which outline was created
             * @param {Object} xblockIndex      XBlock Index
             * @returns
             */
            createChildXBlockInfo = function(category, outlineOptions, xblockIndex) {
                var childInfo = {
                    category: categoryMap[category],
                    display_name: category + '_display_name_' + xblockIndex,
                    id: category + '_ID'
                };
                return createXBlockInfo(parentChildMap[category], outlineOptions, childInfo);
            };

            /**
             * Create parent XBlock info.
             *
             * @param {String} category         XBlock category
             * @param {Object} outlineOptions   options according to which outline was created
             * @param {Object} outline          ouline info being constructed
             * @returns {Object}
             */
            createXBlockInfo = function(category, outlineOptions, outline) {
                var childInfo = {
                        category: categoryMap[category],
                        display_name: category,
                        children: []
                    },
                    xblocks;

                xblocks = outlineOptions[category];
                if (!xblocks) {
                    return outline;
                }

                outline.child_info = childInfo; // eslint-disable-line no-param-reassign
                _.each(_.range(xblocks), function(xblockIndex) {
                    childInfo.children.push(
                        createChildXBlockInfo(category, outlineOptions, xblockIndex)
                    );
                });
                return outline;
            };

            /**
             * Create course outline.
             *
             * @param {Object} outlineOptions   options according to which outline was created
             * @returns {Object}
             */
            createCourseOutline = function(outlineOptions) {
                var courseOutline = {
                    category: 'course',
                    display_name: 'Demo Course',
                    id: 'COURSE_ID_101'
                };
                return createXBlockInfo('section', outlineOptions, courseOutline);
            };

            /**
             * Render breadcrumb and XBlock list view.
             *
             * @param {any} courseOutlineInfo      course outline info
             * @param {any} ancestorInfo           ancestors info
             */
            renderViews = function(courseOutlineInfo, ancestorInfo) {
                moveXBlockBreadcrumbView = new MoveXBlockBreadcrumbView({});
                moveXBlockListView = new MoveXBlockListView(
                    {
                        model: new XBlockInfoModel(courseOutlineInfo, {parse: true}),
                        ancestorInfo: ancestorInfo || {ancestors: []}
                    }
                );
            };

            /**
             * Extract displayed XBlock list info.
             *
             * @returns {Object}
             */
            getDisplayedInfo = function() {
                var viewEl = moveXBlockListView.$el;
                return {
                    categoryText: viewEl.find('.category-text').text().trim(),
                    currentLocationText: viewEl.find('.current-location').text().trim(),
                    xblockCount: viewEl.find('.xblock-item').length,
                    xblockDisplayNames: viewEl.find('.xblock-item .xblock-displayname').map(
                        function() { return $(this).text().trim(); }
                    ).get(),
                    forwardButtonSRTexts: viewEl.find('.xblock-item .forward-sr-text').map(
                        function() { return $(this).text().trim(); }
                    ).get(),
                    forwardButtonCount: viewEl.find('.fa-arrow-right.forward-sr-icon').length
                };
            };

            /**
             * Verify displayed XBlock list info.
             *
             * @param {String} category                 XBlock category
             * @param {Integer} expectedXBlocksCount    number of XBlock childs displayed
             * @param {Boolean} hasCurrentLocation      do we need to check current location
             */
            verifyListViewInfo = function(category, expectedXBlocksCount, hasCurrentLocation) {
                var displayedInfo = getDisplayedInfo();
                expect(displayedInfo.categoryText).toEqual(moveXBlockListView.categoriesText[category] + ':');
                expect(displayedInfo.xblockCount).toEqual(expectedXBlocksCount);
                expect(displayedInfo.xblockDisplayNames).toEqual(
                    _.map(_.range(expectedXBlocksCount), function(xblockIndex) {
                        return category + '_display_name_' + xblockIndex;
                    })
                );
                if (category !== 'component') {
                    if (hasCurrentLocation) {
                        expect(displayedInfo.currentLocationText).toEqual('(Current location)');
                    }
                    expect(displayedInfo.forwardButtonSRTexts).toEqual(
                        _.map(_.range(expectedXBlocksCount), function() {
                            return 'Click for children';
                        })
                    );
                    expect(displayedInfo.forwardButtonCount).toEqual(expectedXBlocksCount);
                }
            };

            /**
             * Verify rendered breadcrumb info.
             *
             * @param {any} category        XBlock category
             * @param {any} xblockIndex     XBlock index
             */
            verifyBreadcrumbViewInfo = function(category, xblockIndex) {
                var displayedBreadcrumbs = moveXBlockBreadcrumbView.$el.find('.breadcrumbs .bc-container').map(
                    function() { return $(this).text().trim(); }
                ).get(),
                    categories = _.keys(parentChildMap).concat(['component']),
                    visitedCategories = categories.slice(0, _.indexOf(categories, category));

                expect(displayedBreadcrumbs).toEqual(
                    _.map(visitedCategories, function(visitedCategory) {
                        return visitedCategory === 'course' ?
                            'Course Outline' : visitedCategory + '_display_name_' + xblockIndex;
                    })
                );
            };

            /**
             * Click forward button in the list of displayed XBlocks.
             *
             * @param {any} buttonIndex     forward button index
             */
            clickForwardButton = function(buttonIndex) {
                buttonIndex = buttonIndex || 0;  // eslint-disable-line no-param-reassign
                moveXBlockListView.$el.find('[data-item-index="' + buttonIndex + '"] button').click();
            };

            /**
             * Click on last clickable breadcrumb button.
             */
            clickBreadcrumbButton = function() {
                moveXBlockBreadcrumbView.$el.find('.bc-container button').last().click();
            };

            /**
             * Returns the parent or child category of current XBlock.
             *
             * @param {String} direction    `forward` or `backward`
             * @param {String} category     XBlock category
             * @returns {String}
             */
            nextCategory = function(direction, category) {
                return direction === 'forward' ? parentChildMap[category] : _.invert(parentChildMap)[category];
            };

            /**
             * Verify renderd info of breadcrumbs and XBlock list.
             *
             * @param {Object} outlineOptions       options according to which outline was created
             * @param {String} category             XBlock category
             * @param {Integer} buttonIndex         forward button index
             * @param {String} direction            `forward` or `backward`
             * @param {String} hasCurrentLocation   do we need to check current location
             * @returns
             */
            verifyXBlockInfo = function(outlineOptions, category, buttonIndex, direction, hasCurrentLocation) {
                var expectedXBlocksCount = outlineOptions[category];

                verifyListViewInfo(category, expectedXBlocksCount, hasCurrentLocation);
                verifyBreadcrumbViewInfo(category, buttonIndex);

                if (direction === 'forward') {
                    if (category === 'component') {
                        return;
                    }
                    clickForwardButton(buttonIndex);
                } else if (direction === 'backward') {
                    if (category === 'section') {
                        return;
                    }
                    clickBreadcrumbButton();
                }
                category = nextCategory(direction, category);  // eslint-disable-line no-param-reassign

                verifyXBlockInfo(outlineOptions, category, buttonIndex, direction, hasCurrentLocation);
            };

            it('renders views with correct information', function() {
                var outlineOptions = {section: 1, subsection: 1, unit: 1, component: 1},
                    outline = createCourseOutline(outlineOptions);

                renderViews(outline);
                verifyXBlockInfo(outlineOptions, 'section', 0, 'forward', false);
                verifyXBlockInfo(outlineOptions, 'component', 0, 'backward', false);
            });

            it('shows correct behavior on breadcrumb navigation', function() {
                var outline = createCourseOutline({section: 1, subsection: 1, unit: 1, component: 1});

                renderViews(outline);
                _.each(_.range(3), function() {
                    clickForwardButton();
                });

                _.each(['component', 'unit', 'subsection', 'section'], function(category) {
                    verifyListViewInfo(category, 1);
                    if (category !== 'section') {
                        moveXBlockBreadcrumbView.$el.find('.bc-container button').last().click();
                    }
                });
            });

            it('shows the correct current location', function() {
                var outlineOptions = {section: 2, subsection: 2, unit: 2, component: 2},
                    outline = createCourseOutline(outlineOptions),
                    ancestorInfo = {
                        ancestors: [
                            {
                                category: 'vertical',
                                display_name: 'unit_display_name_0',
                                id: 'unit_ID'
                            },
                            {
                                category: 'sequential',
                                display_name: 'subsection_display_name_0',
                                id: 'subsection_ID'
                            },
                            {
                                category: 'chapter',
                                display_name: 'section_display_name_0',
                                id: 'section_ID'
                            },
                            {
                                category: 'course',
                                display_name: 'Demo Course',
                                id: 'COURSE_ID_101'
                            }
                        ]
                    };

                renderViews(outline, ancestorInfo);
                verifyXBlockInfo(outlineOptions, 'section', 0, 'forward', true);
                // click the outline breadcrumb to render sections
                moveXBlockBreadcrumbView.$el.find('.bc-container button').first().click();
                verifyXBlockInfo(outlineOptions, 'section', 1, 'forward', false);
            });

            it('shows correct message when parent has no children', function() {
                var outlinesInfo = [
                    {
                        outline: createCourseOutline({}),
                        message: 'This course has no sections'
                    },
                    {
                        outline: createCourseOutline({section: 1}),
                        message: 'This section has no subsections',
                        forwardClicks: 1
                    },
                    {
                        outline: createCourseOutline({section: 1, subsection: 1}),
                        message: 'This subsection has no units',
                        forwardClicks: 2
                    },
                    {
                        outline: createCourseOutline({section: 1, subsection: 1, unit: 1}),
                        message: 'This unit has no components',
                        forwardClicks: 3
                    }
                ];

                _.each(outlinesInfo, function(info) {
                    renderViews(info.outline);
                    _.each(_.range(info.forwardClicks), function() {
                        clickForwardButton();
                    });
                    expect(moveXBlockListView.$el.find('.xblock-no-child-message').text().trim()).toEqual(info.message);
                    moveXBlockListView.undelegateEvents();
                    moveXBlockBreadcrumbView.undelegateEvents();
                });
            });
        });
    });
