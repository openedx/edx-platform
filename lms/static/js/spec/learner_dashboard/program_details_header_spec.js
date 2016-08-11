define([
    'backbone',
    'jquery',
    'js/learner_dashboard/views/program_header_view'
], function(Backbone, $, ProgramHeaderView) {
    'use strict';

    describe('Program Details Header View', function() {
        var view = null,
            context = {
                urls: {
                    program_listing_url: '/dashboard/programs'
                },
                programData: {
                    uuid: '12-ab',
                    name: 'Astrophysics',
                    subtitle: 'Learn contemporary astrophysics from the leaders in the field.',
                    category: 'xseries',
                    organizations: [
                        {
                            display_name: 'Australian National University',
                            img: 'common/test/data/static/picture1.jpg',
                            key: 'ANUx'
                        }
                    ],
                    banner_image_urls: {
                        w1440h480: 'common/test/data/static/picture1.jpg',
                        w726h242: 'common/test/data/static/picture2.jpg',
                        w348h116: 'common/test/data/static/picture3.jpg'
                    },
                    program_details_url: '/dashboard/programs'
                }
            };

        beforeEach(function() {
            setFixtures('<div class="js-program-header"></div>');
            view = new ProgramHeaderView({
                model: new Backbone.Model(context)
            });
            view.render();
        });

        afterEach(function() {
            view.remove();
        });

        it('should exist', function() {
            expect(view).toBeDefined();
        });

        it('should render the header based on the passed in model', function() {
            var programListUrl = view.$('.breadcrumb-list .crumb:nth-of-type(2) .crumb-link').attr('href');

            expect(view.$('.title').html()).toEqual(context.programData.name);
            expect(view.$('.subtitle').html()).toEqual(context.programData.subtitle);
            expect(view.$('.org-logo').length).toEqual(context.programData.organizations.length);
            expect(view.$('.org-logo').attr('src')).toEqual(context.programData.organizations[0].img);
            expect(view.$('.org-logo').attr('alt')).toEqual(
                    context.programData.organizations[0].display_name + '\'s logo'
                );
            expect(programListUrl).toEqual(context.urls.program_listing_url);
        });
    });
}
);
