Tips on formulating problems

I had to write a custom response for determining 
whether or not a student wrote a correct characteristic 
polynomial.  The problem is that there are many
possible equivalent characteristic polynomials.  

For example

L*C*s^2 + 1
and
s^2 + 1/(L*C)

are equivalent characteristic polynomials.

The correct test is whether or 
not the roots s are the right ones.

I wrote the following short code.

     <customresponse>
     <startouttext/>
     <br/>
     <textline size="40"/>
     <endouttext/>
     <answer type="loncapa/python">
     # Test for polynomial equivalent to L*C*s^2 + 1 = 0
     correct = ['correct']
     L = 3.14159 # arbitrary random number
     C = 2.71828 # arbitrary random number
     s = 1j*math.sqrt(1/(L*C))
     try:
       residual = calc.evaluator({'L' : L, 'C' : C, 's' : s},{},submission[0])
     except ValueError:
       correct[0] = 'incorrect'
       residual = 1e6

     if (abs(residual) &gt; 1e-6):
       correct[0] = 'incorrect'
     </answer>
     </customresponse>

A better code would sample various values of L and C and make sure that 
the s calculated would result in a zero residual, but it is pretty
unnecessary in this case.

Note: In Python the imaginary unit is designated 1j.
