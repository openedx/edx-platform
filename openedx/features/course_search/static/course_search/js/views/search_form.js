'use strict';

import 'jquery';
import Backbone from 'backbone';

class SearchForm extends Backbone.View {
  constructor(options) {
    const defaults = {
      el: '',
      events: {
        'submit .search-form': 'submitForm',
        'click .cancel-button': 'clearSearch',
      },
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(options) {
    this.$searchField = this.$el.find('.search-field');
    this.$searchButton = this.$el.find('.search-button');
    this.$cancelButton = this.$el.find('.cancel-button');
    this.supportsActive = options.supportsActive === undefined ? true : options.supportsActive;
  }

  submitForm(event) {
    event.preventDefault();
    this.doSearch();
  }

  doSearch(term) {
    let trimmedTerm;
    if (term) {
      trimmedTerm = term.trim();
      this.$searchField.val(trimmedTerm);
    } else {
      trimmedTerm = this.$searchField.val().trim();
    }
    if (trimmedTerm) {
      this.setActiveStyle();
      this.trigger('search', trimmedTerm);
    } else {
      this.clearSearch();
    }
  }

  resetSearchForm() {
    this.$searchField.val('');
    this.setInitialStyle();
  }

  clearSearch() {
    this.resetSearchForm();
    this.trigger('clear');
  }

  setActiveStyle() {
    if (this.supportsActive) {
      this.$searchField.addClass('is-active');
      this.$searchButton.hide();
      this.$cancelButton.show();
    }
  }

  setInitialStyle() {
    if (this.supportsActive) {
      this.$searchField.removeClass('is-active');
      this.$searchButton.show();
      this.$cancelButton.hide();
    }
  }
}
export { SearchForm as default };
