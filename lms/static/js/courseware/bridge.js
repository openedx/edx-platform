/**
 * JS bridge for communication between the native mobile apps and the xblock.
 *
 * This script is used to send data about student's answer to the native mobile apps (IOS and Android)
 * and to receive data about student's answer from the native mobile apps to fill the form
 * with the student's answer, disable xblock inputs and mark the problem as completed.
 *
 * Separate functions for each platform allow you to flexibly add platform-specific logic
 * as needed without changing the naming on the mobile side.
 */

/**
 * Sends a data about student's answer to the IOS app.
 *
 * @param {string} message The stringified JSON object to be sent to the IOS app
 */
function sendMessageToIOS(message) {
  window?.webkit?.messageHandlers?.IOSBridge?.postMessage(message);
}

/**
 * Sends a data about student's answer to the Android app.
 *
 * @param {string} message The stringified JSON object to be sent to the native Android app
 */
function sendMessageToAndroid(message) {
  window?.AndroidBridge?.postMessage(message);
}

/**
 * Receives a message from the mobile apps and fills the form with the student's answer,
 * disables xblock inputs and marks the problem as completed with appropriate message.
 *
 * @param {string} message The stringified JSON object about the student's answer from the native mobile app.
 */
function markProblemCompleted(message) {
  const data = JSON.parse(message).data;
  const problemContainer = $(".xblock-student_view");
  const submitButton = problemContainer.find(".submit-attempt-container .submit");
  const notificationContainer = problemContainer.find(".notification-gentle-alert");
  submitButton.attr({disabled: "disabled"});
  notificationContainer.find(".notification-message").text("Answer submitted.");
  notificationContainer.show();

  data.split("&").forEach(function (item) {
    const [inputId, answer] = item.split('=', 2);
    problemContainer.find(`input[id$="${answer}"], input[id$="${inputId}"]`).each(function () {
      this.disabled = true;
      if (this.type === "checkbox" || this.type === "radio") {
        this.checked = true;
      } else {
        this.value = answer;
      }
    })
  })
}

/**
 * Overrides the default $.ajax function to intercept the requests to the "handler/xmodule_handler/problem_check"
 * endpoint and send the data to the native mobile apps.
 *
 * @param {Object} options The data object for the ajax request
 */
const originalAjax = $.ajax;
$.ajax = function (options) {
  if (options.url && options.url.endsWith("handler/xmodule_handler/problem_check")) {
    sendMessageToIOS(JSON.stringify(options));
    sendMessageToAndroid(JSON.stringify(options));
  }
  return originalAjax.call(this, options);
}

