import WordCloudMain from './word_cloud_main';

function WordCloud(el) {
  return new WordCloudMain(el);
}

window.WordCloud = WordCloud;
