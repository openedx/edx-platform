

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
    "%(sel)s of %(cnt)s selected": [
      "%(cnt)s\u0d32\u0d4d\u200d %(sel)s \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d24\u0d4d\u0d24\u0d41",
      "%(cnt)s\u0d32\u0d4d\u200d %(sel)s \u0d0e\u0d23\u0d4d\u0d23\u0d02 \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d24\u0d4d\u0d24\u0d41"
    ],
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m",
    "April": "\u0d0f\u0d2a\u0d4d\u0d30\u0d3f\u0d7d",
    "August": "\u0d06\u0d17\u0d38\u0d4d\u0d31\u0d4d\u0d31\u0d4d",
    "Available %s": "\u0d32\u0d2d\u0d4d\u0d2f\u0d2e\u0d3e\u0d2f %s",
    "Cancel": "\u0d31\u0d26\u0d4d\u0d26\u0d3e\u0d15\u0d4d\u0d15\u0d42",
    "Choose": "\u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d42",
    "Choose a Date": "\u0d12\u0d30\u0d41 \u0d24\u0d40\u0d2f\u0d24\u0d3f \u0d24\u0d3f\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d41\u0d15",
    "Choose a Time": "\u0d38\u0d2e\u0d2f\u0d02 \u0d24\u0d3f\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d41\u0d15",
    "Choose a time": "\u0d38\u0d2e\u0d2f\u0d02 \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d42",
    "Choose all": "\u0d0e\u0d32\u0d4d\u0d32\u0d3e\u0d02 \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d41\u0d15",
    "Chosen %s": "\u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d24\u0d4d\u0d24 %s",
    "Click to choose all %s at once.": "%s \u0d0e\u0d32\u0d4d\u0d32\u0d3e\u0d02 \u0d12\u0d28\u0d4d\u0d28\u0d3f\u0d1a\u0d4d\u0d1a\u0d4d \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d3e\u0d28\u0d4d\u200d \u0d15\u0d4d\u0d32\u0d3f\u0d15\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15.",
    "Click to remove all chosen %s at once.": "\u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d2a\u0d4d\u0d2a\u0d46\u0d1f\u0d4d\u0d1f %s \u0d0e\u0d32\u0d4d\u0d32\u0d3e\u0d02 \u0d12\u0d30\u0d41\u0d2e\u0d3f\u0d1a\u0d4d\u0d1a\u0d4d \u0d28\u0d40\u0d15\u0d4d\u0d15\u0d02 \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d3e\u0d28\u0d4d\u200d \u0d15\u0d4d\u0d32\u0d3f\u0d15\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15.",
    "December": "\u0d21\u0d3f\u0d38\u0d02\u0d2c\u0d30\u0d4d",
    "February": "\u0d2b\u0d46\u0d2c\u0d4d\u0d30\u0d41\u0d35\u0d30\u0d3f",
    "Filter": "Filter",
    "Hide": "\u0d2e\u0d31\u0d2f\u0d1f\u0d4d\u0d1f\u0d46",
    "January": "\u0d1c\u0d28\u0d41\u0d35\u0d30\u0d3f",
    "July": "\u0d1c\u0d42\u0d32\u0d48",
    "June": "\u0d1c\u0d42\u0d7a",
    "March": "\u0d2e\u0d3e\u0d7c\u0d1a\u0d4d\u0d1a\u0d4d",
    "May": "\u0d2e\u0d46\u0d2f\u0d4d",
    "Midnight": "\u0d05\u0d30\u0d4d\u200d\u0d27\u0d30\u0d3e\u0d24\u0d4d\u0d30\u0d3f",
    "Noon": "\u0d09\u0d1a\u0d4d\u0d1a",
    "Note: You are %s hour ahead of server time.": [
      "\u0d12\u0d7c\u0d15\u0d4d\u0d15\u0d41\u0d15: \u0d38\u0d46\u0d7c\u0d35\u0d7c \u0d38\u0d2e\u0d2f\u0d24\u0d4d\u0d24\u0d3f\u0d28\u0d46\u0d15\u0d4d\u0d15\u0d3e\u0d33\u0d41\u0d02 \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d7e %s \u0d38\u0d2e\u0d2f\u0d02 \u0d2e\u0d41\u0d7b\u0d2a\u0d3f\u0d32\u0d3e\u0d23\u0d4d.",
      "\u0d12\u0d7c\u0d15\u0d4d\u0d15\u0d41\u0d15: \u0d38\u0d46\u0d7c\u0d35\u0d7c \u0d38\u0d2e\u0d2f\u0d24\u0d4d\u0d24\u0d3f\u0d28\u0d46\u0d15\u0d4d\u0d15\u0d3e\u0d33\u0d41\u0d02 \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d7e %s \u0d38\u0d2e\u0d2f\u0d02 \u0d2e\u0d41\u0d7b\u0d2a\u0d3f\u0d32\u0d3e\u0d23\u0d4d."
    ],
    "Note: You are %s hour behind server time.": [
      "\u0d12\u0d7c\u0d15\u0d4d\u0d15\u0d41\u0d15: \u0d38\u0d46\u0d7c\u0d35\u0d7c \u0d38\u0d2e\u0d2f\u0d24\u0d4d\u0d24\u0d3f\u0d28\u0d46\u0d15\u0d4d\u0d15\u0d3e\u0d33\u0d41\u0d02 \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d7e %s \u0d38\u0d2e\u0d2f\u0d02 \u0d2a\u0d3f\u0d28\u0d4d\u0d28\u0d3f\u0d32\u0d3e\u0d23\u0d4d.",
      "\u0d12\u0d7c\u0d15\u0d4d\u0d15\u0d41\u0d15: \u0d38\u0d46\u0d7c\u0d35\u0d7c \u0d38\u0d2e\u0d2f\u0d24\u0d4d\u0d24\u0d3f\u0d28\u0d46\u0d15\u0d4d\u0d15\u0d3e\u0d33\u0d41\u0d02 \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d7e %s \u0d38\u0d2e\u0d2f\u0d02 \u0d2a\u0d3f\u0d28\u0d4d\u0d28\u0d3f\u0d32\u0d3e\u0d23\u0d4d."
    ],
    "November": "\u0d28\u0d35\u0d02\u0d2c\u0d7c",
    "Now": "\u0d07\u0d2a\u0d4d\u0d2a\u0d4b\u0d33\u0d4d\u200d",
    "October": "\u0d12\u0d15\u0d4d\u0d1f\u0d47\u0d3e\u0d2c\u0d7c",
    "Remove": "\u0d28\u0d40\u0d15\u0d4d\u0d15\u0d02 \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d42",
    "Remove all": "\u0d0e\u0d32\u0d4d\u0d32\u0d3e\u0d02 \u0d28\u0d40\u0d15\u0d4d\u0d15\u0d02 \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15",
    "September": "\u0d38\u0d46\u0d2a\u0d4d\u0d31\u0d4d\u0d31\u0d02\u0d2c\u0d7c",
    "Show": "\u0d15\u0d3e\u0d23\u0d1f\u0d4d\u0d1f\u0d46",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u0d07\u0d24\u0d3e\u0d23\u0d4d \u0d32\u0d2d\u0d4d\u0d2f\u0d2e\u0d3e\u0d2f %s \u0d2a\u0d1f\u0d4d\u0d1f\u0d3f\u0d15. \u0d05\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d1a\u0d3f\u0d32\u0d24\u0d4d \u0d24\u0d3f\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d3e\u0d28\u0d4d\u200d \u0d24\u0d3e\u0d34\u0d46 \u0d15\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d28\u0d3f\u0d28\u0d4d\u0d28\u0d41\u0d02 \u0d09\u0d1a\u0d3f\u0d24\u0d2e\u0d3e\u0d2f\u0d35 \u0d38\u0d46\u0d32\u0d15\u0d4d\u0d1f\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d24 \u0d36\u0d47\u0d37\u0d02 \u0d30\u0d23\u0d4d\u0d1f\u0d41 \u0d15\u0d33\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d\u0d15\u0d4d\u0d15\u0d41\u0d2e\u0d3f\u0d1f\u0d2f\u0d3f\u0d32\u0d46 \"\u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d42\" \u0d05\u0d1f\u0d2f\u0d3e\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d15\u0d4d\u0d32\u0d3f\u0d15\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d2a\u0d4d\u0d2a\u0d46\u0d1f\u0d4d\u0d1f %s \u0d2a\u0d1f\u0d4d\u0d1f\u0d3f\u0d15\u0d2f\u0d3e\u0d23\u0d3f\u0d24\u0d4d. \u0d05\u0d35\u0d2f\u0d3f\u0d32\u0d4d\u200d \u0d1a\u0d3f\u0d32\u0d24\u0d4d \u0d12\u0d34\u0d3f\u0d35\u0d3e\u0d15\u0d4d\u0d15\u0d23\u0d2e\u0d46\u0d28\u0d4d\u0d28\u0d41\u0d23\u0d4d\u0d1f\u0d46\u0d19\u0d4d\u0d15\u0d3f\u0d32\u0d4d\u200d \u0d24\u0d3e\u0d34\u0d46 \u0d15\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d28\u0d3f\u0d28\u0d4d\u0d28\u0d41\u0d02 \u0d05\u0d35 \u0d38\u0d46\u0d32\u0d15\u0d4d\u0d1f\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d24\u0d4d  \u0d15\u0d33\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d\u0d15\u0d4d\u0d15\u0d3f\u0d1f\u0d2f\u0d3f\u0d32\u0d41\u0d33\u0d4d\u0d33 \"\u0d28\u0d40\u0d15\u0d4d\u0d15\u0d02 \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d42\" \u0d0e\u0d28\u0d4d\u0d28 \u0d05\u0d1f\u0d2f\u0d3e\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d15\u0d4d\u0d32\u0d3f\u0d15\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15.",
    "Today": "\u0d07\u0d28\u0d4d\u0d28\u0d4d",
    "Tomorrow": "\u0d28\u0d3e\u0d33\u0d46",
    "Type into this box to filter down the list of available %s.": "\u0d32\u0d2d\u0d4d\u0d2f\u0d2e\u0d3e\u0d2f %s \u0d2a\u0d1f\u0d4d\u0d1f\u0d3f\u0d15\u0d2f\u0d46 \u0d2b\u0d3f\u0d32\u0d4d\u200d\u0d1f\u0d4d\u0d1f\u0d30\u0d4d\u200d \u0d1a\u0d46\u0d2f\u0d4d\u0d24\u0d46\u0d1f\u0d41\u0d15\u0d4d\u0d15\u0d3e\u0d28\u0d4d\u200d \u0d08 \u0d2c\u0d4b\u0d15\u0d4d\u0d38\u0d3f\u0d32\u0d4d\u200d \u0d1f\u0d48\u0d2a\u0d4d\u0d2a\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15.",
    "Yesterday": "\u0d07\u0d28\u0d4d\u0d28\u0d32\u0d46",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d12\u0d30\u0d41 \u0d06\u0d15\u0d4d\u0d37\u0d28\u0d4d\u200d \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d24\u0d4d\u0d24\u0d3f\u0d1f\u0d4d\u0d1f\u0d41\u0d23\u0d4d\u0d1f\u0d4d. \u0d15\u0d33\u0d19\u0d4d\u0d19\u0d33\u0d3f\u0d32\u0d4d\u200d \u0d38\u0d47\u0d35\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d3e\u0d24\u0d4d\u0d24 \u0d2e\u0d3e\u0d31\u0d4d\u0d31\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d07\u0d32\u0d4d\u0d32. \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d\u0d38\u0d47\u0d35\u0d4d \u0d2c\u0d1f\u0d4d\u0d1f\u0d23\u0d4d\u200d \u0d24\u0d28\u0d4d\u0d28\u0d46\u0d2f\u0d3e\u0d23\u0d4b \u0d05\u0d24\u0d4b \u0d17\u0d4b \u0d2c\u0d1f\u0d4d\u0d1f\u0d23\u0d3e\u0d23\u0d4b \u0d09\u0d26\u0d4d\u0d26\u0d47\u0d36\u0d3f\u0d1a\u0d4d\u0d1a\u0d24\u0d4d.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d12\u0d30\u0d41 \u0d06\u0d15\u0d4d\u0d37\u0d28\u0d4d\u200d \u0d24\u0d46\u0d30\u0d1e\u0d4d\u0d1e\u0d46\u0d1f\u0d41\u0d24\u0d4d\u0d24\u0d3f\u0d1f\u0d4d\u0d1f\u0d41\u0d23\u0d4d\u0d1f\u0d4d. \u0d2a\u0d15\u0d4d\u0d37\u0d47, \u0d15\u0d33\u0d19\u0d4d\u0d19\u0d33\u0d3f\u0d32\u0d46 \u0d2e\u0d3e\u0d31\u0d4d\u0d31\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d07\u0d28\u0d3f\u0d2f\u0d41\u0d02 \u0d38\u0d47\u0d35\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d3e\u0d28\u0d41\u0d23\u0d4d\u0d1f\u0d4d. \u0d06\u0d26\u0d4d\u0d2f\u0d02 \u0d38\u0d47\u0d35\u0d4d\u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d3e\u0d28\u0d3e\u0d2f\u0d3f OK \u0d15\u0d4d\u0d32\u0d3f\u0d15\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d41\u0d15. \u0d05\u0d24\u0d3f\u0d28\u0d41 \u0d36\u0d47\u0d37\u0d02 \u0d06\u0d15\u0d4d\u0d37\u0d28\u0d4d\u200d \u0d12\u0d28\u0d4d\u0d28\u0d41 \u0d15\u0d42\u0d1f\u0d3f \u0d2a\u0d4d\u0d30\u0d2f\u0d4b\u0d17\u0d3f\u0d15\u0d4d\u0d15\u0d47\u0d23\u0d4d\u0d1f\u0d3f \u0d35\u0d30\u0d41\u0d02.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u0d35\u0d30\u0d41\u0d24\u0d4d\u0d24\u0d3f\u0d2f \u0d2e\u0d3e\u0d31\u0d4d\u0d31\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d38\u0d47\u0d35\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d24\u0d3f\u0d1f\u0d4d\u0d1f\u0d3f\u0d32\u0d4d\u0d32. \u0d12\u0d30\u0d41 \u0d06\u0d15\u0d4d\u0d37\u0d28\u0d4d\u200d \u0d2a\u0d4d\u0d30\u0d2f\u0d4b\u0d17\u0d3f\u0d1a\u0d4d\u0d1a\u0d3e\u0d32\u0d4d\u200d \u0d38\u0d47\u0d35\u0d4d \u0d1a\u0d46\u0d2f\u0d4d\u0d2f\u0d3e\u0d24\u0d4d\u0d24 \u0d2e\u0d3e\u0d31\u0d4d\u0d31\u0d19\u0d4d\u0d19\u0d33\u0d46\u0d32\u0d4d\u0d32\u0d3e\u0d02 \u0d28\u0d37\u0d4d\u0d1f\u0d2a\u0d4d\u0d2a\u0d46\u0d1f\u0d41\u0d02.",
    "one letter Friday\u0004F": "\u0d35\u0d46",
    "one letter Monday\u0004M": "\u0d24\u0d3f",
    "one letter Saturday\u0004S": "\u0d36",
    "one letter Sunday\u0004S": "\u0d1e\u0d4d\u0d1e\u200d",
    "one letter Thursday\u0004T": "\u0d35\u0d4d\u0d2f\u0d3e",
    "one letter Tuesday\u0004T": "\u0d1a\u0d4a",
    "one letter Wednesday\u0004W": "\u0d2c\u0d41"
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
        return value.constructor === Array ? value[django.pluralidx(count)] : value;
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
    "FIRST_DAY_OF_WEEK": 0,
    "MONTH_DAY_FORMAT": "F j",
    "NUMBER_GROUPING": 3,
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

