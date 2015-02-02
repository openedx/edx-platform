describe 'StudentAdmin', ->
  studentadmin = {}
  beforeEach =>
    loadFixtures 'coffee/fixtures/student_admin.html'
    # have initialize InstructorDashboard.util.PendingInstructorTasks
    # since it is user in construct of StudentAdmin
    window.InstructorDashboard = {}
    window.InstructorDashboard.util =
      std_ajax_err: std_ajax_err
      PendingInstructorTasks: PendingInstructorTasks
      create_task_list_table: create_task_list_table

    studentadmin = new StudentAdmin $('#student_admin')
  it 'expects student admin container to be visible', ->
    expect($('#student_admin')).toBeVisible()

  describe 'EntranceExam', =>
    it 'Expects student identified input to be visible', =>
      expect(studentadmin.$field_entrance_exam_student_select_grade).toBeVisible()

    it 'binds to the btn_reset_entrance_exam_attempts on click event', =>
      expect(studentadmin.$btn_reset_entrance_exam_attempts).toHandle 'click'

    it 'binds to the btn_delete_entrance_exam_state on click event', =>
      expect(studentadmin.$btn_delete_entrance_exam_state).toHandle 'click'

    it 'binds to the btn_rescore_entrance_exam on click event', =>
      expect(studentadmin.$btn_rescore_entrance_exam).toHandle 'click'

    it 'binds to the $btn_entrance_exam_task_history on click event', =>
      expect(studentadmin.$btn_entrance_exam_task_history).toHandle 'click'

    it 'binds to the btn_rescore_entrance_exam on click event', =>
      expect(studentadmin.$btn_rescore_entrance_exam).toHandle 'click'

    it 'Expects student task history table to be visible', =>
      expect(studentadmin.$table_entrance_exam_task_history).toBeVisible()


    it 'binds reset entrance exam ajax call and the result will be success', =>
      studentadmin.$btn_reset_entrance_exam_attempts.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(
        gettext("Please enter a student email address or username.")
      )

      spyOn($, "ajax").andCallFake((params) =>
        params.success({})
      )
      alert_msg = ''
      spyOn(window, 'alert').andCallFake((message) =>
        alert_msg = message
      )

      unique_student_identifier = "john@example.com"
      success_message = gettext("Entrance exam attempts is being reset for student '{student_id}'.")
      full_success_message = interpolate_text(success_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_reset_entrance_exam_attempts.click()
      expect(alert_msg).toEqual(full_success_message)

    it 'binds reset entrance exam ajax call and the result will be error', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.error({})
      )

      unique_student_identifier = "invalid_user"
      error_message = gettext("Error resetting entrance exam attempts for student '{student_id}'. Make sure student identifier is correct.")
      full_error_message = interpolate_text(error_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_reset_entrance_exam_attempts.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message)

    it 'binds rescore entrance exam ajax call and the result will be success', =>
      studentadmin.$btn_rescore_entrance_exam.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(
        gettext("Please enter a student email address or username.")
      )

      spyOn($, "ajax").andCallFake((params) =>
        params.success({})
      )
      alert_msg = ''
      spyOn(window, 'alert').andCallFake((message) =>
        alert_msg = message
      )

      unique_student_identifier = "john@example.com"
      success_message = gettext("Started entrance exam rescore task for student '{student_id}'. Click the 'Show Background Task History for Student' button to see the status of the task.")
      full_success_message = interpolate_text(success_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_rescore_entrance_exam.click()
      expect(alert_msg).toEqual(full_success_message)

    it 'binds rescore entrance exam ajax call and the result will be error', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.error({})
      )

      unique_student_identifier = "invalid_user"
      error_message = gettext("Error starting a task to rescore entrance exam for student '{student_id}'. Make sure that entrance exam has problems in it and student identifier is correct.")
      full_error_message = interpolate_text(error_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_rescore_entrance_exam.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message)

    it 'binds delete student state for entrance exam ajax call and the result will be success', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.success({})
      )
      alert_msg = ''
      spyOn(window, 'alert').andCallFake((message) =>
        alert_msg = message
      )

      unique_student_identifier = "john@example.com"
      success_message = gettext("Entrance exam state is being deleted for student '{student_id}'.")
      full_success_message = interpolate_text(success_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_delete_entrance_exam_state.click()
      expect(alert_msg).toEqual(full_success_message)

    it 'binds delete student state for entrance exam ajax call and the result will be error', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.error({})
      )

      unique_student_identifier = "invalid_user"
      error_message = gettext("Error deleting entrance exam state for student '{student_id}'. Make sure student identifier is correct.")
      full_error_message = interpolate_text(error_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_delete_entrance_exam_state.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message)

    it 'binds list entrance exam task history ajax call and the result will be success', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.success({'tasks':[]})
      )
      success_message = ''
      spyOn(window.InstructorDashboard.util, 'create_task_list_table').andCallFake( =>
        success_message = 'Task table shown'
      )

      create_task_list_table = jasmine.createSpy().andReturn()
      unique_student_identifier = "john@example.com"
      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_entrance_exam_task_history.click()
      expect(success_message).toEqual('Task table shown')

    it 'binds list entrance exam task history ajax call and the result will be error', =>
      spyOn($, "ajax").andCallFake((params) =>
        params.error({})
      )

      unique_student_identifier = "invalid_user"
      error_message = gettext("Error getting entrance exam task history for student '{student_id}'. Make sure student identifier is correct.")
      full_error_message = interpolate_text(error_message, {student_id: unique_student_identifier})

      studentadmin.$field_entrance_exam_student_select_grade.val(unique_student_identifier)
      studentadmin.$btn_entrance_exam_task_history.click()
      expect(studentadmin.$request_response_error_ee.text()).toEqual(full_error_message)
