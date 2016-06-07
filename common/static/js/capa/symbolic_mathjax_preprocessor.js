/* This file defines a processor in between the student's math input
   (AsciiMath) and what is read by MathJax. It allows for our own
   customizations, such as use of the syntax "a_b__x" in superscripts, or
   possibly coloring certain variables, etc&.

   It is used in the <textline> definition like the following:

     <symbolicresponse expect="a_b^c + b_x__d" size="30">
       <textline math="1"
         preprocessorClassName="SymbolicMathjaxPreprocessor"
	 preprocessorSrc="/static/js/capa/symbolic_mathjax_preprocessor.js"/>
     </symbolicresponse>
*/
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
      // input, which is too bad. This would be preferable to this char tag
    }

    return eqn;
  };
};
