describe "Bulk Email Queueing", ->
    beforeEach ->
        testSubject = "Test Subject"
        testBody =  "Hello, World! This is a test email message!"
        loadFixtures 'coffee/fixtures/send_email.html'
        @send_email = new SendEmail $('.send-email')
        @send_email.$subject.val(testSubject)
        @send_email.$send_to.first().prop("checked", true)
        @send_email.$emailEditor =
            save: ->
                {"data": testBody}
        @ajax_params = {
            type: "POST",
            dataType: "json",
            url: undefined,
            data: {
                action: "send",
                send_to: JSON.stringify([@send_email.$send_to.first().val()]),
                subject: testSubject,
                message: testBody,
            },
            success: jasmine.any(Function),
            error: jasmine.any(Function),
        }

    it 'cannot send an email with no target', ->
        spyOn(window, "alert")
        spyOn($, "ajax")
        for target in @send_email.$send_to
            target.checked = false
        @send_email.$btn_send.click()
        expect(window.alert).toHaveBeenCalledWith("Your message must have at least one target.")
        expect($.ajax).not.toHaveBeenCalled()

    it 'cannot send an email with no subject', ->
        spyOn(window, "alert")
        spyOn($, "ajax")
        @send_email.$subject.val("")
        @send_email.$btn_send.click()
        expect(window.alert).toHaveBeenCalledWith("Your message must have a subject.")
        expect($.ajax).not.toHaveBeenCalled()

    it 'cannot send an email with no message', ->
        spyOn(window, "alert")
        spyOn($, "ajax")
        @send_email.$emailEditor =
            save: ->
                {"data": ""}
        @send_email.$btn_send.click()
        expect(window.alert).toHaveBeenCalledWith("Your message cannot be blank.")
        expect($.ajax).not.toHaveBeenCalled()

    it 'can send a simple message to a single target', ->
        spyOn($, "ajax").and.callFake((params) =>
          params.success()
        )
        @send_email.$btn_send.click()
        expect($('.msg-confirm').text()).toEqual('Your email message was successfully queued for sending. In courses with a large number of learners, email messages to learners might take up to an hour to be sent.')
        expect($.ajax).toHaveBeenCalledWith(@ajax_params)

    it 'can send a simple message to a multiple targets', ->
        spyOn($, "ajax").and.callFake((params) =>
            params.success()
        )
        @ajax_params.data.send_to = JSON.stringify(target.value for target in @send_email.$send_to)
        for target in @send_email.$send_to
            target.checked = true
        @send_email.$btn_send.click()
        expect($('.msg-confirm').text()).toEqual('Your email message was successfully queued for sending. In courses with a large number of learners, email messages to learners might take up to an hour to be sent.')
        expect($.ajax).toHaveBeenCalledWith(@ajax_params)

    it 'can handle an error result from the bulk email api', ->
        spyOn($, "ajax").and.callFake((params) =>
            params.error()
        )
        spyOn(console, "warn")
        @send_email.$btn_send.click()
        expect($('.request-response-error').text()).toEqual('Error sending email.')
        expect(console.warn).toHaveBeenCalled()
