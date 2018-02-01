import PagingCollection from 'edx-ui-toolkit/js/pagination/paging-collection';
import BookmarkModel from 'course_bookmarks/js/models/bookmark';

class Bookmark extends PagingCollection {
  constructor(models, options) {
    this.queryParams = { // eslint-disable-line no-this-before-super
      course_id() { return this.options.course_id; },
      fields() { return 'display_name,path'; },
    };

    const defaults = {
      model: BookmarkModel,

    };
    super(models, Object.assign(defaults, options));
    this.options = options;
    this.url = options.url;
  }

  url() {
    return this.url;
  }

}

export { Bookmark as default };
