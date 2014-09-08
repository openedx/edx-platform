.. _MathJax in Studio:

############################################
A Brief Introduction to MathJax in Studio
############################################

To write clear and professional-looking symbols and equations, we use a LaTeX-like 
language called
`MathJax <http://www.google.com/url?q=http%3A%2F%2Fwww.mathjax.org%2F&sa=D&sntz=1&usg=AFQjCNGef2H-mZCdmCo7-kWHfu9fUGVCfg>`_.
Your MathJax equations can appear with other text in the paragraph (inline equations) or
on their own lines (display equations).

- For inline equations, you can do either of the following.

  - Surround your Mathjax expression with backslashes and **parentheses**.
    
    ``\( equation \)``

  - Surround your Mathjax expression with [mathjaxinline] tags. Note that these 
    tags use square brackets ([]).

    [mathjaxinline] equation [/mathjaxinline]
    
- For display equations, you can do either of the following.

  - Surround your Mathjax expression with backslashes and **brackets**.

    ``\[ equation \]``

  - Surround your Mathjax expression with [mathjax] tags. Note that these tags use 
    square brackets ([]).

    [mathjax] equation [/mathjax]

You can use MathJax in HTML (text) components and in Problem components.

.. note:: Complete MathJax documentation (together with a testing tool) can be 
          found at `http://www.onemathematicalcat.org/MathJaxDocumentation/TeXSyntax.htm <http://www.google.com/url?q=http%3A%2F%2Fwww.onemathematicalcat.org%2FMathJaxDocumentation%2FTeXSyntax.htm&sa=D&sntz=1&usg=AFQjCNEV8PtCX6Csp0lW7lDKOLIKCOCkHg>`_.

****************************
HTML (Text) Components
****************************

In the HTML component editor, you can use MathJax both in Visual view and in HTML view.

.. image:: /Images/MathJax_HTML.png
 :alt: Image of an HTML component with MathJax in both the Visual and HTML views

*********************
Problem Components
*********************

In the Problem component editor, you can use MathJax both in the Simple Editor 
and in the Advanced Editor.

In the example problem below, note that the Einstein equation in the
explanation is enclosed in backslashes and parentheses, so it appears inline with the text. The
Navier-Stokes equation is enclosed in backslashes and brackets, so it appears on its
own line.

.. image:: /Images/MathJax_Problem.png
 :alt: Image of a problem component with MathJax in both the Visual and HTML views