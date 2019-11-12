(function (require) {
    require(['xmodule/assets/word_cloud/src/js/word_cloud_main'], function(WordCloudMain) {
        window.WordCloud = WordCloudMain.default;
    });
}).call(this, require || RequireJS.require);