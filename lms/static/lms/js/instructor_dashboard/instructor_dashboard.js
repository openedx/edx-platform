/**
 * Instructor Dashboard Tab Manager
 *
 * The instructor dashboard is broken into sections.
 *
 * Only one section is visible at a time, and it is responsible for its own functionality.
 *
 * NOTE: plantTimeout (which is just setTimeout from util.coffee)
 * is used frequently in the instructor dashboard to isolate
 * failures. If one piece of code under a plantTimeout fails
 * then it will not crash the rest of the dashboard.
 *
 * NOTE: The instructor dashboard currently does not
 * use backbone. Just lots of jquery. This should be fixed.
 *
 * NOTE: Server endpoints in the dashboard are stored in
 * the 'data-endpoint' attribute of relevant html elements.
 * The urls are rendered there by a template.
 *
 * NOTE: For an example of what a section object should look like
 * see course_info.coffee
 *
 */
(function(analytics) {
    'use strict';

    var $active_section, CSS_ACTIVE_SECTION, CSS_IDASH_SECTION, CSS_INSTRUCTOR_CONTENT, CSS_INSTRUCTOR_NAV,
        HASH_LINK_PREFIX, SafeWaiter, plantTimeout, sections_have_loaded, setup_instructor_dashboard,
        setup_instructor_dashboard_sections;

    plantTimeout = function() {
        return window.InstructorDashboard.util.plantTimeout.apply(this, arguments);
    };

    CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2';

    CSS_ACTIVE_SECTION = 'active-section';

    CSS_IDASH_SECTION = 'idash-section';

    CSS_INSTRUCTOR_NAV = 'instructor-nav';

    HASH_LINK_PREFIX = '#view-';

    $active_section = null;

    SafeWaiter = (function() {

        function SafeWaiter() {
            this.after_handlers = [];
            this.waitFor_handlers = [];
            this.fired = false;
        }

        SafeWaiter.prototype.after = function(f) {
            if (this.fired) {
                return f();
            } else {
                return this.after_handlers.push(f);
            }
        };

        SafeWaiter.prototype.waitFor = function(f) {
            var _this = this;
            if (this.fired) {
                return;
            }
            this.waitFor_handlers.push(f);
            return function() {
                _this.waitFor_handlers = _this.waitFor_handlers.filter(function(g) {
                    return g !== f;
                });
                if (_this.waitFor_handlers.length === 0) {
                    _this.fired = true;
                    _this.after_handlers.map(function(cb) {
                        return plantTimeout(0, cb);
                    });
                }
                return f.apply(_this, arguments);
            };
        };

        return SafeWaiter;

    })();

    sections_have_loaded = new SafeWaiter();

    $(function() {
        var instructor_dashboard_content;
        instructor_dashboard_content = $("." + CSS_INSTRUCTOR_CONTENT);
        if (instructor_dashboard_content.length > 0) {
            setup_instructor_dashboard(instructor_dashboard_content);
            return setup_instructor_dashboard_sections(instructor_dashboard_content);
        }
    });

    setup_instructor_dashboard = function(idash_content) {
        var $links, click_first_link, link, rmatch, section_name;
        $links = idash_content.find("." + CSS_INSTRUCTOR_NAV).find('a');
        $links.each(function(i, link) {
            return $(link).click(function(e) {
                var $section, section_name, _ref;
                e.preventDefault();
                idash_content.find("." + CSS_INSTRUCTOR_NAV + " li").children().removeClass(CSS_ACTIVE_SECTION);
                idash_content.find("." + CSS_IDASH_SECTION).removeClass(CSS_ACTIVE_SECTION);
                section_name = $(this).data('section');
                $section = idash_content.find("#" + section_name);
                $(this).addClass(CSS_ACTIVE_SECTION);
                $section.addClass(CSS_ACTIVE_SECTION);
                analytics.pageview("instructor_section:" + section_name);
                location.hash = "" + HASH_LINK_PREFIX + section_name;
                sections_have_loaded.after(function() {
                    $section.data('wrapper').onClickTitle();
                });
                if (!$section.is($active_section)) {
                    if ($active_section !== null) {
                        if ((_ref = $active_section.data('wrapper')) !== null) {
                            if (typeof _ref.onExit === "function") {
                                _ref.onExit();
                            }
                        }
                    }
                }
                $active_section = $section;
            });
        });
        click_first_link = function() {
            var link;
            link = $links.eq(0);
            link.click();
        };
        if ((new RegExp("^" + HASH_LINK_PREFIX)).test(location.hash)) {
            rmatch = (new RegExp("^" + HASH_LINK_PREFIX + "(.*)")).exec(location.hash);
            section_name = rmatch[1];
            link = $links.filter("[data-section='" + section_name + "']");
            if (link.length === 1) {
                link.click();
            } else {
                click_first_link();
            }
        } else {
            click_first_link();
        }
    };

    setup_instructor_dashboard_sections = function(idash_content) {
        var sections_to_initialize;
        sections_to_initialize = [
            {
                constructor: window.InstructorDashboard.sections.CourseInfo,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#course_info")
            }, {
                constructor: window.InstructorDashboard.sections.DataDownload,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#data_download")
            }, {
                constructor: window.InstructorDashboard.sections.ECommerce,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#e-commerce")
            }, {
                constructor: window.InstructorDashboard.sections.Membership,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#membership")
            }, {
                constructor: window.InstructorDashboard.sections.StudentAdmin,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#student_admin")
            }, {
                constructor: window.InstructorDashboard.sections.Extensions,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#extensions")
            }, {
                constructor: window.InstructorDashboard.sections.Email,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#send_email")
            }, {
                constructor: window.InstructorDashboard.sections.InstructorAnalytics,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#instructor_analytics")
            }, {
                constructor: window.InstructorDashboard.sections.Metrics,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#metrics")
            }, {
                constructor: window.InstructorDashboard.sections.CohortManagement,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#cohort_management")
            }, {
                constructor: window.InstructorDashboard.sections.Certificates,
                $element: idash_content.find("." + CSS_IDASH_SECTION + "#certificates")
            }
        ];
        if (edx.instructor_dashboard.proctoring !== void 0) {
            sections_to_initialize = sections_to_initialize.concat([
                {
                    constructor: edx.instructor_dashboard.proctoring.ProctoredExamAllowanceView,
                    $element: idash_content.find("." + CSS_IDASH_SECTION + "#special_exams")
                }, {
                    constructor: edx.instructor_dashboard.proctoring.ProctoredExamAttemptView,
                    $element: idash_content.find("." + CSS_IDASH_SECTION + "#special_exams")
                }
            ]);
        }
        sections_to_initialize.map(function(_arg) {
            var $element, constructor;
            constructor = _arg.constructor;
            $element = _arg.$element;
            return plantTimeout(0, sections_have_loaded.waitFor(function() {
                return new constructor($element);
            }));
        });
    };

}).call(this, analytics);  // jshint ignore:line
