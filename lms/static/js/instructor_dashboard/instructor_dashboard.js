/*
Instructor Dashboard Tab Manager

The instructor dashboard is broken into sections.

Only one section is visible at a time,
  and is responsible for its own functionality.

NOTE: plantTimeout (which is just setTimeout from util.coffee)
      is used frequently in the instructor dashboard to isolate
      failures. If one piece of code under a plantTimeout fails
      then it will not crash the rest of the dashboard.

NOTE: The instructor dashboard currently does not
      use backbone. Just lots of jquery. This should be fixed.

NOTE: Server endpoints in the dashboard are stored in
      the 'data-endpoint' attribute of relevant html elements.
      The urls are rendered there by a template.

NOTE: For an example of what a section object should look like
      see course_info.coffee

imports from other modules
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
*/


(function() {
    'use strict';
    var $activeSection,
        CSS_ACTIVE_SECTION, CSS_IDASH_SECTION, CSS_INSTRUCTOR_CONTENT, CSS_INSTRUCTOR_NAV, HASH_LINK_PREFIX,
        SafeWaiter, plantTimeout, sectionsHaveLoaded, setupInstructorDashboard,
        setupInstructorDashboardSections;

    plantTimeout = function() {
        return window.InstructorDashboard.util.plantTimeout.apply(this, arguments);
    };

    CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    CSS_ACTIVE_SECTION = 'active-section';

    CSS_IDASH_SECTION = 'idash-section';

    CSS_INSTRUCTOR_NAV = 'instructor-nav';

    HASH_LINK_PREFIX = '#view-';

    $activeSection = null;

    SafeWaiter = (function() {
        function safeWaiter() {
            this.after_handlers = [];
            this.waitFor_handlers = [];
            this.fired = false;
        }

        safeWaiter.prototype.afterFor = function(f) {
            if (this.fired) {
                return f();
            } else {
                return this.after_handlers.push(f);
            }
        };

        safeWaiter.prototype.waitFor = function(f) {
            var safeWait = this;
            if (!this.fired) {
                this.waitFor_handlers.push(f);
                return function() {
                    safeWait.waitFor_handlers = safeWait.waitFor_handlers.filter(function(g) {
                        return g !== f;
                    });
                    if (safeWait.waitFor_handlers.length === 0) {
                        safeWait.fired = true;
                        safeWait.after_handlers.map(function(cb) {
                            return plantTimeout(0, cb);
                        });
                    }
                    return f.apply(safeWait, arguments);
                };
            } else {
                return false;
            }
        };

        return safeWaiter;
    }());

    sectionsHaveLoaded = new SafeWaiter;

    $(function() {
        var $instructorDashboardContent;
        $instructorDashboardContent = $('.' + CSS_INSTRUCTOR_CONTENT);
        if ($instructorDashboardContent.length > 0) {
            setupInstructorDashboard($instructorDashboardContent);
            return setupInstructorDashboardSections($instructorDashboardContent);
        }
        return setupInstructorDashboardSections($instructorDashboardContent);
    });

    setupInstructorDashboard = function(idashContent) {
        var $links, clickFirstLink, link, rmatch, sectionName;
        $links = idashContent.find('.' + CSS_INSTRUCTOR_NAV).find('.btn-link');
        $links.each(function(i, linkItem) {
            return $(linkItem).click(function(e) {
                var $section, itemSectionName, ref;
                e.preventDefault();
                idashContent.find('.' + CSS_INSTRUCTOR_NAV + ' li').children().removeClass(CSS_ACTIVE_SECTION);
                idashContent.find('.' + CSS_INSTRUCTOR_NAV + ' li').children().attr('aria-pressed', 'false');
                idashContent.find('.' + CSS_IDASH_SECTION).removeClass(CSS_ACTIVE_SECTION);
                itemSectionName = $(this).data('section');
                $section = idashContent.find('#' + itemSectionName);
                $(this).addClass(CSS_ACTIVE_SECTION);
                $(this).attr('aria-pressed', 'true');
                $section.addClass(CSS_ACTIVE_SECTION);
                window.analytics.pageview('instructor_section:' + itemSectionName);
                location.hash = '' + HASH_LINK_PREFIX + itemSectionName;
                sectionsHaveLoaded.afterFor(function() {
                    return $section.data('wrapper').onClickTitle();
                });
                if (!$section.is($activeSection)) {
                    if ($activeSection != null) {
                        ref = $activeSection.data('wrapper') != null;
                        if (ref) {
                            if (typeof ref.onExit === 'function') {
                                ref.onExit();
                            }
                        }
                    }
                }
                $activeSection = $section;
                return $activeSection;
            });
        });
        clickFirstLink = function() {
            var firstLink;
            firstLink = $links.eq(0);
            return firstLink.click();
        };
        if ((new RegExp('^' + HASH_LINK_PREFIX)).test(location.hash)) {
            rmatch = (new RegExp('^' + HASH_LINK_PREFIX + '(.*)')).exec(location.hash);
            sectionName = rmatch[1];
            link = $links.filter("[data-section='" + sectionName + "']");
            if (link.length === 1) {
                return link.click();
            } else {
                return clickFirstLink();
            }
        } else {
            return clickFirstLink();
        }
    };

    setupInstructorDashboardSections = function(idashContent) {
        var sectionsToInitialize;
        sectionsToInitialize = [
            {
                constructor: window.InstructorDashboard.sections.CourseInfo,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#course_info')
            }, {
                constructor: window.InstructorDashboard.sections.DataDownload,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#data_download')
            }, {
                constructor: window.InstructorDashboard.sections.ECommerce,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#e-commerce')
            }, {
                constructor: window.InstructorDashboard.sections.Membership,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#membership')
            }, {
                constructor: window.InstructorDashboard.sections.StudentAdmin,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#student_admin')
            }, {
                constructor: window.InstructorDashboard.sections.Extensions,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#extensions')
            }, {
                constructor: window.InstructorDashboard.sections.Email,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#send_email')
            }, {
                constructor: window.InstructorDashboard.sections.InstructorAnalytics,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#instructor_analytics')
            }, {
                constructor: window.InstructorDashboard.sections.Metrics,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#metrics')
            }, {
                constructor: window.InstructorDashboard.sections.CohortManagement,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#cohort_management')
            }, {
                constructor: window.InstructorDashboard.sections.Certificates,
                $element: idashContent.find('.' + CSS_IDASH_SECTION + '#certificates')
            }
        ];
        if (edx.instructor_dashboard.proctoring !== void 0) {
            sectionsToInitialize = sectionsToInitialize.concat([
                {
                    constructor: edx.instructor_dashboard.proctoring.ProctoredExamAllowanceView,
                    $element: idashContent.find('.' + CSS_IDASH_SECTION + '#special_exams')
                }, {
                    constructor: edx.instructor_dashboard.proctoring.ProctoredExamAttemptView,
                    $element: idashContent.find('.' + CSS_IDASH_SECTION + '#special_exams')
                }
            ]);
        }
        return sectionsToInitialize.map(function(_arg) {
            var $element, constructor;
            constructor = _arg.constructor;
            $element = _arg.$element;
            return plantTimeout(0, sectionsHaveLoaded.waitFor(function() {
                return new constructor($element);
            }));
        });
    };
}).call(this);
