window.WordCloud = function(el) {
    RequireJS.require(['WordCloudMain'], function(WordCloudMain) {
        new WordCloudMain(el);
    });
};
