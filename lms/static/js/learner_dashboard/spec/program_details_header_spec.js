/* globals setFixtures */

import Backbone from 'backbone';

import ProgramHeaderView from '../views/program_header_view';

describe('Program Details Header View', () => {
    let view = null;
    const context = {
        programData: {
            uuid: 'a87e5eac-3c93-45a1-a8e1-4c79ca8401c8',
            title: 'Food Security and Sustainability',
            subtitle: 'Learn how to feed all people in the world in a sustainable way.',
            type: 'XSeries',
            detail_url: 'https://www.edx.org/foo/bar',
            banner_image: {
                medium: {
                    height: 242,
                    width: 726,
                    url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.medium.jpg',
                },
                'x-small': {
                    height: 116,
                    width: 348,
                    url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.x-small.jpg',
                },
                small: {
                    height: 145,
                    width: 435,
                    url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.small.jpg',
                },
                large: {
                    height: 480,
                    width: 1440,
                    url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.large.jpg',
                },
            },
            authoring_organizations: [
                {
                    uuid: '0c6e5fa2-96e8-40b2-9ebe-c8b0df2a3b22',
                    key: 'WageningenX',
                    name: 'Wageningen University & Research',
                    certificate_logo_image_url: 'https://example.com/org-certificate-logo.jpg',
                    logo_image_url: 'https://example.com/org-logo.jpg',
                },
            ],
        },
    };

    beforeEach(() => {
        setFixtures('<div class="js-program-header"></div>');
        view = new ProgramHeaderView({
            model: new Backbone.Model(context),
        });
        view.render();
    });

    afterEach(() => {
        view.remove();
    });

    it('should exist', () => {
        expect(view).toBeDefined();
    });

    it('should render the header based on the passed in model', () => {
        expect(view.$('.program-title').html()).toEqual(context.programData.title);
        expect(view.$('.org-logo').length).toEqual(context.programData.authoring_organizations.length);
        expect(view.$('.org-logo').attr('src'))
            .toEqual(context.programData.authoring_organizations[0].certificate_logo_image_url);
        expect(view.$('.org-logo').attr('alt'))
            .toEqual(`${context.programData.authoring_organizations[0].name}'s logo`);
    });
});
