/* globals setFixtures */

import ProgramCardView from '../views/program_card_view';
import ProgramModel from '../models/program_model';
import ProgressCollection from '../collections/program_progress_collection';

describe('Program card View', () => {
  let view = null;
  let programModel;
  const program = {
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
  };
  const userProgress = [
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
  ];
  const progressCollection = new ProgressCollection();
  const cardRenders = ($card) => {
    expect($card).toBeDefined();
    expect($card.find('.title').html().trim()).toEqual(program.title);
    expect($card.find('.category span').html().trim()).toEqual(program.type);
    expect($card.find('.organization').html().trim()).toEqual(program.authoring_organizations[0].key);
    expect($card.find('.card-link').attr('href')).toEqual(program.detail_url);
  };

  beforeEach(() => {
    setFixtures('<div class="program-card"></div>');
    programModel = new ProgramModel(program);
    progressCollection.set(userProgress);
    view = new ProgramCardView({
      model: programModel,
      context: {
        progressCollection,
      },
    });
  });

  afterEach(() => {
    view.remove();
  });

  it('should exist', () => {
    expect(view).toBeDefined();
  });

  it('should load the program-card based on passed in context', () => {
    cardRenders(view.$el);
    expect(view.$el.find('.banner-image').attr('srcset')).toEqual(program.banner_image.small.url);
  });

  it('should call reEvaluatePicture if reLoadBannerImage is called', () => {
    spyOn(ProgramCardView, 'reEvaluatePicture');
    view.reLoadBannerImage();
    expect(ProgramCardView.reEvaluatePicture).toHaveBeenCalled();
  });

  it('should handle exceptions from reEvaluatePicture', () => {
    const message = 'Picturefill had exceptions';

    spyOn(ProgramCardView, 'reEvaluatePicture').and.callFake(() => {
      const error = { name: message };

      throw error;
    });
    view.reLoadBannerImage();
    expect(ProgramCardView.reEvaluatePicture).toHaveBeenCalled();
    expect(view.reLoadBannerImage).not.toThrow(message);
  });

  it('should show the right number of progress bar segments', () => {
    expect(view.$('.progress-bar .completed').length).toEqual(4);
    expect(view.$('.progress-bar .enrolled').length).toEqual(2);
  });

  it('should display the correct course status numbers', () => {
    expect(view.$('.number-circle').text()).toEqual('424');
  });

  it('should render cards if there is no progressData', () => {
    view.remove();
    view = new ProgramCardView({
      model: programModel,
      context: {},
    });
    cardRenders(view.$el);
    expect(view.$('.progress').length).toEqual(0);
  });

  it('should render cards if there are missing banner images', () => {
    view.remove();
    const programNoBanner = JSON.parse(JSON.stringify(program));
    delete programNoBanner.banner_image;
    programModel = new ProgramModel(programNoBanner);
    view = new ProgramCardView({
      model: programModel,
      context: {},
    });
    cardRenders(view.$el);
    expect(view.$el.find('.banner-image').attr('srcset')).toEqual('');
  });

  it('should render cards if there are missing banner image sizes', () => {
    view.remove();
    const programNoBanner = JSON.parse(JSON.stringify(program));
    delete programNoBanner.banner_image['x-small'];
    delete programNoBanner.banner_image.small;

    programModel = new ProgramModel(programNoBanner);
    view = new ProgramCardView({
      model: programModel,
      context: {},
    });
    cardRenders(view.$el);
    expect(view.$el.find('.banner-image').attr('srcset')).toEqual('');
  });
});
