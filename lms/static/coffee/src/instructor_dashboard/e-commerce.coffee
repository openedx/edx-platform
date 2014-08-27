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
    @$list_sale_csv_btn = @$section.find("input[name='list-sale-csv']'")
    @$download_company_name = @$section.find("input[name='download_company_name']'")
    @$active_company_name = @$section.find("input[name='active_company_name']'")
    @$spent_company_name = @$section.find('input[name="spent_company_name"]')
    @$download_coupon_codes = @$section.find('input[name="download-coupon-codes-csv"]')
    
    @$download_registration_codes_form = @$section.find("form#download_registration_codes")
    @$active_registration_codes_form = @$section.find("form#active_registration_codes")
    @$spent_registration_codes_form = @$section.find("form#spent_registration_codes")

    @$error_msg = @$section.find('#error-msg')
    
    # attach click handlers
    # this handler binds to both the download
    # and the csv button
    @$list_purchase_csv_btn.click (e) =>
      url = @$list_purchase_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url
    
    @$list_sale_csv_btn.click (e) =>
      url = @$list_sale_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url

    @$download_coupon_codes.click (e) =>
      url = @$download_coupon_codes.data 'endpoint'
      location.href = url

    @$download_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

    @$active_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

    @$spent_registration_codes_form.submit (e) =>
      @$error_msg.attr('style', 'display: none')
      return true

  # handler for when the section title is clicked.
  onClickTitle: ->
    @clear_display()

  # handler for when the section title is clicked.
  onClickTitle: -> @clear_display()

  # handler for when the section is closed
  onExit: -> @clear_display()

  clear_display: ->
    @$error_msg.attr('style', 'display: none')
    @$download_company_name.val('')
    @$active_company_name.val('')
    @$spent_company_name.val('')

  isInt = (n) -> return n % 1 == 0;
    # Clear any generated tables, warning messages, etc.

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
   ECommerce:  ECommerce