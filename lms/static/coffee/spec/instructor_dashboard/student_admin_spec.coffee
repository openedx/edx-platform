describe 'StudentAdmin', ->
  studentadmin = {}
  beforeEach =>
    loadFixtures 'coffee/fixtures/student_admin.html'
    # have initialize InstructorDashboard.util.PendingInstructorTasks
    # since it is user in construct of StudentAdmin
    window.InstructorDashboard = {}
    window.InstructorDashboard.util =
      PendingInstructorTasks: PendingInstructorTasks

    studentadmin = new StudentAdmin $('#student_admin')
  it 'expects student admin container to be visible', ->
    expect($('#student_admin')).toBeVisible()

  describe 'EntranceExam', =>
    it 'binds to the btn_reset_entrance_exam_attempts on click event', =>
      expect(studentadmin.$btn_reset_entrance_exam_attempts).toHandle 'click'

