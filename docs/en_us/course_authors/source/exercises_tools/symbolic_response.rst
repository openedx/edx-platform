.. _Symbolic Response:

#################
Symbolic Response
#################

This document plans to document features that the current symbolic response
supports. In general it allows the input and validation of math expressions,
up to commutativity and some identities.


********
Features
********

This is a partial list of features, to be revised as we go along:
    * sub and superscripts: an expression following the ``^`` character
      indicates exponentiation. To use superscripts in variables, the syntax
      is ``b_x__d`` for the variable ``b`` with subscript ``x`` and super
      ``d``. 

      An example of a problem::

        <symbolicresponse expect="a_b^c + b_x__d" size="30">
          <textline math="1"
           preprocessorClassName="SymbolicMathjaxPreprocessor"
           preprocessorSrc="/static/js/capa/symbolic_mathjax_preprocessor.js"/>
        </symbolicresponse>

      It's a bit of a pain to enter that.

    * The script-style math variant. What would be outputted in latex if you
      entered ``\mathcal{N}``. This is used in some variables.

      An example::

          <symbolicresponse expect="scriptN_B + x" size="30">
            <textline math="1"/>
          </symbolicresponse>

      There is no fancy preprocessing needed, but if you had superscripts or
      something, you would need to include that part.
