/*	SWFObject v2.2 <http://code.google.com/p/swfobject/> is released under the MIT License <http://www.opensource.org/licenses/mit-license.php>
	Express Install Copyright (c) 2007-2008 Adobe Systems Incorporated and its licensors. All Rights Reserved.
*/

System.security.allowDomain("fpdownload.macromedia.com");

var time = 0;
var timeOut = 5; // in seconds
var delay = 10; // in milliseconds
var int_id = setInterval(checkLoaded, delay);
var old_si = null;
var loaderClip = this.createEmptyMovieClip("loaderClip", 0);
var updateSWF = "http://fpdownload.macromedia.com/pub/flashplayer/update/current/swf/autoUpdater.swf?" + Math.random();
loaderClip.loadMovie(updateSWF);

function checkLoaded(){
	time += delay / 1000;
	if (time > timeOut) {
		// updater did not load in time, abort load and force alternative content
		clearInterval(int_id);
		loaderClip.unloadMovie();
		loadTimeOut();
	}
	else if (loaderClip.startInstall.toString() == "[type Function]") {
		// updater has loaded successfully AND has determined that it can do the express install
		if (old_si == null) {
			old_si = loaderClip.startInstall;
			loaderClip.startInstall = function() {
				clearInterval(int_id);
				old_si();
			}
			loadComplete();
		}
	}	
}

function loadTimeOut() {
	callbackSWFObject();
}

function callbackSWFObject() {
	getURL("javascript:swfobject.expressInstallCallback();");
}

function loadComplete() {
	loaderClip.redirectURL = _level0.MMredirectURL;
	loaderClip.MMplayerType = _level0.MMplayerType;
	loaderClip.MMdoctitle = _level0.MMdoctitle;
	loaderClip.startUpdate();
}

function installStatus(statusValue) {
	switch (statusValue) {
		case "Download.Complete":
			// Installation is complete.
			// In most cases the browser window that this SWF is hosted in will be closed by the installer or otherwise it has to be closed manually by the end user.
			// The Adobe Flash installer will attempt to reopen the browser window and reload the page containing the SWF. 
		break;
		case "Download.Cancelled":
			// The end user chose "NO" when prompted to install the new player.
			// By default the SWFObject callback function is called to force alternative content.
			callbackSWFObject();
		break;
		case "Download.Failed":
			// The end user failed to download the installer due to a network failure.
			// By default the SWFObject callback function is called to force alternative content.
			callbackSWFObject();
		break;
	}
}
