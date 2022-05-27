define(['js/models/component_template'],
    function(ComponentTemplate) {
        describe('ComponentTemplates', function() {
            var mockTemplateJSON = {
                templates: [
                    {
                        category: 'problem',
                        boilerplate_name: 'formularesponse.yaml',
                        display_name: 'Math Expression Input'
                    }, {
                        category: 'problem',
                        boilerplate_name: null,
                        display_name: 'Blank Advanced Problem'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'checkboxes.yaml',
                        display_name: 'Checkboxes'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'multiple_choice.yaml',
                        display_name: 'Multiple Choice'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'drag_and_drop.yaml',
                        display_name: 'Drag and Drop'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'problem_with_hint.yaml',
                        display_name: 'Problem with Adaptive Hint'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'imageresponse.yaml',
                        display_name: 'Image Mapped Input'
                    }, {
                        category: 'openassessment',
                        boilerplate_name: null,
                        display_name: 'Peer Assessment'
                    }, {
                        category: 'problem',
                        boilerplate_name: 'an_easy_problem.yaml',
                        display_name: 'An Easy Problem'
                    }, {
                        category: 'word_cloud',
                        boilerplate_name: null,
                        display_name: 'Word Cloud'
                    }, { // duplicate display name to verify sort behavior
                        category: 'word_cloud',
                        boilerplate_name: 'alternate_word_cloud.yaml',
                        display_name: 'Word Cloud'
                    }],
                type: 'problem',
                support_legend: {show_legend: false}
            };

            it('orders templates correctly', function() {
                var lastTemplate = null,
                    firstComparison = true,
                    componentTemplate = new ComponentTemplate(),
                    template, templateName, i;
                componentTemplate.parse(mockTemplateJSON);
                for (i = 0; i < componentTemplate.templates.length; i++) {
                    template = componentTemplate.templates[i];
                    templateName = template.display_name;
                    if (lastTemplate) {
                        if (!firstComparison || lastTemplate.boilerplate_name) {
                            expect(lastTemplate.display_name < templateName).toBeTruthy();
                        }
                        firstComparison = false;
                    } else {
                        // If the first template is blank, make sure that it has the correct category
                        if (!template.boilerplate_name) {
                            expect(template.category).toBe('problem');
                        }
                        lastTemplate = template;
                    }
                }
            });
        });
    });
