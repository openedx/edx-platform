define(['underscore', 'URI', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'], function(_, URI, AjaxHelpers) {
    'use strict';
    var B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=',
        LONG_TEXT, PRUNED_TEXT, TRUNCATED_TEXT, SHORT_TEXT,
        base64Encode, makeToken, getChapter, getSection, getUnit, getDefaultNotes,
        verifyUrl, verifyRequestParams, createNotesData, respondToRequest,
        verifyPaginationInfo, verifyPageData;

    LONG_TEXT = [
        'Adipisicing elit, sed do eiusmod tempor incididunt ',
        'ut labore et dolore magna aliqua. Ut enim ad minim ',
        'veniam, quis nostrud exercitation ullamco laboris ',
        'nisi ut aliquip ex ea commodo consequat. Duis aute ',
        'irure dolor in reprehenderit in voluptate velit esse ',
        'cillum dolore eu fugiat nulla pariatur. Excepteur ',
        'sint occaecat cupidatat non proident, sunt in culpa ',
        'qui officia deserunt mollit anim id est laborum.'
    ].join('');
    PRUNED_TEXT = [
        'Adipisicing elit, sed do eiusmod tempor incididunt ',
        'ut labore et dolore magna aliqua. Ut enim ad minim ',
        'veniam, quis nostrud exercitation ullamco laboris ',
        'nisi ut aliquip ex ea commodo consequat. Duis aute ',
        'irure dolor in reprehenderit in voluptate velit esse ',
        'cillum dolore eu fugiat nulla pariatur...'
    ].join('');
    TRUNCATED_TEXT = [
        'Adipisicing elit, sed do eiusmod tempor incididunt ',
        'ut labore et dolore magna aliqua. Ut enim ad minim ',
        'veniam, quis nostrud exercitation ullamco laboris ',
        'nisi ut aliquip ex ea commodo consequat. Duis aute ',
        'irure dolor in reprehenderit in voluptate velit esse ',
        'cillum dolore eu fugiat nulla pariatur. Exce'
    ].join('');
    SHORT_TEXT = 'Adipisicing elit, sed do eiusmod tempor incididunt';

    base64Encode = function(data) {
        var ac, bits, enc, h1, h2, h3, h4, i, o1, o2, o3, r, tmp_arr;
        if (btoa) {
            // Gecko and Webkit provide native code for this
            return btoa(data);
        } else {
            // Adapted from MIT/BSD licensed code at http://phpjs.org/functions/base64_encode
            // version 1109.2015
            i = 0;
            ac = 0;
            enc = '';
            tmp_arr = [];
            if (!data) {
                return data;
            }
            data += '';
            while (i < data.length) {
                o1 = data.charCodeAt(i++);
                o2 = data.charCodeAt(i++);
                o3 = data.charCodeAt(i++);
                bits = o1 << 16 | o2 << 8 | o3;
                h1 = bits >> 18 & 0x3f;
                h2 = bits >> 12 & 0x3f;
                h3 = bits >> 6 & 0x3f;
                h4 = bits & 0x3f;
                tmp_arr[ac++] = B64.charAt(h1) + B64.charAt(h2) + B64.charAt(h3) + B64.charAt(h4);
            }
            enc = tmp_arr.join('');
            r = data.length % 3;
            return (r ? enc.slice(0, r - 3) : enc) + '==='.slice(r || 3);
        }
    };

    makeToken = function() {
        var now = (new Date()).getTime() / 1000,
            rawToken = {
                sub: 'sub',
                exp: now + 100,
                iat: now
            };

        return 'header.' + base64Encode(JSON.stringify(rawToken)) + '.signature';
    };
    getChapter = function(name, location, index, children) {
        return {
            display_name: name,
            location: 'i4x://chapter/' + location,
            index: index,
            children: _.map(children, function(i) {
                return 'i4x://section/' + i;
            })
        };
    };

    getSection = function(name, location, children) {
        return {
            display_name: name,
            location: 'i4x://section/' + location,
            children: _.map(children, function(i) {
                return 'i4x://unit/' + i;
            })
        };
    };

    getUnit = function(name, location) {
        return {
            display_name: name,
            location: 'i4x://unit/' + location,
            url: 'http://example.com'
        };
    };

    getDefaultNotes = function() {
        // Note that the server returns notes in reverse chronological order (newest first).
        return {
            count: 5,
            current_page: 1,
            num_pages: 1,
            start: 0,
            next: null,
            previous: null,
            results: [
                {
                    chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                    section: getSection('Third Section', 0, ['w_n', 1, 0]),
                    unit: getUnit('Fourth Unit', 0),
                    created: 'December 11, 2014 at 11:12AM',
                    updated: 'December 11, 2014 at 11:12AM',
                    text: 'Third added model',
                    quote: 'Note 4',
                    tags: ['Pumpkin', 'pumpkin', 'yummy']
                },
                {
                    chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                    section: getSection('Third Section', 0, ['w_n', 1, 0]),
                    unit: getUnit('Fourth Unit', 0),
                    created: 'December 11, 2014 at 11:11AM',
                    updated: 'December 11, 2014 at 11:11AM',
                    text: 'Third added model',
                    quote: 'Note 5'
                },
                {
                    chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                    section: getSection('Third Section', 0, ['w_n', 1, 0]),
                    unit: getUnit('Third Unit', 1),
                    created: 'December 11, 2014 at 11:11AM',
                    updated: 'December 11, 2014 at 11:11AM',
                    text: 'Second added model',
                    quote: 'Note 3',
                    tags: ['yummy']
                },
                {
                    chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                    section: getSection('Second Section', 1, [2]),
                    unit: getUnit('Second Unit', 2),
                    created: 'December 11, 2014 at 11:10AM',
                    updated: 'December 11, 2014 at 11:10AM',
                    text: 'First added model',
                    quote: 'Note 2',
                    tags: ['PUMPKIN', 'pie']
                },
                {
                    chapter: getChapter('First Chapter', 1, 0, [2]),
                    section: getSection('First Section', 2, [3]),
                    unit: getUnit('First Unit', 3),
                    created: 'December 11, 2014 at 11:10AM',
                    updated: 'December 11, 2014 at 11:10AM',
                    text: 'First added model',
                    quote: 'Note 1',
                    tags: ['pie', 'pumpkin']
                }
            ]
        };
    };

    verifyUrl = function(requestUrl, expectedUrl, expectedParams) {
        expect(requestUrl.slice(0, expectedUrl.length) === expectedUrl).toBeTruthy();
        verifyRequestParams(requestUrl, expectedParams);
    };

    verifyRequestParams = function(requestUrl, expectedParams) {
        var urlParams = (new URI(requestUrl)).query(true);
        _.each(expectedParams, function(value, key) {
            expect(urlParams[key]).toBe(value);
        });
    };

    createNotesData = function(options) {
        var data = {
            count: options.count || 0,
            num_pages: options.num_pages || 1,
            current_page: options.current_page || 1,
            start: options.start || 0,
            results: []
        };

        for (var i = 0; i < options.numNotesToCreate; i++) {
            var notesInfo = {
                chapter: getChapter('First Chapter__' + i, 1, 0, [2]),
                section: getSection('First Section__' + i, 2, [3]),
                unit: getUnit('First Unit__' + i, 3),
                created: new Date().toISOString(),
                updated: new Date().toISOString(),
                text: 'text__' + i,
                quote: 'Note__' + i,
                tags: ['tag__' + i, 'tag__' + i + 1]
            };

            data.results.push(notesInfo);
        }

        return data;
    };

    respondToRequest = function(requests, responseJson, respondToEvent) {
        // Respond to the analytics event
        if (respondToEvent) {
            AjaxHelpers.respondWithNoContent(requests);
        }
        // Now process the actual request
        AjaxHelpers.respondWithJson(requests, responseJson);
    };

    verifyPaginationInfo = function(view, headerMessage, footerHidden, currentPage, totalPages) {
        expect(view.$('.search-count.listing-count').text().trim()).toBe(headerMessage);
        expect(view.$('.pagination.bottom').parent().hasClass('hidden')).toBe(footerHidden);
        if (!footerHidden) {
            expect(parseInt(view.$('.pagination span.current-page').text().trim())).toBe(currentPage);
            expect(parseInt(view.$('.pagination span.total-pages').text().trim())).toBe(totalPages);
        }
    };

    verifyPageData = function(view, tabsCollection, tabInfo, tabId, notes) {
        expect(tabsCollection).toHaveLength(1);
        expect(tabsCollection.at(0).toJSON()).toEqual(tabInfo);
        expect(view.$(tabId)).toExist();
        expect(view.$('.note')).toHaveLength(notes.results.length);
        _.each(view.$('.note'), function(element, index) {
            expect($('.note-comments', element)).toContainText(notes.results[index].text);
            expect($('.note-excerpt', element)).toContainText(notes.results[index].quote);
        });
    };

    return {
        LONG_TEXT: LONG_TEXT,
        PRUNED_TEXT: PRUNED_TEXT,
        TRUNCATED_TEXT: TRUNCATED_TEXT,
        SHORT_TEXT: SHORT_TEXT,
        base64Encode: base64Encode,
        makeToken: makeToken,
        getChapter: getChapter,
        getSection: getSection,
        getUnit: getUnit,
        getDefaultNotes: getDefaultNotes,
        verifyUrl: verifyUrl,
        verifyRequestParams: verifyRequestParams,
        createNotesData: createNotesData,
        respondToRequest: respondToRequest,
        verifyPaginationInfo: verifyPaginationInfo,
        verifyPageData: verifyPageData
    };
});
