/**
* @file The main module definition for Word Cloud XModule.
*
*  Defines a constructor function which operates on a DOM element. Either
*  show the user text inputs so he can enter words, or render his selected
*  words along with the word cloud representing the top words.
*
*  @module WordCloudMain
*
*  @exports WordCloudMain
*
*  @external $
*/

import * as HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import d3 from 'd3.min';
import { cloud as d3Cloud } from 'd3.layout.cloud';
import gettext from 'gettext';

function generateUniqueId(wordCloudId, counter) {
    return `_wc_${wordCloudId}_${counter}`;
}

/**
* @function WordCloudMain
*
* This function will process all the attributes from the DOM element passed, taking all of
* the configuration attributes. It will either then attach a callback handler for the click
* event on the button in the case when the user needs to enter words, or it will call the
* appropriate mehtod to generate and render a word cloud from user's enetered words along with
* all of the other words.
*
* @constructor
*
* @param {jQuery} el DOM element where the word cloud will be processed and created.
*/
export default class WordCloudMain {
    constructor(el) {
        this.wordCloudEl = $(el).find('.word_cloud');

        // Get the URL to which we will post the users words.
        this.ajax_url = this.wordCloudEl.data('ajax-url');

        // Dimensions of the box where the word cloud will be drawn.
        this.width = 635;
        this.height = 635;

        // Hide WordCloud container before Ajax request done
        this.wordCloudEl.hide();

        // Retriveing response from the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            `${this.ajax_url}/get_state`,
            null,
            (response) => {
                if (response.status !== 'success') {
                    return;
                }

                this.configJson = response;
            },
        )
            .done(() => {
                // Show WordCloud container after Ajax request done
                this.wordCloudEl.show();

                if (this.configJson && this.configJson.submitted) {
                    this.showWordCloud(this.configJson);
                }
            });

        $(el).find('.save').on('click', () => {
            this.submitAnswer();
        });
    }

    /**
  * @function submitAnswer
  *
  * Callback to be executed when the user eneter his words. It will send user entries to the
  * server, and upon receiving correct response, will call the function to generate the
  * word cloud.
  */
    submitAnswer() {
        const data = { student_words: [] };

        // Populate the data to be sent to the server with user's words.
        this.wordCloudEl.find('input.input-cloud').each((index, value) => {
            data.student_words.push($(value).val());
        });

        // Send the data to the server as an AJAX request. Attach a callback that will
        // be fired on server's response.
        $.postWithPrefix(
            `${this.ajax_url}/submit`, $.param(data),
            (response) => {
                if (response.status !== 'success') {
                    return;
                }

                this.showWordCloud(response);
            },
        );
    }

    /**
  * @function showWordCloud
  *
  * @param {object} response The response from the server that contains the user's entered words
  * along with all of the top words.
  *
  * This function will set up everything for d3 and launch the draw method. Among other things,
  * iw will determine maximum word size.
  */
    showWordCloud(response) {
        const words = response.top_words;
        let maxSize = 0;
        let minSize = 10000;
        let scaleFactor = 1;
        let maxFontSize = 200;
        const minFontSize = 16;

        this.wordCloudEl.find('.input_cloud_section').hide();

        // Find the word with the maximum percentage. I.e. the most popular word.
        $.each(words, (index, word) => {
            if (word.size > maxSize) {
                maxSize = word.size;
            }
            if (word.size < minSize) {
                minSize = word.size;
            }
        });

        // Find the longest word, and calculate the scale appropriately. This is
        // required so that even long words fit into the drawing area.
        //
        // This is a fix for: if the word is very long and/or big, it is discarded by
        // for unknown reason.
        $.each(words, (index, word) => {
            let tempScaleFactor = 1.0;
            const size = ((word.size / maxSize) * maxFontSize);

            if (size * 0.7 * word.text.length > this.width) {
                tempScaleFactor = ((this.width / word.text.length) / 0.7) / size;
            }

            if (scaleFactor > tempScaleFactor) {
                scaleFactor = tempScaleFactor;
            }
        });

        // Update the maximum font size based on the longest word.
        maxFontSize *= scaleFactor;

        // Generate the word cloud.
        d3Cloud().size([this.width, this.height])
            .words(words)
            .rotate(() => Math.floor((Math.random() * 2)) * 90)
            .font('Impact')
            .fontSize((d) => {
                let size = (d.size / maxSize) * maxFontSize;

                size = size >= minFontSize ? size : minFontSize;

                return size;
            })
        // Draw the word cloud.
            .on('end', (wds, bounds) => this.drawWordCloud(response, wds, bounds))
            .start();
    }

    /**
  * @function drawWordCloud
  *
  * This function will be called when d3 has finished initing the state for our word cloud,
  * and it is ready to hand off the process to the drawing routine. Basically set up everything
  * necessary for the actual drwing of the words.
  *
  * @param {object} response The response from the server that contains the user's entered words
  * along with all of the top words.
  *
  * @param {array} words An array of objects. Each object must have two properties. One property
  * is 'text' (the actual word), and the other property is 'size' which represents the number that the
  * word was enetered by the students.
  *
  * @param {array} bounds An array of two objects. First object is the top-left coordinates of the bounding
  * box where all of the words fir, second object is the bottom-right coordinates of the bounding box. Each
  * coordinate object contains two properties: 'x', and 'y'.
  */
    drawWordCloud(response, words, bounds) {
    // Color words in different colors.
        const fill = d3.scale.category20();

        // Will be populated by words the user enetered.
        const studentWordsKeys = [];

        // By default we do not scale.
        let scale = 1;

        // Caсhing of DOM element
        const cloudSectionEl = this.wordCloudEl.find('.result_cloud_section');

        // Iterator for word cloud count for uniqueness
        let wcCount = 0;

        // If bounding rectangle is given, scale based on the bounding box of all the words.
        if (bounds) {
            scale = 0.5 * Math.min(
                this.width / Math.abs(bounds[1].x - (this.width / 2)),
                this.width / Math.abs(bounds[0].x - (this.width / 2)),
                this.height / Math.abs(bounds[1].y - (this.height / 2)),
                this.height / Math.abs(bounds[0].y - (this.height / 2)),
            );
        }

        $.each(response.student_words, (word, stat) => {
            const percent = (response.display_student_percents) ? ` ${Math.round(100 * (stat / response.total_count))}%` : '';

            studentWordsKeys.push(HtmlUtils.interpolateHtml(
                '{listStart}{startTag}{word}{endTag}{percent}{listEnd}',
                {
                    listStart: HtmlUtils.HTML('<li>'),
                    startTag: HtmlUtils.HTML('<strong>'),
                    word,
                    endTag: HtmlUtils.HTML('</strong>'),
                    percent,
                    listEnd: HtmlUtils.HTML('</li>'),
                },
            ).toString());
        });

        // Comma separated string of user enetered words.
        const studentWordsStr = studentWordsKeys.join('');

        cloudSectionEl
            .addClass('active');

        HtmlUtils.setHtml(
            cloudSectionEl.find('.your_words'),
            HtmlUtils.HTML(studentWordsStr),
        );

        HtmlUtils.setHtml(
            cloudSectionEl.find('.your_words').end().find('.total_num_words'),
            HtmlUtils.interpolateHtml(
                gettext('{start_strong}{total}{end_strong} words submitted in total.'),
                {
                    start_strong: HtmlUtils.HTML('<strong>'),
                    end_strong: HtmlUtils.HTML('</strong>'),
                    total: response.total_count,
                },
            ),
        );

        $(`${cloudSectionEl.attr('id')} .word_cloud`).empty();

        // Actual drawing of word cloud.
        const groupEl = d3.select(`#${cloudSectionEl.attr('id')} .word_cloud`).append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .append('g')
            .attr('transform', `translate(${0.5 * this.width},${0.5 * this.height})`)
            .selectAll('text')
            .data(words)
            .enter()
            .append('g')
            .attr('data-id', () => {
                wcCount += 1;
                return wcCount;
            })
            .attr('aria-describedby', () => HtmlUtils.interpolateHtml(
                gettext('text_word_{uniqueId} title_word_{uniqueId}'),
                {
                    uniqueId: generateUniqueId(cloudSectionEl.attr('id'), $(this).data('id')),
                },
            ));

        groupEl
            .append('title')
            .attr('id', () => HtmlUtils.interpolateHtml(
                gettext('title_word_{uniqueId}'),
                {
                    uniqueId: generateUniqueId(cloudSectionEl.attr('id'), $(this).parent().data('id')),
                },
            ))
            .text((d) => {
                let res = '';

                $.each(response.top_words, (index, value) => {
                    if (value.text === d.text) {
                        res = `${value.percent}%`;
                    }
                });

                return res;
            });

        groupEl
            .append('text')
            .attr('id', () => HtmlUtils.interpolateHtml(
                gettext('text_word_{uniqueId}'),
                {
                    uniqueId: generateUniqueId(cloudSectionEl.attr('id'), $(this).parent().data('id')),
                },
            ))
            .style('font-size', d => `${d.size}px`)
            .style('font-family', 'Impact')
            .style('fill', (d, i) => fill(i))
            .attr('text-anchor', 'middle')
            .attr('transform', d => `translate(${d.x}, ${d.y})rotate(${d.rotate})scale(${scale})`)
            .text(d => d.text);
    }
}
