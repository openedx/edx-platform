import Backbone from 'backbone';

class Bookmark extends Backbone.Model {
  constructor(models, option) {
    const defaults = {
      idAttribute: 'id',
      defaults: {
        course_id: '',
        usage_id: '',
        display_name: '',
        path: [],
        created: '',
      },
      blockUrl: () => `/courses/${this.get('course_id')}/jump_to/${this.get('usage_id')}`,
    };
    super(models, Object.assign(defaults, option));
  }
}

export default Bookmark;
