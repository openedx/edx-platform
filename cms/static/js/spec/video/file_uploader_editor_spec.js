define(
    [
        'jquery', 'underscore', 'squire'
    ],
function ($, _, Squire) {
    'use strict';
    describe('FileUploader', function () {
        var FileUploaderTemplate = readFixtures(
                'metadata-file-uploader-entry.underscore'
            ),
            FileUploaderItemTemplate = readFixtures(
                'metadata-file-uploader-item.underscore'
            ),
            locator = 'locator',
            modelStub = {
                default_value: 'http://example.org/test_1',
                display_name: 'File Upload',
                explicitly_set: false,
                field_name: 'file_upload',
                help: 'Specifies the name for this component.',
                type: 'FileUploader',
                value: 'http://example.org/test_1'
            },
            self, injector;

        var setValue = function (view, value) {
            view.setValueInEditor(value);
            view.updateModel();
        };

        var createPromptSpy = function (name) {
            var spy = jasmine.createSpyObj(name, ['constructor', 'show', 'hide']);
            spy.constructor.and.returnValue(spy);
            spy.show.and.returnValue(spy);
            spy.extend = jasmine.createSpy().and.returnValue(spy.constructor);

            return spy;
        };

        beforeEach(function (done) {
            self = this;

            jasmine.addMatchers({
                assertValueInView: function() {
                    return {
                        compare: function (actual, expected) {
                            var value = actual.getValueFromEditor(),
                            passed = _.isEqual(value, expected);

                            return {
                                pass: passed,
                                message: 'Expected ' + actual + (passed ? '' : ' not') + ' to equal ' + expected
                            };
                        }
                    };
                },
                assertCanUpdateView: function () {
                    return {
                        compare: function (actual, expected) {
                            var view = actual,
                                value,
                                passed;

                            view.setValueInEditor(expected);
                            value = view.getValueFromEditor();

                            passed = _.isEqual(value, expected);

                            return {
                                pass: passed,
                                message: 'Expected ' + actual + (passed ? '' : ' not') + ' to equal ' + expected
                            };
                        }
                    };
                },
                assertClear: function () {
                    return {
                        compare: function (actual, modelValue) {
                            var view = actual,
                                model = view.model,
                                passed;

                            passed = model.getValue() === null &&
                                _.isEqual(model.getDisplayValue(), modelValue) &&
                                _.isEqual(view.getValueFromEditor(), modelValue);

                            return {
                                pass: passed
                            };
                        }
                    };
                },
                assertUpdateModel: function () {
                    return {
                        compare: function (actual, originalValue, newValue) {
                            var view = actual,
                                model = view.model,
                                expectOriginal,
                                passed;

                            view.setValueInEditor(newValue);
                            expectOriginal = _.isEqual(model.getValue(), originalValue);
                            view.updateModel();

                            passed = expectOriginal &&
                                _.isEqual(model.getValue(), newValue);

                            return {
                                pass: passed
                            };
                        }
                    };
                },
                verifyButtons: function () {
                    return {
                        compare: function (actual, upload, download) {
                            var view = actual,
                                uploadBtn = view.$('.upload-setting'),
                                downloadBtn = view.$('.download-setting'),
                                passed;

                            upload = upload ? uploadBtn.length : !uploadBtn.length;
                            download = download ? downloadBtn.length : !downloadBtn.length;
                            passed = upload && download;

                            return {
                                pass: passed
                            };
                        }
                    };
                }
            });

            appendSetFixtures($('<script>', {
                id: 'metadata-file-uploader-entry',
                type: 'text/template'
            }).text(FileUploaderTemplate));

            appendSetFixtures($('<script>', {
                id: 'metadata-file-uploader-item',
                type: 'text/template'
            }).text(FileUploaderItemTemplate));

            this.uploadSpies = createPromptSpy('UploadDialog');

            injector = new Squire();
            injector.mock('js/views/uploads', function () {
                return self.uploadSpies.constructor;
            });
            injector.mock('js/views/video/transcripts/metadata_videolist');
            injector.mock('js/views/video/translations_editor');

            injector.require([
                    'js/models/metadata', 'js/views/metadata'
                ],
                function (MetadataModel, MetadataView) {
                    var model = new MetadataModel($.extend(true, {}, modelStub));
                    self.view = new MetadataView.FileUploader({
                        model: model,
                        locator: locator
                    });

                    done();
                });
        });

        afterEach(function () {
            injector.clean();
            injector.remove();
        });

        it('returns the initial value upon initialization', function () {
            expect(this.view).assertValueInView('http://example.org/test_1');
            expect(this.view).verifyButtons(true, true);
        });

        it('updates its value correctly', function () {
            expect(this.view).assertCanUpdateView('http://example.org/test_2');
        });

        it('upload works correctly', function () {
            var options;

            setValue(this.view, '');
            expect(this.view).verifyButtons(true, false);

            this.view.$el.find('.upload-setting').click();

            expect(this.uploadSpies.constructor).toHaveBeenCalled();
            expect(this.uploadSpies.show).toHaveBeenCalled();

            options = this.uploadSpies.constructor.calls.mostRecent().args[0];
            options.onSuccess({
                'asset': {
                    'url': 'http://example.org/test_3'
                }
            });

            expect(this.view).verifyButtons(true, true);
            expect(this.view.getValueFromEditor()).toEqual('http://example.org/test_3');
        });

        it('has a clear method to revert to the model default', function () {
            setValue(this.view, 'http://example.org/test_5');

            this.view.clear();
            expect(this.view).assertClear('http://example.org/test_1');
        });

        it('has an update model method', function () {
            expect(this.view).assertUpdateModel(null, 'http://example.org/test_6');
        });
    });
});
