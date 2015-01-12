"""
Standard resistor values.

Commonly used for verifying electronic components in circuit classes are
standard values, or conversely, for generating realistic component
values in parameterized problems. For details, see:

http://en.wikipedia.org/wiki/Electronic_color_code
"""

# pylint: disable=invalid-name
# r is standard name for a resistor. We would like to use it as such.

import math
import numbers

E6 = [10, 15, 22, 33, 47, 68]

E12 = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
E24 = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82, 11, 13, 16, 20,
       24, 30, 36, 43, 51, 62, 75, 91]

E48 = [100, 121, 147, 178, 215, 261, 316, 383, 464, 562, 681, 825, 105,
       127, 154, 187, 226, 274, 332, 402, 487, 590, 715, 866, 110, 133,
       162, 196, 237, 287, 348, 422, 511, 619, 750, 909, 115, 140, 169,
       205, 249, 301, 365, 442, 536, 649, 787, 953]

E96 = [100, 121, 147, 178, 215, 261, 316, 383, 464, 562, 681, 825, 102,
       124, 150, 182, 221, 267, 324, 392, 475, 576, 698, 845, 105, 127,
       154, 187, 226, 274, 332, 402, 487, 590, 715, 866, 107, 130, 158,
       191, 232, 280, 340, 412, 499, 604, 732, 887, 110, 133, 162, 196,
       237, 287, 348, 422, 511, 619, 750, 909, 113, 137, 165, 200, 243,
       294, 357, 432, 523, 634, 768, 931, 115, 140, 169, 205, 249, 301,
       365, 442, 536, 649, 787, 953, 118, 143, 174, 210, 255, 309, 374,
       453, 549, 665, 806, 976]

E192 = [100, 121, 147, 178, 215, 261, 316, 383, 464, 562, 681, 825, 101,
        123, 149, 180, 218, 264, 320, 388, 470, 569, 690, 835, 102, 124,
        150, 182, 221, 267, 324, 392, 475, 576, 698, 845, 104, 126, 152,
        184, 223, 271, 328, 397, 481, 583, 706, 856, 105, 127, 154, 187,
        226, 274, 332, 402, 487, 590, 715, 866, 106, 129, 156, 189, 229,
        277, 336, 407, 493, 597, 723, 876, 107, 130, 158, 191, 232, 280,
        340, 412, 499, 604, 732, 887, 109, 132, 160, 193, 234, 284, 344,
        417, 505, 612, 741, 898, 110, 133, 162, 196, 237, 287, 348, 422,
        511, 619, 750, 909, 111, 135, 164, 198, 240, 291, 352, 427, 517,
        626, 759, 920, 113, 137, 165, 200, 243, 294, 357, 432, 523, 634,
        768, 931, 114, 138, 167, 203, 246, 298, 361, 437, 530, 642, 777,
        942, 115, 140, 169, 205, 249, 301, 365, 442, 536, 649, 787, 953,
        117, 142, 172, 208, 252, 305, 370, 448, 542, 657, 796, 965, 118,
        143, 174, 210, 255, 309, 374, 453, 549, 665, 806, 976, 120, 145,
        176, 213, 258, 312, 379, 459, 556, 673, 816, 988]


def iseia(r, valid_types=(E6, E12, E24)):
    '''
    Check if a component is a valid EIA value.

    By default, check 5% component values
    '''

    # Step 1: Discount things which are not numbers
    if not isinstance(r, numbers.Number) or \
       r < 0 or \
       math.isnan(r) or \
       math.isinf(r):
        return False

    # Special case: 0 is an okay resistor
    if r == 0:
        return True

    # Step 2: Move into the range [100, 1000)
    while r < 100:
        r = r * 10
    while r >= 1000:
        r = r / 10

    # Step 3: Discount things which are not integers, and cast to int
    if abs(r - round(r)) > 0.01:
        return False
    r = int(round(r))

    # Step 4: Check if we're a valid EIA value
    for type_list in valid_types:
        if r in type_list:
            return True
        if int(r / 10.) in type_list and (r % 10) == 0:
            return True

    return False

if __name__ == '__main__':
    # Test cases. All of these should return True
    print iseia(100)        # 100 ohm resistor is EIA
    print not iseia(101)    # 101 is not
    print not iseia(100.3)  # Floating point close to EIA is not EIA
    print iseia(100.001)    # But within floating point error is
    print iseia(1e5)        # We handle big numbers well
    print iseia(2200)       # We handle middle-of-the-list well
    # We can handle 1% components correctly; 2.2k is EIA24, but not EIA48.
    print not iseia(2200, (E48, E96, E192))
    print iseia(5490e2, (E48, E96, E192))
    print iseia(2200)
    print not iseia(5490e2)
    print iseia(1e-5)      # We handle little numbers well
    print not iseia("Hello")  # Junk handled okay
    print not iseia(float('NaN'))
    print not iseia(-1)
    print not iseia(iseia)
    print not iseia(float('Inf'))
    print iseia(0)  # Corner case. 0 is a standard resistor value.
