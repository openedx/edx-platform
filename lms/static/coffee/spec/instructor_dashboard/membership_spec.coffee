describe 'AutoEnrollment', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/autoenrollment.html'
    @autoenrollment = new AutoEnrollmentViaCsv $('.auto_enroll_csv')

  it 'binds to the enrollment_signup_button on click event', ->
    expect(@autoenrollment.$enrollment_signup_button).toHandle 'click'

  it 'binds to the browse button on change event', ->
    expect(@autoenrollment.$browse_button).toHandle 'change'

  it 'binds the ajax call and the result will be success', ->
    spyOn($, "ajax").andCallFake((params) =>
      params.success({row_errors: [], general_errors: [], warnings: []})
      {always: ->}
    )
    submitCallback = jasmine.createSpy().andReturn()
    @autoenrollment.$student_enrollment_form.submit(submitCallback)
    @autoenrollment.$enrollment_signup_button.click()
    expect($('.results .message-title').text()).toEqual('All accounts were created successfully.')
    expect(submitCallback).toHaveBeenCalled()

  it 'binds the ajax call and the result will be error', ->
    spyOn($, "ajax").andCallFake((params) =>
      params.success({
        row_errors: [{
          'username': 'testuser1',
          'email': 'testemail1@email.com',
          'response': 'Username already exists'
        }],
        general_errors: [{
          'response': 'cannot read the line 2'
        }],
        warnings: []
      })
      {always: ->}
    )

    submitCallback = jasmine.createSpy().andReturn()
    @autoenrollment.$student_enrollment_form.submit(submitCallback)
    @autoenrollment.$enrollment_signup_button.click()
    expect($('.results .list-summary').text()).toEqual('cannot read the line 2testuser1  (testemail1@email.com):     (Username already exists)');
    expect(submitCallback).toHaveBeenCalled()

  it 'binds the ajax call and the result will be warnings', ->
    spyOn($, "ajax").andCallFake((params) =>
      params.success({
        row_errors: [],
        general_errors: [],
        warnings: [{
          'username': 'user1',
          'email': 'user1email',
          'response': 'email is in valid'
        }]
      })
      {always: ->}
    )

    submitCallback = jasmine.createSpy().andReturn()
    @autoenrollment.$student_enrollment_form.submit(submitCallback)
    @autoenrollment.$enrollment_signup_button.click()
    expect($('.results .list-summary').text()).toEqual('user1  (user1email):     (email is in valid)')
    expect(submitCallback).toHaveBeenCalled()