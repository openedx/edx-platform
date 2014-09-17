define(['backbone', 'jquery', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/views/cohorts', 'js/collections/cohort'],
    function (Backbone, $, AjaxHelpers, TemplateHelpers, CohortsView, CohortCollection) {
        describe("Cohorts View", function () {
            var createMockCohorts, createCohortsView, cohortsView, requests;

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

            createCohortsView = function (test) {
                var cohorts = new CohortCollection(createMockCohorts(), {parse: true});
                cohorts.url = '/mock_service';
                requests = AjaxHelpers.requests(test);
                cohortsView = new CohortsView({
                    model: cohorts
                });
                cohortsView.render();
            };

            beforeEach(function () {
                setFixtures("<div></div>");
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohort-editor');
                TemplateHelpers.installTemplate('templates/instructor/instructor_dashboard_2/cohorts');
            });

            describe("Cohort Selector", function () {
                it('has no initial selection', function () {
                    createCohortsView(this);
                    expect(cohortsView.$('.cohort-select').val()).toBe('');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('');
                });

                it('can select a cohort', function () {
                    createCohortsView(this);
                    cohortsView.$('.cohort-select').val("1").change();
                    expect(cohortsView.$('.cohort-select').val()).toBe('1');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('Cat Lovers');
                    expect(cohortsView.$('.cohort-management-group-header .group-count').text()).toBe('123');
                });

                it('can switch cohort', function () {
                    createCohortsView(this);
                    cohortsView.$('.cohort-select').val("1").change();
                    cohortsView.$('.cohort-select').val("2").change();
                    expect(cohortsView.$('.cohort-select').val()).toBe('2');
                    expect(cohortsView.$('.cohort-management-group-header .title-value').text()).toBe('Dog Lovers');
                    expect(cohortsView.$('.cohort-management-group-header .group-count').text()).toBe('456');
                });
            });

            describe("Add Students Button", function () {
                it('can add a student', function() {
                    createCohortsView(this);
                    cohortsView.$('.cohort-select').val("1").change();
                    cohortsView.$('.cohort-management-group-add-students').text('student@sample.com');
                    cohortsView.$('.cohort-management-group-add-form').submit();
                    // TODO: get this to work...
                    /*
                    AjaxHelpers.expectJsonRequest(requests, 'POST', '/mock_service/1/add', {
                        'users': 'student@sample.com'
                    });
                    AjaxHelpers.respondWithJson(requests, {});
                    */
                });
            });
        });
    });
