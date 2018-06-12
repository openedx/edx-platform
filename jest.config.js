module.exports = {
  "globals": {
    "gettext": (t) => { return t; },
  },
  "modulePaths": [
    "common/static/common/js/components",
  ],
  "testMatch": [
    "**/ProblemBrowser/**/*.test.jsx",
    "common/static/common/js/components/**/?(*.)+(spec|test).js?(x)",
  ],
  "transform": {
    "^.+\\.jsx$": "babel-jest",
    "^.+\\.js$": "babel-jest",
  },
}
