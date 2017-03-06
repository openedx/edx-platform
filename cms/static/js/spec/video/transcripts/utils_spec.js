define(
    [
        'jquery', 'underscore',
        'js/views/video/transcripts/utils',
        'underscore.string', 'xmodule'
    ],
function ($, _, Utils, _str) {
'use strict';
describe('Transcripts.Utils', function () {
    var videoId = 'OEoXaMPEzfM',
        ytLinksList = (function (id) {
            var links = [
                'http://www.youtube.com/watch?v=%s&feature=feedrec_grec_index',
                'http://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/%s',
                'http://www.youtube.com/v/%s?fs=1&amp;hl=en_US&amp;rel=0',
                'http://www.youtube.com/watch?v=%s#t=0m10s',
                'http://www.youtube.com/embed/%s?rel=0',
                'http://www.youtube.com/watch?v=%s',
                'http://youtu.be/%s'
            ];

            return $.map(links, function (link) {
                return _str.sprintf(link, id);
            });

        } (videoId)),
        html5FileName = 'file_name',
        html5LinksList =  (function (videoName) {
            var videoTypes = ['mp4', 'webm', 'm4v', 'ogv'],
                links = [
                    'http://somelink.com/%s.%s?param=1&param=2#hash',
                    'http://somelink.com/%s.%s#hash',
                    'http://somelink.com/%s.%s?param=1&param=2',
                    'http://somelink.com/%s.%s',
                    'ftp://somelink.com/%s.%s',
                    'https://somelink.com/%s.%s',
                    'https://somelink.com/sub/sub/%s.%s',
                    'http://cdn.somecdn.net/v/%s.%s',
                    'somelink.com/%s.%s',
                     '%s.%s'
                ],
                data = {};

            $.each(videoTypes, function (index, type) {
                data[type] = $.map(links, function (link) {
                    return _str.sprintf(link, videoName, type);
                });
            });

            return data;

        } (html5FileName)),
        otherLinkId = 'other_link_id',
        otherLinksList =  (function (linkId) {
            var links = [
                    'http://goo.gl/%s?param=1&param=2#hash',
                    'http://goo.gl/%s?param=1&param=2',
                    'http://goo.gl/%s#hash',
                    'http://goo.gl/%s',
                    'http://goo.gl/%s',
                    'ftp://goo.gl/%s',
                    'https://goo.gl/%s',
                     '%s'
                ];

            return $.map(links, function (link) {
                return _str.sprintf(link, linkId);
            });

        } (otherLinkId));

    describe('Method: getField', function (){
        var collection,
            testFieldName = 'test_field';

        beforeEach(function() {
            collection = jasmine.createSpyObj(
                                'Collection',
                                [
                                    'findWhere'
                                ]
                            );
        });

        it('All works okay if all arguments are passed', function () {
            Utils.getField(collection, testFieldName);

            expect(collection.findWhere).toHaveBeenCalledWith({
                field_name: testFieldName
            });
        });

        var wrongArgumentLists = [
            {
                argName: 'collection',
                list: [undefined, testFieldName]
            },
            {
                argName: 'field name',
                list: [collection, undefined]
            },
            {
                argName: 'both',
                list: [undefined, undefined]
            }
        ];

        $.each(wrongArgumentLists, function (index, element) {
            it(element.argName + ' argument(s) is/are absent', function () {
                var result = Utils.getField.apply(this, element.list);

                expect(result).toBeUndefined();
            });
        });
    });

    describe('Method: parseYoutubeLink', function () {
        describe('Supported urls', function () {
            $.each(ytLinksList, function (index, link) {
                it(link, function () {
                    var result = Utils.parseYoutubeLink(link);

                    expect(result).toBe(videoId);
                });
            });
        });

        describe('Wrong arguments ', function () {
            beforeEach(function(){
                spyOn(console, 'log');
            });

            it('no arguments', function () {
                var result = Utils.parseYoutubeLink();

                expect(result).toBeUndefined();
            });

            it('wrong data type', function () {
                var result = Utils.parseYoutubeLink(1);

                expect(result).toBeUndefined();
            });

            var wrongUrls = [
                'http://youtu.be/',
                '/static/example',
                'http://google.com/somevideo.mp4'
            ];

            $.each(wrongUrls, function (index, link) {
                it(link, function () {
                    var result = Utils.parseYoutubeLink(link);

                    expect(result).toBeUndefined();
                });
            });
        });
    });

    describe('Method: parseHTML5Link', function () {
        describe('Supported urls', function () {
            $.each(html5LinksList, function (format, linksList) {
                $.each(linksList, function (index, link) {
                    it(link, function () {
                        var result = Utils.parseHTML5Link(link);

                        expect(result).toEqual({
                            video: html5FileName,
                            type: format
                        });
                    });
                });
            });

            $.each(otherLinksList, function (index, link) {
                it(link, function () {
                    var result = Utils.parseHTML5Link(link);

                    expect(result).toEqual({
                        video: otherLinkId,
                        type: 'other'
                    });
                });
            });
        });

        describe('Wrong arguments ', function () {
            beforeEach(function(){
                spyOn(console, 'log');
            });

            it('no arguments', function () {
                var result = Utils.parseHTML5Link();

                expect(result).toBeUndefined();
            });

            it('wrong data type', function () {
                var result = Utils.parseHTML5Link(1);

                expect(result).toBeUndefined();
            });

            var html5WrongUrls = [
                'http://youtu.be/',
                'http://example.com/.mp4',
                'http://example.com/video_name.',
                'http://example.com/',
                'http://example.com'
            ];

            $.each(html5WrongUrls, function (index, link) {
                it(link, function () {
                    var result = Utils.parseHTML5Link(link);

                    expect(result).toBeUndefined();
                });
            });
        });
    });

    it('Method: getYoutubeLink', function () {
        var videoId = 'video_id',
            result = Utils.getYoutubeLink(videoId),
            expectedResult = 'http://youtu.be/' + videoId;

        expect(result).toBe(expectedResult);
    });

    describe('Method: parseLink', function () {
        var resultDataDict = {
            'html5': {
                 link: html5LinksList.mp4[0],
                 resp: {
                    mode: 'html5',
                    video: html5FileName,
                    type: 'mp4'
                }
            },
            'youtube': {
                link: ytLinksList[0],
                resp: {
                    mode: 'youtube',
                    video: videoId,
                    type: 'youtube'
                }
            },
            'incorrect': {
                link: 'http://example.com',
                resp: {
                    mode: 'incorrect'
                }
            }
        };

        $.each(resultDataDict, function (mode, data) {
            it(mode, function () {
                var result = Utils.parseLink(data.link);

                expect(result).toEqual(data.resp);
            });
        });

        describe('Wrong arguments ', function () {
            it('youtube videoId is wrong', function () {
                var videoId = 'wrong_id',
                    link = 'http://youtu.be/' + videoId,
                    result = Utils.parseLink(link);

                expect(result).toEqual({ mode : 'incorrect' });
            });

            it('no arguments', function () {
                var result = Utils.parseLink();

                expect(result).toBeUndefined();
            });

            it('wrong data type', function () {
                var result = Utils.parseLink(1);

                expect(result).toBeUndefined();
            });
        });
    });
});
});
