import Backbone from 'backbone';

/**
 *  Store data to enroll learners into the course
 */
class CourseEnrollModel extends Backbone.Model {
    constructor(attrs, ...args) {
        const defaults = {
            course_id: '',
            optIn: false,
        };
        // eslint-disable-next-line prefer-object-spread
        super(Object.assign({}, defaults, attrs), ...args);
    }
}

export default CourseEnrollModel;
