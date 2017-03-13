const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');

const isProd = process.env.NODE_ENV === 'production';

const wpconfig = {
  context: __dirname,

  entry: {
    CourseOutline: './openedx/features/course_experience/static/course_experience/js/CourseOutline.js',
  },

  output: {
      path: path.resolve(__dirname, 'common/static/bundles'),
      filename: '[name]-[hash].js',
      libraryTarget: 'window',
  },

  plugins: [
    new webpack.NoEmitOnErrorsPlugin(),
    new webpack.NamedModulesPlugin(),
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    }),
    new webpack.LoaderOptionsPlugin({
      debug: !isProd,
    }),
    new BundleTracker({
      filename: './webpack-stats.json'
    }),
  ],

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: 'babel-loader',
      },
    ],
  },
  resolve: {
    extensions: ['.js', '.json'],
  }
};

if (isProd) {
  wpconfig.plugins = [
    new webpack.LoaderOptionsPlugin({
      minimize: true,
    }),
    new webpack.optimize.UglifyJsPlugin(),
    ...wpconfig.plugins,
  ];
}

module.exports = wpconfig;
