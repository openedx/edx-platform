/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
