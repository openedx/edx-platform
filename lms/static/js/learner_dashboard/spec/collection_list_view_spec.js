/* globals setFixtures */

import CollectionListView from '../views/collection_list_view';
import ProgramCardView from '../views/program_card_view';
import ProgramCollection from '../collections/program_collection';
import ProgressCollection from '../collections/program_progress_collection';

describe('Collection List View', () => {
  let view = null;
  let programCollection;
  let progressCollection;
  const context = {
    programsData: [
      {
        uuid: 'a87e5eac-3c93-45a1-a8e1-4c79ca8401c8',
        title: 'Food Security and Sustainability',
        subtitle: 'Learn how to feed all people in the world in a sustainable way.',
        type: 'XSeries',
        detail_url: 'https://www.edx.org/foo/bar',
        banner_image: {
          medium: {
            height: 242,
            width: 726,
            url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.medium.jpg',
          },
          'x-small': {
            height: 116,
            width: 348,
            url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.x-small.jpg',
          },
          small: {
            height: 145,
            width: 435,
            url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.small.jpg',
          },
          large: {
            height: 480,
            width: 1440,
            url: 'https://example.com/a87e5eac-3c93-45a1-a8e1-4c79ca8401c8.large.jpg',
          },
        },
        authoring_organizations: [
          {
            uuid: '0c6e5fa2-96e8-40b2-9ebe-c8b0df2a3b22',
            key: 'WageningenX',
            name: 'Wageningen University & Research',
          },
        ],
      },
      {
        uuid: '91d144d2-1bb1-4afe-90df-d5cff63fa6e2',
        title: 'edX Course Creator',
        subtitle: 'Become an expert in creating courses for the edX platform.',
        type: 'XSeries',
        detail_url: 'https://www.edx.org/foo/bar',
        banner_image: {
          medium: {
            height: 242,
            width: 726,
            url: 'https://example.com/91d144d2-1bb1-4afe-90df-d5cff63fa6e2.medium.jpg',
          },
          'x-small': {
            height: 116,
            width: 348,
            url: 'https://example.com/91d144d2-1bb1-4afe-90df-d5cff63fa6e2.x-small.jpg',
          },
          small: {
            height: 145,
            width: 435,
            url: 'https://example.com/91d144d2-1bb1-4afe-90df-d5cff63fa6e2.small.jpg',
          },
          large: {
            height: 480,
            width: 1440,
            url: 'https://example.com/91d144d2-1bb1-4afe-90df-d5cff63fa6e2.large.jpg',
          },
        },
        authoring_organizations: [
          {
            uuid: '4f8cb2c9-589b-4d1e-88c1-b01a02db3a9c',
            key: 'edX',
            name: 'edX',
          },
        ],
      },
    ],
    userProgress: [
      {
        uuid: 'a87e5eac-3c93-45a1-a8e1-4c79ca8401c8',
        completed: 4,
        in_progress: 2,
        not_started: 4,
      },
      {
        uuid: '91d144d2-1bb1-4afe-90df-d5cff63fa6e2',
        completed: 1,
        in_progress: 0,
        not_started: 3,
      },
    ],
  };

  beforeEach(() => {
    setFixtures('<div class="program-cards-container"></div>');
    programCollection = new ProgramCollection(context.programsData);
    progressCollection = new ProgressCollection();
    progressCollection.set(context.userProgress);
    context.progressCollection = progressCollection;

    view = new CollectionListView({
      el: '.program-cards-container',
      childView: ProgramCardView,
      collection: programCollection,
      context,
    });
    view.render();
  });

  afterEach(() => {
    view.remove();
  });

  it('should exist', () => {
    expect(view).toBeDefined();
  });

  it('should load the collection items based on passed in collection', () => {
    const $cards = view.$el.find('.program-card');
    expect($cards.length).toBe(2);
    $cards.each((index, el) => {
      // eslint-disable-next-line newline-per-chained-call
      expect($(el).find('.title').html().trim()).toEqual(context.programsData[index].title);
    });
  });

  it('should display no item if collection is empty', () => {
    view.remove();
    programCollection = new ProgramCollection([]);
    view = new CollectionListView({
      el: '.program-cards-container',
      childView: ProgramCardView,
      context: {},
      collection: programCollection,
    });
    view.render();
    const $cards = view.$el.find('.program-card');
    expect($cards.length).toBe(0);
  });

  it('should have no title when title not provided', () => {
    setFixtures('<div class="test-container"><div class="program-cards-container"></div></div>');
    view.remove();
    view.render();
    expect(view).toBeDefined();
    const $title = view.$el.parent().find('.collection-title');
    expect($title.html()).not.toBeDefined();
  });

  it('should display screen reader header when provided', () => {
    const titleContext = { el: 'h2', title: 'list start' };

    view.remove();
    setFixtures('<div class="test-container"><div class="program-cards-container"></div></div>');
    programCollection = new ProgramCollection(context.programsData);
    view = new CollectionListView({
      el: '.program-cards-container',
      childView: ProgramCardView,
      context,
      collection: programCollection,
      titleContext,
    });
    view.render();
    const $title = view.$el.parent().find('.collection-title');
    expect($title.html()).toBe(titleContext.title);
  });
});
