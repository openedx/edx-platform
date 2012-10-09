from __future__ import division
import copy
import logging
import math
import operator
import re
import unittest
import numpy
import numbers
import scipy.constants

from pyparsing import Literal, Keyword, Word, nums, StringEnd, Optional, Forward, OneOrMore
from pyparsing import ParseException
import nltk
from nltk.tree import Tree

local_debug = None


def log(s, output_type=None):
    if local_debug:
        print s
        if output_type == 'html':
            f.write(s + '\n<br>\n')

## Defines a simple pyparsing tokenizer for chemical equations
elements = ['Ac','Ag','Al','Am','Ar','As','At','Au','B','Ba','Be',
            'Bh','Bi','Bk','Br','C','Ca','Cd','Ce','Cf','Cl','Cm',
            'Cn','Co','Cr','Cs','Cu','Db','Ds','Dy','Er','Es','Eu',
            'F','Fe','Fl','Fm','Fr','Ga','Gd','Ge','H','He','Hf',
            'Hg','Ho','Hs','I','In','Ir','K','Kr','La','Li','Lr',
            'Lu','Lv','Md','Mg','Mn','Mo','Mt','N','Na','Nb','Nd',
            'Ne','Ni','No','Np','O','Os','P','Pa','Pb','Pd','Pm',
            'Po','Pr','Pt','Pu','Ra','Rb','Re','Rf','Rg','Rh','Rn',
            'Ru','S','Sb','Sc','Se','Sg','Si','Sm','Sn','Sr','Ta',
            'Tb','Tc','Te','Th','Ti','Tl','Tm','U','Uuo','Uup',
            'Uus','Uut','V','W','Xe','Y','Yb','Zn','Zr']
digits = map(str, range(10))
symbols = list("[](){}^+-/")
phases = ["(s)", "(l)", "(g)", "(aq)"]
tokens = reduce(lambda a, b: a ^ b, map(Literal, elements + digits + symbols + phases))
tokenizer = OneOrMore(tokens) + StringEnd()


def orjoin(l):
    return "'" + "' | '".join(l) + "'"

## Defines an NLTK parser for tokenized equations
grammar = """
  S -> multimolecule | multimolecule '+' S
  multimolecule -> count molecule | molecule
  count -> number | number '/' number
  molecule -> unphased | unphased phase
  unphased -> group | paren_group_round | paren_group_square
  element -> """ + orjoin(elements) + """
  digit -> """ + orjoin(digits) + """
  phase -> """ + orjoin(phases) + """
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
parser = nltk.ChartParser(nltk.parse_cfg(grammar))


def clean_parse_tree(tree):
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

    if type(tree) == str:
        return tree

    old_node = None
    ## This loop means that if a node is processed, and returns a child,
    ## the child will be processed.
    while tree.node in dispatch and tree.node != old_node:
        old_node = tree.node
        tree = dispatch[tree.node](tree)

    children = []
    for child in tree:
        child = clean_parse_tree(child)
        children.append(child)

    tree = nltk.tree.Tree(tree.node, children)

    return tree


def merge_children(tree, tags):
    ''' nltk, by documentation, cannot do arbitrary length
    groups. Instead of:
    (group 1 2 3 4)
    It has to handle this recursively:
    (group 1 (group 2 (group 3 (group 4))))
    We do the cleanup of converting from the latter to the former (as a
    '''
    if type(tree) == str:
        return tree

    merged_children = []
    done = False
    #print '00000', tree
    ## Merge current tag
    while not done:
        done = True
        for child in tree:
            if type(child) == nltk.tree.Tree and child.node == tree.node and tree.node in tags:
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
        children.append(merge_children(child, tags))

    #return tree
    return nltk.tree.Tree(tree.node, children)


def render_to_html(tree):
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

    if type(tree) == str:
        return tree
    else:
        children = "".join(map(render_to_html, tree))
        if tree.node in dispatch:
            return dispatch[tree.node](tree, children)
        else:
            return children.replace(' ', '')


def clean_and_render_to_html(s):
    ''' render a string to html '''
    status = render_to_html(get_finale_tree(s))
    return status


def get_finale_tree(s):
    '''  return final tree after merge and clean  '''
    tokenized = tokenizer.parseString(s)
    parsed = parser.parse(tokenized)
    merged = merge_children(parsed, {'S','group'})
    final = clean_parse_tree(merged)
    return final


def check_equality(tuple1, tuple2):
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
    ''' It does comparison between two equations.
        It uses divide_chemical_expression and check if division is 1
    '''
    return divide_chemical_expression(s1, s2, ignore_state) == 1


def divide_chemical_expression(s1, s2, ignore_state=False):
    ''' Compare chemical equations for difference
    in factors. Ideas:
        - extract factors and phases to standalone lists,
        - compare equations without factors and phases,
        - divide lists of factors for each other and check
             for equality of every element in list,
        - return result of factor division '''

    # parsed final trees
    treedic = {}
    treedic['1'] = get_finale_tree(s1)
    treedic['2'] = get_finale_tree(s2)

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

    # check if equations are correct without factors
    if not check_equality(treedic['1 cleaned_mm_list'], treedic['2 cleaned_mm_list']):
        return False

    # phases are ruled by ingore_state flag
    if not ignore_state:  # phases matters
        if treedic['1 phases'] != treedic['2 phases']:
            return False

    if any(map(lambda x, y: x / y - treedic['1 factors'][0] / treedic['2 factors'][0],
                                         treedic['1 factors'], treedic['2 factors'])):
        log('factors are not proportional')
        return False
    else:  # return ratio
        return int(max(treedic['1 factors'][0] / treedic['2 factors'][0],
                    treedic['2 factors'][0] / treedic['1 factors'][0]))


class Test_Compare_Equations(unittest.TestCase):

        def test_compare_incorrect_order_of_atoms_in_molecule(self):
            self.assertFalse(compare_chemical_expression("H2O + CO2", "O2C + OH2"))

        def test_compare_same_order_no_phases_no_factors_no_ions(self):
            self.assertTrue(compare_chemical_expression("H2O + CO2", "CO2+H2O"))

        def test_compare_different_order_no_phases_no_factors_no_ions(self):
            self.assertTrue(compare_chemical_expression("H2O + CO2", "CO2 + H2O"))

        def test_compare_different_order_three_multimolecule(self):
            self.assertTrue(compare_chemical_expression("H2O + Fe(OH)3 +  CO2", "CO2 + H2O + Fe(OH)3"))

        def test_compare_same_factors(self):
            self.assertTrue(compare_chemical_expression("3H2O +  2CO2", "2CO2 + 3H2O "))

        def test_compare_different_factors(self):
            self.assertFalse(compare_chemical_expression("2H2O +  3CO2", "2CO2 + 3H2O "))

        def test_compare_correct_ions(self):
            self.assertTrue(compare_chemical_expression("H^+ + OH^-", " OH^- + H^+ "))

        def test_compare_wrong_ions(self):
            self.assertFalse(compare_chemical_expression("H^+ + OH^-", " OH^- + H^- "))

        def test_compare_parent_groups_ions(self):
            self.assertTrue(compare_chemical_expression("Fe(OH)^2- + (OH)^-", " (OH)^- + Fe(OH)^2- "))

        def test_compare_correct_factors_ions_and_one(self):
            self.assertTrue(compare_chemical_expression("3H^+ + 2OH^-", " 2OH^- + 3H^+ "))

        def test_compare_wrong_factors_ions(self):
            self.assertFalse(compare_chemical_expression("2H^+ + 3OH^-", " 2OH^- + 3H^+ "))

        def test_compare_float_factors(self):
            self.assertTrue(compare_chemical_expression("7/2H^+ + 3/5OH^-", " 3/5OH^- + 7/2H^+ "))

        # Phases tests
        def test_compare_phases_ignored(self):
            self.assertTrue(compare_chemical_expression(
                "H2O(s) + CO2", "H2O+CO2", ignore_state=True))

        def test_compare_phases_not_ignored_explicitly(self):
            self.assertFalse(compare_chemical_expression(
                "H2O(s) + CO2", "H2O+CO2", ignore_state=False))

        def test_compare_phases_not_ignored(self):  # same as previous
            self.assertFalse(compare_chemical_expression(
                "H2O(s) + CO2", "H2O+CO2"))

        def test_compare_phases_not_ignored_explicitly(self):
            self.assertTrue(compare_chemical_expression(
                "H2O(s) + CO2", "H2O(s)+CO2", ignore_state=False))

        # all in one cases
        def test_complex_additivity(self):
            self.assertTrue(compare_chemical_expression(
                "5(H1H212)^70010- + 2H20 + 7/2HCl + H2O",
                "7/2HCl + 2H20 + H2O + 5(H1H212)^70010-"))

        def test_complex_additivity_wrong(self):
            self.assertFalse(compare_chemical_expression(
                "5(H1H212)^70010- + 2H20 + 7/2HCl + H2O",
                "2H20 + 7/2HCl + H2O + 5(H1H212)^70011-"))

        def test_complex_all_grammar(self):
            self.assertTrue(compare_chemical_expression(
                "5[Ni(NH3)4]^2+ + 5/2SO4^2-",
                "5/2SO4^2- + 5[Ni(NH3)4]^2+"))

        # special cases

        def test_compare_one_superscript_explicitly_set(self):
            self.assertTrue(compare_chemical_expression("H^+ + OH^1-", " OH^- + H^+ "))

        def test_compare_equal_factors_differently_set(self):
            self.assertTrue(compare_chemical_expression("6/2H^+ + OH^-", " OH^- + 3H^+ "))

        def test_compare_one_subscript_explicitly_set(self):
            self.assertFalse(compare_chemical_expression("H2 + CO2", "H2 + C102"))


class Test_Divide_Equations(unittest.TestCase):
    ''' as compare_ use divide_,
    tests here must consider different
    division (not equality) cases '''

    def test_divide_wrong_factors(self):
        self.assertFalse(divide_chemical_expression(
            "5(H1H212)^70010- + 10H2O", "5H2O + 10(H1H212)^70010-"))

    def test_divide_right(self):
        self.assertEqual(divide_chemical_expression(
            "5(H1H212)^70010- + 10H2O", "10H2O + 5(H1H212)^70010-"), 1)

    def test_divide_wrong_reagents(self):
        self.assertFalse(divide_chemical_expression(
            "H2O + CO2", "CO2"))

    def test_divide_right_simple(self):
        self.assertEqual(divide_chemical_expression(
            "H2O + CO2", "H2O+CO2"), 1)

    def test_divide_right_phases(self):
        self.assertEqual(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O(s)+2CO2"), 2)

    def test_divide_wrong_phases(self):
        self.assertFalse(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O+2CO2(s)"))

    def test_divide_wrong_phases_but_phases_ignored(self):
        self.assertEqual(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O+2CO2(s)", ignore_state=True), 2)

    def test_divide_order(self):
        self.assertEqual(divide_chemical_expression(
            "2CO2 + H2O", "2H2O+4CO2"), 2)

    def test_divide_fract_to_int(self):
        self.assertEqual(divide_chemical_expression(
            "3/2CO2 + H2O", "2H2O+3CO2"), 2)

    def test_divide_fract_to_frac(self):
        self.assertEqual(divide_chemical_expression(
            "3/4CO2 + H2O", "2H2O+9/6CO2"), 2)

    def test_divide_fract_to_frac_wrog(self):
        self.assertFalse(divide_chemical_expression(
            "6/2CO2 + H2O", "2H2O+9/6CO2"), 2)


class Test_Render_Equations(unittest.TestCase):

        def test_render1(self):
            s = "H2O + CO2"
            out = clean_and_render_to_html(s)
            correct = "H<sub>2</sub>O+CO<sub>2</sub>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render_uncorrect_reaction(self):
            s = "O2C + OH2"
            out = clean_and_render_to_html(s)
            correct = "O<sub>2</sub>C+OH<sub>2</sub>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render2(self):
            s = "CO2 + H2O + Fe(OH)3"
            out = clean_and_render_to_html(s)
            correct = "CO<sub>2</sub>+H<sub>2</sub>O+Fe(OH)<sub>3</sub>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render3(self):
            s = "3H2O + 2CO2"
            out = clean_and_render_to_html(s)
            correct = "3H<sub>2</sub>O+2CO<sub>2</sub>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render4(self):
            s = "H^+ + OH^-"
            out = clean_and_render_to_html(s)
            correct = "H<sup>+</sup>+OH<sup>-</sup>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render5(self):
            s = "Fe(OH)^2- + (OH)^-"
            out = clean_and_render_to_html(s)
            correct = "Fe(OH)<sup>2-</sup>+(OH)<sup>-</sup>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render6(self):
            s = "7/2H^+ + 3/5OH^-"
            out = clean_and_render_to_html(s)
            correct = "<sup>7</sup>&frasl;<sub>2</sub>H<sup>+</sup>+<sup>3</sup>&frasl;<sub>5</sub>OH<sup>-</sup>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render7(self):
            s = "5(H1H212)^70010- + 2H2O + 7/2HCl + H2O"
            out = clean_and_render_to_html(s)
            correct = "5(H<sub>1</sub>H<sub>212</sub>)<sup>70010-</sup>+2H<sub>2</sub>O+<sup>7</sup>&frasl;<sub>2</sub>HCl+H<sub>2</sub>O"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render8(self):
            s = "H2O(s) + CO2"
            out = clean_and_render_to_html(s)
            correct = "H<sub>2</sub>O(s)+CO<sub>2</sub>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render9(self):
            s = "5[Ni(NH3)4]^2+ + 5/2SO4^2-"
            #import ipdb; ipdb.set_trace()
            out = clean_and_render_to_html(s)
            correct = "5[Ni(NH<sub>3</sub>)<sub>4</sub>]<sup>2+</sup>+<sup>5</sup>&frasl;<sub>2</sub>SO<sub>4</sub><sup>2-</sup>"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)

        def test_render_error(self):
            s = "5.2H20"
            self.assertRaises(ParseException, clean_and_render_to_html, s)

        def test_render_simple_brackets(self):
            s = "(Ar)"
            out = clean_and_render_to_html(s)
            correct = "(Ar)"
            log(out + ' ------- ' + correct, 'html')
            self.assertEqual(out, correct)


def suite():

    testcases = [Test_Compare_Equations, Test_Divide_Equations, Test_Render_Equations]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    local_debug = True
    with open('render.html', 'w') as f:
        unittest.TextTestRunner(verbosity=2).run(suite())
    # open render.html to look at rendered equations
