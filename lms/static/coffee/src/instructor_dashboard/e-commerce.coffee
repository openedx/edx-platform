###
E-Commerce Download Section
###

# Ecommerce Purchase Download Section
class ECommerce
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # gather elements
    @$list_purchase_csv_btn = @$section.find("input[name='list-purchase-transaction-csv']'")

    # attach click handlers
    # this handler binds to both the download
    # and the csv button
    @$list_purchase_csv_btn.click (e) =>
      url = @$list_purchase_csv_btn.data 'endpoint'
      url += '/csv'
      location.href = url


  # handler for when the section title is clicked.
  onClickTitle: ->
    @clear_display()

  clear_display: ->


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  ECommerce: ECommerce
