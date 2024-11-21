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
 * Sends a JSON-formatted message to the iOS bridge if available.
 * @param {string} message - The JSON message to send.
 */
function sendMessageToIOS(message) {
  try {
    if (window?.webkit?.messageHandlers?.IOSBridge) {
      window.webkit.messageHandlers.IOSBridge.postMessage(message);
      console.log("Message sent to iOS:", message);
    }
  } catch (error) {
    console.error("Failed to send message to iOS:", error);
  }
}

/**
 * Sends a JSON-formatted message to the Android bridge if available.
 * @param {string} message - The JSON message to send.
 */
function sendMessageToAndroid(message) {
  try {
    if (window?.AndroidBridge) {
      window.AndroidBridge.postMessage(message);
      console.log("Message sent to Android:", message);
    }
  } catch (error) {
    console.error("Failed to send message to Android:", error);
  }
}

/**
 * Receives a message from the mobile apps and fills the form with the student's answer,
 * disables xblock inputs and marks the problem as completed with appropriate message.
 *
 * @param {string} message The stringified JSON object about the student's answer from the native mobile app.
 */
function markProblemCompleted(message) {
  let data;
  try {
    data = JSON.parse(message).data
  } catch (error) {
    console.error("Failed to parse message:", error)
    return
  }
  const problemContainer = $(".xblock-student_view");

  const submitButton = problemContainer.find(".submit-attempt-container .submit");
  const notificationContainer = problemContainer.find(".notification-gentle-alert");

  submitButton.attr({disabled: "disabled"});
  notificationContainer.find(".notification-message").text("Answer submitted");
  notificationContainer.find(".icon").remove();
  notificationContainer.show();

  data.split("&").forEach(function (item) {
    const [inputId, answer] = item.split('=', 2);
    problemContainer.find(
      `input[id$="${answer}"], input[id$="${inputId}"]`
    ).each(function () {
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
    if (options.data) {
      // Replace spaces with URLEncoded value to ensure correct parsing on the backend
      let formattedData = options.data.replace(/\+/g, '%20');
      let jsonMessage = JSON.stringify(formattedData)

      sendMessageToIOS(jsonMessage)
      sendMessageToAndroid(jsonMessage)
    }
  }
  return originalAjax.call(this, options);
}

