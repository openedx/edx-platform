if (!CMS.Models['Settings']) CMS.Models.Settings = new Object();

CMS.Models.Settings.CourseDetails = Backbone.Model.extend({
	defaults: {
		location : null,	// the course's Location model, required
		start_date: null,	// maps to 'start'
		end_date: null,		// maps to 'end'
		enrollment_start: null,
		enrollment_end: null,
		syllabus: null,
		overview: "",
		intro_video: null,
		effort: null	// an int or null
	},
	
	// When init'g from html script, ensure you pass {parse: true} as an option (2nd arg to reset)
	parse: function(attributes) {
		if (attributes['course_location']) {
			attributes.location = new CMS.Models.Location(attributes.course_location, {parse:true});
		}
		if (attributes['start_date']) {
			attributes.start_date = new Date(attributes.start_date);
		}
		if (attributes['end_date']) {
			attributes.end_date = new Date(attributes.end_date);
		}
		if (attributes['enrollment_start']) {
			attributes.enrollment_start = new Date(attributes.enrollment_start);
		}
		if (attributes['enrollment_end']) {
			attributes.enrollment_end = new Date(attributes.enrollment_end);
		}
		return attributes;
	},
	
	validate: function(newattrs) {
		// Returns either nothing (no return call) so that validate works or an object of {field: errorstring} pairs
		// A bit funny in that the video key validation is asynchronous; so, it won't stop the validation.
		var errors = {};
		if (newattrs.start_date && newattrs.end_date && newattrs.start_date >= newattrs.end_date) {
			errors.end_date = "The course end date cannot be before the course start date.";
		}
		if (newattrs.start_date && newattrs.enrollment_start && newattrs.start_date < newattrs.enrollment_start) {
			errors.enrollment_start = "The course start date cannot be before the enrollment start date.";
		}
		if (newattrs.enrollment_start && newattrs.enrollment_end && newattrs.enrollment_start >= newattrs.enrollment_end) {
			errors.enrollment_end = "The enrollment start date cannot be after the enrollment end date.";
		}
		if (newattrs.end_date && newattrs.enrollment_end && newattrs.end_date < newattrs.enrollment_end) {
			errors.enrollment_end = "The enrollment end date cannot be after the course end date.";
		}
		if (newattrs.intro_video && newattrs.intro_video != this.get('intro_video')) {
			var videos = this.parse_videosource(newattrs.intro_video);
			var vid_errors = new Array();
			var cachethis = this;
			for (var i=0; i<videos.length; i++) {
				// doesn't call parseFloat or Number b/c they stop on first non parsable and return what they have
				if (!isFinite(videos[i].speed)) vid_errors.push(videos[i].speed + " is not a valid speed.");
				else if (!videos[i].key) vid_errors.push(videos[i].speed + " does not have a video id");
				// can't use get from client to test if video exists b/c of CORS (crossbrowser get not allowed)
				// GET "http://gdata.youtube.com/feeds/api/videos/" + videokey
			}
			if (!_.isEmpty(vid_errors)) {
				errors.intro_video = vid_errors.join(' ');
			}
		}
		if (!_.isEmpty(errors)) return errors;
		// NOTE don't return empty errors as that will be interpreted as an error state
	},
	
	url: function() {
		var location = this.get('location');
		return '/' + location.get('org') + "/" + location.get('course') + '/settings/' + location.get('name') + '/section/details';
	},
	
	_videoprefix : /\s*<video\s*youtube="/g,
	// the below is lax to enable validation
	_videospeedparse : /[^:]*/g, // /\d+\.?\d*(?=:)/g,
	_videokeyparse : /([^,\/>]+)/g,
	_videonosuffix : /[^"\/>]+/g,
	_getNextMatch : function (regex, string, cursor) {
		regex.lastIndex = cursor;
		var result = regex.exec(string);
		if (_.isArray(result)) return result[0];
		else return result;
	},
	// the whole string for editing (put in edit box)
	getVideoSource: function() {
		if (this.get('intro_video')) {
			var cursor = 0;
			var videostring = this.get('intro_video');
			this._getNextMatch(this._videoprefix, videostring, cursor);
			cursor = this._videoprefix.lastIndex;
			return this._getNextMatch(this._videonosuffix, videostring, cursor);
		}
		else return "";
	},
	// the source closest to 1.0 speed
	videosourceSample: function() {
		if (this.get('intro_video')) {
			var cursor = 0;
			var videostring = this.get('intro_video');
			this._getNextMatch(this._videoprefix, videostring, cursor);
			cursor = this._videoprefix.lastIndex;
			
			// parse from [speed:id,/s?]* to find 1.0 or take first
			var parsedspeed = this._getNextMatch(this._videospeedparse, videostring, cursor);
			var bestkey;
			if (parsedspeed) {
				cursor = this._videospeedparse.lastIndex + 1;
				var bestspeed = Number(parsedspeed);
				bestkey = this._getNextMatch(this._videokeyparse, videostring, cursor);
				cursor = this._videokeyparse.lastIndex + 1;
				while (cursor < videostring.length && bestspeed != 1.0) {
					parsedspeed = this._getNextMatch(this._videospeedparse, videostring, cursor);
					if (parsedspeed) cursor = this._videospeedparse.lastIndex + 1;
					else break;
					if (Math.abs(Number(parsedspeed) - 1.0) < Math.abs(bestspeed - 1.0)) {
						bestspeed = Number(parsedspeed);
						bestkey = this._getNextMatch(this._videokeyparse, videostring, cursor);
					}
					else this._getNextMatch(this._videokeyparse, videostring, cursor);
					if (this._videokeyparse.lastIndex > cursor)	cursor = this._videokeyparse.lastIndex + 1;
					else cursor++;
				}
			}
			else {
				bestkey = this._getNextMatch(this._videokeyparse, videostring, cursor);
			}
			if (bestkey) {
				// WTF? for some reason bestkey is an array [key, key] (same one repeated)
				if (_.isArray(bestkey)) bestkey = bestkey[0];
				return "http://www.youtube.com/embed/" + bestkey;
			}
			else return "";
		}
	},
	parse_videosource: function(videostring) {
		// used to validate before set so cannot get from model attr. Returns [{ speed: fff, key: sss }]
		var cursor = 0;
		this._getNextMatch(this._videoprefix, videostring, cursor);
		cursor = this._videoprefix.lastIndex;
		videostring = this._getNextMatch(this._videonosuffix, videostring, cursor);
		cursor = 0;
		// parsed to "fff:kkk,fff:kkk"
		var result = new Array();
		if (!videostring || videostring.length == 0) return result;
		while (cursor < videostring.length) {
			var speed = this._getNextMatch(this._videospeedparse, videostring, cursor);
			if (speed) cursor = this._videospeedparse.lastIndex + 1;
			else return result;
			var key = this._getNextMatch(this._videokeyparse, videostring, cursor);
			if (key) cursor = this._videokeyparse.lastIndex + 1;
			// See the WTF above
			if (_.isArray(key)) key = key[0];
			result.push({speed: speed, key: key});
		}
		return result;
	},
	save_videosource: function(newsource) {
		// newsource either is <video youtube="speed:key, *"/> or just the "speed:key, *" string
		// returns the videosource for the preview which iss the key whose speed is closest to 1
		if (newsource == null) this.save({'intro_video': null}); 
		// TODO remove all whitespace w/in string
		else if (this._getNextMatch(this._videoprefix, newsource, 0)) this.save('intro_video', newsource);
		else this.save('intro_video', '<video youtube="' + newsource + '"/>');
		
		return this.videosourceSample();
	}
});
