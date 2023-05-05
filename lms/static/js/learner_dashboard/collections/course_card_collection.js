/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import Backbone from 'backbone';
import CourseCard from '../models/course_card_model';

class CourseCardCollection extends Backbone.Collection {
    constructor(models, options) {
        const defaults = {
            model: CourseCard,
        };
        // eslint-disable-next-line prefer-object-spread
        super(models, Object.assign({}, defaults, options));
    }
}

export default CourseCardCollection;
