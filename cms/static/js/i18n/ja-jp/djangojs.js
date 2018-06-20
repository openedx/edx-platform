

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=0;
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "\n      Because the due date has passed, you are no longer able to take this exam.\n    ": "\n\u7de0\u5207\u65e5\u304c\u904e\u304e\u305f\u305f\u3081\u3001\u672c\u8a66\u9a13\u3092\u53d7\u3051\u308b\u3053\u3068\u304c\u3067\u304d\u307e\u305b\u3093\u3002", 
    "\n      The due date for this exam has passed\n    ": "\n\u3053\u306e\u8a66\u9a13\u306e\u7de0\u5207\u306f\u65e2\u306b\u904e\u304e\u3066\u3044\u307e\u3059\u3002", 
    "%(sel)s of %(cnt)s selected": [
      "%(cnt)s\u500b\u4e2d%(sel)s\u500b\u9078\u629e"
    ], 
    "(required):": "(\u5fc5\u9808): ", 
    "6 a.m.": "\u5348\u524d 6 \u6642", 
    "6 p.m.": "\u5348\u5f8c 6 \u6642", 
    "After you upload new files all your previously uploaded files will be overwritten. Continue?": "\u65b0\u898f\u30d5\u30a1\u30a4\u30eb\u3092\u30a2\u30c3\u30d7\u30ed\u30fc\u30c9\u3059\u308b\u3068\u3001\u4ee5\u524d\u30a2\u30c3\u30d7\u30ed\u30fc\u30c9\u3057\u305f\u30d5\u30a1\u30a4\u30eb\u304c\u3059\u3079\u3066\u4e0a\u66f8\u304d\u3055\u308c\u307e\u3059\u3002\u7d9a\u3051\u307e\u3059\u304b\uff1f", 
    "April": "4\u6708", 
    "Assessment": "\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8", 
    "Assessments": "\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8", 
    "August": "8\u6708", 
    "Available %s": "\u5229\u7528\u53ef\u80fd %s", 
    "Back to Full List": "\u5168\u30ea\u30b9\u30c8\u3078\u623b\u308b", 
    "Block view is unavailable": "\u30d6\u30ed\u30c3\u30af\u30fb\u30d3\u30e5\u30fc\u306f\u4e0d\u53ef", 
    "Cancel": "\u30ad\u30e3\u30f3\u30bb\u30eb", 
    "Changes to steps that are not selected as part of the assignment will not be saved.": "\u8ab2\u984c\u306e\u4e00\u90e8\u3068\u3057\u3066\u9078\u629e\u3055\u308c\u3066\u3044\u306a\u3044\u30b9\u30c6\u30c3\u30d7\u306e\u5909\u66f4\u306f\u4fdd\u5b58\u3055\u308c\u307e\u305b\u3093\u3002", 
    "Choose": "\u9078\u629e", 
    "Choose a Date": "\u65e5\u4ed8\u3092\u9078\u629e", 
    "Choose a Time": "\u6642\u9593\u3092\u9078\u629e", 
    "Choose a time": "\u6642\u9593\u3092\u9078\u629e", 
    "Choose all": "\u5168\u3066\u9078\u629e", 
    "Chosen %s": "\u9078\u629e\u3055\u308c\u305f %s", 
    "Click to choose all %s at once.": "\u30af\u30ea\u30c3\u30af\u3059\u308b\u3068\u3059\u3079\u3066\u306e %s \u3092\u9078\u629e\u3057\u307e\u3059\u3002", 
    "Click to remove all chosen %s at once.": "\u30af\u30ea\u30c3\u30af\u3059\u308b\u3068\u3059\u3079\u3066\u306e %s \u3092\u9078\u629e\u304b\u3089\u524a\u9664\u3057\u307e\u3059\u3002", 
    "Could not retrieve download url.": "\u30c0\u30a6\u30f3\u30ed\u30fc\u30c9URL\u304c\u5fa9\u65e7\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "Could not retrieve upload url.": "\u30a2\u30c3\u30d7\u30ed\u30fc\u30c9URL\u304c\u5fa9\u65e7\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "Couldn't Save This Assignment": "\u3053\u306e\u8ab2\u984c\u3092\u4fdd\u5b58\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f", 
    "Criterion Added": "\u8a55\u4fa1\u57fa\u6e96\u8ffd\u52a0\u6e08", 
    "Criterion Deleted": "\u8a55\u4fa1\u57fa\u6e96\u524a\u9664\u6e08", 
    "December": "12\u6708", 
    "Describe ": "\u8a18\u8ff0\u3059\u308b", 
    "Do you want to upload your file before submitting?": "\u63d0\u51fa\u524d\u306b\u30d5\u30a1\u30a4\u30eb\u3092\u30a2\u30c3\u30d7\u30ed\u30fc\u30c9\u3057\u307e\u3059\u304b\uff1f", 
    "Error": "\u30a8\u30e9\u30fc", 
    "Error getting the number of ungraded responses": "\u63a1\u70b9\u5bfe\u8c61\u5916\u306e\u8fd4\u4fe1\u6570\u306e\u53d6\u5f97\u30a8\u30e9\u30fc", 
    "February": "2\u6708", 
    "Feedback available for selection.": "\u9078\u629e\u306b\u5bfe\u3059\u308b\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af\u304c\u3054\u89a7\u3044\u305f\u3060\u3051\u307e\u3059\u3002", 
    "File size must be 10MB or less.": "\u30d5\u30a1\u30a4\u30eb\u30b5\u30a4\u30ba\u306f10MB\u3092\u8d85\u3048\u3066\u306f\u3044\u3051\u307e\u305b\u3093\u3002", 
    "File type is not allowed.": "\u30d5\u30a1\u30a4\u30eb\u30bf\u30a4\u30d7\u304c\u4e0d\u6b63\u3067\u3059\u3002", 
    "File types can not be empty.": "\u30d5\u30a1\u30a4\u30eb\u30bf\u30a4\u30d7\u3092\u6307\u5b9a\u3057\u3066\u304f\u3060\u3055\u3044\u3002", 
    "Filter": "\u30d5\u30a3\u30eb\u30bf\u30fc", 
    "Final Grade Received": "\u6700\u7d42\u6210\u7e3e\u53d7\u53d6\u6e08", 
    "Go Back": "\u623b\u308b", 
    "Hide": "\u975e\u8868\u793a", 
    "If you leave this page without saving or submitting your response, you will lose any work you have done on the response.": "\u8fd4\u4fe1\u3092\u4fdd\u5b58\u307e\u305f\u306f\u63d0\u51fa\u305b\u305a\u306b\u5225\u306e\u30da\u30fc\u30b8\u3078\u79fb\u52d5\u3059\u308b\u5834\u5408\u3001\u8a18\u8ff0\u3057\u305f\u5185\u5bb9\u304c\u5931\u308f\u308c\u307e\u3059\u3002", 
    "If you leave this page without submitting your peer assessment, you will lose any work you have done.": "\u30d4\u30a2\u30fb\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u3092\u63d0\u51fa\u305b\u305a\u306b\u5225\u306e\u30da\u30fc\u30b8\u3078\u79fb\u52d5\u3059\u308b\u5834\u5408\u3001\u8a18\u8ff0\u3057\u305f\u5185\u5bb9\u304c\u5931\u308f\u308c\u307e\u3059\u3002", 
    "If you leave this page without submitting your self assessment, you will lose any work you have done.": "\u30bb\u30eb\u30d5\u30fb\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u3092\u63d0\u51fa\u305b\u305a\u306b\u5225\u306e\u30da\u30fc\u30b8\u3078\u79fb\u52d5\u3059\u308b\u3068\u3001\u8a18\u8ff0\u3057\u305f\u5185\u5bb9\u304c\u5931\u308f\u308c\u307e\u3059\u3002", 
    "If you leave this page without submitting your staff assessment, you will lose any work you have done.": "\u30b9\u30bf\u30c3\u30d5\u30fb\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u3092\u63d0\u51fa\u305b\u305a\u306b\u5225\u306e\u30da\u30fc\u30b8\u3078\u79fb\u52d5\u3059\u308b\u3068\u3001\u8a18\u8ff0\u3057\u305f\u5185\u5bb9\u304c\u5931\u308f\u308c\u307e\u3059\u3002", 
    "January": "1\u6708", 
    "July": "7\u6708", 
    "June": "6\u6708", 
    "List of Open Assessments is unavailable": "\u30aa\u30fc\u30d7\u30f3\u30fb\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u306e\u30ea\u30b9\u30c8\u306f\u3042\u308a\u307e\u305b\u3093", 
    "March": "3\u6708", 
    "May": "5\u6708", 
    "Midnight": "0\u6642", 
    "Noon": "12\u6642", 
    "Not Selected": "\u672a\u9078\u629e", 
    "Note: You are %s hour ahead of server time.": [
      "\u30ce\u30fc\u30c8: \u3042\u306a\u305f\u306e\u74b0\u5883\u306f\u30b5\u30fc\u30d0\u30fc\u6642\u9593\u3088\u308a\u3001%s\u6642\u9593\u9032\u3093\u3067\u3044\u307e\u3059\u3002"
    ], 
    "Note: You are %s hour behind server time.": [
      "\u30ce\u30fc\u30c8: \u3042\u306a\u305f\u306e\u74b0\u5883\u306f\u30b5\u30fc\u30d0\u30fc\u6642\u9593\u3088\u308a\u3001%s\u6642\u9593\u9045\u308c\u3066\u3044\u307e\u3059\u3002"
    ], 
    "November": "11\u6708", 
    "Now": "\u73fe\u5728", 
    "October": "10\u6708", 
    "One or more rescheduling tasks failed.": "\u30b9\u30b1\u30b8\u30e5\u30fc\u30eb\u5909\u66f4\u30bf\u30b9\u30af\u5931\u6557\u3002", 
    "Option Deleted": "\u9078\u629e\u80a2\u524a\u9664\u6e08", 
    "Peer": "\u30d4\u30a2", 
    "Please correct the outlined fields.": "\u7e01\u53d6\u3089\u308c\u305f\u6b04\u3092\u6b63\u3057\u304f\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002", 
    "Please wait": "\u304a\u5f85\u3061\u304f\u3060\u3055\u3044", 
    "Remove": "\u524a\u9664", 
    "Remove all": "\u3059\u3079\u3066\u524a\u9664", 
    "Saving...": "\u4fdd\u5b58\u4e2d...", 
    "Self": "\u30bb\u30eb\u30d5", 
    "September": "9\u6708", 
    "Server error.": "\u30b5\u30fc\u30d0\u30fc\u30a8\u30e9\u30fc\u3002", 
    "Show": "\u8868\u793a", 
    "Staff": "\u30b9\u30bf\u30c3\u30d5", 
    "Status of Your Response": "\u3042\u306a\u305f\u306e\u8fd4\u4fe1\u306e\u30b9\u30c6\u30fc\u30bf\u30b9", 
    "The display of ungraded and checked out responses could not be loaded.": "\u63a1\u70b9\u5bfe\u8c61\u5916\u304a\u3088\u3073\u30c1\u30a7\u30c3\u30af\u30a2\u30a6\u30c8\u6e08\u306e\u8fd4\u4fe1\u306e\u8868\u793a\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "The following file types are not allowed: ": "\u6b21\u306b\u793a\u3059\u30d5\u30a1\u30a4\u30eb\u30bf\u30a4\u30d7\u306f\u4e0d\u6b63\u3067\u3059\uff1a", 
    "The server could not be contacted.": "\u30b5\u30fc\u30d0\u30fc\u306b\u63a5\u7d9a\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "The staff assessment form could not be loaded.": "\u30b9\u30bf\u30c3\u30d5\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u30d5\u30a9\u30fc\u30e0\u3092\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "The submission could not be removed from the grading pool.": "\u63d0\u51fa\u7269\u3092\u63a1\u70b9\u30d7\u30fc\u30eb\u304b\u3089\u524a\u9664\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This assessment could not be submitted.": "\u3053\u306e\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u306f\u63d0\u51fa\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This feedback could not be submitted.": "\u3053\u306e\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af\u306f\u63d0\u51fa\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "\u3053\u308c\u304c\u4f7f\u7528\u53ef\u80fd\u306a %s \u306e\u30ea\u30b9\u30c8\u3067\u3059\u3002\u4e0b\u306e\u30dc\u30c3\u30af\u30b9\u3067\u9805\u76ee\u3092\u9078\u629e\u3057\u30012\u3064\u306e\u30dc\u30c3\u30af\u30b9\u9593\u306e \"\u9078\u629e\"\u306e\u77e2\u5370\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u3001\u3044\u304f\u3064\u304b\u3092\u9078\u629e\u3059\u308b\u3053\u3068\u304c\u3067\u304d\u307e\u3059\u3002", 
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "\u3053\u308c\u304c\u9078\u629e\u3055\u308c\u305f %s \u306e\u30ea\u30b9\u30c8\u3067\u3059\u3002\u4e0b\u306e\u30dc\u30c3\u30af\u30b9\u3067\u9078\u629e\u3057\u30012\u3064\u306e\u30dc\u30c3\u30af\u30b9\u9593\u306e \"\u524a\u9664\"\u77e2\u5370\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u4e00\u90e8\u3092\u524a\u9664\u3059\u308b\u3053\u3068\u304c\u3067\u304d\u307e\u3059\u3002", 
    "This problem could not be saved.": "\u3053\u306e\u554f\u984c\u306f\u4fdd\u5b58\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This problem has already been released. Any changes will apply only to future assessments.": "\u3053\u306e\u554f\u984c\u306f\u65e2\u306b\u516c\u958b\u6e08\u307f\u306e\u305f\u3081\u3001\u5909\u66f4\u306f\u4eca\u5f8c\u306e\u30a2\u30bb\u30b9\u30e1\u30f3\u30c8\u306e\u307f\u306b\u9069\u7528\u3055\u308c\u307e\u3059\u3002", 
    "This response could not be saved.": "\u3053\u306e\u8fd4\u4fe1\u306f\u4fdd\u5b58\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This response could not be submitted.": "\u3053\u306e\u8fd4\u4fe1\u306f\u63d0\u51fa\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "This response has been saved but not submitted.": "\u3053\u306e\u8fd4\u4fe1\u306f\u4fdd\u5b58\u3055\u308c\u3066\u3044\u307e\u3059\u304c\u3001\u63d0\u51fa\u306f\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002", 
    "This response has not been saved.": "\u3053\u306e\u8fd4\u4fe1\u306f\u4fdd\u5b58\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002", 
    "This section could not be loaded.": "\u3053\u306e\u30bb\u30af\u30b7\u30e7\u30f3\u306f\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093\u3067\u3057\u305f\u3002", 
    "Thumbnail view of ": "\u30b5\u30e0\u30cd\u30a4\u30eb\u30fb\u30d3\u30e5\u30fc", 
    "Today": "\u4eca\u65e5", 
    "Tomorrow": "\u660e\u65e5", 
    "Total Responses": "\u7dcf\u8fd4\u4fe1\u6570", 
    "Training": "\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0", 
    "Type into this box to filter down the list of available %s.": "\u4f7f\u7528\u53ef\u80fd\u306a %s \u306e\u30ea\u30b9\u30c8\u3092\u7d5e\u308a\u8fbc\u3080\u306b\u306f\u3001\u3053\u306e\u30dc\u30c3\u30af\u30b9\u306b\u5165\u529b\u3057\u307e\u3059\u3002", 
    "Unable to load": "\u8aad\u307f\u8fbc\u3081\u307e\u305b\u3093", 
    "Unexpected server error.": "\u4e88\u671f\u3057\u306a\u3044\u30b5\u30fc\u30d0\u30fc\u30a8\u30e9\u30fc\u3002", 
    "Unit Name": "\u30e6\u30cb\u30c3\u30c8\u540d", 
    "Units": "\u30e6\u30cb\u30c3\u30c8", 
    "Unnamed Option": "\u540d\u79f0\u672a\u8a2d\u5b9a\u306e\u30aa\u30d7\u30b7\u30e7\u30f3", 
    "Waiting": "\u5f85\u6a5f\u4e2d", 
    "Warning": "\u8b66\u544a", 
    "Yesterday": "\u6628\u65e5", 
    "You can upload files with these file types: ": "\u6b21\u306b\u793a\u3059\u30d5\u30a1\u30a4\u30eb\u30bf\u30a4\u30d7\u3067\u3042\u308c\u3070\u30a2\u30c3\u30d7\u30ed\u30fc\u30c9\u3067\u304d\u307e\u3059: ", 
    "You have added a criterion. You will need to select an option for the criterion in the Learner Training step. To do this, click the Settings tab.": "\u8a55\u4fa1\u57fa\u6e96\u3092\u8ffd\u52a0\u3057\u307e\u3057\u305f\u3002\u53d7\u8b1b\u8005\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u306e\u8a55\u4fa1\u57fa\u6e96\u306e\u9078\u629e\u80a2\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002\u9078\u629e\u3059\u308b\u306b\u306f\u8a2d\u5b9a\u30bf\u30d6\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u304f\u3060\u3055\u3044\u3002", 
    "You have deleted a criterion. The criterion has been removed from the example responses in the Learner Training step.": "\u8a55\u4fa1\u57fa\u6e96\u3092\u524a\u9664\u3057\u307e\u3057\u305f\u3002\u53d7\u8b1b\u8005\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u306e\u89e3\u7b54\u4f8b\u304b\u3089\u8a55\u4fa1\u57fa\u6e96\u304c\u524a\u9664\u3055\u308c\u307e\u3057\u305f\u3002", 
    "You have deleted all the options for this criterion. The criterion has been removed from the sample responses in the Learner Training step.": "\u3053\u306e\u8a55\u4fa1\u57fa\u6e96\u306e\u5168\u3066\u306e\u9078\u629e\u80a2\u3092\u524a\u9664\u3057\u307e\u3057\u305f\u3002\u53d7\u8b1b\u8005\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u306e\u89e3\u7b54\u4f8b\u304b\u3089\u3001\u3053\u306e\u8a55\u4fa1\u57fa\u6e96\u304c\u524a\u9664\u3055\u308c\u307e\u3057\u305f\u3002", 
    "You have deleted an option. That option has been removed from its criterion in the sample responses in the Learner Training step. You might have to select a new option for the criterion.": "\u9078\u629e\u80a2\u3092\u524a\u9664\u3057\u307e\u3057\u305f\u3002\u53d7\u8b1b\u8005\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u306e\u89e3\u7b54\u4f8b\u306b\u3042\u308b\u8a55\u4fa1\u57fa\u6e96\u304b\u3089\u3001\u3053\u306e\u9078\u629e\u80a2\u304c\u524a\u9664\u3055\u308c\u307e\u3057\u305f\u3002\u5fc5\u8981\u306b\u5fdc\u3058\u3066\u65b0\u3057\u3044\u9078\u629e\u80a2\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002", 
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "\u64cd\u4f5c\u3092\u9078\u629e\u3057\u307e\u3057\u305f\u304c\u3001\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u5909\u66f4\u306f\u3042\u308a\u307e\u305b\u3093\u3067\u3057\u305f\u3002\u3082\u3057\u304b\u3057\u3066\u4fdd\u5b58\u30dc\u30bf\u30f3\u3067\u306f\u306a\u304f\u3066\u5b9f\u884c\u30dc\u30bf\u30f3\u3092\u304a\u63a2\u3057\u3067\u3059\u304b\u3002", 
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "\u64cd\u4f5c\u3092\u9078\u629e\u3057\u307e\u3057\u305f\u304c\u3001\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u304c\u3042\u308a\u307e\u3059\u3002OK\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u4fdd\u5b58\u3057\u3066\u304f\u3060\u3055\u3044\u3002\u305d\u306e\u5f8c\u3001\u64cd\u4f5c\u3092\u518d\u5ea6\u5b9f\u884c\u3059\u308b\u5fc5\u8981\u304c\u3042\u308a\u307e\u3059\u3002", 
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "\u30d5\u30a3\u30fc\u30eb\u30c9\u306b\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u304c\u3042\u308a\u307e\u3059\u3002\u64cd\u4f5c\u3092\u5b9f\u884c\u3059\u308b\u3068\u672a\u4fdd\u5b58\u306e\u5909\u66f4\u306f\u5931\u308f\u308c\u307e\u3059\u3002", 
    "You must provide a learner name.": "\u53d7\u8b1b\u8005\u540d\u3092\u6307\u5b9a\u3057\u3066\u4e0b\u3055\u3044\u3002", 
    "You're about to submit your response for this assignment. After you submit this response, you can't change it or submit a new response.": "\u3053\u306e\u8ab2\u984c\u306b\u95a2\u3059\u308b\u8fd4\u4fe1\u3092\u63d0\u51fa\u3057\u3088\u3046\u3068\u3057\u3066\u3044\u307e\u3059\u3002\u8fd4\u4fe1\u3092\u63d0\u51fa\u3057\u305f\u5f8c\u306f\u3001\u5909\u66f4\u3057\u305f\u308a\u65b0\u3057\u3044\u8fd4\u4fe1\u3092\u63d0\u51fa\u3059\u308b\u3053\u3068\u306f\u3067\u304d\u307e\u305b\u3093\u3002", 
    "one letter Friday\u0004F": "\u91d1", 
    "one letter Monday\u0004M": "\u6708", 
    "one letter Saturday\u0004S": "\u571f", 
    "one letter Sunday\u0004S": "\u65e5", 
    "one letter Thursday\u0004T": "\u6728", 
    "one letter Tuesday\u0004T": "\u706b", 
    "one letter Wednesday\u0004W": "\u6c34"
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
    "DATETIME_FORMAT": "Y\u5e74n\u6708j\u65e5G:i", 
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
    "DATE_FORMAT": "Y\u5e74n\u6708j\u65e5", 
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d", 
      "%m/%d/%Y", 
      "%m/%d/%y", 
      "%b %d %Y", 
      "%b %d, %Y", 
      "%d %b %Y", 
      "%d %b, %Y", 
      "%B %d %Y", 
      "%B %d, %Y", 
      "%d %B %Y", 
      "%d %B, %Y"
    ], 
    "DECIMAL_SEPARATOR": ".", 
    "FIRST_DAY_OF_WEEK": "0", 
    "MONTH_DAY_FORMAT": "n\u6708j\u65e5", 
    "NUMBER_GROUPING": "0", 
    "SHORT_DATETIME_FORMAT": "Y/m/d G:i", 
    "SHORT_DATE_FORMAT": "Y/m/d", 
    "THOUSAND_SEPARATOR": ",", 
    "TIME_FORMAT": "G:i", 
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S", 
      "%H:%M:%S.%f", 
      "%H:%M"
    ], 
    "YEAR_MONTH_FORMAT": "Y\u5e74n\u6708"
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

