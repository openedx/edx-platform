// single per course holds the updates and handouts
CMS.Models.CourseInfo = Backbone.Model.extend({
	// This model class is not suited for restful operations and is considered just a server side initialized container
	url: '',

	defaults: {
		"courseId": "", // the location url
		"updates" : null,	// UpdateCollection
		"handouts": null	// HandoutCollection
		},

	idAttribute : "courseId"
});

// course update -- biggest kludge here is the lack of a real id to map updates to originals
CMS.Models.CourseUpdate = Backbone.Model.extend({
	defaults: {
		"date" : $.datepicker.formatDate('MM d, yy', new Date()),
		"content" : ""
	}
});

/*
	The intitializer of this collection must set id to the update's location.url and courseLocation to the course's location. Must pass the
	collection of updates as [{ date : "month day", content : "html"}]
*/
CMS.Models.CourseUpdateCollection = Backbone.Collection.extend({
	url : function() {return this.urlbase  + "course_info/updates/";},

	model : CMS.Models.CourseUpdate
});





