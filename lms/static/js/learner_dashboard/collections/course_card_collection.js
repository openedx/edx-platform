import Backbone from 'backbone';
import CourseCard from '../models/course_card_model';

class CourseCardCollection extends Backbone.Collection {
  constructor(models, options) {
    const defaults = {
      model: CourseCard,
    };
    super(models, Object.assign({}, defaults, options));
  }
}

export default CourseCardCollection;
