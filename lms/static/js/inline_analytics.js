window.InlineAnalytics = (function() {

    'use strict';

    function processResponse(response,
        partsToGet,
        questionTypesByPart,
        correctResponses) {

        var dataByPart = response.data_by_part;
        var countByPart = response.count_by_part;
        var messageByPart = response.message_by_part;
        var lastUpdateDate = response.last_update_date;
        var totalAttemptCount;
        var totalCorrectCount;
        var totalIncorrectCount;

        var partId;
        var index;

        // Render the appropriate analytics graphics for each part_id
        var arrayLength = partsToGet.length;
        for (index = 0; index < arrayLength; index++) {
            partId = partsToGet[index];
            
            if (messageByPart[partId]) {
            	// An error was encountered processing the API data so set the appropriate
            	// error message and continue.
            	setErrorMessageOnPart(partId, messageByPart[partId]);
            	continue;
            }

            if (countByPart[partId]) {
                totalAttemptCount = countByPart[partId]['totalAttemptCount'];
                totalCorrectCount = countByPart[partId]['totalCorrectCount'];
                totalIncorrectCount = countByPart[partId]['totalIncorrectCount'];
            } else {
                totalAttemptCount = 0;
                totalCorrectCount = 0;
                totalIncorrectCount = 0;
            }

            if (questionTypesByPart[partId] === 'radio') {
                renderRadioAnalytics(dataByPart[partId],
                    partId,
                    totalAttemptCount,
                    totalCorrectCount,
                    totalIncorrectCount,
                    correctResponses[partId],
                    lastUpdateDate);
            } else if (questionTypesByPart[partId] === 'checkbox') {
                renderCheckboxAnalytics(dataByPart[partId],
                    partId,
                    totalAttemptCount,
                    totalCorrectCount,
                    totalIncorrectCount,
                    correctResponses[partId],
                    lastUpdateDate);
            } else {
                // Just set the text on the div
                setCountAndDate(partId,
                    totalAttemptCount,
                    lastUpdateDate);

                setAggregateCounts(partId,
                    totalAttemptCount,
                    totalCorrectCount,
                    totalIncorrectCount);
            }
        }
    }


    function renderRadioAnalytics(result,
        partId,
        totalAttemptCount,
        totalCorrectCount,
        totalIncorrectCount,
        correctResponse,
        lastUpdateDate) {

        var valueId;
        var currentIndex;
        var valueIndex;
        var lastIndex;
        var correct;
        var count;
        var percent;
        var answerClass;
        var index;
        var tr;
        var trs = [];
        var lastRow = $('#' + partId + '_table tr:last');

        // Build the array of choice texts
        var choiceText = getChoiceTexts(partId);

        if (result) {
            // Loop through results and construct row array
            // Rows returned from the analytics API are in "option" order so we use this
            // to determine if any rows are "missing" from the data.
            var arrayLength = result.length;
            for (index = 0; index < arrayLength; index++) {

                // valueId: option for this row in the api result
                valueId = result[index]['value_id'];
                // currentIndex: number of rows already added to graphic
                currentIndex = trs.length;
                // valueIndex: index of the option for this row in the api result
                valueIndex = valueId.replace('choice_', '');

                // If the current row we are looking to add is less than the row indicated
                // by the option for this index then add rows for those that are missing
                if (currentIndex < valueIndex) {
                    insertMissingRows(partId,
                        currentIndex,
                        valueIndex,
                        correctResponse,
                        choiceText,
                        trs);
                }

                correct = result[index]['correct'];
                count = result[index]['count'];
                percent = Math.round(count * 1000 / (totalAttemptCount * 10));

                if (correct) {
                    answerClass = 'inline-analytics-correct';
                } else {
                    answerClass = 'inline-analytics-incorrect';
                }
                tr = $('<tr><td class="answer_box" title="' + choiceText[valueIndex] + '">' +
                    (parseInt(valueIndex, 10) + 1) + '</td><td class="answer_box ' +
                    answerClass + '"><span class="dot"></span></td><td class="answer_box">' +
                    count + '</td><td class="answer_box">' + percent + '%</td></tr>');
                trs.push(tr[0]);
            }

            // Generate rows for missing answers at the end of results
            lastIndex = parseInt(result[result.length - 1]['value_id'].replace('choice_', ''), 10);
            if (lastIndex < choiceText.length - 1) {
                insertMissingRows(partId,
                    lastIndex + 1,
                    choiceText.length,
                    correctResponse,
                    choiceText,
                    trs);
            }

        } else {
            // There were no results
            trs = insertMissingRows(partId,
                0,
                choiceText.length,
                correctResponse,
                choiceText,
                trs);
        }

        // Append the row array to the table
        lastRow.after(trs);

        // Set student count and last_update_date
        setCountAndDate(partId,
            totalAttemptCount,
            lastUpdateDate);
    }


    function insertMissingRows(partId,
        currentIndex,
        finalIndex,
        correctResponse,
        choiceText,
        trs) {

        var answerClass;
        var tr;
        correctResponse = correctResponse.substring(2, correctResponse.length - 2);

        // Insert rows between currentIndex and finalIndex
        while (currentIndex < finalIndex) {
            if ('choice_' + currentIndex === correctResponse) {
                answerClass = 'inline-analytics-correct';
            } else {
                answerClass = 'inline-analytics-incorrect';
            }
            tr = $('<tr><td class="answer_box" title="' + choiceText[currentIndex] + '">' + (currentIndex + 1) +
                '</td><td class="answer_box ' + answerClass +
                '"><span class="dot"></span> \
                </td><td class="answer_box">0</td><td class="answer_box">0%</td></tr>');
            trs.push(tr[0]);
            currentIndex += 1;
        }
        return trs;
    }


    function renderCheckboxAnalytics(result,
        partId,
        totalAttemptCount,
        totalCorrectCount,
        totalIncorrectCount,
        correctResponse,
        lastUpdateDate) {

        var count;
        var percent;
        var answerClass;
        var actualResponse;
        var imaginedResponse;
        var checkboxChecked;
        var countRow;
        var index;
        var maxColumns = 10;
        var choiceCounter = 1;
        var tr;
        var choiceTrs = [];
        var headerTrs = [];
        var dataTrs = [];

        // Construct the array of choice texts
        var choiceText = getChoiceTexts(partId);

        // Add "Last Attempt" to the choice number column
        $('#' + partId + '_table .checkbox_header_row').after('<tr><td id="last_attempt" class="answer_box checkbox_last_attempt">Last Attempt</td></tr>');

        // Contruct the choice number column array
        while (choiceCounter <= choiceText.length) {
            tr = $('<tr><td id="column0:row' + choiceCounter + '" class="answer_box" title="' +
                choiceText[choiceCounter - 1] + '">' + choiceCounter + '</td></tr>');
            choiceTrs.push(tr[0]);
            choiceCounter += 1;
        }

        // Append the choice number column array to the header row
        var headerRow = $('#' + partId + '_table .checkbox_header_row');
        headerRow.after(choiceTrs);

        // Loop through results constructing header row and data row arrays
        if (result) {
            // Sort the results in decending response count order
            result.sort(orderByCount);

            var arrayLength = result.length;
            for (index = 0; index < arrayLength; index++) {
                // Append columns to the header row array
                tr = $('<th class="header"></th>');
                headerTrs.push(tr[0]);

                // Append message and break if number of distinct choices >= max_columns
                if (index >= maxColumns) {
                    var notDisplayed = result.length - maxColumns;
                    tr = $('<th class="not_displayed"> ' + notDisplayed + ' columns not displayed.</th>');
                    headerTrs.push(tr[0]);
                    break;
                }

                actualResponse = result[index]['value_id'];
                choiceCounter = 1;

                // Construct the data row array from student responses
                while (choiceCounter <= choiceText.length) {
                    imaginedResponse = 'choice_' + (choiceCounter - 1);

                    // Can't rely in contains method in all browsers so use indexOf
                    if ((correctResponse.indexOf(imaginedResponse) === -1) &&
                        (actualResponse.indexOf(imaginedResponse) === -1) ||
                        (correctResponse.indexOf("'" + imaginedResponse + "'") > -1 &&
                            actualResponse.indexOf(imaginedResponse) > -1)) {

                        answerClass = 'inline-analytics-correct';
                    } else {
                        answerClass = 'inline-analytics-incorrect';
                    }
                    if (actualResponse.indexOf(imaginedResponse) !== -1) {
                        checkboxChecked = '<span class="dot"></span>';
                    } else {
                        checkboxChecked = '';
                    }
                    tr = $('<td id="column' + index + ':row' + choiceCounter + '" class="answer_box ' +
                        answerClass + '">' + checkboxChecked + '</td>');
                    dataTrs.push([choiceCounter, tr[0]]);

                    choiceCounter += 1;
                }

                // Construct the Last Attempt row
                count = result[index]['count'];
                percent = Math.round(count * 1000 / (totalAttemptCount * 10));
                countRow += '<td class="answer_box">' + count + '<br/>' + percent + '%</td>'
            }

            // Append the header row array to the header row
            $('#' + partId + '_table tr:eq(0)').append(headerTrs);

            // Construct row array from the data array and append to the appropriate row in the table
            choiceCounter = 1;
            var rowArray = [];
            while (choiceCounter <= choiceText.length) {
                for (index = 0; index < dataTrs.length; index++) {
                    if (dataTrs[index][0] === choiceCounter) {
                        rowArray.push(dataTrs[index][1]);
                    }
                }
                $('#' + partId + '_table tr:eq(' + choiceCounter + ')').append(rowArray);
                rowArray = [];

                choiceCounter += 1;
            }

        }
        // Append count row to the last attempt row
        $('#' + partId + '_table #last_attempt').after(countRow);

        // Set student count and last_update_date
        setCountAndDate(partId,
            totalAttemptCount,
            lastUpdateDate);
    }


    function getChoiceTexts(partId) {
        var choiceText = [];
        $('#inputtype_' + partId).find("fieldset label").each(function(index) {
        	// Filter out the tick or cross text indicating correctness if present
            choiceText[index] = $(this).contents().filter(function() {
                return this.nodeType === 3; //Node.TEXT_NODE
            }).text();
        });
        return choiceText;
    }


    function setCountAndDate(partId,
        totalAttemptCount,
        lastUpdateDate) {

        // Set the Count and Date
        var part = document.getElementById(partId + '_analytics');
        part = $(part);
        part.find('.num-students').text(totalAttemptCount);
        part.find('.last-update').text(lastUpdateDate);

    }


    function setAggregateCounts(partId,
        totalAttemptCount,
        totalCorrectCount,
        totalIncorrectCount) {

        // Set text information for questions that have no inline analytics
        // graphics (not radio or checkbox)
        var part = document.getElementById(partId + '_analytics');
        part = $(part);
        var correctPercent = Math.round(totalCorrectCount * 1000 / (totalAttemptCount * 10));
        var incorrectPercent = Math.round(totalIncorrectCount * 1000 / (totalAttemptCount * 10));
        part.find('.num-students-extra').text(totalCorrectCount + ' (' + correctPercent + '%) correct and ' +
            totalIncorrectCount + ' (' + incorrectPercent + '%) incorrect.');
    }


    function orderByCount(a, b) {
        if (a['count'] > b['count']) {
            return -1;
        }
        if (a['count'] < b['count']) {
            return 1;
        }
        return 0;
    }


    function setErrorMessageOnPart(elementId, message) {
        // Set the error message on the element
    	$('#' + elementId + '_analytics').html(message);
    }


    function runDocReady(elementId) {


        // Variable for storing if a problem's analytics data has previously been retrieved.
        var elementsRetrieved = [];

        // Use elementId to attach handlers to the correct button since there
        // may be many problems on the page.
        $('#' + elementId + '_analytics_button').click(function(event) {

            var location = this.dataset.location;
            var answerDistUrl = this.dataset.answer_dist_url;
            var courseId = this.dataset.course_id;

            // If data already retrieved for this problem, just show the div
            if (elementsRetrieved.indexOf(elementId) !== -1) {
                $('#' + elementId + '_analytics_close').show();
                return;
            }

            //Hide the error message div
            $('#' + elementId + '_analytics_error_message').hide();

            var partsToGet = [];
            var questionTypesByPart = {};
            var correctResponses = {};
            var index;
            var id, partId;
            var numOptionsByPart = {};

            var divs = $('.' + elementId + '_analytics_div');

            // Construct array so we don't call the api for problems that have no questions supported by the api
            var arrayLength = divs.length;
            for (index = 0; index < arrayLength; index++) {
                id = divs[index].id;
                partId = id.substring(0, id.indexOf('_analytics'));
                if (divs[index].dataset.question_type) {
                    partsToGet.push(partId);
                }

                // Build dict of question types
                questionTypesByPart[partId] = divs[index].dataset.question_type;

                // Build dict of correct responses
                correctResponses[partId] = divs[index].dataset.correct_response;

                // Build dict of number of options (choices)
                numOptionsByPart[partId] = getChoiceTexts(partId).length;
            }

            var data = {
            		module_id: location,
            		question_types_by_part: questionTypesByPart,
            		num_options_by_part: numOptionsByPart,
            		course_id: courseId,
            };

            if (partsToGet.length > 0) {
                $.ajax({
                    context: this,
                    url: answerDistUrl,
                    type: 'POST',
                    data: {data: JSON.stringify(data)},
                    dataType: 'json',
                    contentType: "application/json",

                    success: function(response) {
                        if (response) {
                            window.InlineAnalytics.processResponse(response, partsToGet, questionTypesByPart, correctResponses);
                            // Store that we retrieved data for this problem
                            elementsRetrieved.push(elementId);
                            // Show all the graphics
                            $('#' + elementId + '_analytics_close').show();
                        }
                    },

                    error: function(jqXHR) {
                        $('#' + elementId + '_analytics_error_message').html(jqXHR.responseText).show();
                    }
                });

            } else {
            	// API was not called, (no parts to get) so display the existing messages
            	$('#' + elementId + '_analytics_close').show();
            }
        });

        $('#' + elementId + '_analytics_close .close').click(function() {
            $(this).parent().hide();
        });

    }

    return {
        processResponse: processResponse,
        runDocReady: runDocReady,
    };

})();
