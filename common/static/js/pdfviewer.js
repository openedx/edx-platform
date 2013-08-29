/* Copyright 2012 Mozilla Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 * Modified (and JQuerified) from PDF-JS sample code (viewer.js) 
 */
/* globals: PDFJS as defined in pdf.js.  Also assumes that jquery is included. */

//
// Disable workers to avoid yet another cross-origin issue (workers need the URL of
// the script to be loaded, and currently do not allow cross-origin scripts)
//
PDFJS.disableWorker = true;

(function($) {
    $.fn.PDFViewer = function(options) {
        var pdfViewer = this;

        var pdfDocument = null;
        var urlToLoad = null;
        if (options.url) {
            urlToLoad = options.url;
        }
        var chapterUrls = null;
        if (options.chapters) {
            chapterUrls = options.chapters;
        }
        var chapterToLoad = 1;
        if (options.chapterNum) {
            // TODO: this should only be specified if there are 
            // chapters, and it should be in-bounds.
            chapterToLoad = options.chapterNum;
        }
        var pageToLoad = 1;
        if (options.pageNum) {
            pageToLoad = options.pageNum;
        }

        var chapterNum = 1;
        var pageNum = 1;

        var viewerElement = document.getElementById('viewer');
        var ANNOT_MIN_SIZE = 10;
        var DEFAULT_SCALE_DELTA = 1.1;
        var UNKNOWN_SCALE = 0;
        var MIN_SCALE = 0.25;
        var MAX_SCALE = 4.0;

        var currentScale = UNKNOWN_SCALE;
        var currentScaleValue = "0";
        var DEFAULT_SCALE_VALUE = "1";

        var setupText = function setupText(textdiv, content, viewport) {

            function getPageNumberFromDest(dest) {
                var destPage = 1;
                if (dest instanceof Array) {
                    var destRef = dest[0]; 
                    if (destRef instanceof Object) {
                        // we would need to look this up in the 
                        // list of all pages that have been loaded,
                        // but we're trying to not have to load all the pages
                        // right now.  
                        // destPage = this.pagesRefMap[destRef.num + ' ' + destRef.gen + ' R'];
                    } else {
                        destPage = (destRef + 1);
                    }
                }
                return destPage;
            }

            function bindLink(link, dest) {
                // get page number from dest:
                destPage = getPageNumberFromDest(dest);
                link.href = '#page=' + destPage;
                link.onclick = function pageViewSetupLinksOnclick() {
                    if (dest && dest instanceof Array )
                        renderPage(destPage);
                    return false;
                };
            }

            function createElementWithStyle(tagName, item, rect) {
                if (!rect) {
                    rect = viewport.convertToViewportRectangle(item.rect);
                    rect = PDFJS.Util.normalizeRect(rect);
                }
                var element = document.createElement(tagName);
                element.style.left = Math.floor(rect[0]) + 'px';
                element.style.top = Math.floor(rect[1]) + 'px';
                element.style.width = Math.ceil(rect[2] - rect[0]) + 'px';
                element.style.height = Math.ceil(rect[3] - rect[1]) + 'px';
                // BW: my additions here, but should use css:
                // TODO: move these to css
                element.style.position = 'absolute';
                element.style.cursor = 'auto';

                return element;
            }

            function createTextAnnotation(item) {
                var container = document.createElement('section');
                container.className = 'annotText';
                var rect = viewport.convertToViewportRectangle(item.rect);
                rect = PDFJS.Util.normalizeRect(rect);
                // sanity check because of OOo-generated PDFs
                if ((rect[3] - rect[1]) < ANNOT_MIN_SIZE) {
                    rect[3] = rect[1] + ANNOT_MIN_SIZE;
                }
                if ((rect[2] - rect[0]) < ANNOT_MIN_SIZE) {
                    rect[2] = rect[0] + (rect[3] - rect[1]);
                    // make it square
                }
                var image = createElementWithStyle('img', item, rect);
                var iconName = item.name;
            }


            content.getAnnotations().then(function(items) {
                for (var i = 0; i < items.length; i++) {
                    var item = items[i];
                    switch (item.type) {
                        case 'Link':
                            var link = createElementWithStyle('a', item);
                            link.href = item.url || '';
                            if (!item.url)
                                bindLink(link, ('dest' in item) ? item.dest : null);
                            textdiv.appendChild(link);
                            break;
                        case 'Text':
                            var textAnnotation = createTextAnnotation(item);
                            if (textAnnotation)
                                textdiv.appendChild(textAnnotation);
                            break;
                    }
                }
            });
        }

        //
        // Get page info from document, resize canvas accordingly, and render page
        //
        renderPage = function(num) {
            // don't try to render a page that cannot be rendered
            if (num < 1 || num > pdfDocument.numPages) {
                return;
            }

            // Update logging:
            Logger.log("book", { "type" : "gotopage", "old" : pageNum, "new" : num });

            parentElement = viewerElement;
            while (parentElement.hasChildNodes())
                parentElement.removeChild(parentElement.lastChild);

            // Using promise to fetch the page
            pdfDocument.getPage(num).then(function(page) {
                var viewport = page.getViewport(currentScale);

                var pageDisplayWidth = viewport.width;
                var pageDisplayHeight = viewport.height;

                var pageDivHolder = document.createElement('div');
                pageDivHolder.className = 'pdfpage';
                pageDivHolder.style.width = pageDisplayWidth + 'px';
                pageDivHolder.style.height = pageDisplayHeight + 'px';
                parentElement.appendChild(pageDivHolder);

                // Prepare canvas using PDF page dimensions
                var canvas = document.createElement('canvas');
                var context = canvas.getContext('2d');
                canvas.width = pageDisplayWidth;
                canvas.height = pageDisplayHeight;
                pageDivHolder.appendChild(canvas);

                // Render PDF page into canvas context
                var renderContext = {
                    canvasContext : context,
                    viewport : viewport
                };
                page.render(renderContext);

                // Prepare and populate text elements layer
                setupText(pageDivHolder, page, viewport);

            });
            pageNum = num;

            // Update page counters
            document.getElementById('numPages').textContent = 'of ' + pdfDocument.numPages;
            $("#pageNumber").max = pdfDocument.numPages;
            $("#pageNumber").val(pageNum);
        }

        // Go to previous page
        prevPage = function prev_page() {
            if (pageNum <= 1)
                return;
            renderPage(pageNum - 1);
            Logger.log("book", { "type" : "prevpage", "new" : pageNum });
        }

        // Go to next page
        nextPage = function next_page() {
            if (pageNum >= pdfDocument.numPages)
                return;
            renderPage(pageNum + 1);
            Logger.log("book", { "type" : "nextpage", "new" : pageNum });
        }

        selectScaleOption = function(value) {
            var options = $('#scaleSelect options');
            var predefinedValueFound = false;
            for (var i = 0; i < options.length; i++) {
                var option = options[i];
                if (option.value != value) {
                    option.selected = false;
                    continue;
                }
                option.selected = true;
                predefinedValueFound = true;
            }
            return predefinedValueFound;
        }

        setScale = function pdfViewSetScale(val, resetAutoSettings, noScroll) {
            if (val == currentScale)
                return;
            currentScale = val;
            var customScaleOption = $('#customScaleOption')[0];
            customScaleOption.selected = false
            var predefinedValueFound = selectScaleOption('' + currentScale);
            if (!predefinedValueFound) {
                customScaleOption.textContent = Math.round(currentScale * 10000) / 100 + '%';
                customScaleOption.selected = true;
            }
            $('#zoom_in').disabled = (currentScale === MAX_SCALE);
            $('#zoom_out').disabled = (currentScale === MIN_SCALE);

            // Just call renderPage once the scale
            // has been changed.  If we were saving information about
            // the rendering of other pages, we would need
            // to reset those as well.
            renderPage(pageNum);
        };

        parseScale = function pdfViewParseScale(value, resetAutoSettings, noScroll) {
            // we shouldn't be choosing the 'custom' value -- it's only for display.  
            // Check, just in case.
            if ('custom' == value)
                return;

            var scale = parseFloat(value);
            if (scale) {
                currentScaleValue = value;
                setScale(scale, true, noScroll);
                return;
            }
        };

        zoomIn = function pdfViewZoomIn() {
            var newScale = (currentScale * DEFAULT_SCALE_DELTA).toFixed(2);
            newScale = Math.min(MAX_SCALE, newScale);
            parseScale(newScale, true);
        };

        zoomOut = function pdfViewZoomOut() {
            var newScale = (currentScale / DEFAULT_SCALE_DELTA).toFixed(2);
            newScale = Math.max(MIN_SCALE, newScale);
            parseScale(newScale, true);
        };

        //
        // Asynchronously download PDF as an ArrayBuffer
        //
        loadUrl = function pdfViewLoadUrl(url, page) {
            PDFJS.getDocument(url).then(
                function getDocument(_pdfDocument) {
                    pdfDocument = _pdfDocument;
                    pageNum = page;
                    // if the scale has not been set before, set it now.
                    // Otherwise, don't change the current scale,
                    // but make sure it gets refreshed.
                    if (currentScale == UNKNOWN_SCALE) {
                        parseScale(DEFAULT_SCALE_VALUE);
                    } else {
                        var preservedScale = currentScale;
                        currentScale = UNKNOWN_SCALE;
                        parseScale(preservedScale);
                    }
                }, 
                function getDocumentError(message, exception) {
                    // placeholder: don't expect errors :)
                }, 
                function getDocumentProgress(progressData) {
                    // placeholder: not yet ready to display loading progress
                });
            }; 

        loadChapterUrl = function pdfViewLoadChapterUrl(chapterNum, pageVal) {
            if (chapterNum < 1 || chapterNum > chapterUrls.length) {
                return;
            }
            var chapterUrl = chapterUrls[chapterNum-1];
            loadUrl(chapterUrl, pageVal);
        }

        $("#previous").click(function(event) {
            prevPage();
        });

        $("#next").click(function(event) {
            nextPage();
        });

        $('#zoom_in').click(function(event) {
            zoomIn();
        });
        $('#zoom_out').click(function(event) {
            zoomOut();
        });

        $('#scaleSelect').change(function(event) {
            parseScale(this.value);
        });


        $('#pageNumber').change(function(event) {
            var newPageVal = parseInt(this.value);
            if (newPageVal) {
                renderPage(newPageVal);
            }
        });

        // define navigation links for chapters:  
        if (chapterUrls != null) {
            var loadChapterUrlHelper = function(i) {
                return function(event) {
                    // when opening a new chapter, always open the first page:
                    loadChapterUrl(i, 1);
                };
            };
            for (var index = 1; index <= chapterUrls.length; index += 1) {
                $("#pdfchapter-" + index).click(loadChapterUrlHelper(index));
            }   
        }

        // finally, load the appropriate url/page
        if (urlToLoad != null) {
            loadUrl(urlToLoad, pageToLoad);
        } else {
            loadChapterUrl(chapterToLoad, pageToLoad);
        }       
            
        return pdfViewer;
    }
})(jQuery);
