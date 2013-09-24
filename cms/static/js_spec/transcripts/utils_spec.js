(function () {
    describe('Transcripts.Utils', function () {
        var utils = Transcripts.Utils,
            videoId = 'OEoXaMPEzfM',
            ytLinksList = [
                'http://www.youtube.com/watch?v=' + videoId + '&feature=feedrec_grec_index',
                'http://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/' + videoId,
                'http://www.youtube.com/v/' + videoId + '?fs=1&amp;hl=en_US&amp;rel=0',
                'http://www.youtube.com/watch?v=' + videoId + '#t=0m10s',
                'http://www.youtube.com/embed/' + videoId + '?rel=0',
                'http://www.youtube.com/watch?v=' + videoId,
                'http://youtu.be/' + videoId,
            ],
            html5FileName = 'file_name',
            html5LinksList = {
                'mp4': [
                    'http://somelink.com/' + html5FileName + '.mp4?param=1&param=2#hash',
                    'http://somelink.com/' + html5FileName + '.mp4#hash',
                    'http://somelink.com/' + html5FileName + '.mp4?param=1&param=2',
                    'http://somelink.com/' + html5FileName + '.mp4',
                    'ftp://somelink.com/' + html5FileName + '.mp4',
                    'https://somelink.com/' + html5FileName + '.mp4',
                    'somelink.com/' + html5FileName + '.mp4',
                     html5FileName + '.mp4',
                ],
                'webm': [
                    'http://somelink.com/' + html5FileName + '.webm?param=1&param=2#hash',
                    'http://somelink.com/' + html5FileName + '.webm#hash',
                    'http://somelink.com/' + html5FileName + '.webm?param=1&param=2',
                    'http://somelink.com/' + html5FileName + '.webm',
                    'ftp://somelink.com/' + html5FileName + '.webm',
                    'https://somelink.com/' + html5FileName + '.webm',
                    'somelink.com/' + html5FileName + '.webm',
                     html5FileName + '.webm',
                ]
            };

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
                utils.getField(collection, testFieldName);

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
            ]

            $.each(wrongArgumentLists, function (index, element) {
                it(element.argName + ' argument(s) is/are absent', function () {
                    var result = utils.getField.apply(this, element.list);

                    expect(result).toBeUndefined();
                });
            });
        });

        describe('Method: parseYoutubeLink', function () {
            describe('Supported urls', function () {
                $.each(ytLinksList, function (index, link) {
                    it(link, function () {
                        var result = utils.parseYoutubeLink(link);

                        expect(result).toBe(videoId);
                    });
                });
            });

            describe('Wrong arguments ', function () {

                beforeEach(function(){
                    spyOn(console, 'log');
                });

                it('no arguments', function () {
                    var result = utils.parseYoutubeLink();

                    expect(result).toBeUndefined();
                });

                it('wrong data type', function () {
                    var result = utils.parseYoutubeLink(1);

                    expect(result).toBeUndefined();
                });

                it('videoId is wrong', function () {
                    var videoId = 'wrong_id',
                        link = 'http://youtu.be/' + videoId,
                        result = utils.parseYoutubeLink(link);

                    expect(result).toBeUndefined();
                });

                var wrongUrls = [
                    'http://youtu.bee/' + videoId,
                    'http://youtu.be/',
                    'example.com',
                    'http://google.com/somevideo.mp4'
                ];

                $.each(wrongUrls, function (index, link) {
                    it(link, function () {
                        var result = utils.parseYoutubeLink(link);

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
                            var result = utils.parseHTML5Link(link);

                            expect(result).toEqual({
                                video: html5FileName,
                                type: format
                            });
                        });
                    });
                });
            });

            describe('Wrong arguments ', function () {

                beforeEach(function(){
                    spyOn(console, 'log');
                });

                it('no arguments', function () {
                    var result = utils.parseHTML5Link();

                    expect(result).toBeUndefined();
                });

                it('wrong data type', function () {
                    var result = utils.parseHTML5Link(1);

                    expect(result).toBeUndefined();
                });

                var html5WrongUrls = [
                    'http://youtu.bee/' + videoId,
                    'http://youtu.be/',
                    'example.com',
                    'http://google.com/somevideo.mp1',
                    'http://google.com/somevideomp4',
                    'http://google.com/somevideo_mp4',
                    'http://google.com/somevideo:mp4',
                    'http://google.com/somevideo',
                    'http://google.com/somevideo.webm_'
                ];

                $.each(html5WrongUrls, function (index, link) {
                    it(link, function () {
                        var result = utils.parseHTML5Link(link);

                        expect(result).toBeUndefined();
                    });
                });
            });
        });

        it('Method: getYoutubeLink', function () {
            var videoId = 'video_id',
                result = utils.getYoutubeLink(videoId),
                expectedResult = 'http://youtu.be/' + videoId;

            expect(result).toBe(expectedResult);
        });

        describe('Method: parseLink', function () {
            var resultDataDict = {
                'html5': {
                     link: html5LinksList['mp4'][0],
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
                    var result = utils.parseLink(data.link);

                    expect(result).toEqual(data.resp);
                });
            });

            describe('Wrong arguments ', function () {

                beforeEach(function(){
                    spyOn(console, 'log');
                });

                it('no arguments', function () {
                    var result = utils.parseLink();

                    expect(console.log).toHaveBeenCalled();
                });

                it('wrong data type', function () {
                    var result = utils.parseLink(1);

                    expect(console.log).toHaveBeenCalled();
                });
            });
        });
    });

}).call(this);
