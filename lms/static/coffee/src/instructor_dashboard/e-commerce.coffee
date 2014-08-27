###
E-Commerce Section
###

class ECommerce
# E-Commerce Section
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @
    # gather elements
    @$list_purchase_csv_btn = @$section.find("input[name='list-purchase-transaction-csv']'")
    @$transaction_group_name = @$section.find("input[name='transaction_group_name']'")
    @$course_registration_number = @$section.find("input[name='course_registration_code_number']'")
    @$download_transaction_group_name = @$section.find("input[name='download_transaction_group_name']'")
    @$active_transaction_group_name = @$section.find("input[name='active_transaction_group_name']'")
    @$spent_transaction_group_name = @$section.find('input[name="spent_transaction_group_name"]')

    @$generate_registration_code_form = @$section.find("form#course_codes_number")
    @$download_registration_codes_form = @$section.find("form#download_registration_codes")
    @$active_registration_codes_form = @$section.find("form#active_registration_codes")
    @$spent_registration_codes_form = @$section.find("form#spent_registration_codes")

    @$coupoon_error = @$section.find('#coupon-error')
    @$course_code_error = @$section.find('#code-error')
    
    # attach click handlers
    # this handler binds to both the download
    # and the csv button
    @$list_purchase_csv_btn.click (e) =>
      url = @$list_purchase_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url

    @$download_registration_codes_form.submit (e) =>
      @$course_code_error.attr('style', 'display: none')
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$active_registration_codes_form.submit (e) =>
      @$course_code_error.attr('style', 'display: none')
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$spent_registration_codes_form.submit (e) =>
      @$course_code_error.attr('style', 'display: none')
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$generate_registration_code_form.submit (e) =>
      @$course_code_error.attr('style', 'display: none')
      @$coupoon_error.attr('style', 'display: none')
      group_name = @$transaction_group_name.val()
      if group_name == ''
        @$course_code_error.html('Please Enter the Transaction Group Name').show()
        return false

      if ($.isNumeric(group_name))
        @$course_code_error.html('Please Enter the non-numeric value for Transaction Group Name').show()
        return false;

      registration_codes = @$course_registration_number.val();
      if (isInt(registration_codes) && $.isNumeric(registration_codes))
        if (parseInt(registration_codes) > 1000 )
          @$course_code_error.html('You can only generate 1000 Registration Codes at a time').show()
          return false;
        if (parseInt(registration_codes) == 0 )
          @$course_code_error.html('Please Enter the Value greater than 0 for Registration Codes').show()
          return false;
        return true;
      else
        @$course_code_error.html('Please Enter the Integer Value for Registration Codes').show()
        return false;

  # handler for when the section title is clicked.
  onClickTitle: ->
    @clear_display()

  # handler for when the section title is clicked.
  onClickTitle: -> @clear_display()

  # handler for when the section is closed
  onExit: -> @clear_display()

  clear_display: ->
    @$course_code_error.attr('style', 'display: none')
    @$coupoon_error.attr('style', 'display: none')
    @$course_registration_number.val('')
    @$transaction_group_name.val('')
    @$download_transaction_group_name.val('')
    @$active_transaction_group_name.val('')
    @$spent_transaction_group_name.val('')


  isInt = (n) -> return n % 1 == 0;
    # Clear any generated tables, warning messages, etc.

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
   ECommerce:  ECommerce