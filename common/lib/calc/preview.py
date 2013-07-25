"""
Provide a `latex_preview` method similar in syntax to `evaluator`.

That is, given a math string, parse it and render each branch of the result,
always returning valid latex.

Because intermediate values of the render contain more data than simply the
string of latex, store it in a custom class `LatexRendered`.
"""

from calc import ParseAugmenter, add_defaults, SUFFIXES


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


def render_number(children):
    """
    Combine the elements forming the number, escaping the suffix if needed.
    """
    # TODO exponential notation
    if children[-1].latex in SUFFIXES:
        children[-1].latex = ur"\text{{{suffix}}}".format(suffix=children[-1].latex)
    return LatexRendered("".join(k.latex for k in children))


def variable_closure(variables, casify):
    """
    Wrap `render_variable` so it knows the variables allowed.
    """
    def render_variable(children):
        """
        Replace greek letters, otherwise escape the variable names.
        """
        # TODO epsilon_0
        # TODO check if valid and color accordingly
        greek = "alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi varphi chi psi omega".split(" ")
        varname = children[0].latex
        if casify(varname) not in variables:
            pass

        if varname in greek:
            return LatexRendered(ur"\{letter} ".format(letter=varname))
        else:
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
            pass

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
    children_latex = [k.latex for k in children]
    latex = "".join(children_latex)
    tall = any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_atom(children):
    """
    Properly handle parens, otherwise this is trivial.
    """
    parens = None
    if children[0].latex in "([{":
        # then len(children) == 3
        parens = children[0].latex
        children = [children[1]]
    return LatexRendered(
        children[0].latex,
        parens,
        children[0].tall
    )


def latex_preview(math_expr, variables=(), functions=(), case_sensitive=False):
    """
    Convert `math_expr` into latex, guaranteeing its parse-ability.

    Analagous to `evaluator`.
    """
    # No need to go further
    if math_expr.strip() == "":
        return "<nada/>"

    # Parse tree
    thing = ParseAugmenter(math_expr, case_sensitive)
    thing.parse_algebra()

    # Get our variables together.
    variables, functions = add_defaults(variables, functions, case_sensitive)

    # Create a recursion to evaluate the tree.
    if case_sensitive:
        casify = lambda x: x
    else:
        casify = lambda x: x.lower()  # Lowercase for case insens.

    render_actions = {
        'number': render_number,
        'variable': variable_closure(set(variables), casify),
        'function': function_closure(set(functions), casify),
        'atom': render_atom,
        'power': render_power,
        'parallel': render_parallel,
        'product': render_product,
        'sum': render_sum
    }

    bksh = "\\"
    wrap_escaped_strings = lambda s: LatexRendered(s.replace(bksh, bksh * 2))

    output = thing.handle_tree(render_actions, wrap_escaped_strings)
    return output.latex
