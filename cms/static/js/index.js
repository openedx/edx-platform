define(['domReady', 'jquery', 'underscore', 'js/utils/cancel_on_escape', 'js/views/utils/create_course_utils',
 'js/views/utils/create_library_utils','js/views/utils/create_liveclass_utils', 'js/views/utils/get_liveclass_utils','common/js/components/utils/view_utils'],
 function(domReady, $, _, CancelOnEscape, CreateCourseUtilsFactory, CreateLibraryUtilsFactory, CreateLiveClassUtilsFactory,GetiveClassUtilsFactory,ViewUtils) {
 'use strict';
 var CreateCourseUtils = new CreateCourseUtilsFactory({
 name: '.new-course-name',
 org: '.new-course-org',
 number: '.new-course-number',
 run: '.new-course-run',
 save: '.new-course-save',
 errorWrapper: '.create-course .wrap-error',
 errorMessage: '#course_creation_error',
 tipError: '.create-course span.tip-error',
 error: '.create-course .error',
 allowUnicode: '.allow-unicode-course-id'
 }, {
 shown: 'is-shown',
 showing: 'is-showing',
 hiding: 'is-hiding',
 disabled: 'is-disabled',
 error: 'error'
 });

 var CreateLibraryUtils = new CreateLibraryUtilsFactory({
 name: '.new-library-name',
 org: '.new-library-org',
 number: '.new-library-number',
 save: '.new-library-save',
 errorWrapper: '.create-library .wrap-error',
 errorMessage: '#library_creation_error',
 tipError: '.create-library span.tip-error',
 error: '.create-library .error',
 allowUnicode: '.allow-unicode-library-id'
 }, {
 shown: 'is-shown',
 showing: 'is-showing',
 hiding: 'is-hiding',
 disabled: 'is-disabled',
 error: 'error'
 });

 var CreateLiveClassUtils = new CreateLiveClassUtilsFactory({
 name: '.new-liveclass-name',
 save: '.new-liveclass-save',
 errorWrapper: '.create-liveclass .wrap-error',
 errorMessage: '#liveclass_creation_error',
 tipError: '.create-liveclass span.tip-error',
 error: '.create-liveclass .error',
 allowUnicode: '.allow-unicode-liveclass-id'
 }, {
 shown: 'is-shown',
 showing: 'is-showing',
 hiding: 'is-hiding',
 disabled: 'is-disabled',
 error: 'error'
 });

 var GetLiveClassUtils = new GetiveClassUtilsFactory({
 });

 var saveNewCourse = function(e) {
 e.preventDefault();

 if (CreateCourseUtils.hasInvalidRequiredFields()) {
 return;
 }

 var $newCourseForm = $(this).closest('#create-course-form');
 var display_name = $newCourseForm.find('.new-course-name').val();
 var org = $newCourseForm.find('.new-course-org').val();
 var number = $newCourseForm.find('.new-course-number').val();
 var run = $newCourseForm.find('.new-course-run').val();

 var course_info = {
 org: org,
 number: number,
 display_name: display_name,
 run: run
 };

 analytics.track('Created a Course', course_info);
 CreateCourseUtils.create(course_info, function(errorMessage) {
 var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
 $('.create-course .wrap-error').addClass('is-shown');
 edx.HtmlUtils.setHtml($('#course_creation_error'), msg);
 $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
 });
 };

 var rtlTextDirection = function() {
 var Selectors = {
 new_course_run: '#new-course-run'
 };

 if ($('body').hasClass('rtl')) {
 $(Selectors.new_course_run).addClass('course-run-text-direction placeholder-text-direction');
 $(Selectors.new_course_run).on('input', function() {
 if (this.value === '') {
 $(Selectors.new_course_run).addClass('placeholder-text-direction');
 } else {
 $(Selectors.new_course_run).removeClass('placeholder-text-direction');
 }
 });
 }
 };

 var makeCancelHandler = function(addType) {
 return function(e) {
 e.preventDefault();
 $('.new-' + addType + '-button').removeClass('is-disabled').attr('aria-disabled', false);
 $('.wrapper-create-' + addType).removeClass('is-shown');
 // Clear out existing fields and errors
 $('#create-' + addType + '-form input[type=text]').val('');
 $('#' + addType + '_creation_error').html('');
 $('.create-' + addType + ' .wrap-error').removeClass('is-shown');
 $('.new-' + addType + '-save').off('click');
 };
 };

 var addNewCourse = function(e) {
 var $newCourse,
 $cancelButton,
 $courseName;
 e.preventDefault();
 $('.new-course-button').addClass('is-disabled').attr('aria-disabled', true);
 $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
 $newCourse = $('.wrapper-create-course').addClass('is-shown');
 $cancelButton = $newCourse.find('.new-course-cancel');
 $courseName = $('.new-course-name');
 $courseName.focus().select();
 $('.new-course-save').on('click', saveNewCourse);
 $cancelButton.bind('click', makeCancelHandler('course'));
 CancelOnEscape($cancelButton);
 CreateCourseUtils.setupOrgAutocomplete();
 CreateCourseUtils.configureHandlers();
 rtlTextDirection();
 };

 var saveNewLibrary = function(e) {
 e.preventDefault();

 if (CreateLibraryUtils.hasInvalidRequiredFields()) {
 return;
 }

 var $newLibraryForm = $(this).closest('#create-library-form');
 var display_name = $newLibraryForm.find('.new-library-name').val();
 var org = $newLibraryForm.find('.new-library-org').val();
 var number = $newLibraryForm.find('.new-library-number').val();

 var lib_info = {
 org: org,
 number: number,
 display_name: display_name
 };

 analytics.track('Created a Library', lib_info);
 CreateLibraryUtils.create(lib_info, function(errorMessage) {
 var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
 $('.create-library .wrap-error').addClass('is-shown');
 edx.HtmlUtils.setHtml($('#library_creation_error'), msg);
 $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
 });
 };

 var addNewLibrary = function(e) {
 e.preventDefault();
 $('.new-library-button').addClass('is-disabled').attr('aria-disabled', true);
 $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
 var $newLibrary = $('.wrapper-create-library').addClass('is-shown');
 var $cancelButton = $newLibrary.find('.new-library-cancel');
 var $libraryName = $('.new-library-name');
 $libraryName.focus().select();
 $('.new-library-save').on('click', saveNewLibrary);
 $cancelButton.bind('click', makeCancelHandler('library'));
 CancelOnEscape($cancelButton);
 CreateLibraryUtils.configureHandlers();
 };


 var saveNewLiveClass= function(e) {
 e.preventDefault();

 
 
 var $newLiveClassForm = $(this).closest('#create-liveclass-form');
 
 var display_name = $newLiveClassForm.find('.new-liveclass-name').val();
 
 
 let crt_room = {"name": display_name,
 "privacy": "public",
 "properties" : {
 "start_audio_off":true,
 "start_video_off":true,
 // nbf:start_unix,
 // exp:end_unix
 }}
 fetch("https://api.daily.co/v1/rooms/", {
 method: "POST",
 headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer a471ccb8f1587c7a95c5fdd63556391cf898fd210a997ae6635b2915b585dc10'}, 
 body: JSON.stringify(crt_room)
 }).then(function(res){ return res.json(); })
 .then(function(data){ 
 var lib_info = {
 'topic_name':display_name,
 'is_recurrence_meeting':false,
 'meeting_link':data.url
 };
 analytics.track('Created a LiveClass', lib_info);

 CreateLiveClassUtils.create(lib_info, function(errorMessage) {
 if(errorMessage.id==undefined)
 {
 var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
 $('.create-liveclass .wrap-error').addClass('is-shown');
 edx.HtmlUtils.setHtml($('#liveclass_creation_error'), msg);
 $('.new-liveclass-save').addClass('is-disabled').attr('aria-disabled', true);
 }
 else
 {
 alert('Live Class Created')
 localStorage.setItem('liveclass_id',errorMessage.id)
 }
 });
 
 }) 
 
 };

 var addNewLiveClass = function(e) {
 e.preventDefault();
 $('.new-liveclass-button').addClass('is-disabled').attr('aria-disabled', true);
 $('.new-liveclass-save').addClass('is-disabled').attr('aria-disabled', true);
 var $newLiveClass = $('.wrapper-create-liveclass').addClass('is-shown');
 var $cancelButton = $newLiveClass.find('.new-liveclass-cancel');
 $('.new-liveclass-save').on('click', saveNewLiveClass);
 
 $cancelButton.bind('click', makeCancelHandler('liveclass'));
 CancelOnEscape($cancelButton);
 CreateLiveClassUtils.configureHandlers();
 };
 var checkClass = function(e) {
 if(e.target.checked)
 {
 document.getElementById('field-liveclass-repeatcriteria').style.display = 'block';
 document.getElementById('field-liveclass-date').style.display = 'none'
 }
 else
 {
 document.getElementById('field-liveclass-repeatcriteria').style.display = 'none';
 document.getElementById('field-liveclass-date').style.display = 'block'
 }
 }
 var loadData = function(e) {
 var lib_info={}
 GetLiveClassUtils.create(lib_info, function(res,errorMessage) {
 //alert(res)
 });
 }
 var showTab = function(tab) {
 return function(e) {
 e.preventDefault();
 window.location.hash = tab;
 $('.courses-tab').toggleClass('active', tab === 'courses-tab');
 $('.archived-courses-tab').toggleClass('active', tab === 'archived-courses-tab');
 $('.libraries-tab').toggleClass('active', tab === 'libraries-tab');
 $('.liveclass-tab').toggleClass('active', tab === 'liveclass-tab');

 // Also toggle this course-related notice shown below the course tab, if it is present:
 $('.wrapper-creationrights').toggleClass('is-hidden', tab !== 'courses-tab');
 };
 };
 var libraryTab= function(tab) {
 var output = document.getElementById('output');
 output.style.display='none'
 }
 var courseTab= function(tab) {
 var output = document.getElementById('output');
 output.style.display='none'
 }

 var assignUsers= function(tab) {
 if(localStorage.getItem('liveclass_id')!=undefined)
 {
 let id = localStorage.getItem('liveclass_id');
 var username = document.getElementById('new-liveclass-username').value;
 GetLiveClassUtils.getUser({}, function(errorMessage) {
 
 var res = errorMessage.results;
//  alert(JSON.stringify(res)) 
 let data = res.filter((data)=>data['email']==username);
 
 if(data.length>0)
 {
 let info = {
 "user":data[0]['id'].toString(),
 "live_class":id.toString()
 }
 GetLiveClassUtils.assignUser(info, function(response) {
 alert("User Assigned")
 });
 
 }
 else
 {
 alert('User not exist')
 }
 });
 }
 }
 
 
 var onReady = function() {
 var courseTabHref = $('#course-index-tabs .courses-tab a').attr('href');
 var libraryTabHref = $('#course-index-tabs .libraries-tab a').attr('href');
 var ArchivedTabHref = $('#course-index-tabs .archived-courses-tab a').attr('href');
 var LiveClassTabHref = $('#course-index-tabs .liveclass-tab a').attr('href');
 
 $('.new-liveclass-recurrence').bind('click', checkClass);
 $('.new-course-button').bind('click', addNewCourse);
 $('.new-library-button').bind('click', addNewLibrary);
 $('.new-liveclass-button').bind('click', addNewLiveClass);
 $('.liveclass-tab').bind('click', loadData);
 $('.libraries-tab').bind('click', libraryTab);
 $('.courses-tab').bind('click', courseTab);
 $('.new-liveclass-repeattype').bind('click', courseTab);
 $('.new-liveclass-user').bind('click', assignUsers);
 
 
 $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function() {
 ViewUtils.reload();
 }));

 $('.action-reload').bind('click', ViewUtils.reload);

 if (courseTabHref === '#') {
 $('#course-index-tabs .courses-tab').bind('click', showTab('courses-tab'));
 }

 if (libraryTabHref === '#') {
 $('#course-index-tabs .libraries-tab').bind('click', showTab('libraries-tab'));
 }

 if (LiveClassTabHref === '#') {
 $('#course-index-tabs .liveclass-tab').bind('click', showTab('liveclass-tab'));
 }

 if (ArchivedTabHref === '#') {
 $('#course-index-tabs .archived-courses-tab').bind('click', showTab('archived-courses-tab'));
 }
 if (window.location.hash) {
 $(window.location.hash.replace('#', '.')).first('a').trigger('click');
 }
 };

 domReady(onReady);

 return {
 onReady: onReady
 };
 });