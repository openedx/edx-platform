window.InlineAnalytics = (function() {

    'use strict';

    function processResponse(
        response,
        partsToGet,
        questionTypesByPart,
        correctResponses,
        choiceNameListByPart) {

        var dataByPart = response.data_by_part;
        var countByPart = response.count_by_part;
        var messageByPart = response.message_by_part;
        var lastUpdateDate = response.last_update_date;
        var totalFirstAttemptCount;
        var totalFirstCorrectCount;
        var totalFirstIncorrectCount;
        var totalLastAttemptCount;
        var totalLastCorrectCount;
        var totalLastIncorrectCount;

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
                totalFirstAttemptCount = countByPart[partId]['totalFirstAttemptCount'];
                totalFirstCorrectCount = countByPart[partId]['totalFirstCorrectCount'];
                totalFirstIncorrectCount = countByPart[partId]['totalFirstIncorrectCount'];
                totalLastAttemptCount = countByPart[partId]['totalLastAttemptCount'];
                totalLastCorrectCount = countByPart[partId]['totalLastCorrectCount'];
                totalLastIncorrectCount = countByPart[partId]['totalLastIncorrectCount'];
            } else {
                totalFirstAttemptCount = 0;
                totalFirstCorrectCount = 0;
                totalFirstIncorrectCount = 0;
                totalLastAttemptCount = 0;
                totalLastCorrectCount = 0;
                totalLastIncorrectCount = 0;
            }

            if (questionTypesByPart[partId] === 'radio') {
                renderRadioAnalytics(
                    dataByPart[partId],
                    partId,
                    totalFirstAttemptCount,
                    totalLastAttemptCount,
                    correctResponses[partId],
                    lastUpdateDate,
                    choiceNameListByPart[partId]);
            } else if (questionTypesByPart[partId] === 'checkbox') {
                renderCheckboxAnalytics(
                    dataByPart[partId],
                    partId,
                    totalFirstAttemptCount,
                    totalLastAttemptCount,
                    correctResponses[partId],
                    lastUpdateDate);
            } else {
                // Just set the text on the div
                setCountAndDate(
                    partId,
                    totalLastAttemptCount,
                    lastUpdateDate);

                setAggregateCounts(
                    partId,
                    totalFirstAttemptCount,
                    totalFirstCorrectCount,
                    totalFirstIncorrectCount,
                    totalLastAttemptCount,
                    totalLastCorrectCount,
                    totalLastIncorrectCount);
            }
        }
    }


    function renderRadioAnalytics(
        result,
        partId,
        totalFirstAttemptCount,
        totalLastAttemptCount,
        correctResponse,
        lastUpdateDate,
        choiceNameString) {

        var valueId;
        var currentIndex;
        var valueIndex;
        var lastIndex;
        var correct;
        var firstCount;
        var lastCount;
        var firstPercent;
        var lastPercent;
        var answerClass;
        var index;
        var tr;
        var tdChoice;
        var tdDot;
        var tdFirstCount;
        var tdLastCount;
        var tdFirstPercent;
        var tdLastPercent;
        var trs = [];
        var valueIdArray;
        var arrayLength;
        var lastTableRow = $('#' + partId + '_table tr:last');
        var currentResult;

        // Build the array of choice texts
        var choiceText = getChoiceTexts(partId);

        // Generate choice name array
        var choiceNameArray = JSON.parse(choiceNameString);

        if (result) {
            // Build the array of value_id's
            valueIdArray = constructValueIdArray(result);

            // Loop through choiceNameArray and construct row array.
            // We can determine if any rows are "missing" from the api data
            // since the choiceNameArray is a list of all possible rows.
            arrayLength = choiceNameArray.length;
            for (index = 0; index < arrayLength; index++) {

                // If value is not in array then add row
                if (valueIdArray.indexOf(choiceNameArray[index]) === -1) {
                    insertMissingRows(partId,
                        index,
                        index + 1,
                        correctResponse,
                        choiceText,
                        choiceNameArray,
                        trs);
                } else {
                    currentResult = result[valueIdArray.indexOf(choiceNameArray[index])]
                    correct = currentResult['correct'];
                    firstCount = currentResult['first_count'];
                    lastCount = currentResult['last_count'];
                    firstPercent = Math.round(firstCount * 1000 / (totalFirstAttemptCount * 10));
                    lastPercent = Math.round(lastCount * 1000 / (totalLastAttemptCount * 10));

                    if (correct) {
                        answerClass = 'inline-analytics-correct';
                    } else {
                        answerClass = 'inline-analytics-incorrect';
                    }

                    tr = $('<tr>');
                    tdChoice = $('<td class="answer-box">');
                    tdChoice.attr('title', choiceText[index]);
                    tdChoice.text(parseInt(index, 10) + 1);
                    tdDot = $('<td class="answer-box">');
                    tdDot.addClass(answerClass);
                    tdDot.append($('<span class="dot">'));
                    tdFirstCount = $('<td class="checkbox-first-attempt">');
                    tdFirstCount.text(firstCount);
                    tdFirstPercent = $('<td class="checkbox-first-attempt">');
                    tdFirstPercent.text(firstPercent + '%');
                    tdLastCount = $('<td class="checkbox-last-attempt">');
                    tdLastCount.text(lastCount);
                    tdLastPercent = $('<td class="checkbox-last-attempt">');
                    tdLastPercent.text(lastPercent + '%');

                    tr.append(tdChoice);
                    tr.append(tdDot);
                    tr.append(tdFirstCount);
                    tr.append(tdFirstPercent);
                    tr.append(tdLastCount);
                    tr.append(tdLastPercent);
                    trs.push(tr[0]);
                }
            }
        } else {
            // There were no results
            trs = insertMissingRows(partId,
                0,
                choiceNameArray.length,
                correctResponse,
                choiceText,
                choiceNameArray,
                trs);
        }

        // Append the row array to the table
        lastTableRow.after(trs);

        // Set student count and last_update_date
        setCountAndDate(partId,
            totalLastAttemptCount,
            lastUpdateDate);
    }


    function insertMissingRows(
        partId,
        currentIndex,
        finalIndex,
        correctResponse,
        choiceText,
        choiceNameArray,
        trs) {

        var answerClass;
        var tr;
        var tdChoice;
        var tdDot;
        var tdFirstCount;
        var tdLastCount;
        var tdFirstPercent;
        var tdLastPercent;

        correctResponse = correctResponse.substring(2, correctResponse.length - 2);

        // Insert rows between currentIndex and finalIndex
        while (currentIndex < finalIndex) {
            if (choiceNameArray[currentIndex] === correctResponse) {
                answerClass = 'inline-analytics-correct';
            } else {
                answerClass = 'inline-analytics-incorrect';
            }

            tr = $('<tr>');
            tdChoice = $('<td class="answer-box">');
            tdChoice.attr('title', choiceText[currentIndex]);
            tdChoice.text(parseInt(currentIndex, 10) + 1);
            tdDot = $('<td class="answer-box">');
            tdDot.addClass(answerClass);
            tdDot.append($('<span class="dot">'));
            tdFirstCount = $('<td class="checkbox-first-attempt">');
            tdFirstCount.text(0);
            tdLastCount = $('<td class="checkbox-last-attempt">');
            tdLastCount.text(0);
            tdFirstPercent = $('<td class="checkbox-first-attempt">');
            tdFirstPercent.text('0%');
            tdLastPercent = $('<td class="checkbox-last-attempt">');
            tdLastPercent.text('0%');

            tr.append(tdChoice);
            tr.append(tdDot);
            tr.append(tdFirstCount);
            tr.append(tdFirstPercent);
            tr.append(tdLastCount);
            tr.append(tdLastPercent);
            trs.push(tr[0]);
            currentIndex += 1;
        }
        return trs;
    }


    function renderCheckboxAnalytics(
        result,
        partId,
        totalFirstAttemptCount,
        totalLastAttemptCount,
        correctResponse,
        lastUpdateDate) {

        var firstCount;
        var lastCount;
        var firstPercent;
        var lastPercent;
        var answerClass;
        var actualResponse;
        var imaginedResponse;
        var checkboxChecked;
        var firstCountRow;
        var lastCountRow;
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
        $('#' + partId + '_table .checkbox_header_row').after('<tr><td id="last_attempt" class="answer-box checkbox-last-attempt">' + gettext('Last Attempt') + '</td></tr>');

        // Add "First Attempt" to the choice number column
        $('#' + partId + '_table .checkbox_header_row').after('<tr><td id="first_attempt" class="answer-box checkbox-first-attempt">' + gettext('First Attempt') + '</td></tr>');

        // Construct the choice number column array
        while (choiceCounter <= choiceText.length) {
            tr = $('<tr><td id="column0:row' + choiceCounter + '" class="answer-box" title="' +
                choiceText[choiceCounter - 1] + '">' + choiceCounter + '</td></tr>');
            choiceTrs.push(tr[0]);
            choiceCounter += 1;
        }

        // Append the choice number column array to the header row
        var headerRow = $('#' + partId + '_table .checkbox_header_row');
        headerRow.after(choiceTrs);

        // Loop through results constructing header row and data row arrays
        if (result) {
            // Sort the results in descending response count order
            result.sort(orderByCount);

            var arrayLength = result.length;
            for (index = 0; index < arrayLength; index++) {
                // Append columns to the header row array
                tr = $('<th class="header"></th>');
                headerTrs.push(tr[0]);

                // Append message and break if number of distinct choices >= max_columns
                if (index >= maxColumns) {
                    var notDisplayed = result.length - maxColumns;
                    tr = $('<th class="not-displayed"> ' + notDisplayed + ' columns not displayed.</th>');
                    headerTrs.push(tr[0]);
                    break;
                }

                actualResponse = result[index]['value_id'];
                choiceCounter = 1;

                // Construct the data row array from student responses
                while (choiceCounter <= choiceText.length) {
                    imaginedResponse = 'choice_' + (choiceCounter - 1);

                    // Can't rely on contains method in all browsers so use indexOf
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

                    tr = $('<td id="column' + index + ':row' + choiceCounter + '" class="answer-box ' +
                        answerClass + '">' + checkboxChecked + '</td>');
                    dataTrs.push([choiceCounter, tr[0]]);

                    choiceCounter += 1;
                }

                // Construct the First Attempt row
                firstCount = result[index]['first_count'];
                firstPercent = Math.round(firstCount * 1000 / (totalFirstAttemptCount * 10));
                firstCountRow += '<td class="answer-box checkbox-first-attempt">' + firstCount + '<br/>' + firstPercent + '%</td>'

                // Construct the Last Attempt row
                lastCount = result[index]['last_count'];
                lastPercent = Math.round(lastCount * 1000 / (totalLastAttemptCount * 10));
                lastCountRow += '<td class="answer-box checkbox-last-attempt">' + lastCount + '<br/>' + lastPercent + '%</td>'
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
        //Append count row to the first attempt row
        $('#' + partId + '_table #first_attempt').after(firstCountRow);

        // Append count row to the last attempt row
        $('#' + partId + '_table #last_attempt').after(lastCountRow);

        // Set student count and last_update_date
        setCountAndDate(
            partId,
            totalLastAttemptCount,
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


    function setCountAndDate(
        partId,
        totalLastAttemptCount,
        lastUpdateDate) {

        // Set the Count and Date
        var part = document.getElementById(partId + '_analytics');
        part = $(part);
        part.find('.num-students').text(totalLastAttemptCount);
        part.find('.last-update').text(lastUpdateDate);

    }


    function setAggregateCounts(
        partId,
        totalFirstAttemptCount,
        totalFirstCorrectCount,
        totalFirstIncorrectCount,
        totalLastAttemptCount,
        totalLastCorrectCount,
        totalLastIncorrectCount) {

        // Set text information for questions that have no inline analytics
        // graphics (not radio or checkbox)
        var part = document.getElementById(partId + '_analytics');
        part = $(part);

        var correctFirstPercent = Math.round(totalFirstCorrectCount * 1000 / (totalFirstAttemptCount * 10));
        var incorrectFirstPercent = Math.round(totalFirstIncorrectCount * 1000 / (totalFirstAttemptCount * 10));

        var correctLastPercent = Math.round(totalLastCorrectCount * 1000 / (totalLastAttemptCount * 10));
        var incorrectLastPercent = Math.round(totalLastIncorrectCount * 1000 / (totalLastAttemptCount * 10));

        part.find('.num-students-extra-first-correct').text(totalFirstCorrectCount + ' (' + correctFirstPercent + '%) ');
        part.find('.num-students-extra-first-incorrect').text(totalFirstIncorrectCount + ' (' + incorrectFirstPercent + '%) ');

        part.find('.num-students-extra-last-correct').text(totalLastCorrectCount + ' (' + correctLastPercent + '%) ');
        part.find('.num-students-extra-last-incorrect').text(totalLastIncorrectCount + ' (' + incorrectLastPercent + '%) ');
    }


    function orderByCount(a, b) {
        if (a['last_count'] > b['last_count']) {
            return -1;
        }
        if (a['last_count'] < b['last_count']) {
            return 1;
        }
        return 0;
    }


    function setErrorMessageOnPart(
        elementId,
        message) {
        // Set the error message on the element
        $('#' + elementId + '_analytics').html(message);
    }


    function constructValueIdArray(result) {
        var valueIdArray = [];
        valueIdArray = result.map(function(element) {
            return element['value_id'];
        });
        return valueIdArray;
    }


    function runDocReady(elementId) {

        // Variable for storing if a problem's analytics data has previously been retrieved.
        var elementsRetrieved = [];

        // Use elementId to attach handlers to the correct button since there
        // may be many problems on the page.
        $('#' + elementId + '_analytics_button').click(function(event) {
            event.preventDefault();
            var location = this.dataset.location;
            var answerDistUrl = this.dataset.answerDistUrl;
            var courseId = this.dataset.courseId;

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
            var choiceNameListByPart = {};

            var divs = $('.' + elementId + '_analytics_div');

            // Construct array so we don't call the api for problems that have no questions supported by the api
            var arrayLength = divs.length;
            for (index = 0; index < arrayLength; index++) {
                id = divs[index].id;
                partId = id.substring(0, id.indexOf('_analytics'));
                if (divs[index].dataset.questionType) {
                    partsToGet.push(partId);
                }

                // Build dict of question types
                questionTypesByPart[partId] = divs[index].dataset.questionType;

                // Build dict of correct responses
                correctResponses[partId] = divs[index].dataset.correctResponse;

                // Build dict of number of options (choices)
                numOptionsByPart[partId] = getChoiceTexts(partId).length;

                // Build dict of choice name lists
                choiceNameListByPart[partId] = divs[index].dataset.choiceNameList;
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
                    data: JSON.stringify(data),
                    dataType: 'json',
                    contentType: "application/json",

                    success: function(response) {
                        if (response) {
                            window.InlineAnalytics.processResponse(response, partsToGet, questionTypesByPart, correctResponses, choiceNameListByPart);
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
        runDocReady: runDocReady,
        processResponse: processResponse,
    };

})();
