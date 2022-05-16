/**
 * Provides helper methods for invoking Studio modal windows in Jasmine tests.
 */
define(['jquery', 'underscore'],
    function($, _) {
        var installTemplate, installTemplates;

        installTemplate = function(templateFile, isFirst, templateId) {
            var template = readFixtures(templateFile + '.underscore'),
                templateName = templateFile,
                slashIndex = _.lastIndexOf(templateName, '/');
            if (slashIndex >= 0) {
                templateName = templateFile.substring(slashIndex + 1);
            }
            if (!templateId) {
                templateId = templateName + '-tpl';
            }

            if (isFirst) {
                setFixtures($('<script>', {id: templateId, type: 'text/template'}).text(template));
            } else {
                appendSetFixtures($('<script>', {id: templateId, type: 'text/template'}).text(template));
            }
        };

        installTemplates = function(templateNames, isFirst) {
            if (!$.isArray(templateNames)) {
                templateNames = [templateNames];
            }

            $.each(templateNames, function(index, templateName) {
                installTemplate(templateName, isFirst);
                if (isFirst) {
                    isFirst = false;
                }
            });
        };

        return {
            installTemplate: installTemplate,
            installTemplates: installTemplates
        };
    });
