var sslaConfig = {
    autoLaunchFirstSco: true,
    setDataAjaxMethod: "POST",
    getDataAjaxMethod: "POST",
    setDataUrl: setDataURL,
    getDataUrl: getDataURL,
    setDataHeaders: dataHeaders,
    getDataHeaders: dataHeaders,
    openContentIn: openContentIn,
    courseId: courseId,
    courseDirectory: courseDirectory,
    studentId: studentId,
    studentName: studentName,
	
    // McKA specific configurations
    closePopupSingleScoBehavior: "custom",
    closePopupMultiScoBehavior: "custom",
    closePopupSingleScoCustomFunction: closePopupSingleSco,
    closePopupMultiScoCustomFunction: closePopupMultiSco,
    singleScoView: "HIDE_ALL",
    popupMainContentMessageAfterOpen: function() {
        return '';
    },
    popupMainContentMessageFailed: function() {
        return '<div style="background-color:rgb(250,250,250); width: 100%; height: 100%; display: table;"> <p style="font-family: \'Open Sans\', Arial, sans-serif; font-size: 14px; color: #000000; padding-top: 54px;">It looks like your browser settings has pop-ups disabled. <br>The content takes place in a new window.</p> <br><br> <button onclick="parent.ssla.ssla.popupManually();" style="background-color: #3385C7; color: white; padding: 1rem 2rem; font-family: \'Open Sans\', Arial, sans-serif; font-size: 14px; border-width: 0; font-weight: 700; border-color: #2s6a9f; border-radius: 5px;">Launch pop-up to continue</button></div>';
    },
    popupWindowParams: "status=1,toolbar=1,scrollbars=yes,resizable=yes,alwaysRaised=1"
};





var messageData = null;
var ssla_player_debug = false;

// we don't want alerts displaying in production
if (!(ssla_player_debug)) window.alert = function() {};

window.addEventListener("message", receiveMessage, false);

function receiveMessage(event) {
  console.log("Receive Message:", event);
  var origin = event.origin || event.originalEvent.origin; // For Chrome, the origin property is in the event.originalEvent object.
  /*
  if (origin !== "http://example.org:8080")
    return;
  */
  if (ssla_player_debug) alert('SSLA player received message!');
  messageData = event.data;
  ssla.ssla.start();
}

function dataHeaders() {
   try {
     return {"X-CSRFToken": messageData.csrftoken};
   }
   catch (e) {
     //fail on cross-domain security error...
     return {};
   }
}

function getDataURL() {
  console.log('calling getDataURL');
  try {
    return messageData.get_url;
  }
  catch (e){
    //fail on cross-domain security error...
    //we don't want preview from Studio to send get/set
    return "#";
  }
}

function setDataURL() {
  try {
    return messageData.set_url;
  }
  catch (e){
    //fail on cross-domain security error...
    //we don't want preview from Studio to send get/set
    return "#";
  }
}

function openContentIn() {
  try {
    return messageData.display_type.toLowerCase() == "iframe" ? "inline" : "popup";
  }
  catch (e){
    return "1";
  }
}

function popupWindowParams() {
  try {
    width = messageData.display_width;
    height = messageData.display_height;
    menubar = toolbar = status = scrollbar = "no";
    if (ssla_player_debug) {
      menubar = toolbar = status = scrollbar = "yes";
    }
    attrstr = "width="+width+",height="+height+",menubar="+menubar+",toolbar="+toolbar+",status="+status+",scrollbar="+scrollbar;
    return attrstr;
  }
  catch (e){
    return "";
  }
}

function courseId() {
  try {
    return messageData.course_id;
  }
  catch (e){
    return "";
  }
}

function courseDirectory() {
  try {
    return messageData.course_location.replace(/^.*\/\/[^\/]+/, '');
  }
  catch (e){
    console.log(e)
    return "";
  }
}

function studentId() {
  try {
    return messageData.student_id;
  }
  catch (e){
    return "";
  }
}

function studentName() {
  try {
    return messageData.student_name;
  }
  catch (e){
    return "";
  }
}

function closePopupSingleSco(){
    console.log('Closing single sco popup');
    handlePopupClosed();
}

function closePopupMultiSco() {
    console.log('Closing multi sco popup');
    handlePopupClosed();
}

function handlePopupClosed() {
    parent.document.handleScormPopupClosed()
}
