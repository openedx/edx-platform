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
	
	urlRoot: function() {
		var location = this.get('location');
		return '/' + location.get('org') + "/" + location.get('course') + '/settings/' + location.get('name') + '/section/details';
	},
	
	_videoprefix : /\s*<video\s*youtube="/g,
	_videospeedparse : /\d+\.?\d*(?=:)/g,
	_videokeyparse : /([^,\/]+)/g,
	_videonosuffix : /[^\"]+/g,
	_getNextMatch : function (regex, string, cursor) {
		regex.lastIndex = cursor;
		return regex.exec(string);
	},
	// the whole string for editing
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
					cursor = this._videospeedparse.lastIndex + 1;
					if (Math.abs(Number(parsedspeed) - 1.0) < Math.abs(bestspeed - 1.0)) {
						bestspeed = Number(parsedspeed);
						bestkey = this._getNextMatch(this._videokeyparse, videostring, cursor);
					}
					else this._getNextMatch(this._videokeyparse, videostring, cursor);
					cursor = this._videokeyparse.lastIndex + 1;
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
	save_videosource: function(newsource) {
		// newsource either is <video youtube="speed:key, *"/> or just the "speed:key, *" string
		// returns the videosource for the preview which iss the key whose speed is closest to 1
		if (newsource == null) this.save({'intro_video': null}); 
		else if (this._getNextMatch(this._videoprefix, newsource, 0)) this.save('intro_video', newsource);
		else this.save('intro_video', '<video youtube="' + newsource + '"/>');
		
		return this.videosourceSample();
	}
});
