describe 'MarkdownEditingDescriptor', ->
  describe 'markdownToXml', ->
    it 'converts raw text to paragraph', ->
      data = MarkdownEditingDescriptor.markdownToXml('foo')
      expect(data).toEqual('<problem>\n<p>foo</p>\n</problem>')
    # test default templates
    it 'converts numerical response to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.

        The answer is correct if it is within a specified numerical tolerance of the expected answer.

        Enter the numerical value of Pi:
        = 3.14159 +- .02
        
        Enter the approximate value of 502*9:
        = 4518 +- 15%
        
        Enter the number of fingers on a human hand:
        = 5
        
        <solution>
        <div class='detailed-solution'>
        Explanation
        
        Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.
        
        Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.
        
        If you look at your hand, you can count that you have five fingers.
        </div>
        </solution>
        """)
      expect(data).toEqual("""<problem>
        <p>A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>
        
        <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>
        
        <p>Enter the numerical value of Pi:</p>
        <numericalresponse answer="3.14159 ">
          <responseparam type="tolerance" default=".02" />
          <textline />
        </numericalresponse>
        
        <p>Enter the approximate value of 502*9:</p>
        <numericalresponse answer="4518 ">
          <responseparam type="tolerance" default="15%" />
          <textline />
        </numericalresponse>
        
        <p>Enter the number of fingers on a human hand:</p>
        <numericalresponse answer="5">
          <textline />
        </numericalresponse>
        
        <solution>
        <div class='detailed-solution'>
        <p>Explanation</p>
        
        <p>Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.</p>
        
        <p>Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.</p>
        
        <p>If you look at your hand, you can count that you have five fingers.</p>
        </div>
        </solution>
        </problem>""")
    it 'converts multiple choice to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.
        
        One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.
        
        What Apple device competed with the portable CD player?
        ( ) The iPad
        ( ) Napster
        (x) The iPod
        ( ) The vegetable peeler
        ( ) Android
        ( ) The Beatles
        
        <solution>
        <div class='detailed-solution'>
        Explanation
        
        The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.
        </div>
        </solution>
        """)
      expect(data).toEqual("""<problem>
        <p>A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.</p>
        
        <p>One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.</p>
        
        <p>What Apple device competed with the portable CD player?</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">The iPad</choice>
            <choice correct="false">Napster</choice>
            <choice correct="true">The iPod</choice>
            <choice correct="false">The vegetable peeler</choice>
            <choice correct="false">Android</choice>
            <choice correct="false">The Beatles</choice>
          </choicegroup>
        </multiplechoiceresponse>
        
        <solution>
        <div class='detailed-solution'>
        <p>Explanation</p>
        
        <p>The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.</p>
        </div>
        </solution>
        </problem>""")        
    it 'converts OptionResponse to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""OptionResponse gives a limited set of options for students to respond with, and presents those options in a format that encourages them to search for a specific answer rather than being immediately presented with options from which to recognize the correct answer.
        
        The answer options and the identification of the correct answer is defined in the <b>optioninput</b> tag.
        
        Translation between Option Response and __________ is extremely straightforward:
        [[(Multiple Choice), String Response, Numerical Response, External Response, Image Response]]
        
        <solution>
        <div class='detailed-solution'>
        Explanation
        
        Multiple Choice also allows students to select from a variety of pre-written responses, although the format makes it easier for students to read very long response options. Optionresponse also differs slightly because students are more likely to think of an answer and then search for it rather than relying purely on recognition to answer the question.
        </div>
        </solution>
        """)
      expect(data).toEqual("""<problem>
        <p>OptionResponse gives a limited set of options for students to respond with, and presents those options in a format that encourages them to search for a specific answer rather than being immediately presented with options from which to recognize the correct answer.</p>
        
        <p>The answer options and the identification of the correct answer is defined in the <b>optioninput</b> tag.</p>
        
        <p>Translation between Option Response and __________ is extremely straightforward:</p>
        
        <optionresponse>
          <optioninput options="('Multiple Choice','String Response','Numerical Response','External Response','Image Response')" correct="Multiple Choice"></optioninput>
        </optionresponse>
        
        <solution>
        <div class='detailed-solution'>
        <p>Explanation</p>
        
        <p>Multiple Choice also allows students to select from a variety of pre-written responses, although the format makes it easier for students to read very long response options. Optionresponse also differs slightly because students are more likely to think of an answer and then search for it rather than relying purely on recognition to answer the question.</p>
        </div>
        </solution>
        </problem>""")        
    it 'converts OptionResponse to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A string response problem accepts a line of text input from the student, and evaluates the input for correctness based on an expected answer within each input box.
        
        The answer is correct if it matches every character of the expected answer. This can be a problem with international spelling, dates, or anything where the format of the answer is not clear.
        
        Which US state has Lansing as its capital?
        = Michigan
        
        <solution>
        <div class='detailed-solution'>
        Explanation
        
        Lansing is the capital of Michigan, although it is not Michgan's largest city, or even the seat of the county in which it resides.
        
        </div>
        </solution>
        """)
      expect(data).toEqual("""<problem>
        <p>A string response problem accepts a line of text input from the student, and evaluates the input for correctness based on an expected answer within each input box.</p>
        
        <p>The answer is correct if it matches every character of the expected answer. This can be a problem with international spelling, dates, or anything where the format of the answer is not clear.</p>
        
        <p>Which US state has Lansing as its capital?</p>
        <stringresponse answer="Michigan" type="ci">
          <textline size="20"/>
        </stringresponse>
        
        <solution>
        <div class='detailed-solution'>
        <p>Explanation</p>
        
        <p>Lansing is the capital of Michigan, although it is not Michgan's largest city, or even the seat of the county in which it resides.</p>
        
        </div>
        </solution>
        </problem>""")
    # test oddities
    it 'converts headers and oddities to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Not a header
        A header
        ==============
        
        Multiple choice w/ parentheticals
        ( ) option (with parens)
        ( ) xd option (x)
        ()) parentheses inside
        () no space b4 close paren
        
        Choice checks
        [ ] option1 [x]
        [x] correct
        [x] redundant
        [(] distractor
        [] no space
        
        {{video abcd1s}}
        
        Option with multiple correct ones
        [[one option, (correct one), (should not be correct)]]
        
        Option with embedded parens
        [[My (heart), another, (correct)]]
        
        What happens w/ empty correct options?
        [[()]]
        
        No p tags in the below
        <script type='javascript'>
           var two = 2;

           console.log(two * 2);
        </script>
        
        But in this there should be
        <div>
        Great ideas require offsetting.
        
        bad tests require drivel
        </div>
        """)
      expect(data).toEqual("""<problem>
        <p>Not a header</p>
        <h1>A header</h1>
        
        <p>Multiple choice w/ parentheticals</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">option (with parens)</choice>
            <choice correct="false">xd option (x)</choice>
            <choice correct="false">parentheses inside</choice>
            <choice correct="false">no space b4 close paren</choice>
          </choicegroup>
        </multiplechoiceresponse>
        
        <p>Choice checks</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoiceChecks">
            <choice correct="false">option1 [x]</choice>
            <choice correct="true">correct</choice>
            <choice correct="true">redundant</choice>
            <choice correct="false">distractor</choice>
            <choice correct="false">no space</choice>
          </choicegroup>
        </multiplechoiceresponse>
        
        <video youtube="1.0:abcd1s" />
        
        <p>Option with multiple correct ones</p>
        
        <optionresponse>
          <optioninput options="('one option','correct one','should not be correct')" correct="correct one"></optioninput>
        </optionresponse>
        
        <p>Option with embedded parens</p>
        
        <optionresponse>
          <optioninput options="('My (heart)','another','correct')" correct="correct"></optioninput>
        </optionresponse>
        
        <p>What happens w/ empty correct options?</p>
        
        <optionresponse>
          <optioninput options="('')" correct=""></optioninput>
        </optionresponse>
        
        <p>No p tags in the below</p>
        <script type='javascript'>
           var two = 2;

           console.log(two * 2);
        </script>
        
        <p>But in this there should be</p>
        <div>
        <p>Great ideas require offsetting.</p>
        
        <p>bad tests require drivel</p>
        </div>
        </problem>""")
    # failure tests