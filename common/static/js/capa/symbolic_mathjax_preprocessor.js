window.SymbolicMathjaxPreprocessor = function () {
    this.fn = function (eqn) {
      // flags and config
      var superscriptsOn = true;

      if (superscriptsOn) {
	// find instances of "__" and make them superscripts ("^") and tag them
	// as such. Specifcally replace instances of "__X" or "__{XYZ}" with
	// "^{CHAR$1}", marking superscripts as different from powers

	// a zero width space--this is an invisible character that no one would
	// use, that gets passed through MathJax and to the server
	var c = "\u200b";
	eqn = eqn.replace(/__(?:([^\{])|\{([^\}]+)\})/g, '^{' + c + '$1$2}');

	// NOTE: MathJax supports '\class{name}{mathcode}' but not for asciimath
	// input, which is too bad. This would be preferable to the char tag
      }

      return eqn;
    };
};
