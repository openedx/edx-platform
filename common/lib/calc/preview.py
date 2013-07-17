"""
Provide a `latex_preview` method similar in syntax to `evaluator`.

That is, given a math string, parse it and render each branch of the result,
always returning valid latex.

Because intermediate values of the render contain more data than simply the
string of latex, store it in a custom class `LatexRendered`
"""

from pyparsing import ParseResults
from calc import parse_algebra, add_defaults, SUFFIXES


def PRINT(x):
    PREVIEW_DEBUG = False
    if PREVIEW_DEBUG:
        print x


class LatexRendered(object):
    """
    Data structure to hold a typeset representation of some math.

    Fields:
      -`latex` is a generated, valid latex string (as if it were standalone)
      -`sans_parens` is usually the same as `latex` except without the outermost
       parens (if applicable)
      -`tall` is a boolean representing if the latex has any elements extending
       above or below a normal height, specifically things of the form 'a^b' and
       '\frac{a}{b}'. This affects the height of wrapping parenthesis.
    """
    def __init__(self, latex, parens=None, tall=False):
        """
        Instantiate with the latex representing the math

        Optionally include parenthesis to wrap around it and the height.
        `parens` must be one of '(', '[' or '{'
        `tall` is a boolean (see note above)
        """
        self.latex = latex
        self.sans_parens = latex
        self.tall = tall

        # generate parens and overwrite self.latex
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
    PRINT("rendering number ['{}']".format("', '".join(k.latex for k in children)))
    # TODO exponential notation
    if children[-1].latex in SUFFIXES:
        children[-1].latex = ur"\text{{{suffix}}}".format(suffix=children[-1].latex)
    return LatexRendered("".join(k.latex for k in children))


def variable_closure(variables, casify):
    def render_variable(children):
        # TODO epsilon_0
        # TODO check if valid and color accordingly
        greek = "alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi varphi chi psi omega".split(" ")
        varname = children[0].latex
        PRINT("rendering variable {}".format(varname))
        if casify(varname) not in variables:
            pass

        if varname in greek:
            return LatexRendered(ur"\{letter} ".format(letter=varname))
        else:
            return LatexRendered(varname)  # .replace("_", r"\_"))
    return render_variable


def function_closure(functions, casify):
    def render_function(children):
        fname = children[0].latex
        PRINT("rendering function {}".format(fname))
        if casify(fname) not in functions:
            pass

        inner = children[1].latex
        if fname == "sqrt":
            inner = u"{{{expr}}}".format(expr=inner)
        else:
            if children[1].tall:
                inner = ur"\left({expr}\right)".format(expr=inner)
            else:
                inner = u"({expr})".format(expr=inner)

        if fname == "sqrt":
            fname = ur"\sqrt"
        elif fname == "log10":
            fname = ur"\log_{10}"
        elif fname == "log2":
            fname = ur"\log_2"
        else:
            fname = ur"\text{{{fname}}}".format(fname=fname)

        latex = fname + inner
        return LatexRendered(latex, tall=children[1].tall)
    return render_function


def render_power(children):
    children_latex = [k.latex for k in children if k.latex != "^"]
    children_latex[-1] = children[-1].sans_parens

    PRINT("rendering power ['{}']".format("', '".join(children_latex)))
    raise_power = lambda x, y: u"{}^{{{}}}".format(y, x)
    latex = reduce(raise_power, reversed(children_latex))
    return LatexRendered(latex, tall=True)


def render_parallel(children):
    children_latex = [k.latex for k in children if k.latex != "||"]
    PRINT("rendering parallel ['{}']".format("', '".join(children_latex)))
    latex = r"\|".join(children_latex)
    tall = any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_frac(numerator, denominator):
    # subtlety: avoid parens if there is only thing in that part
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
    PRINT("rendering product ['{}']".format("', '".join(k.latex for k in children)))
    position = "numerator"  # or denominator
    fraction_mode_ever = False
    numerator = []
    denominator = []
    latex = ""

    for kid in children:
        if position == "numerator":
            if kid.latex == "*":
                pass
            elif kid.latex == "/":
                fraction_mode_ever = True
                position = "denominator"
            else:
                numerator.append(kid)
        else:
            if kid.latex == "*":
                # render the current fraction and add it to the latex
                latex += render_frac(numerator, denominator) + r"\cdot "

                # reset back to beginning state
                position = "numerator"
                numerator = []
                denominator = []
            elif kid.latex == "/":
                pass
            else:
                denominator.append(kid)

    if position == "denominator":
        latex += render_frac(numerator, denominator)
    else:
        num_latex = r"\cdot ".join(k.latex for k in numerator)
        latex += num_latex

    tall = fraction_mode_ever or any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_sum(children):
    children_latex = [k.latex for k in children]
    PRINT("rendering sum ['{}']".format("', '".join(children_latex)))
    latex = "".join(children_latex)
    tall = any(k.tall for k in children)
    return LatexRendered(latex, tall=tall)


def render_atom(children):
    PRINT("rendering atom ['{}']".format("', '".join(k.latex for k in children)))
    parens = None
    if children[0].latex in "([{":
        parens = children[0].latex
        children = children[1:-1]
    tall = any(k.tall for k in children)
    PRINT("  -latex: '{}'".format("".join(k.latex for k in children)))
    PRINT("  -parens: '{}'".format(parens))
    PRINT("  -tall: '{}'".format(tall))
    return LatexRendered(
        "".join(k.latex for k in children),
        parens,
        tall
    )


def latex_preview(string, variables=None, functions=None, case_sensitive=False):
    """
    """
    # No need to go further
    if string.strip() == "":
        return "<nada/>"

    # Parse tree
    tree = parse_algebra(string)

    # Get our variables together.
    variables, functions = add_defaults(variables or (), functions or (), case_sensitive)

    # Create a recursion to evaluate the tree.
    if case_sensitive:
        casify = lambda x: x
    else:
        casify = lambda x: x.lower()  # Lowercase for case insens.

    render_action = {
        'number': render_number,
        'variable': variable_closure(set(variables), casify),
        'function': function_closure(set(functions), casify),
        'atom': render_atom,
        'power': render_power,
        'parallel': render_parallel,
        'product': render_product,
        'sum': render_sum
    }

    def render_branch(branch):
        if not isinstance(branch, ParseResults):
            bs = "\\"
            return LatexRendered(branch.replace(bs, bs * 2))

        name = branch.getName()
        if len(branch) == 1 and name not in ("number", "variable"):
            return render_branch(branch[0])
        elif name not in render_action:  # pragma: no cover
            raise Exception(u"Unknown branch name '{}'".format(name))
        else:
            action = render_action[name]
            evaluated_kids = [render_branch(k) for k in branch]
            return action(evaluated_kids)

    # Do it
    return render_branch(tree).latex
