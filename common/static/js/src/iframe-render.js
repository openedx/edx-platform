// List of the classes to hide while rendered in an iframe
const classesToHide = ['.global-header', '.wrapper-course-material', '.a--footer'];

document.addEventListener('DOMContentLoaded', function () {
  // Check if rendered in iframe
  if (window.self !== window.top) {
    classesToHide.forEach(function (className) {
      document.querySelectorAll(className).forEach(function (element) {
        element.classList.add('hidden-in-iframe');
      });
    });
  }
});
