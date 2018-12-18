

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n != 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "(filtered from _MAX_ total coupons)": "(filtered from _MAX_ total coupons)", 
    "(filtered from _MAX_ total courses)": "(filtered from _MAX_ total courses)", 
    "<Choose state/province>": "<Choose state/province>", 
    "A course with the specified ID already exists.": "A course with the specified ID already exists.", 
    "A valid Program UUID is required.": "A valid Program UUID is required.", 
    "A valid course ID is required": "A valid course ID is required", 
    "All course seats must have a price.": "All course seats must have a price.", 
    "All credit seats must designate a number of credit hours.": "All credit seats must designate a number of credit hours.", 
    "All credit seats must have a credit provider.": "All credit seats must have a credit provider.", 
    "An error occurred while attempting to process your payment. You have not been charged. Please check your payment details, and try again.": "An error occurred while attempting to process your payment. You have not been charged. Please check your payment details, and try again.", 
    "An error occurred while processing your payment. Please try again.": "An error occurred while processing your payment. Please try again.", 
    "An error occurred while processing your payment. You have NOT been charged. Please try again, or select another payment method.": "An error occurred while processing your payment. You have NOT been charged. Please try again, or select another payment method.", 
    "An error occurred while saving the data.": "An error occurred while saving the data.", 
    "Apple Pay is not available at this time. Please try another payment method.": "Apple Pay is not available at this time. Please try another payment method.", 
    "At least one seat type must be selected.": "At least one seat type must be selected.", 
    "Audit": "Audit", 
    "Can be used multiple times by multiple customers": "Can be used multiple times by multiple customers", 
    "Can be used once by multiple customers": "Can be used once by multiple customers", 
    "Can be used once by one customer": "Can be used once by one customer", 
    "Card expired": "Card expired", 
    "Category": "Category", 
    "Caution! Using the back button on this page may cause you to be charged again.": "Caution! Using the back button on this page may cause you to be charged again.", 
    "Client": "Client", 
    "Coupon Codes": "Coupon Codes", 
    "Coupon Report": "Coupon Report", 
    "Course": [
      "Course"
    ], 
    "Course ID": "Course ID", 
    "Course Name": "Course Name", 
    "Course Type": "Course Type", 
    "Courses": "Courses", 
    "Create Coupon": "Create Coupon", 
    "Create New Coupon": "Create New Coupon", 
    "Create New Course": "Create New Course", 
    "Created": "Created", 
    "Credit": "Credit", 
    "Custom Code": "Custom Code", 
    "Discount Code": "Discount Code", 
    "Display _MENU_ coupons": "Display _MENU_ coupons", 
    "Display _MENU_ courses": "Display _MENU_ courses", 
    "Displaying _START_ to _END_ of _TOTAL_ coupons": "Displaying _START_ to _END_ of _TOTAL_ coupons", 
    "Displaying _START_ to _END_ of _TOTAL_ courses": "Displaying _START_ to _END_ of _TOTAL_ courses", 
    "Edit Coupon": "Edit Coupon", 
    "Edit Course": "Edit Course", 
    "Ellipsis": "Ellipsis", 
    "Email domain {%s} is invalid.": "Email domain {%s} is invalid.", 
    "Enrollment Code": "Enrollment Code", 
    "Error": "Error", 
    "Error!": "Error!", 
    "Failed to fulfill order %(order_number)s: %(error)s": "Failed to fulfill order %(order_number)s: %(error)s", 
    "Failed to process refund #%(refund_id)s: %(error)s. Please try again, or contact the E-Commerce Development Team.": "Failed to process refund #%(refund_id)s: %(error)s. Please try again, or contact the E-Commerce Development Team.", 
    "Free (Audit)": "Free (Audit)", 
    "Free audit track. No certificate.": "Free audit track. No certificate.", 
    "Honor": "Honor", 
    "Honor Certificate": "Honor Certificate", 
    "Include Honor Seat": "Include Honor Seat", 
    "Invalid card number": "Invalid card number", 
    "Invalid month": "Invalid month", 
    "Invalid security number": "Invalid security number", 
    "Invalid year": "Invalid year", 
    "Last Edited": "Last Edited", 
    "Load the records for page ": "Load the records for page ", 
    "Load the records for the next page": "Load the records for the next page", 
    "Load the records for the previous page": "Load the records for the previous page", 
    "Max uses for multi-use coupons must be higher than 2.": "Max uses for multi-use coupons must be higher than 2.", 
    "Must occur after start date": "Must occur after start date", 
    "Must occur before end date": "Must occur before end date", 
    "Name": "Name", 
    "Next": "Next", 
    "No Certificate": "No Certificate", 
    "Order %(order_number)s has been fulfilled.": "Order %(order_number)s has been fulfilled.", 
    "Paid certificate track with initial verification and Professional Education Certificate": "Paid certificate track with initial verification and Professional Education Certificate", 
    "Paid certificate track with initial verification and Verified Certificate": "Paid certificate track with initial verification and Verified Certificate", 
    "Paid certificate track with initial verification and Verified Certificate, and option to purchase credit": "Paid certificate track with initial verification and Verified Certificate, and option to purchase credit", 
    "Please complete all required fields.": "Please complete all required fields.", 
    "Please select a valid credit provider.": "Please select a valid credit provider.", 
    "Previous": "Previous", 
    "Problem occurred during checkout. Please contact support.": "Problem occurred during checkout. Please contact support.", 
    "Product validation failed.": "Product validation failed.", 
    "Professional": "Professional", 
    "Professional Certificate": "Professional Certificate", 
    "Professional Education": "Professional Education", 
    "Redeem": "Redeem", 
    "Refund #%(refund_id)s has been processed.": "Refund #%(refund_id)s has been processed.", 
    "Save Changes": "Save Changes", 
    "Saving...": "Saving...", 
    "Search...": "Search...", 
    "Seat title": "Seat title", 
    "Seat type": "Seat type", 
    "Select": "Select", 
    "Selected": "Selected", 
    "State/Province (required)": "State/Province (required)", 
    "The upgrade deadline must occur BEFORE the verification deadline.": "The upgrade deadline must occur BEFORE the verification deadline.", 
    "The verification deadline must occur AFTER the upgrade deadline.": "The verification deadline must occur AFTER the upgrade deadline.", 
    "This field is required": "This field is required", 
    "This field is required.": "This field is required.", 
    "This field must be empty or contain 1-16 alphanumeric characters.": "This field must be empty or contain 1-16 alphanumeric characters.", 
    "This value must be a date.": "This value must be a date.", 
    "This value must be a number.": "This value must be a number.", 
    "Trailing comma not allowed.": "Trailing comma not allowed.", 
    "Unsupported card type": "Unsupported card type", 
    "Verification Deadline": "Verification Deadline", 
    "Verified": "Verified", 
    "Verified Certificate": "Verified Certificate", 
    "Verified seats must have an upgrade deadline.": "Verified seats must have an upgrade deadline.", 
    "View Coupon": "View Coupon", 
    "View Course": "View Course", 
    "You must choose if an honor seat should be created.": "You must choose if an honor seat should be created.", 
    "You must select a course type.": "You must select a course type."
  };
  for (var key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      var value = django.catalog[msgid];
      if (typeof(value) == 'undefined') {
        return msgid;
      } else {
        return (typeof(value) == 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      var value = django.catalog[singular];
      if (typeof(value) == 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value[django.pluralidx(count)];
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      var value = django.gettext(context + '\x04' + msgid);
      if (value.indexOf('\x04') != -1) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.indexOf('\x04') != -1) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "N j, Y, P", 
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S", 
      "%Y-%m-%d %H:%M:%S.%f", 
      "%Y-%m-%d %H:%M", 
      "%Y-%m-%d", 
      "%m/%d/%Y %H:%M:%S", 
      "%m/%d/%Y %H:%M:%S.%f", 
      "%m/%d/%Y %H:%M", 
      "%m/%d/%Y", 
      "%m/%d/%y %H:%M:%S", 
      "%m/%d/%y %H:%M:%S.%f", 
      "%m/%d/%y %H:%M", 
      "%m/%d/%y"
    ], 
    "DATE_FORMAT": "N j, Y", 
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d", 
      "%m/%d/%Y", 
      "%m/%d/%y"
    ], 
    "DECIMAL_SEPARATOR": ".", 
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "F j", 
    "NUMBER_GROUPING": "3", 
    "SHORT_DATETIME_FORMAT": "m/d/Y P", 
    "SHORT_DATE_FORMAT": "m/d/Y", 
    "THOUSAND_SEPARATOR": ",", 
    "TIME_FORMAT": "P", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "F Y"
  };

    django.get_format = function(format_type) {
      var value = django.formats[format_type];
      if (typeof(value) == 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }

}(this));

