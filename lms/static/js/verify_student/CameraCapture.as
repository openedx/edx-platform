/**
 * Simple Camera Capture application meant to be used where WebRTC is not supported
 * (e.g. Safari, Internet Explorer, Opera). All orchestration is assumed to happen
 * in JavaScript. The only function this application has is to capture a snapshot
 * and allow a 640x480 PNG of that snapshot to be made available to the JS as a
 * base64 encoded data URL.
 * 
 * There are really only three methods:
 *   snap() freezes the video and returns a PNG file as a data URL string. You can
 *          assign this return value to an img's src attribute.
 *   reset() restarts the the video.
 *   imageDataUrl() returns the same thing as snap() -- 
 *
 * Note that this file is merely the source code for CameraCapture.swf; to make
 * changes, you must edit this file, compile it to .swf, and check in the .swf
 * file separately
 */

package
{
	import flash.display.BitmapData;
	import flash.display.PNGEncoderOptions;
	import flash.display.Sprite;
	import flash.events.Event;
	import flash.external.ExternalInterface;
	import flash.geom.Rectangle;
	import flash.media.Camera;
	import flash.media.Video;
	import flash.utils.ByteArray;
	
	import mx.utils.Base64Encoder;
	
	[SWF(width="640", height="480")]
	public class CameraCapture extends Sprite
	{
		// We pick these values because that's captured by the WebRTC spec
		private const VIDEO_WIDTH:int = 640;
		private const VIDEO_HEIGHT:int = 480;
		
		private var camera:Camera;
		private var video:Video;
		private var b64EncodedImage:String = null;
		
		public function CameraCapture()
		{
			addEventListener(Event.ADDED_TO_STAGE, init); 
		}
		
		protected function init(e:Event):void {
			camera = Camera.getCamera();
			camera.setMode(VIDEO_WIDTH, VIDEO_HEIGHT, 30);
			
			video = new Video(VIDEO_WIDTH, VIDEO_HEIGHT);
			video.attachCamera(camera);
			
			addChild(video);
			
			ExternalInterface.addCallback("snap", snap);
			ExternalInterface.addCallback("reset", reset);
			ExternalInterface.addCallback("imageDataUrl", imageDataUrl);
			ExternalInterface.addCallback("cameraAuthorized", cameraAuthorized);
			ExternalInterface.addCallback("hasCamera", hasCamera);
			
			// Notify the container that the SWF is ready to be called. 
			ExternalInterface.call("setSWFIsReady"); 
		}
		
		public function snap():String {
			// If we already have a b64 encoded image, just return that. The user
			// is calling snap() multiple times in a row without reset()
			if (b64EncodedImage) {
				return imageDataUrl();
			}
			
			var bitmapData:BitmapData = new BitmapData(video.width, video.height);
			bitmapData.draw(video); // Draw a snapshot of the video onto our bitmapData
			video.attachCamera(null); // Stop capturing video
			
			// Convert to PNG
			var pngBytes:ByteArray = new ByteArray();
			bitmapData.encode(
				new Rectangle(0, 0, video.width, video.height),
				new PNGEncoderOptions(),
				pngBytes
			);
			
			// Convert to Base64 encoding of PNG
			var b64Encoder:Base64Encoder = new Base64Encoder();
			b64Encoder.encodeBytes(pngBytes);
			b64EncodedImage = b64Encoder.toString();
			
			return imageDataUrl();
		}

		public function reset():String {
			video.attachCamera(camera);
			b64EncodedImage = null;
			
			return imageDataUrl();
		}

		public function imageDataUrl():String {
			if (b64EncodedImage) {
				return "data:image/png;base64," + b64EncodedImage;
			}
			return "";
		}
		
		public function cameraAuthorized():Boolean {
			return !(camera.muted);
		}
		
		public function hasCamera():Boolean {
			return (Camera.names.length != 0);
		}
	}
}

