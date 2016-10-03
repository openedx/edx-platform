if (typeof $.fn.leanModal === 'undefined') {
    var vendorScript = document.createElement("script");
    vendorScript.src = '/static/js/vendor/jquery.leanModal.js';
    document.head.appendChild(vendorScript);
}
