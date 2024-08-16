// List of the classes to hide while rendered in an iframe
const classesToHide = ['.global-header', '.wrapper-course-material', '.a--footer'];

// Function to get a cookie by name
function getCookieByName(name) {
  let cname = name + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let cookies = decodedCookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

document.addEventListener('DOMContentLoaded', function () {
  const hideElements = getCookieByName('hideElements');

  if (hideElements) {
    classesToHide.forEach(function (className) {
      document.querySelectorAll(className).forEach(function (element) {
        element.classList.add('hidden-element');
      });
    });
  }
});
