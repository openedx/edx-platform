define(
    [
        'jquery', 'backbone', 'underscore',
        'js/views/video/transcripts/utils', 'js/views/video/transcripts/editor',
        'js/views/metadata', 'js/models/metadata', 'js/collections/metadata',
        'underscore.string', 'xmodule', 'js/views/video/transcripts/metadata_videolist'
    ],
function($, Backbone, _, Utils, Editor, MetadataView, MetadataModel, MetadataCollection, _str) {
    describe('Transcripts.Editor', function() {
        var VideoListEntry = {
                default_value: ['a thing', 'another thing'],
                display_name: 'Video URL',
                explicitly_set: true,
                field_name: 'video_url',
                help: 'A list of things.',
                options: [],
                type: MetadataModel.VIDEO_LIST_TYPE,
                value: [
                    'http://youtu.be/12345678901',
                    'video.mp4',
                    'video.webm'
                ]
            },
            DisplayNameEntry = {
                default_value: 'default value',
                display_name: 'Dispaly Name',
                explicitly_set: true,
                field_name: 'display_name',
                help: 'Specifies the name for this component.',
                options: [],
                type: MetadataModel.GENERIC_TYPE,
                value: 'display value'
            },
            VideoIDEntry = {
                default_value: 'test default value',
                display_name: 'Video ID',
                explicitly_set: true,
                field_name: 'edx_video_id',
                help: 'Specifies the video ID.',
                options: [],
                type: 'VideoID',
                value: 'basic tab video id'
            },
            models = [DisplayNameEntry, VideoListEntry, VideoIDEntry],
            testData = {
                display_name: DisplayNameEntry,
                video_url: VideoListEntry,
                edx_video_id: VideoIDEntry
            },
            metadataDict = {
                object: testData,
                string: JSON.stringify(testData)
            },
            component_locator = 'component_locator',
            transcripts, $container, waitForEvent, editor;

        var waitsForDisplayName = function(collection) {
            return jasmine.waitUntil(function() {
                var displayNameValue = collection[0].getValue();
                return displayNameValue !== '' && displayNameValue !== 'video_id';
            });
        };

        beforeEach(function() {
            var tpl = sandbox({
                class: 'wrapper-comp-settings basic_metadata_edit',
                'data-metadata': JSON.stringify(metadataDict.object)
            });

            appendSetFixtures(tpl);
            $container = $('.basic_metadata_edit');

            spyOn(Utils, 'command');
        });

        afterEach(function() {
            Utils.Storage.remove('sub');
        });

        describe('Events', function() {
            beforeEach(function() {
                Utils.command.and.callThrough();
                spyOn(Backbone, 'trigger').and.callThrough();
                spyOn(Editor.prototype, 'destroy').and.callThrough();
                spyOn(Editor.prototype, 'handleFieldChanged').and.callThrough();
                spyOn(Editor.prototype, 'getLocator').and.returnValue(component_locator);

                appendSetFixtures(
                    sandbox({  // eslint-disable-line no-undef
                        class: 'wrapper-comp-settings basic_metadata_edit',
                        'data-metadata': JSON.stringify({video_url: VideoListEntry, edx_video_id: VideoIDEntry})
                    })
                );

                appendSetFixtures(
                    $('<script>',
                        {
                            id: 'metadata-videolist-entry',
                            type: 'text/template'
                        }
                    ).text(readFixtures('video/transcripts/metadata-videolist-entry.underscore'))
                );

                appendSetFixtures(
                    $('<script>',
                        {
                            id: 'metadata-string-entry',
                            type: 'text/template'
                        }
                    ).text(readFixtures('metadata-string-entry.underscore'))
                );

                editor = new Editor({
                    el: $('.basic_metadata_edit')
                });

                // reset the already triggered events
                Backbone.trigger.calls.reset();
                // reset the manual call to `handleFieldChanged` we made in the `editor.js::initialize`
                Editor.prototype.handleFieldChanged.calls.reset();
            });

            waitForEvent = function(eventName) {
                var triggerCallArgs;
                return jasmine.waitUntil(function() {
                    triggerCallArgs = Backbone.trigger.calls.mostRecent().args;
                    return Backbone.trigger.calls.count() === 1 && triggerCallArgs[0] === eventName;
                });
            };

            afterEach(function() {
                Backbone.trigger.calls.reset();
                Editor.prototype.destroy.calls.reset();
                Editor.prototype.handleFieldChanged.calls.reset();
            });

            it('handles transcripts:basicTabFieldChanged', function(done) {
                var event = 'transcripts:basicTabFieldChanged';

                Backbone.trigger(event);
                waitForEvent(event)
                    .then(function() {
                        expect(Editor.prototype.handleFieldChanged).toHaveBeenCalled();
                        expect(Utils.command).toHaveBeenCalledWith(
                            'check',
                            component_locator,
                            [
                                {mode: 'youtube', video: '12345678901', type: 'youtube'},
                                {mode: 'html5', video: 'video', type: 'mp4'},
                                {mode: 'html5', video: 'video', type: 'webm'},
                                {mode: 'edx_video_id', type: 'edx_video_id', video: 'basic tab video id'}
                            ]
                        );
                    }).always(done);
            });

            it('handles xblock:editorModalHidden', function(done) {
                var event = 'xblock:editorModalHidden';

                Backbone.trigger(event);
                waitForEvent(event)
                    .then(function() {
                        expect(Editor.prototype.destroy).toHaveBeenCalled();
                    }).always(done);
            });
        });

        describe('Test initialization', function() {
            beforeEach(function() {
                spyOn(MetadataView, 'Editor');
                spyOn(Editor.prototype, 'handleFieldChanged');

                transcripts = new Editor({
                    el: $container
                });
            });

            afterEach(function() {
                MetadataView.Editor.calls.reset();
                Editor.prototype.handleFieldChanged.calls.reset();
            });

            $.each(metadataDict, function(index, val) {
                it('toModels with argument as ' + index, function() {
                    expect(transcripts.toModels(val)).toEqual(models);
                });
            });

            it('MetadataView.Editor is initialized', function() {
                expect(MetadataView.Editor).toHaveBeenCalledWith({
                    el: $container,
                    collection: transcripts.collection
                });
            });
        });

        describe('Test synchronization', function() {
            var nameEntry = {
                    default_value: 'default value',
                    display_name: 'Display Name',
                    explicitly_set: true,
                    field_name: 'display_name',
                    help: 'Specifies the name for this component.',
                    options: [],
                    type: MetadataModel.GENERIC_TYPE,
                    value: 'default'
                },

                subEntry = {
                    default_value: 'default value',
                    display_name: 'Timed Transcript',
                    explicitly_set: true,
                    field_name: 'sub',
                    help: 'Specifies the name for this component.',
                    options: [],
                    type: 'Generic',
                    value: 'default'
                },

                html5SourcesEntry = {
                    default_value: ['a thing', 'another thing'],
                    display_name: 'Video Sources',
                    explicitly_set: true,
                    field_name: 'html5_sources',
                    help: 'A list of html5 sources.',
                    options: [],
                    type: MetadataModel.LIST_TYPE,
                    value: ['default.mp4', 'default.webm']
                },

                youtubeEntry = {
                    default_value: 'OEoXaMPEzfM',
                    display_name: 'Youtube ID',
                    explicitly_set: true,
                    field_name: 'youtube_id_1_0',
                    help: 'Specifies the name for this component.',
                    options: [],
                    type: MetadataModel.GENERIC_TYPE,
                    value: 'OEoXaMPEzfM'
                },
                videoIDEntry = {
                    default_value: 'test default value',
                    display_name: 'Video ID',
                    explicitly_set: true,
                    field_name: 'edx_video_id',
                    help: 'Specifies the video ID.',
                    options: [],
                    type: MetadataModel.GENERIC_TYPE,
                    value: 'advanced tab video id'
                },
                metadataCollection,
                metadataView;


            beforeEach(function() {
                spyOn(MetadataView, 'Editor');
                spyOn(Editor.prototype, 'handleFieldChanged');

                transcripts = new Editor({
                    el: $container
                });

                metadataCollection = new MetadataCollection(
                    [
                        nameEntry,
                        subEntry,
                        html5SourcesEntry,
                        youtubeEntry,
                        videoIDEntry
                    ]
                );

                metadataView = jasmine.createSpyObj(
                    'MetadataView.Editor',
                    [
                        'getModifiedMetadataValues'
                    ]
                );
            });

            afterEach(function() {
                MetadataView.Editor.calls.reset();
                Editor.prototype.handleFieldChanged.calls.reset();
            });

            describe('Test Advanced to Basic synchronization', function() {
                it('Correct data', function(done) {
                    transcripts.syncBasicTab(metadataCollection, metadataView);
                    var collection = transcripts.collection.models;

                    waitsForDisplayName(collection)
                    .then(function() {
                        var displayNameValue, videoUrlValue, videoIDValue;

                        displayNameValue = transcripts.collection.findWhere({
                            field_name: 'display_name'
                        }).getValue();
                        expect(displayNameValue).toEqual('default');

                        videoUrlValue = transcripts.collection.findWhere({
                            field_name: 'video_url'
                        }).getValue();
                        expect(videoUrlValue).toEqual([
                            'http://youtu.be/OEoXaMPEzfM',
                            'default.mp4',
                            'default.webm'
                        ]);

                        videoIDValue = transcripts.collection.findWhere({
                            field_name: 'edx_video_id'
                        }).getValue();
                        expect(videoIDValue).toEqual('advanced tab video id');
                    })
                    .always(done);
                });

                it('If metadataCollection is not defined', function() {
                    var videoUrlValue, videoIDValue;

                    transcripts.syncBasicTab(null);

                    videoUrlValue = transcripts.collection.findWhere({
                        field_name: 'video_url'
                    }).getValue();

                    expect(videoUrlValue).toEqual([
                        'http://youtu.be/12345678901',
                        'video.mp4',
                        'video.webm'
                    ]);

                    videoIDValue = transcripts.collection.findWhere({
                        field_name: 'edx_video_id'
                    }).getValue();
                    expect(videoIDValue).toEqual('basic tab video id');
                });

                it('Youtube Id has length not eqaul 11', function() {
                    var model, videoUrlValue;

                    model = metadataCollection.findWhere({
                        field_name: 'youtube_id_1_0'
                    });

                    model.setValue([
                        '12345678',
                        'default.mp4',
                        'default.webm'
                    ]);

                    transcripts.syncBasicTab(metadataCollection, metadataView);

                    videoUrlValue = transcripts.collection.findWhere({
                        field_name: 'video_url'
                    }).getValue();

                    expect(videoUrlValue).toEqual([
                        '',
                        'default.mp4',
                        'default.webm'
                    ]);
                });
            });

            describe('Test Basic to Advanced synchronization', function() {
                it('Correct data', function(done) {
                    transcripts.syncAdvancedTab(metadataCollection);

                    var collection = metadataCollection.models;
                    waitsForDisplayName(collection)
                    .then(function() {
                        var displayNameValue, subValue, html5SourcesValue, youtubeValue, videoIDValue;

                        displayNameValue = metadataCollection.findWhere({
                            field_name: 'display_name'
                        }).getValue();
                        expect(displayNameValue).toEqual('display value');

                        subValue = metadataCollection.findWhere({
                            field_name: 'sub'
                        }).getValue();
                        expect(subValue).toEqual('default');

                        html5SourcesValue = metadataCollection.findWhere({
                            field_name: 'html5_sources'
                        }).getValue();
                        expect(html5SourcesValue).toEqual([
                            'video.mp4',
                            'video.webm'
                        ]);

                        youtubeValue = metadataCollection.findWhere({
                            field_name: 'youtube_id_1_0'
                        }).getValue();
                        expect(youtubeValue).toEqual('12345678901');

                        videoIDValue = metadataCollection.findWhere({
                            field_name: 'edx_video_id'
                        }).getValue();
                        expect(videoIDValue).toEqual('basic tab video id');
                    })
                    .always(done);
                });

                it('metadataCollection is not defined', function() {
                    var displayNameValue, subValue, html5SourcesValue, youtubeValue, videoIDValue;

                    transcripts.syncAdvancedTab(null);

                    displayNameValue = metadataCollection.findWhere({
                        field_name: 'display_name'
                    }).getValue();
                    expect(displayNameValue).toEqual('default');

                    subValue = metadataCollection.findWhere({
                        field_name: 'sub'
                    }).getValue();
                    expect(subValue).toEqual('default');

                    html5SourcesValue = metadataCollection.findWhere({
                        field_name: 'html5_sources'
                    }).getValue();
                    expect(html5SourcesValue).toEqual([
                        'default.mp4',
                        'default.webm'
                    ]);

                    youtubeValue = metadataCollection.findWhere({
                        field_name: 'youtube_id_1_0'
                    }).getValue();
                    expect(youtubeValue).toEqual('OEoXaMPEzfM');

                    videoIDValue = metadataCollection.findWhere({
                        field_name: 'edx_video_id'
                    }).getValue();
                    expect(videoIDValue).toEqual('advanced tab video id');
                });

                it('Youtube Id is not adjusted', function() {
                    var model, html5SourcesValue, youtubeValue;

                    model = transcripts.collection.findWhere({
                        field_name: 'video_url'
                    });

                    model.setValue([
                        'video.mp4',
                        'video.webm'
                    ]);

                    transcripts.syncAdvancedTab(metadataCollection);

                    html5SourcesValue = metadataCollection.findWhere({
                        field_name: 'html5_sources'
                    }).getValue();
                    expect(html5SourcesValue).toEqual([
                        'video.mp4',
                        'video.webm'
                    ]);

                    youtubeValue = metadataCollection.findWhere({
                        field_name: 'youtube_id_1_0'
                    }).getValue();
                    expect(youtubeValue).toEqual('');
                });
            });
        });
    });
});
