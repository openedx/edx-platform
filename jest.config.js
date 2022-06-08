const { createConfig } = require('@edx/frontend-build');

module.exports = createConfig('jest', {
  "globals": {
    "gettext": (t) => { return t; },
  },
  "modulePaths": [
    "common/static/common/js/components",
  ],
  "setupFilesAfterEnv": ["<rootDir>/setupTests.js"],
  "testMatch": [
    "/**/*.test.jsx",
    "common/static/common/js/components/**/?(*.)+(spec|test).js?(x)",
  ],
  "testEnvironment": "jsdom",
  "transform": {
    "^.+\\.jsx$": "babel-jest",
    "^.+\\.js$": "babel-jest",
  }
});
