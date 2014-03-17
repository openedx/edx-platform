"""
Provide a `latex_preview` method similar in syntax to `evaluator`.

That is, given a math string, parse it and render each branch of the result,
always returning valid latex.

Because intermediate values of the render contain more data than simply the
string of latex, store it in a custom class `LatexRendered`.
"""

from calc import ParseAugmenter, DEFAULT_VARIABLES, DEFAULT_FUNCTIONS, SUFFIXES


class LatexRendered(object):
    """
    Data structure to hold a typeset representation of some math.

    Fields:
     -`latex` is a generated, valid latex string (as if it were standalone).
     -`sans_parens` is usually the same as `latex` except without the outermost
      parens (if applicable).
     -`tall` is a boolean representing if the latex has any elements extending
      above or below a normal height, specifically things of the form 'a^b' and
      '\frac{a}{b}'. This affects the height of wrapping parenthesis.
    """
    def __init__(self, latex, parens=None, tall=False):
        """
        Instantiate with the latex representing the math.

        Optionally include parenthesis to wrap around it and the height.
        `parens` must be one of '(', '[' or '{'.
        `tall` is a boolean (see note above).
        """
        self.latex = latex
        self.sans_parens = latex
        self.tall = tall

        # Generate parens and overwrite `self.latex`.
        if parens is not None:
            left_parens = parens
            if left_parens == '{':
                left_parens = r'\{'

            pairs = {'(': ')',
                     '[': ']',
                     r'\{': r'\}'}
            if left_parens not in pairs:
                raise Exception(
                    u"Unknown parenthesis '{}': coder error".format(left_parens)
                )
            right_parens = pairs[left_parens]

            if self.tall:
                left_parens = r"\left" + left_parens
                right_parens = r"\right" + right_parens

            self.latex = u"{left}{expr}{right}".format(
                left=left_parens,
                expr=latex,
                right=right_parens
            )

    def __repr__(self):  # pragma: no cover
        """
        Give a sensible representation of the object.

        If `sans_parens` is different, include both.
        If `tall` then have '<[]>' around the code, otherwise '<>'.
        """
        if self.latex == self.sans_parens:
            latex_repr = u'"{}"'.format(self.latex)
        else:
            latex_repr = u'"{}" or "{}"'.format(self.latex, self.sans_parens)

        if self.tall:
            wrap = u'<[{}]>'
        else:
            wrap = u'<{}>'

        return wrap.format(latex_repr)


def render_number(children):
    """
    Combine the elements forming the number, escaping the suffix if needed.
    """
    children_latex = [k.latex for k in children]

    suffix = ""
    if children_latex[-1] in SUFFIXES:
        suffix = children_latex.pop()
        suffix = ur"\text{{{s}}}".format(s=suffix)

    # Exponential notation-- the "E" splits the mantissa and exponent
    if "E" in children_latex:
        pos = children_latex.index("E")
        mantissa = "".join(children_latex[:pos])
        exponent = "".join(children_latex[pos + 1:])
        latex = ur"{m}\!\times\!10^{{{e}}}{s}".format(
            m=mantissa, e=exponent, s=suffix
        )
        return LatexRendered(latex, tall=True)
    else:
        easy_number = "".join(children_latex)
        return LatexRendered(easy_number + suffix)


def enrich_varname(varname):
    """
    Prepend a backslash if we're given a greek character.
    """
    greek = ("alpha beta gamma delta epsilon varepsilon zeta eta theta "
             "vartheta iota kappa lambda mu nu xi pi rho sigma tau upsilon "
             "phi varphi chi psi omega").split()

    # add capital greek letters
    greek += [x.capitalize() for x in greek]

    # add hbar for QM
    greek.append('hbar')

    # add infinity
    greek.append('infty')

    if varname in greek:
        return ur"\{letter}".format(letter=varname)
    else:
        return varname.replace("_", r"\_")


def variable_closure(variables, casify):
    """
    Wrap `render_variable` so it knows the variables allowed.
    """
    def render_variable(children):
        """
        Replace greek letters, otherwise escape the variable names.
        """
        varname = children[0].latex
        if casify(varname) not in variables:
            pass  # TODO turn unknown variable red or give some kind of error

        first, _, second = varname.partition("_")

        if second:
            # Then 'a_b' must become 'a_{b}'
            varname = ur"{a}_{{{b}}}".format(
                a=enrich_varname(first),
                b=enrich_varname(second)
            )
        else:
            varname = enrich_varname(varname)

        return LatexRendered(varname)  # .replace("_", r"\_"))
    return render_variable


def function_closure(functions, casify):
    """
    Wrap `render_function` so it knows the functions allowed.
    """
    def render_function(children):
        """
        Escape function names and give proper formatting to exceptions.

        The exceptions being 'sqrt', 'log2', and 'log10' as of now.
        """
        fname = children[0].latex
        if casify(fname) not in functions:
            pass  # TODO turn unknown function red or give some kind of error

        # Wrap the input of the function with parens or braces.
        inner = children[1].latex
        if fname == "sqrt":
            inner = u"{{{expr}}}".format(expr=inner)
        else:
            if children[1].tall:
                inner = ur"\left({expr}\right)".format(expr=inner)
            else:
                inner = u"({expr})".format(expr=inner)

        # Correctly format the name of the function.
        if fname == "sqrt":
            fname = ur"\sqrt"
        elif fname == "log10":
            fname = ur"\log_{10}"
        elif fname == "log2":
            fname = ur"\log_2"
        else:
            fname = ur"\text{{{fname}}}".format(fname=fname)

        # Put it together.
        latex = fname + inner
        return LatexRendered(latex, tall=children[1].tall)
    # Return the function within the closure.
    return render_function


def render_power(children):
    """
    Combine powers so that the latex is wrapped in curly braces correctly.

    Also, if you have 'a^(b+c)' don't include that last set of parens:
    'a^{b+c}' is correct, whereas 'a^{(b+c)}' is extraneous.
    """
    if len(children) == 1:
        return children[0]

    children_latex = [k.latex for k in children if k.latex != "^"]
    children_latex[-1] = children[-1].sans_parens

    raise_power = lambda x, y: u"{}^{{{}}}".format(y, x)
    latex = reduce(raise_power, reversed(children_latex))
    return LatexRendered(latex, tall=True)


def render_parallel(children):
    """
    Simply join the child nodes with a double vertical line.
    """
    if len(children) == 1:
        return children[0]

    children_latex = [k.latex for k in children if k.latex != "||"]
    latex = r"\|".join(children_latex)
    tall = any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_frac(numerator, denominator):
    r"""
    Given a list of elements in the numerator and denominator, return a '\frac'

    Avoid parens if they are unnecessary (i.e. the only thing in that part).
    """
    if len(numerator) == 1:
        num_latex = numerator[0].sans_parens
    else:
        num_latex = r"\cdot ".join(k.latex for k in numerator)

    if len(denominator) == 1:
        den_latex = denominator[0].sans_parens
    else:
        den_latex = r"\cdot ".join(k.latex for k in denominator)

    latex = ur"\frac{{{num}}}{{{den}}}".format(num=num_latex, den=den_latex)
    return latex


def render_product(children):
    r"""
    Format products and division nicely.

    Group bunches of adjacent, equal operators. Every time it switches from
    denominator to the next numerator, call `render_frac`. Join these groupings
    together with '\cdot's, ending on a numerator if needed.

    Examples: (`children` is formed indirectly by the string on the left)
      'a*b' -> 'a\cdot b'
      'a/b' -> '\frac{a}{b}'
      'a*b/c/d' -> '\frac{a\cdot b}{c\cdot d}'
      'a/b*c/d*e' -> '\frac{a}{b}\cdot \frac{c}{d}\cdot e'
    """
    if len(children) == 1:
        return children[0]

    position = "numerator"  # or denominator
    fraction_mode_ever = False
    numerator = []
    denominator = []
    latex = ""

    for kid in children:
        if position == "numerator":
            if kid.latex == "*":
                pass  # Don't explicitly add the '\cdot' yet.
            elif kid.latex == "/":
                # Switch to denominator mode.
                fraction_mode_ever = True
                position = "denominator"
            else:
                numerator.append(kid)
        else:
            if kid.latex == "*":
                # Switch back to numerator mode.
                # First, render the current fraction and add it to the latex.
                latex += render_frac(numerator, denominator) + r"\cdot "

                # Reset back to beginning state
                position = "numerator"
                numerator = []
                denominator = []
            elif kid.latex == "/":
                pass  # Don't explicitly add a '\frac' yet.
            else:
                denominator.append(kid)

    # Add the fraction/numerator that we ended on.
    if position == "denominator":
        latex += render_frac(numerator, denominator)
    else:
        # We ended on a numerator--act like normal multiplication.
        num_latex = r"\cdot ".join(k.latex for k in numerator)
        latex += num_latex

    tall = fraction_mode_ever or any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_sum(children):
    """
    Concatenate elements, including the operators.
    """
    if len(children) == 1:
        return children[0]

    children_latex = [k.latex for k in children]
    latex = "".join(children_latex)
    tall = any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_atom(children):
    """
    Properly handle parens, otherwise this is trivial.
    """
    if len(children) == 3:
        return LatexRendered(
            children[1].latex,
            parens=children[0].latex,
            tall=children[1].tall
        )
    else:
        return children[0]


def add_defaults(var, fun, case_sensitive=False):
    """
    Create sets with both the default and user-defined variables.

    Compare to calc.add_defaults
    """
    var_items = set(DEFAULT_VARIABLES)
    fun_items = set(DEFAULT_FUNCTIONS)

    var_items.update(var)
    fun_items.update(fun)

    if not case_sensitive:
        var_items = set(k.lower() for k in var_items)
        fun_items = set(k.lower() for k in fun_items)

    return var_items, fun_items


def latex_preview(math_expr, variables=(), functions=(), case_sensitive=False):
    """
    Convert `math_expr` into latex, guaranteeing its parse-ability.

    Analagous to `evaluator`.
    """
    # No need to go further
    if math_expr.strip() == "":
        return ""

    # Parse tree
    latex_interpreter = ParseAugmenter(math_expr, case_sensitive)
    latex_interpreter.parse_algebra()

    # Get our variables together.
    variables, functions = add_defaults(variables, functions, case_sensitive)

    # Create a recursion to evaluate the tree.
    if case_sensitive:
        casify = lambda x: x
    else:
        casify = lambda x: x.lower()  # Lowercase for case insens.

    render_actions = {
        'number': render_number,
        'variable': variable_closure(variables, casify),
        'function': function_closure(functions, casify),
        'atom': render_atom,
        'power': render_power,
        'parallel': render_parallel,
        'product': render_product,
        'sum': render_sum
    }

    backslash = "\\"
    wrap_escaped_strings = lambda s: LatexRendered(
        s.replace(backslash, backslash * 2)
    )

    output = latex_interpreter.reduce_tree(
        render_actions,
        terminal_converter=wrap_escaped_strings
    )
    return output.latex
