import Backbone from 'backbone';

/**
 * Model for Course Programs.
 */
class ProgramModel extends Backbone.Model {
  initialize(data) {
    if (data) {
      this.set({
        title: data.title,
        type: data.type,
        subtitle: data.subtitle,
        authoring_organizations: data.authoring_organizations,
        detailUrl: data.detail_url,
        xsmallBannerUrl: (data.banner_image && data.banner_image['x-small']) ? data.banner_image['x-small'].url : '',
        smallBannerUrl: (data.banner_image && data.banner_image.small) ? data.banner_image.small.url : '',
        mediumBannerUrl: (data.banner_image && data.banner_image.medium) ? data.banner_image.medium.url : '',
        breakpoints: {
          max: {
            xsmall: '320px',
            small: '540px',
            medium: '768px',
            large: '979px',
          },
        },
      });
    }
  }
}

export default ProgramModel;
