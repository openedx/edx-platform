/* global define, DataDownload */

define([
    'jquery',
    'js/instructor_dashboard/data_download_2',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
],
  function($, id, AjaxHelper) {
      'use strict';
      describe('edx.instructor_dashboard.data_download', function() {
          var requests, $selected, dataDownload, url, errorMessage;

          beforeEach(function() {
              loadFixtures('js/fixtures/instructor_dashboard/data_download.html');

              dataDownload = window.InstructorDashboard.sections;
              dataDownload.DataDownloadV2($('#data_download_2'));
              window.InstructorDashboard.util.PendingInstructorTasks = function() {
                  return;
              };
              requests = AjaxHelper.requests(this);
              $selected = $('<option data-endpoint="api/url/fake"></option>');
              url = $selected.data('endpoint');
              errorMessage = 'An Error is occurred with request';
          });

          it('renders success message properly', function() {
              dataDownload.downloadCSV($selected, errorMessage);

              AjaxHelper.expectRequest(requests, 'POST', url);
              AjaxHelper.respondWithJson(requests, {
                  status: 'Request is succeeded'
              });
              expect(dataDownload.$reports_request_response.text()).toContain('Request is succeeded');
          });


          it('renders grading config returned by the server in case of successful request ', function() {
              dataDownload.downloadCSV($selected, errorMessage);

              AjaxHelper.expectRequest(requests, 'POST', url);
              AjaxHelper.respondWithJson(requests, {
                  grading_config_summary: 'This is grading config'
              });
              expect(dataDownload.$download_display_text.text()).toContain('This is grading config');
          });

          it('renders enrolled student list in case of successful request ', function() {
              var data = {
                  available_features: [
                      'id',
                      'username',
                      'first_name',
                      'last_name',
                      'is_staff',
                      'email',
                      'date_joined',
                      'last_login',
                      'name',
                      'language',
                      'location',
                      'year_of_birth',
                      'gender',
                      'level_of_education',
                      'mailing_address',
                      'goals',
                      'meta',
                      'city',
                      'country'
                  ],
                  course_id: 'test_course_101',
                  feature_names: {
                      gender: 'Gender',
                      goals: 'Goals',
                      enrollment_mode: 'Enrollment Mode',
                      email: 'Email',
                      country: 'Country',
                      id: 'User ID',
                      mailing_address: 'Mailing Address',
                      last_login: 'Last Login',
                      date_joined: 'Date Joined',
                      location: 'Location',
                      city: 'City',
                      verification_status: 'Verification Status',
                      year_of_birth: 'Birth Year',
                      name: 'Name',
                      username: 'Username',
                      level_of_education: 'Level of Education',
                      language: 'Language'
                  },
                  students: [
                      {
                          gender: 'Male',
                          goals: 'Goal',
                          enrollment_mode: 'audit',
                          email: 'test@example.com',
                          country: 'PK',
                          year_of_birth: 'None',
                          id: '8',
                          mailing_address: 'None',
                          last_login: '2020-06-17T08:17:00.561Z',
                          date_joined: '2019-09-25T20:06:17.564Z',
                          location: 'None',
                          verification_status: 'N/A',
                          city: 'None',
                          name: 'None',
                          username: 'test',
                          level_of_education: 'None',
                          language: 'None'
                      }
                  ],
                  queried_features: [
                      'id',
                      'username',
                      'name',
                      'email',
                      'language',
                      'location',
                      'year_of_birth',
                      'gender',
                      'level_of_education',
                      'mailing_address',
                      'goals',
                      'enrollment_mode',
                      'verification_status',
                      'last_login',
                      'date_joined',
                      'city',
                      'country'
                  ],
                  students_count: 1
              };
              dataDownload.renderDataTable($selected, errorMessage);
              AjaxHelper.expectRequest(requests, 'POST', url);
              AjaxHelper.respondWithJson(requests, data);
            // eslint-disable-next-line vars-on-top
              var dataTable = dataDownload.$data_display_table.html();
            // eslint-disable-next-line vars-on-top
              var existInHtml = function(value) {
                  expect(dataTable.indexOf(data.feature_names[value]) !== -1).toBe(false);
                  expect(dataTable.indexOf(data.students[0][value]) !== -1).toBe(false);
              };
              data.queried_features.forEach(existInHtml);
          });


          it('calls renderDataTable function if data-datatable is true', function() {
              $selected = $selected.attr('data-datatable', true);
              spyOn(dataDownload, 'selectedOption').and.returnValue($selected);
              spyOn(dataDownload, 'renderDataTable');
              dataDownload.downloadReportClickHandler();
              expect(dataDownload.renderDataTable).toHaveBeenCalled();
          });

          it('calls downloadCSV function if no other data type is specified', function() {
              spyOn(dataDownload, 'selectedOption').and.returnValue($selected);
              spyOn(dataDownload, 'downloadCSV');
              dataDownload.downloadReportClickHandler();
              expect(dataDownload.downloadCSV).toHaveBeenCalled();
          });
      });
  });
