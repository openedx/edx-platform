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
            models = [DisplayNameEntry, VideoListEntry],
            testData = {
                'display_name': DisplayNameEntry,
                'video_url': VideoListEntry
            },
            metadataDict = {
                object: testData,
                string: JSON.stringify(testData)
            },
            transcripts, container;

        var waitsForDisplayName = function(collection) {
            return jasmine.waitUntil(function() {
                var displayNameValue = collection[0].getValue();
                return displayNameValue !== '' && displayNameValue !== 'video_id';
            });
        };

        beforeEach(function() {
            var tpl = sandbox({
                'class': 'wrapper-comp-settings basic_metadata_edit',
                'data-metadata': JSON.stringify(metadataDict['object'])
            });

            appendSetFixtures(tpl);
            container = $('.basic_metadata_edit');

            spyOn(Utils, 'command');
        });

        afterEach(function() {
            Utils.Storage.remove('sub');
        });

        describe('Test initialization', function() {
            beforeEach(function() {
                spyOn(MetadataView, 'Editor');

                transcripts = new Editor({
                    el: container
                });
            });

            $.each(metadataDict, function(index, val) {
                it('toModels with argument as ' + index, function() {
                    expect(transcripts.toModels(val)).toEqual(models);
                });
            });

            it('MetadataView.Editor is initialized', function() {
                expect(MetadataView.Editor).toHaveBeenCalledWith({
                    el: container,
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
                metadataCollection,
                metadataView;


            beforeEach(function() {
                spyOn(MetadataView, 'Editor');

                transcripts = new Editor({
                    el: container
                });

                metadataCollection = new MetadataCollection(
                    [
                        nameEntry,
                        subEntry,
                        html5SourcesEntry,
                        youtubeEntry
                    ]
                );

                metadataView = jasmine.createSpyObj(
                    'MetadataView.Editor',
                    [
                        'getModifiedMetadataValues'
                    ]
                );
            });

            describe('Test Advanced to Basic synchronization', function() {
                it('Correct data', function(done) {
                    transcripts.syncBasicTab(metadataCollection, metadataView);
                    var collection = transcripts.collection.models;

                    waitsForDisplayName(collection)
                        .then(function() {
                            var displayNameValue = collection[0].getValue(),
                                videoUrlValue = collection[1].getValue();

                            expect(displayNameValue).toEqual('default');
                            expect(videoUrlValue).toEqual([
                                'http://youtu.be/OEoXaMPEzfM',
                                'default.mp4',
                                'default.webm'
                            ]);
                        })
                        .always(done);
                });

                it('If metadataCollection is not defined', function() {
                    transcripts.syncBasicTab(null);

                    var collection = transcripts.collection.models,
                        videoUrlValue = collection[1].getValue();

                    expect(videoUrlValue).toEqual([
                        'http://youtu.be/12345678901',
                        'video.mp4',
                        'video.webm'
                    ]);
                });

                it('Youtube Id has length not eqaul 11', function() {
                    var model = metadataCollection.findWhere({
                        field_name: 'youtube_id_1_0'
                    });

                    model.setValue([
                        '12345678',
                        'default.mp4',
                        'default.webm'
                    ]);

                    transcripts.syncBasicTab(metadataCollection, metadataView);

                    var collection = transcripts.collection.models,
                        videoUrlValue = collection[1].getValue();

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
                            var displayNameValue = collection[0].getValue();
                            var subValue = collection[1].getValue();
                            var html5SourcesValue = collection[2].getValue();
                            var youtubeValue = collection[3].getValue();

                            expect(displayNameValue).toEqual('display value');
                            expect(subValue).toEqual('default');
                            expect(html5SourcesValue).toEqual([
                                'video.mp4',
                                'video.webm'
                            ]);
                            expect(youtubeValue).toEqual('12345678901');
                        })
                        .always(done);
                });

                it('metadataCollection is not defined', function() {
                    transcripts.syncAdvancedTab(null);

                    var collection = metadataCollection.models,
                        displayNameValue = collection[0].getValue(),
                        subValue = collection[1].getValue(),
                        html5SourcesValue = collection[2].getValue(),
                        youtubeValue = collection[3].getValue();

                    expect(displayNameValue).toEqual('default');
                    expect(subValue).toEqual('default');
                    expect(html5SourcesValue).toEqual([
                        'default.mp4',
                        'default.webm'
                    ]);
                    expect(youtubeValue).toEqual('OEoXaMPEzfM');
                });

                it('Youtube Id is not adjusted', function() {
                    var model = transcripts.collection.models[1];

                    model.setValue([
                        'video.mp4',
                        'video.webm'
                    ]);

                    transcripts.syncAdvancedTab(metadataCollection);

                    var collection = metadataCollection.models,
                        html5SourcesValue = collection[2].getValue(),
                        youtubeValue = collection[3].getValue();

                    expect(html5SourcesValue).toEqual([
                        'video.mp4',
                        'video.webm'
                    ]);
                    expect(youtubeValue).toEqual('');
                });

                it('Timed Transcript field is updated', function() {
                    Utils.Storage.set('sub', 'test_value');

                    transcripts.syncAdvancedTab(metadataCollection);

                    var collection = metadataCollection.models,
                        subValue = collection[1].getValue();

                    expect(subValue).toEqual('test_value');
                });

                it('Timed Transcript field is updated just once', function() {
                    Utils.Storage.set('sub', 'test_value');

                    var collection = metadataCollection.models,
                        subModel = collection[1];

                    spyOn(subModel, 'setValue');

                    transcripts.syncAdvancedTab(metadataCollection);
                    transcripts.syncAdvancedTab(metadataCollection);
                    transcripts.syncAdvancedTab(metadataCollection);
                    expect(subModel.setValue.calls.count()).toEqual(1);
                });
            });
        });
    });
});
