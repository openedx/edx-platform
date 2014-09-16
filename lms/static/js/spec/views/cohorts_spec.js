define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/cohorts', 'js/collections/cohort'],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, CohortsView, CohortCollection) {
        describe("Cohorts View", function () {
            var createMockCohorts, createCohortsView;

            createMockCohorts = function () {
                return {
                    cohorts: [
                        {
                            id: 1,
                            name: 'Cat Lovers',
                            user_count: 123
                        },
                        {
                            id: 2,
                            name: 'Dog Lovers',
                            user_count: 456
                        }
                    ]
                };
            };

            createCohortsView = function () {
                var cohorts, view;
                cohorts = new CohortCollection(createMockCohorts(), {parse: true});
                view = new CohortsView({
                    model: cohorts
                });
                view.render();
                return view;
            };

            beforeEach(function () {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-editor');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohorts');
            });

            describe("Cohort Selector", function () {
                it('has no initial selection', function () {
                    var view = createCohortsView();
                    expect(view.$('.cohort-select').val()).toBe('');
                    expect(view.$('.cohort-management-group-header .title-value').text()).toBe('');
                });

                it('can select a cohort', function () {
                    var view = createCohortsView();
                    view.$('.cohort-select').val("1").change();
                    expect(view.$('.cohort-select').val()).toBe('1');
                    expect(view.$('.cohort-management-group-header .title-value').text()).toBe('Cat Lovers');
                    expect(view.$('.cohort-management-group-header .group-count').text()).toBe('123');
                });

                it('can switch cohort', function () {
                    var view = createCohortsView();
                    view.$('.cohort-select').val("1").change();
                    view.$('.cohort-select').val("2").change();
                    expect(view.$('.cohort-select').val()).toBe('2');
                    expect(view.$('.cohort-management-group-header .title-value').text()).toBe('Dog Lovers');
                    expect(view.$('.cohort-management-group-header .group-count').text()).toBe('456');
                });
            });
        });
    });
