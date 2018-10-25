function _templateLoader(templateName, staticPath, callback, errorCallback) {
    var templateURL = staticPath + '/common/templates/gradebook/' + templateName + '.underscore';

    $.ajax({
        url: templateURL,
        method: 'GET',
        dataType: 'html',
        success: function (data) {
            callback(data);
        },
        error: function (errorMessage) {
            console.log(errorMessage);
            errorCallback('Error has occurred while rendering table.');
        }
    });
}

function courseXblockUpdater(courseID, dataToSend, visibilityData, callback, errorCallback) {
    var cleanData = {'users' : {}};

    if (dataToSend instanceof Array)
        for (var i = 0; i < dataToSend.length; i++) {
            cleanData.users['id_' + dataToSend.userID] = {
                'block_id' : dataToSend[i].blockID || '',
                'grade' : dataToSend[i].grade || '',
                'max_grade' : dataToSend[i].maxGrade || null,
                'state' :  dataToSend[i].state || '{}',
                'user_id' : dataToSend[i].userID || ''
            };
        }
    else if (dataToSend instanceof Object)
        cleanData.users = dataToSend;

    var postUrl = '/api/score/courses/' + courseID;

    if (!_.isEmpty(visibilityData))
        cleanData.visibility = visibilityData;

    $.ajax({
        url: postUrl,
        method: 'POST',
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        data: JSON.stringify(cleanData),
        success: function (data) {
            callback(data);
        },
        error: function (errorMessage) {
            console.log(errorMessage);
            errorCallback('Error has occurred while updating grades.');
        }
    });
}

function getEdxUserInfoAsObject() {
    return JSON.parse($.cookie('edx-user-info').replace(/\\054/g, ',').replace(/^"(.*)"$/, '$1').replace(/\\"/g, '"'));
}

$(document).ready(function() {
    var dataTable,
        $gradebookWrapper = $('.gradebook-content'),
        $courseSectionFilter = $gradebookWrapper.find('#course-sections'),
        $errorMessageContainer = $gradebookWrapper.find('#error-message'),
        $filtersWrapper = $gradebookWrapper.find('#filters-container'),
        $gradebookNotification = $gradebookWrapper.find('#gradebook-notification'),
        $gradesTableWrapper = $gradebookWrapper.find('#gradebook-table-container'),
        $gradingPolicyFilter = $filtersWrapper.find('#grading-policy'),
        adjustedGradesData = {},
        courseID = $gradebookWrapper.attr('data-course-id'),
        edxUserInfo = getEdxUserInfoAsObject(),
        gradeBookData = [],
        gradeOverrideObject = {},
        isFetchingComplete = false,
        isFetchingSuccessful = true,
        isManualGrading = false,
        modalDataTable,
        module_list = {'users': {}},
        renderAllGradebook = true,
        sectionBlockId = '',
        staticPath = $gradebookWrapper.attr('data-static-path'),
        userAdjustedGrades = {},
        userAutoGrades = {},
        userComments = {},
        createMainDataTable = function(studentsDataLength) {
            const $gradebookErrorMessageContainer = $gradebookWrapper.find('#gradebook-table-empty-message');
            const $studentGradesTable = $gradesTableWrapper.find('#student-grades-table');
            const options = {
                fixedColumns: true,
                language: {
                    zeroRecords: ''
                },
                paging: studentsDataLength > 10,
                scrollX: true
            };
            dataTable = initializeDataTable($studentGradesTable, options, studentsDataLength);
            setUpDataTableSearch($studentGradesTable, $gradebookErrorMessageContainer);
            $studentGradesTable.on('draw.dt', displayGrades);
        },
        createModalTable = function(studentsDataLength) {
            const $gradeOverrideModalTable = $gradesTableWrapper.find('#grade-override-modal-table');
            const $modalErrorMessageContainer = $gradesTableWrapper.find('#modal-table-empty-message');
            const options = {
                columnDefs: [{
                    orderable: false,
                    targets: 3
                }],
                language: {
                    zeroRecords: ''
                },
                paging: studentsDataLength > 10
            };
            modalDataTable = initializeDataTable($gradeOverrideModalTable, options, studentsDataLength);
            setUpDataTableSearch($gradeOverrideModalTable, $modalErrorMessageContainer);
        },
        destroyDataTable = function($table) {
            if ($.fn.DataTable.isDataTable($table)) {
                $table.DataTable().destroy();
                $table.unbind();
            }
        },
        displayError = function(message) {
            $errorMessageContainer.text(message);
            $errorMessageContainer.toggleClass('hidden');
        },
        displayAbsoluteGrade = function($cell) {
            var $input = $cell.find('input'),
                title = $cell.attr('title');

            if (title !== 'Total' && title !== 'Current grade' && $input.length) {
                $input.prop('disabled', false);
                $input.val($cell.attr('data-score-earned'));
                return;
            }

            $cell.text($cell.attr('data-score-absolute'));
        },
        displayGrades = function() {
            var display = $('#table-data-view-percent').is(':checked') ? displayPercentGrade : displayAbsoluteGrade;

            $('#save-grade-field').hide();

            $('.data-score-container-class').each(function() {
                display($(this));
            });
        },
        displayPercentGrade = function($cell) {
            var $input = $cell.find('input'),
                title = $cell.attr('title');

            if (title !== 'Total' && $input.length){
                $input.prop('disabled', true);
                $input.val($cell.attr('data-score-percent'));
                return;
            }

            $cell.text($cell.attr('data-score-percent'));
        },
        fetchGrades = function(get_url) {
            $.ajax({
                type: 'GET',
                url: get_url,
                contentType: 'application/json; charset=utf-8',
                success: onPageFetched,
                failure: function(errMsg) {
                    isFetchingComplete = true;
                    isFetchingSuccessful = false;
                    console.log(errMsg);
                    displayError('Error has occurred while fetching grades.');
                }
            });
        },
        filterGradebook = function() {
            var gradingPolicy = $gradingPolicyFilter.val(),
                courseSection = $courseSectionFilter.val(),
                filterClasses = '.user-data';
            if (gradingPolicy && courseSection)
                filterClasses += ',.' + gradingPolicy + '.' + courseSection;
            else if (gradingPolicy || courseSection)
                filterClasses += ',.' + (gradingPolicy || courseSection);
            else
                filterClasses = '';

            dataTable.columns(':not(' + filterClasses + ')').visible(false, false);
            dataTable.columns(filterClasses).visible(true, false);
            dataTable.columns.adjust().draw(false);
        },
        initializeDataTable = function($table, options, studentsDataLength) {
            $table.on('length.dt', function(_, _, tableLength) {
                // If the provided data is longer than the table length selected
                // display the paggination buttons, otherwise hide them.
                $(this).parents('.dataTables_wrapper')
                       .find('.dataTables_paginate')
                       .toggleClass('hidden', studentsDataLength <= tableLength);
            });

            return $table.DataTable(options);
        },
        onFinishedFetchingGrades = function(response) {
            isFetchingComplete = true;
            isFetchingSuccessful = true;
            if (renderAllGradebook)
                $filtersWrapper.toggleClass('hidden');
            $gradebookNotification.toggleClass('hidden');
            gradeBookData = gradeBookData.concat(response.results);
            gradeBookData = gradeBookData.map(data => {
                data.section_breakdown = data.section_breakdown.filter(b => b.chapter_name !== 'holding section')
                return data;
            });
            renderGradebook(gradeBookData);
        },
        onPageFetched = function(response) {
            if (response.next) {
                gradeBookData = gradeBookData.concat(response.results);
                return fetchGrades(response.next);
            }
            onFinishedFetchingGrades(response);
        },
        renderGradingPolicyFilters = function(studentsData) {
            _templateLoader('_grading_policies', staticPath, function(template) {
                var $tpl = edx.HtmlUtils.template(template)({
                    gradingPolicies: Object.keys(studentsData[0].aggregates)
                }).toString();
                $('#grading-policy').append($tpl);
                $('#grading-policy').append(edx.HtmlUtils.ensureHtml(displayError).toString());
            }, displayError);
        },
        renderGradebook = function(studentsData) {
            if (renderAllGradebook)
                renderGradingPolicyFilters(studentsData);
            renderGradebookTable(studentsData);
        },
        renderGradebookTable = function(studentsData) {
            _templateLoader('_gradebook_table', staticPath, function(template) {
                var $tpl = edx.HtmlUtils.template(template)({
                    studentsData: studentsData,
                    strLib: {
                        userHeading: gettext('Username'),
                        total: gettext('Total')
                    }
                }).toString();
                $gradesTableWrapper.append($tpl);
                createMainDataTable(studentsData.length);
                ShowBlockIdEventBinder();
                filterGradebook();
            }, displayError);
            renderAllGradebook = true;
        },
        startFetchingGrades = function() {
            $gradebookNotification.toggleClass('hidden');
            fetchGrades('api/grades/v1/gradebook/' + courseID + '/');
        };

    $gradingPolicyFilter.change(function() { filterGradebook(); });
    $courseSectionFilter.change(function() { filterGradebook(); });

    function renderModalTemplateData(template) {
        var blockID = $(gradeOverrideObject).attr('data-block-id');
        var studentsData = [];
        var tpl = edx.HtmlUtils.template(template);

        gradeBookData.map(function(userData){
            var gradeData = userData.section_breakdown.filter(function(sectionData){
                return (sectionData.module_id === blockID);
            });

            if (!_.isEmpty(gradeData)) {
                var auto_grade = parseFloat(gradeData[0].auto_grade);
                var score_earned = parseFloat(gradeData[0].score_earned);
                var score_possible = parseFloat(gradeData[0].score_possible);
                var username = userData.username;
                userComments[username] = gradeData[0].comment;

                if (! (isNaN(score_earned) || isNaN(score_possible))) {
                    if (! isNaN(auto_grade)) {
                        userAutoGrades[username] = auto_grade + '/' + score_possible;
                        userAdjustedGrades[username] = score_earned + '/' + score_possible;
                    }
                    else
                        userAutoGrades[username] = score_earned + '/' + score_possible;

                    studentsData.push(userData);
                }
            }
        });

        edx.HtmlUtils.setHtml(
            $('#grade-override-modal'),
            tpl({
                studentsData: studentsData,
                strLib: {
                    heading: gettext("The Assignment name is:"),
                    publishGrades: gettext("Publish grades"),
                    noMatch: gettext("No matching records found"),
                    studentNameHeading: gettext("Student Name"),
                    commentHeading: gettext("Comment"),
                    save: gettext("Save"),
                    cancel: gettext("Cancel")
                }
            })
        );
        createModalTable(studentsData.length);
        fillModalTemplate();
    }

    function fillModalTemplate() {
        var $modal = $('.grade-override-modal');
        var $adjustedGradeHeader = $modal.find('#adjusted-grade-header');
        var $autoGradeHeader = $modal.find('#auto-grade-header');
        var $manualGradeVisibilityWrapper = $modal.find('#manual-grade-visibility');
        var $saveGradeOverrideButton = $modal.find('.grade-override-modal-save');
        var $tableWrapper = $modal.find('.grade-override-table-wrapper');
        var assignmentName = $(gradeOverrideObject).attr('data-assignment-name');
        var blockID = $(gradeOverrideObject).attr('data-block-id');
        var dataPublished = $(gradeOverrideObject).attr('data-published') || false;
        sectionBlockId = $(gradeOverrideObject).attr('data-section-block-id');
        gradesPublished = JSON.parse(dataPublished);
        isManualGrading = JSON.parse($(gradeOverrideObject).attr('data-manual-grading'));
        $modal.find('.assignment-name-placeholder').text(assignmentName);
        $modal.find('.block-id-placeholder').text(blockID);
        if ( _.isEmpty(userAutoGrades) ) {
            $tableWrapper.hide();
            $manualGradeVisibilityWrapper.toggle(false);
            $modal.find('.grade-override-message').text(gettext('There are no student grades to adjust.'));
            $modal.find('.grade-override-message').show();
            $saveGradeOverrideButton.hide();
        }
        else {
            $adjustedGradeHeader.text(isManualGrading ? 'Manual grade' : 'Adjusted grade');
            $autoGradeHeader.text(isManualGrading ? 'Current grade' : 'Auto grade');

            $manualGradeVisibilityWrapper.toggle(isManualGrading);
            $saveGradeOverrideButton.attr('data-manual-grading', isManualGrading);
            $manualGradeVisibilityWrapper.attr('data-visibility', gradesPublished);
            $('input[name=grades-published]').prop('checked', gradesPublished);

            $tableWrapper.attr('data-manual-grading', isManualGrading);
            $tableWrapper.show();
            $saveGradeOverrideButton.show().prop('disabled', true);
            modalDataTable.$('tr').each(function(){
                $(this).attr('data-block-id', blockID);
                var $adjustedGradePlaceholder = $(this).find('td.user-adjusted-grade');
                var $autoGradePlaceholder = $(this).find('td.user-auto-grade');
                var $commentPlaceholder = $(this).find('td.user-grade-comment');
                var $commentTextArea = $commentPlaceholder.find('textarea');
                var comment;
                var username = $autoGradePlaceholder.attr('data-username');

                if (username in userAutoGrades) {
                    $autoGradePlaceholder.text(userAutoGrades[username]);
                    var autoEarnedGrade = userAutoGrades[username].split('/')[0],
                        autoPossibleGrade = userAutoGrades[username].split('/')[1];
                    $adjustedGradePlaceholder.attr('data-score-earned', autoEarnedGrade);
                    $adjustedGradePlaceholder.attr('data-score-possible', autoPossibleGrade);
                    $autoGradePlaceholder.attr('data-sort', autoEarnedGrade);

                    if (username in userAdjustedGrades) {
                        var adjustedGrade = userAdjustedGrades[username].split('/')[0];
                        $adjustedGradePlaceholder.attr('data-score-earned', adjustedGrade);
                        $adjustedGradePlaceholder.attr('data-sort', adjustedGrade);
                        $adjustedGradePlaceholder.addClass('has-adjusted-score');
                        if (autoEarnedGrade != adjustedGrade){
                            DisplayGradeComment(username, $commentPlaceholder, $commentTextArea);
                        }
                        else
                            $commentTextArea.prop('disabled', true).val('');
                    }
                    else if (isManualGrading) {
                        $adjustedGradePlaceholder.attr('data-sort', autoEarnedGrade);
                        DisplayGradeComment(username, $commentPlaceholder, $commentTextArea);
                    }
                    else {
                        $(this).find('.user-grade-comment textarea').attr('disabled', 'disabled');
                        $adjustedGradePlaceholder.attr('data-sort', autoEarnedGrade);
                        $commentTextArea.prop('disabled', true).val('');
                    }
                    $adjustedGradePlaceholder.find('input').val($adjustedGradePlaceholder.attr('data-score-earned'));
                    $adjustedGradePlaceholder.find('span').text($adjustedGradePlaceholder.attr('data-score-possible'));
                }
                else
                    $(this).hide();
            });
        }
        $modal.show();
    }

    /* Autograde override modal window manipulation */
    $(document).on('click', '.grade-override', function() {
        gradeOverrideObject = this;
        _templateLoader('_gradebook_modal_table', staticPath, renderModalTemplateData, displayError);
    });

    function setUpDataTableSearch($table, $tableEmptyMessage) {
        $table.on('search.dt', function () {
            if (!$table.DataTable().page.info().recordsDisplay) {
                $tableEmptyMessage.show();
            }
            else {
                $tableEmptyMessage.hide();
            }
        });
    }

    $(document).on('click', '.grade-override-modal-close', function(){
        gradebookOverrideModalReset();
    });

    function gradebookOverrideModalReset() {
        var $modal = $('.grade-override-modal');
        adjustedGradesData = {};
        userAdjustedGrades = {};
        userAutoGrades = {};
        userComments = {};

        $modal.hide();
        $modal.find('.grade-override-table-wrapper').find('tr').show();
        $modal.find('#manual-grade-visibility').hide();
        $modal.find('.grade-override-message').removeClass('error').empty().hide();
        $modal.find('table').find('input').removeClass('score-visited').removeClass('error');
        $modal.find('table').find('textarea').removeClass('score-visited').removeClass('error');
        $modal.find('#modal-table-empty-message').hide();
        destroyDataTable($('#grade-override-modal-table'));
    }

    function DisplayGradeComment(username, $commentPlaceholder, $commentTextArea) {
        comment = userComments[username];
        $commentPlaceholder.attr('data-comment', comment);
        $commentTextArea.prop('disabled', false).val(comment);
    }

    /* Block ID modal window manipulation */
    function ShowBlockIdEventBinder() {
        $('.eye-icon.block-id-info').on('click', function(e){
            e.stopPropagation();
            $('.block-id-modal').find('.block-id-placeholder').empty();
            $('.block-id-modal').find('.block-id-placeholder').text($(this).data('block-id'));
            $('.block-id-modal').find('.display-name-placeholder').text($(this).data('display-name'));
            $('.block-id-modal').show();
        });
    }

    function HasUserMadeChanges() {
        var areScoresModified = $('.score-visited').length > 0;
        var originalGradeVisibility = $('#manual-grade-visibility').attr('data-visibility');
        var currentGradeVisibility = JSON.stringify($('input[name=grades-published]').prop('checked'));

        return areScoresModified || originalGradeVisibility !== currentGradeVisibility;
    }

    function ToggleSaveButton(shouldDisable) {
        var $modalSaveButton = $('.grade-override-modal').find('.grade-override-modal-save');
        $modalSaveButton.prop('disabled', shouldDisable);
    }

    $(document).on('keyup focus', '.user-adjusted-grade input', function(){
        var $row = $(this).parents('tr'),
            $cell = $(this).parents('td'),
            $commentTextArea = $row.find('.user-grade-comment textarea'),
            autoGrade = $row.find('.user-auto-grade').html().split('/')[0],
            previousGrade = $cell.attr('data-score-earned');
            adjustedGrade = $(this).val();

        $cell.attr('data-sort', adjustedGrade);

        if (autoGrade != adjustedGrade || previousGrade != adjustedGrade)
            $(this).addClass('score-visited');
        else
            $(this).removeClass('score-visited');

        ToggleSaveButton(!HasUserMadeChanges());

        if (!isManualGrading) {
            if (autoGrade == adjustedGrade)
                $commentTextArea.prop('disabled', true).val('');
            else
                $commentTextArea.prop('disabled', false);
        }

        modalDataTable.rows().invalidate();
    });

    $(document).on('keyup focus', '.user-grade-comment textarea', function(){
        var originalComment = $(this).parents('td').attr('data-comment'),
            changedComment = $(this).val();

        $(this).toggleClass('score-visited', changedComment != originalComment)

        ToggleSaveButton(!HasUserMadeChanges());
    });

    $(document).on('change', 'input[name=grades-published]', function() {
        ToggleSaveButton(!HasUserMadeChanges());
    });

    function collectOverrideGradebookData() {
        var $modal = $('.grade-override-modal');
        var $table = $modal.find('table').dataTable();
        $table.$('tr').each(function(){
            var $row = $(this);
            var $gradeCell = $row.find('.user-adjusted-grade');
            var $grade = $gradeCell.find('input');
            var $commentCell = $row.find('.user-grade-comment');
            var $comment = $commentCell.find('textarea');
            var username = $gradeCell.attr('data-username');
            var autoGrade;
            var grade;
            var removeAdjustedGrade;

            if ($grade.hasClass('score-visited') || $comment.hasClass('score-visited'))
                adjustedGradesData[username] = {
                    'block_id' : $row.attr('data-block-id'),
                    'max_grade' : $gradeCell.attr('data-score-possible'),
                    'state' : { 'username': edxUserInfo.username},
                    'user_id' : $row.attr('data-user-id')
                };

            if (username in adjustedGradesData) {
                autoGrade = $row.find('.user-auto-grade').text().split('/')[0];
                grade = $grade.val().trim();
                removeAdjustedGrade = isManualGrading || autoGrade === grade;

                adjustedGradesData[username].grade = grade;
                adjustedGradesData[username].state.comment = $comment.val().trim();
                adjustedGradesData[username].remove_adjusted_grade = removeAdjustedGrade;
                adjustedGradesData[username].section_block_id = sectionBlockId;
            }
        });
    }

    $(document).on('click', '.grade-override-modal-save', function() {
        var visibilityData = {};
        if (isManualGrading) {
            visibilityData = {
                'block_id': $('.block-id-placeholder').html(),
                'visibility': JSON.stringify($('input[name=grades-published]').prop('checked')),
            }
        }
        collectOverrideGradebookData();
        if (Object.keys(adjustedGradesData).length === 0 && !isManualGrading)
            return;
        var validStatus = ValidateAdjustedGradesData();
        if (validStatus) {
            courseXblockUpdater(
                courseID,
                adjustedGradesData,
                visibilityData,
                function(data){
                    gradebookOverrideModalReset();
                    renderAllGradebook = false;
                    gradeBookData = [];
                    $gradesTableWrapper.empty();
                    startFetchingGrades();
                }, function(data){
                    console.log(data);
                }
            );
        }
    });

    function ValidateAdjustedGradesData() {
        var isValid = true;
        var $table = $('.grade-override-modal').find('table');
        var $messageField = $('.grade-override-modal').find('.grade-override-message');
        $messageField.empty();
        _.each(adjustedGradesData, function(data, username){
            adjustedGradesData[username].errors = [];
            var userAdjustedGradeSelector = '*[data-username="' + username + '"].user-adjusted-grade';
            var $adjustedGradePlaceholder = $table.find(userAdjustedGradeSelector).find('input');
            // Is it a valid number
            if (isNaN(data.grade)) {
                isValid = false;
                $adjustedGradePlaceholder.addClass('error');
                adjustedGradesData[username].errors.push('Adjusted grade must be an integer number');
            }

            // Is it within range
            var floatGrade = parseFloat(data.grade);
            var errorMessage;
            if (floatGrade < 0 || floatGrade > parseFloat(data.max_grade)) {
                errorMessage = 'Adjusted grade must be within range [0 - ' + data.max_grade + ']';
                isValid = false;
                $adjustedGradePlaceholder.addClass('error');
                adjustedGradesData[username].errors.push(errorMessage);
            }

            for (var i = 0; i < adjustedGradesData[username].errors.length; i++) {
                $errorMessage = edx.HtmlUtils.joinHtml('Error for user ', username, ': ', adjustedGradesData[username].errors[i], '<br>').toString();
                $messageField.append($errorMessage);
            }

            if (adjustedGradesData[username].errors.length === 0) {
                $adjustedGradePlaceholder.removeClass('error');
                delete adjustedGradesData[username].errors;
            }
        });

        if (! isValid) {
            $messageField.addClass('error');
            $messageField.show();
        }

        return isValid;
    }

    $(document).on('change', '#table-data-view-percent', displayGrades);

    $(document).on('change', '#table-data-view-absolute', displayGrades);

    $('.data-score-container-class').each(function(){
        var title = $(this).attr('title');
        if (title !== 'Total' && title !== 'Current grade')
            if ($(this).find('input').length)
                $(this).find('input').prop('disabled', false);
            else
                $(this).text($(this).attr('data-score-absolute'));
    });

    $(document).on('change', '#save-grade-field textarea', function(){
        var editor = $('#save-grade-field'),
            studentID = editor.attr('data-student-id'),
            blockID = editor.attr('data-block-id'),
            module_key = studentID + blockID;

        if (!module_list.users[module_key])
            module_list.users[module_key] = {
                'user_id': studentID,
                'grade': parseFloat(editor.attr('data-new-score')).toFixed(2),
                'max_grade': parseFloat(editor.attr('data-score-possible')).toFixed(2),
                'course_id': courseID,
                'block_id': blockID,
                'state': {}
            };
        module_list.users[module_key].state.comment = $(this).val();
    });

    if ($gradebookWrapper.attr('data-number-of-students') > 0)
        startFetchingGrades();
});