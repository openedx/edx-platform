define(['jquery', 'logger', 'js/courseware/courseware_factory'], function($, Logger, coursewareFactory) {
    'use strict';

    describe('Courseware link click eventing', function() {
        beforeEach(function() {
            loadFixtures('js/fixtures/courseware/link_clicked_events.html');
            coursewareFactory();
            spyOn(Logger, 'log');
        });

        it('sends an event when an external link is clicked', function() {
            $('.external-link').click();
            expect(Logger.log).toHaveBeenCalledWith('edx.ui.lms.link_clicked', {
                target_url: 'http://example.com/',
                current_url: 'http://' + window.location.host + '/context.html'
            });
        });

        it('sends an event when an internal link is clicked', function() {
            $('.internal-link').click();
            expect(Logger.log).toHaveBeenCalledWith('edx.ui.lms.link_clicked', {
                target_url: 'http://' + window.location.host + '/some/internal/link',
                current_url: 'http://' + window.location.host + '/context.html'
            });
        });

        it('does not send an event when a page navigation link is clicked', function() {
            $('.page-nav').click();
            expect(Logger.log).not.toHaveBeenCalledWith('edx.ui.lms.link_clicked');
        });
    });
});
