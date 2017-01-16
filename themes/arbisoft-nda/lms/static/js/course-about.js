
(function(require) {
    'use strict';

    require([
        'edx-ui-toolkit/js/utils/html-utils',
        '/static/example/js/leanModal.js'
    ], function(HtmlUtils) { // eslint-disable-line no-unused-vars // jshint ignore:line
        function expandDescription(entireDescriptionContent) {
            var showLessLinkHtml = '<a id="description_less" href="#" class="brand-link">Less</a>';
            HtmlUtils.setHtml('.course-description', HtmlUtils.HTML(entireDescriptionContent + showLessLinkHtml));
            $('#description_less').click(function(event) {
                event.preventDefault();
                truncateDescription(entireDescriptionContent);  // eslint-disable-line no-use-before-define
            });
        }
        function truncateDescription(entireDescriptionContent) {
            var showMoreLink = '',
                truncatedContent = '';
            if (entireDescriptionContent.length > 500) {
                showMoreLink = '... <a id="description_show" href="#" class="brand-link">See More</a>';
                truncatedContent = entireDescriptionContent.substring(0, entireDescriptionContent.indexOf(' ', 500));
                HtmlUtils.setHtml('.course-description', HtmlUtils.HTML(truncatedContent + showMoreLink));
                $('#description_show').click(function(event) {
                    event.preventDefault();
                    expandDescription(entireDescriptionContent);
                });
            }
        }
        function expandLearningPoints(entireLearningContent) {
            var showLessLinkHtml = '<a id="learning_less" href="#" class="brand-link learning-points-btn">Less</a>';
            HtmlUtils.setHtml(
                '.course-learning .list-bulleted',
                HtmlUtils.HTML(entireLearningContent + showLessLinkHtml)
            );
            $('#learning_less').click(function() {
                truncateLearningPoints(entireLearningContent);  // eslint-disable-line no-use-before-define
            });
        }
        function truncateLearningPoints(entireLearningContent) {
            var learningPointsCount = $('.course-learning .list-bulleted').children().length,
                points = '',
                showMoreLink = '';
            if (learningPointsCount > 6) {
                points = $('.course-learning .list-bulleted').children().slice((6 - learningPointsCount));
                points.remove();
                showMoreLink = '<a id="learning_show" href="#" class="brand-link learning-points-btn">See More</a>';
                HtmlUtils.append('.course-learning .list-bulleted', HtmlUtils.HTML(showMoreLink));
                $('#learning_show').click(function(event) {
                    event.preventDefault();
                    expandLearningPoints(entireLearningContent);
                });
            }
        }
        function init() {
            var entireDescriptionContent = $('.course-description').html(),
                entireLearningContent = $('.course-learning .list-bulleted').html();

            // Truncating the Course Description
            truncateDescription(entireDescriptionContent);

            // Truncating the Course learning points
            truncateLearningPoints(entireLearningContent);

            // Instructor Modal
            $('.instructor-image').leanModal({closeButton: '.modal_close', top: '10%'});
        }
        init();
    });
}).call(this, require || RequireJS.require);
