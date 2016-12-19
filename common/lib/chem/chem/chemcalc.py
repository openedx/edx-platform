from __future__ import division
from fractions import Fraction

from pyparsing import (Literal, StringEnd, OneOrMore, ParseException)
import nltk
from nltk.tree import Tree

ARROWS = ('<->', '->')

## Defines a simple pyparsing tokenizer for chemical equations
elements = ['Ac', 'Ag', 'Al', 'Am', 'Ar', 'As', 'At', 'Au', 'B', 'Ba', 'Be',
            'Bh', 'Bi', 'Bk', 'Br', 'C', 'Ca', 'Cd', 'Ce', 'Cf', 'Cl', 'Cm',
            'Cn', 'Co', 'Cr', 'Cs', 'Cu', 'Db', 'Ds', 'Dy', 'Er', 'Es', 'Eu',
            'F', 'Fe', 'Fl', 'Fm', 'Fr', 'Ga', 'Gd', 'Ge', 'H', 'He', 'Hf',
            'Hg', 'Ho', 'Hs', 'I', 'In', 'Ir', 'K', 'Kr', 'La', 'Li', 'Lr',
            'Lu', 'Lv', 'Md', 'Mg', 'Mn', 'Mo', 'Mt', 'N', 'Na', 'Nb', 'Nd',
            'Ne', 'Ni', 'No', 'Np', 'O', 'Os', 'P', 'Pa', 'Pb', 'Pd', 'Pm',
            'Po', 'Pr', 'Pt', 'Pu', 'Ra', 'Rb', 'Re', 'Rf', 'Rg', 'Rh', 'Rn',
            'Ru', 'S', 'Sb', 'Sc', 'Se', 'Sg', 'Si', 'Sm', 'Sn', 'Sr', 'Ta',
            'Tb', 'Tc', 'Te', 'Th', 'Ti', 'Tl', 'Tm', 'U', 'Uuo', 'Uup',
            'Uus', 'Uut', 'V', 'W', 'Xe', 'Y', 'Yb', 'Zn', 'Zr']
digits = map(str, range(10))
symbols = list("[](){}^+-/")
phases = ["(s)", "(l)", "(g)", "(aq)"]
tokens = reduce(lambda a, b: a ^ b, map(Literal, elements + digits + symbols + phases))
tokenizer = OneOrMore(tokens) + StringEnd()


def _orjoin(l):
    return "'" + "' | '".join(l) + "'"

## Defines an NLTK parser for tokenized expressions
grammar = """
  S -> multimolecule | multimolecule '+' S
  multimolecule -> count molecule | molecule
  count -> number | number '/' number
  molecule -> unphased | unphased phase
  unphased -> group | paren_group_round | paren_group_square
  element -> """ + _orjoin(elements) + """
  digit -> """ + _orjoin(digits) + """
  phase -> """ + _orjoin(phases) + """
  number -> digit | digit number
  group -> suffixed | suffixed group
  paren_group_round -> '(' group ')'
  paren_group_square -> '[' group ']'
  plus_minus -> '+' | '-'
  number_suffix -> number
  ion_suffix -> '^' number plus_minus | '^' plus_minus
  suffix -> number_suffix | number_suffix ion_suffix | ion_suffix
  unsuffixed -> element | paren_group_round | paren_group_square

  suffixed -> unsuffixed | unsuffixed suffix
"""
# This will be lazily loaded...
parser = None

def _clean_parse_tree(tree):
    ''' The parse tree contains a lot of redundant
    nodes. E.g. paren_groups have groups as children, etc. This will
    clean up the tree.
    '''
    def unparse_number(n):
        ''' Go from a number parse tree to a number '''
        if len(n) == 1:
            rv = n[0][0]
        else:
            rv = n[0][0] + unparse_number(n[1])
        return rv

    def null_tag(n):
        ''' Remove a tag '''
        return n[0]

    def ion_suffix(n):
        '''1. "if" part handles special case
           2. "else" part is general behaviour '''

        if n[1:][0].node == 'number' and n[1:][0][0][0] == '1':
            # if suffix is explicitly 1, like ^1-
            # strip 1, leave only sign: ^-
            return nltk.tree.Tree(n.node, n[2:])
        else:
            return nltk.tree.Tree(n.node, n[1:])

    dispatch = {'number': lambda x: nltk.tree.Tree("number", [unparse_number(x)]),
                'unphased': null_tag,
                'unsuffixed': null_tag,
                'number_suffix': lambda x: nltk.tree.Tree('number_suffix', [unparse_number(x[0])]),
                'suffixed': lambda x: len(x) > 1 and x or x[0],
                'ion_suffix': ion_suffix,
                'paren_group_square': lambda x: nltk.tree.Tree(x.node, x[1]),
                'paren_group_round': lambda x: nltk.tree.Tree(x.node, x[1])}

    if isinstance(tree, str):
        return tree

    old_node = None
    ## This loop means that if a node is processed, and returns a child,
    ## the child will be processed.
    while tree.node in dispatch and tree.node != old_node:
        old_node = tree.node
        tree = dispatch[tree.node](tree)

    children = []
    for child in tree:
        child = _clean_parse_tree(child)
        children.append(child)

    tree = nltk.tree.Tree(tree.node, children)

    return tree


def _merge_children(tree, tags):
    ''' nltk, by documentation, cannot do arbitrary length
    groups. Instead of:
    (group 1 2 3 4)
    It has to handle this recursively:
    (group 1 (group 2 (group 3 (group 4))))
    We do the cleanup of converting from the latter to the former.
    '''
    if tree is None:
        # There was a problem--shouldn't have empty trees (NOTE: see this with input e.g. 'H2O(', or 'Xe+').
        # Haven't grokked the code to tell if this is indeed the right thing to do.
        raise ParseException("Shouldn't have empty trees")

    if isinstance(tree, str):
        return tree

    merged_children = []
    done = False
    #print '00000', tree
    ## Merge current tag
    while not done:
        done = True
        for child in tree:
            if isinstance(child, nltk.tree.Tree) and child.node == tree.node and tree.node in tags:
                merged_children = merged_children + list(child)
                done = False
            else:
                merged_children = merged_children + [child]
        tree = nltk.tree.Tree(tree.node, merged_children)
        merged_children = []
    #print '======',tree

    # And recurse
    children = []
    for child in tree:
        children.append(_merge_children(child, tags))

    #return tree
    return nltk.tree.Tree(tree.node, children)


def _render_to_html(tree):
    ''' Renders a cleaned tree to HTML '''

    def molecule_count(tree, children):
        # If an integer, return that integer
        if len(tree) == 1:
            return tree[0][0]
        # If a fraction, return the fraction
        if len(tree) == 3:
            return " <sup>{num}</sup>&frasl;<sub>{den}</sub> ".format(num=tree[0][0], den=tree[2][0])
        return "Error"

    def subscript(tree, children):
        return "<sub>{sub}</sub>".format(sub=children)

    def superscript(tree, children):
        return "<sup>{sup}</sup>".format(sup=children)

    def round_brackets(tree, children):
        return "({insider})".format(insider=children)

    def square_brackets(tree, children):
        return "[{insider}]".format(insider=children)

    dispatch = {'count': molecule_count,
                'number_suffix': subscript,
                'ion_suffix': superscript,
                'paren_group_round': round_brackets,
                'paren_group_square': square_brackets}

    if isinstance(tree, str):
        return tree
    else:
        children = "".join(map(_render_to_html, tree))
        if tree.node in dispatch:
            return dispatch[tree.node](tree, children)
        else:
            return children.replace(' ', '')


def render_to_html(eq):
    '''
    Render a chemical equation string to html.

    Renders each molecule separately, and returns invalid input wrapped in a <span>.
    '''
    def err(s):
        "Render as an error span"
        return '<span class="inline-error inline">{0}</span>'.format(s)

    def render_arrow(arrow):
        """Turn text arrows into pretty ones"""
        if arrow == '->':
            return u'\u2192'
        if arrow == '<->':
            return u'\u2194'

        # this won't be reached unless we add more arrow types, but keep it to avoid explosions when
        # that happens.
        return arrow

    def render_expression(ex):
        """
        Render a chemical expression--no arrows.
        """
        try:
            return _render_to_html(_get_final_tree(ex))
        except ParseException:
            return err(ex)

    def spanify(s):
        return u'<span class="math">{0}</span>'.format(s)

    left, arrow, right = split_on_arrow(eq)
    if arrow == '':
        # only one side
        return spanify(render_expression(left))

    return spanify(render_expression(left) + render_arrow(arrow) + render_expression(right))


def _get_final_tree(s):
    '''
    Return final tree after merge and clean.

    Raises pyparsing.ParseException if s is invalid.
    '''
    global parser
    if parser is None:
        parser = nltk.ChartParser(nltk.parse_cfg(grammar))

    tokenized = tokenizer.parseString(s)
    parsed = parser.parse(tokenized)
    merged = _merge_children(parsed, {'S', 'group'})
    final = _clean_parse_tree(merged)
    return final


def _check_equality(tuple1, tuple2):
    ''' return True if tuples of multimolecules are equal '''
    list1 = list(tuple1)
    list2 = list(tuple2)

    # Hypo: trees where are levels count+molecule vs just molecule
    # cannot be sorted properly (tested on test_complex_additivity)
    # But without factors and phases sorting seems to work.

    # Also for lists of multimolecules without factors and phases
    # sorting seems to work fine.
    list1.sort()
    list2.sort()
    return list1 == list2


def compare_chemical_expression(s1, s2, ignore_state=False):
    ''' It does comparison between two expressions.
        It uses divide_chemical_expression and check if division is 1
    '''
    return divide_chemical_expression(s1, s2, ignore_state) == 1


def divide_chemical_expression(s1, s2, ignore_state=False):
    '''Compare two chemical expressions for equivalence up to a multiplicative factor:

    - If they are not the same chemicals, returns False.
    - If they are the same, "divide" s1 by s2 to returns a factor x such that s1 / s2 == x as a Fraction object.
    - if ignore_state is True, ignores phases when doing the comparison.

    Examples:
    divide_chemical_expression("H2O", "3H2O") -> Fraction(1,3)
    divide_chemical_expression("3H2O", "H2O") -> 3  # actually Fraction(3, 1), but compares == to 3.
    divide_chemical_expression("2H2O(s) + 2CO2", "H2O(s)+CO2") -> 2
    divide_chemical_expression("H2O(s) + CO2", "3H2O(s)+2CO2") -> False

    Implementation sketch:
        - extract factors and phases to standalone lists,
        - compare expressions without factors and phases,
        - divide lists of factors for each other and check
             for equality of every element in list,
        - return result of factor division

    '''

    # parsed final trees
    treedic = {}
    treedic['1'] = _get_final_tree(s1)
    treedic['2'] = _get_final_tree(s2)

    # strip phases and factors
    # collect factors in list
    for i in ('1', '2'):
        treedic[i + ' cleaned_mm_list'] = []
        treedic[i + ' factors'] = []
        treedic[i + ' phases'] = []
        for el in treedic[i].subtrees(filter=lambda t: t.node == 'multimolecule'):
            count_subtree = [t for t in el.subtrees() if t.node == 'count']
            group_subtree = [t for t in el.subtrees() if t.node == 'group']
            phase_subtree = [t for t in el.subtrees() if t.node == 'phase']
            if count_subtree:
                if len(count_subtree[0]) > 1:
                    treedic[i + ' factors'].append(
                        int(count_subtree[0][0][0]) /
                        int(count_subtree[0][2][0]))
                else:
                    treedic[i + ' factors'].append(int(count_subtree[0][0][0]))
            else:
                treedic[i + ' factors'].append(1.0)
            if phase_subtree:
                treedic[i + ' phases'].append(phase_subtree[0][0])
            else:
                treedic[i + ' phases'].append(' ')
            treedic[i + ' cleaned_mm_list'].append(
                Tree('multimolecule', [Tree('molecule', group_subtree)]))

    # order of factors and phases must mirror the order of multimolecules,
    # use 'decorate, sort, undecorate' pattern
    treedic['1 cleaned_mm_list'], treedic['1 factors'], treedic['1 phases'] = zip(
        *sorted(zip(treedic['1 cleaned_mm_list'], treedic['1 factors'], treedic['1 phases'])))

    treedic['2 cleaned_mm_list'], treedic['2 factors'], treedic['2 phases'] = zip(
        *sorted(zip(treedic['2 cleaned_mm_list'], treedic['2 factors'], treedic['2 phases'])))

    # check if expressions are correct without factors
    if not _check_equality(treedic['1 cleaned_mm_list'], treedic['2 cleaned_mm_list']):
        return False

    # phases are ruled by ingore_state flag
    if not ignore_state:  # phases matters
        if treedic['1 phases'] != treedic['2 phases']:
            return False

    if any(
        [
            x / y - treedic['1 factors'][0] / treedic['2 factors'][0]
            for (x, y) in zip(treedic['1 factors'], treedic['2 factors'])
        ]
    ):
        # factors are not proportional
        return False
    else:
        # return ratio
        return Fraction(treedic['1 factors'][0] / treedic['2 factors'][0])


def split_on_arrow(eq):
    """
    Split a string on an arrow.  Returns left, arrow, right.  If there is no arrow, returns the
    entire eq in left, and '' in arrow and right.

    Return left, arrow, right.
    """
    # order matters -- need to try <-> first
    for arrow in ARROWS:
        left, a, right = eq.partition(arrow)
        if a != '':
            return left, a, right

    return eq, '', ''


def chemical_equations_equal(eq1, eq2, exact=False):
    """
    Check whether two chemical equations are the same.  (equations have arrows)

    If exact is False, then they are considered equal if they differ by a
    constant factor.

    arrows matter: -> and <-> are different.

    e.g.
    chemical_equations_equal('H2 + O2 -> H2O2', 'O2 + H2 -> H2O2') -> True
    chemical_equations_equal('H2 + O2 -> H2O2', 'O2 + 2H2 -> H2O2') -> False

    chemical_equations_equal('H2 + O2 -> H2O2', 'O2 + H2 <-> H2O2') -> False

    chemical_equations_equal('H2 + O2 -> H2O2', '2 H2 + 2 O2 -> 2 H2O2') -> True
    chemical_equations_equal('H2 + O2 -> H2O2', '2 H2 + 2 O2 -> 2 H2O2', exact=True) -> False


    If there's a syntax error, we return False.
    """

    left1, arrow1, right1 = split_on_arrow(eq1)
    left2, arrow2, right2 = split_on_arrow(eq2)

    if arrow1 == '' or arrow2 == '':
        return False

    # TODO: may want to be able to give student helpful feedback about why things didn't work.
    if arrow1 != arrow2:
        # arrows don't match
        return False

    try:
        factor_left = divide_chemical_expression(left1, left2)
        if not factor_left:
            # left sides don't match
            return False

        factor_right = divide_chemical_expression(right1, right2)
        if not factor_right:
            # right sides don't match
            return False

        if factor_left != factor_right:
            # factors don't match (molecule counts to add up)
            return False

        if exact and factor_left != 1:
            # want an exact match.
            return False

        return True
    except ParseException:
        # Don't want external users to have to deal with parsing exceptions.  Just return False.
        return False
