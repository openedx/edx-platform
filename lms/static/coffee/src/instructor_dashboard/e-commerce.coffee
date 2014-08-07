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
    @$download_transaction_group_name = @$section.find("input[name='download_transaction_group_name']'")
    @$active_transaction_group_name = @$section.find("input[name='active_transaction_group_name']'")
    @$spent_transaction_group_name = @$section.find('input[name="spent_transaction_group_name"]')

    @$generate_registration_code_form = @$section.find("form#generate_codes")
    @$download_registration_codes_form = @$section.find("form#download_registration_codes")
    @$active_registration_codes_form = @$section.find("form#active_registration_codes")
    @$spent_registration_codes_form = @$section.find("form#spent_registration_codes")

    @$generate_registration_button = @$section.find('input[name="generate-registration-codes-csv"]')

    @$coupoon_error = @$section.find('#coupon-error')
    @$registration_code_error = @$section.find('#generate_codes #registration_code_form_error')
    
    # attach click handlers
    # this handler binds to both the download
    # and the csv button
    @$list_purchase_csv_btn.click (e) =>
      url = @$list_purchase_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url

    @$download_registration_codes_form.submit (e) =>
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$active_registration_codes_form.submit (e) =>
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$spent_registration_codes_form.submit (e) =>
      @$coupoon_error.attr('style', 'display: none')
      return true

    @$generate_registration_code_form.submit (e) =>
      @$registration_code_error.attr('style', 'display: none')
      @$generate_registration_button.attr('disabled', true)
      company_name = @$section.find('input[name="company_name"]').val()
      @$coupoon_error.attr('style', 'display: none')
      total_registration_codes = @$section.find('input[name="total-registration-codes"]').val()
      purchaser_contact = @$section.find('input[name="purchaser_contact"]').val()
      sale_price = @$section.find('input[name="sale_price"]').val()
      purchaser_name = @$section.find('input[name="purchaser_name"]').val()
      purchaser_email = @$section.find('input[name="purchaser_email"]').val()

      if (company_name == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Company Name')
        @$generate_registration_button.removeAttr('disabled')
        return false

      if ($.isNumeric(company_name))
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the non-numeric value for Company Name')
        @$generate_registration_button.removeAttr('disabled')
        return false

      if (sale_price == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Sale Price')
        @$generate_registration_button.removeAttr('disabled')
        return false

      if (!($.isNumeric(sale_price)))
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the numeric value for Sale Price')
        @$generate_registration_button.removeAttr('disabled')
        return false

      if (total_registration_codes == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Total Registration Codes')
        @$generate_registration_button.removeAttr('disabled')
        return false

      if (!($.isNumeric(total_registration_codes)))
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the numeric value for Total Registration Codes')
        @$generate_registration_button.removeAttr('disabled')
        return false;

      if (purchaser_contact == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Purchaser Contact')
        @$generate_registration_button.removeAttr('disabled')
        return false;

      if (purchaser_name == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Purchaser Name')
        @$generate_registration_button.removeAttr('disabled')
        return false;

      if (purchaser_email == '')
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the Purchaser Email')
        @$generate_registration_button.removeAttr('disabled')
        return false;

      if (!(validateEmail(purchaser_email)))
        @$registration_code_error.attr('style', 'display: block !important')
        @$registration_code_error.text('Please Enter the valid email address of Purchase')
        @$generate_registration_button.removeAttr('disabled')

  # handler for when the section title is clicked.
  onClickTitle: ->
    @clear_display()

  # handler for when the section title is clicked.
  onClickTitle: -> @clear_display()

  # handler for when the section is closed
  onExit: -> @clear_display()

  clear_display: ->
    @$coupoon_error.attr('style', 'display: none')
    @$download_transaction_group_name.val('')
    @$active_transaction_group_name.val('')
    @$spent_transaction_group_name.val('')

  validateEmail = (sEmail) ->
    filter = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/
    return filter.test(sEmail)

  isInt = (n) -> return n % 1 == 0;
    # Clear any generated tables, warning messages, etc.

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
   ECommerce:  ECommerce