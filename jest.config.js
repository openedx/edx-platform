module.exports = {
  "globals": {
    "gettext": (t) => { return t; },
  },
  "modulePaths": [
    "common/static/common/js/components",
  ],
  "setupTestFrameworkScriptFile": "<rootDir>/setupTests.js",
  "testMatch": [
    "/**/*.test.jsx",
    "common/static/common/js/components/**/?(*.)+(spec|test).js?(x)",
  ],
  "transform": {
    "^.+\\.jsx$": "babel-jest",
    "^.+\\.js$": "babel-jest",
  },
};
