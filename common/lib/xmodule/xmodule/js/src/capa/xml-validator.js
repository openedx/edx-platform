/* 
1. Stealed from W3Schools XML Validator <www.w3schools.com/xml/xml_validator.asp>
2. Beautified with jsbeautifier.org
3. Feed in XML string and use return instead of alert. 
*/

var xt = "",
    h3OK = 1;

function checkErrorXML(x) {
    xt = "";
    h3OK = 1;
    checkXML(x);
}

function checkXML(n) {
    var l, i, nam;
    nam = n.nodeName;
    if (nam == "h3") {
        if (h3OK == 0) {
            return;
        }
        h3OK = 0
    }
    if (nam == "#text") {
        xt = xt + n.nodeValue + "\n"
    }
    l = n.childNodes.length
    for (i = 0; i < l; i++) {
        checkXML(n.childNodes[i])
    }
}

function validateXML(txt) {
    // code for IE
    console.log(txt);
    if (window.ActiveXObject) {
        var xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
        xmlDoc.async = false;
        xmlDoc.loadXML(txt);

        if (xmlDoc.parseError.errorCode != 0) {
            txt = "Error Code: " + xmlDoc.parseError.errorCode + "\n";
            txt = txt + "Error Reason: " + xmlDoc.parseError.reason;
            return txt;
        } else {
            return xmlDoc;
        }
    }
    // code for Mozilla, Firefox, Opera, etc.
    else if (document.implementation.createDocument) {
        var parser = new DOMParser();
        var xmlDoc = parser.parseFromString(txt, "text/xml");

        if (xmlDoc.getElementsByTagName("parsererror").length > 0) {
            checkErrorXML(xmlDoc.getElementsByTagName("parsererror")[0]);
            return xt;
        } else {
            return xmlDoc;
        }
    } else {
    }
}