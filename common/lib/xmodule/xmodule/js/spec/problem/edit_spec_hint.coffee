# This file tests the parsing of  extended-hints, double bracket sections {{ .. }}
# for all sorts of markdown.
describe 'Markdown to xml extended hint dropdown', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      Translation between Dropdown and ________ is straightforward.

      [[
         (Multiple Choice) 	 {{ Good Job::Yes, multiple choice is the right answer. }}
         Text Input	                  {{ No, text input problems don't present options. }}
         Numerical Input	 {{ No, numerical input problems don't present options. }}
      ]]



      Clowns have funny _________ to make people laugh.

      [[
        dogs		{{ NOPE::Not dogs, not cats, not toads }}
        (FACES)	{{ With lots of makeup, doncha know?}}

        money       {{ Clowns don't have any money, of course }}
        donkeys     {{don't be an ass.}}
        -no hint-
      ]]

    """)
    expect(data).toXMLEqual("""
    <problem>
      <p>Translation between Dropdown and ________ is straightforward.</p>
      <optionresponse>
        <optioninput>
          <option correct="True">Multiple Choice 
            <optionhint label="Good Job">Yes, multiple choice is the right answer.</optionhint>
          </option>
          <option correct="False">Text Input 
            <optionhint>No, text input problems don't present options.</optionhint>
          </option>
          <option correct="False">Numerical Input 
            <optionhint>No, numerical input problems don't present options.</optionhint>
          </option>
        </optioninput>
      </optionresponse>
      <p>Clowns have funny _________ to make people laugh.</p>
      <optionresponse>
        <optioninput>
          <option correct="False">dogs 
            <optionhint label="NOPE">Not dogs, not cats, not toads</optionhint>
          </option>
          <option correct="True">FACES 
            <optionhint>With lots of makeup, doncha know?</optionhint>
          </option>
          <option correct="False">money 
            <optionhint>Clowns don't have any money, of course</optionhint>
          </option>
          <option correct="False">donkeys 
            <optionhint>don't be an ass.</optionhint>
          </option>
          <option correct="False">-no hint-</option>
        </optioninput>
      </optionresponse>
    </problem>
    """)

  it 'produces xml with demand hint', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      Translation between Dropdown and ________ is straightforward.

      [[
         (Right) 	 {{ Good Job::yes }}
         Wrong 1	                  {{no}}
         Wrong 2	 {{ Label::no }}
      ]]

      || 0) zero ||
      || 1) one ||
      || 2) two ||
    """)
    expect(data).toXMLEqual("""
    <problem>
    <optionresponse>
      <p>Translation between Dropdown and ________ is straightforward.</p>
    <optioninput>
        <option correct="True">Right <optionhint label="Good Job">yes</optionhint>
    </option>
        <option correct="False">Wrong 1 <optionhint>no</optionhint>
    </option>
        <option correct="False">Wrong 2 <optionhint label="Label">no</optionhint>
    </option>
      </optioninput>
    </optionresponse>

    <demandhint>
      <hint>0) zero</hint>
      <hint>1) one</hint>
      <hint>2) two</hint>
    </demandhint>
    </problem>
    """)

  it 'produces xml with single-line markdown syntax', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      A Question ________ is answered.

      [[(Right), Wrong 1, Wrong 2]]
      || 0) zero ||
      || 1) one ||
    """)
    expect(data).toXMLEqual("""
    <problem>
    <optionresponse>
      <p>A Question ________ is answered.</p>
    <optioninput options="('Right','Wrong 1','Wrong 2')" correct="Right"/>
    </optionresponse>

    <demandhint>
      <hint>0) zero</hint>
      <hint>1) one</hint>
    </demandhint>
    </problem>
    """)

  it 'produces xml with fewer newlines', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>q1<<
      [[ (aa) 	 {{ hint1 }}
         bb
         cc	 {{ hint2 }} ]]
    """)
    expect(data).toXMLEqual("""
    <problem>
    <optionresponse>
      <label>q1</label>
    <optioninput>
        <option correct="True">aa <optionhint>hint1</optionhint>
    </option>
        <option correct="False">bb</option>
        <option correct="False">cc <optionhint>hint2</optionhint>
    </option>
      </optioninput>
    </optionresponse>


    </problem>
    """)

  it 'produces xml even with lots of whitespace', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>q1<<
      [[


          aa   {{ hint1 }}

              bb   {{ hint2 }}
       (cc)

              ]]
    """)
    expect(data).toXMLEqual("""
    <problem>
    <optionresponse>
      <label>q1</label>
    <optioninput>
        <option correct="False">aa <optionhint>hint1</optionhint>
    </option>
        <option correct="False">bb <optionhint>hint2</optionhint>
    </option>
        <option correct="True">cc</option>
      </optioninput>
    </optionresponse>


    </problem>
    """)

describe 'Markdown to xml extended hint checkbox', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>Select all the fruits from the list<<

      [x] Apple     	 	 {{ selected: You're right that apple is a fruit. }, {unselected: Remember that apple is also a fruit.}}
      [ ] Mushroom	   	 {{U: You're right that mushrooms aren't fruit}, { selected: Mushroom is a fungus, not a fruit.}}
      [x] Grape		     {{ selected: You're right that grape is a fruit }, {unselected: Remember that grape is also a fruit.}}
      [ ] Mustang
      [ ] Camero            {{S:I don't know what a Camero is but it isn't a fruit.},{U:What is a camero anyway?}}


      {{ ((A*B)) You're right that apple is a fruit, but there's one you're missing. Also, mushroom is not a fruit.}}
      {{ ((B*C)) You're right that grape is a fruit, but there's one you're missing. Also, mushroom is not a fruit.    }}


      >>Select all the vegetables from the list<<

      [ ] Banana     	 	 {{ selected: No, sorry, a banana is a fruit. }, {unselected: poor banana.}}
      [ ] Ice Cream
      [ ] Mushroom	   	 {{U: You're right that mushrooms aren't vegetables.}, { selected: Mushroom is a fungus, not a vegetable.}}
      [x] Brussel Sprout	 {{S: Brussel sprouts are vegetables.}, {u: Brussel sprout is the only vegetable in this list.}}


      {{ ((A*B)) Making a banana split? }}
      {{ ((B*D)) That will make a horrible dessert: a brussel sprout split? }}
    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>Select all the fruits from the list</label>
        <choiceresponse>
            <checkboxgroup>
                <choice correct="true">Apple
                    <choicehint selected="true">You're right that apple is a fruit.</choicehint>
                    <choicehint selected="false">Remember that apple is also a fruit.</choicehint>
                </choice>
                <choice correct="false">Mushroom
                    <choicehint selected="true">Mushroom is a fungus, not a fruit.</choicehint>
                    <choicehint selected="false">You're right that mushrooms aren't fruit</choicehint>
                </choice>
                <choice correct="true">Grape
                    <choicehint selected="true">You're right that grape is a fruit</choicehint>
                    <choicehint selected="false">Remember that grape is also a fruit.</choicehint>
                </choice>
                <choice correct="false">Mustang</choice>
                <choice correct="false">Camero
                    <choicehint selected="true">I don't know what a Camero is but it isn't a fruit.</choicehint>
                    <choicehint selected="false">What is a camero anyway?</choicehint>
                </choice>
                <compoundhint value="A*B">You're right that apple is a fruit, but there's one you're missing. Also, mushroom is not a fruit.</compoundhint>
                <compoundhint value="B*C">You're right that grape is a fruit, but there's one you're missing. Also, mushroom is not a fruit.</compoundhint>
            </checkboxgroup>
        </choiceresponse>

        <label>Select all the vegetables from the list</label>
        <choiceresponse>
            <checkboxgroup>
                <choice correct="false">Banana
                    <choicehint selected="true">No, sorry, a banana is a fruit.</choicehint>
                    <choicehint selected="false">poor banana.</choicehint>
                </choice>
                <choice correct="false">Ice Cream</choice>
                <choice correct="false">Mushroom
                    <choicehint selected="true">Mushroom is a fungus, not a vegetable.</choicehint>
                    <choicehint selected="false">You're right that mushrooms aren't vegetables.</choicehint>
                </choice>
                <choice correct="true">Brussel Sprout
                    <choicehint selected="true">Brussel sprouts are vegetables.</choicehint>
                    <choicehint selected="false">Brussel sprout is the only vegetable in this list.</choicehint>
                </choice>
                <compoundhint value="A*B">Making a banana split?</compoundhint>
                <compoundhint value="B*D">That will make a horrible dessert: a brussel sprout split?</compoundhint>
            </checkboxgroup>
        </choiceresponse>
    </problem>
    """)

  it 'produces xml also with demand hints', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>Select all the fruits from the list<<

      [x] Apple     	 	 {{ selected: You're right that apple is a fruit. }, {unselected: Remember that apple is also a fruit.}}
      [ ] Mushroom	   	 {{U: You're right that mushrooms aren't fruit}, { selected: Mushroom is a fungus, not a fruit.}}
      [x] Grape		     {{ selected: You're right that grape is a fruit }, {unselected: Remember that grape is also a fruit.}}
      [ ] Mustang
      [ ] Camero            {{S:I don't know what a Camero is but it isn't a fruit.},{U:What is a camero anyway?}}

      {{ ((A*B)) You're right that apple is a fruit, but there's one you're missing. Also, mushroom is not a fruit.}}
      {{ ((B*C)) You're right that grape is a fruit, but there's one you're missing. Also, mushroom is not a fruit.}}

      >>Select all the vegetables from the list<<

      [ ] Banana     	 	 {{ selected: No, sorry, a banana is a fruit. }, {unselected: poor banana.}}
      [ ] Ice Cream
      [ ] Mushroom	   	 {{U: You're right that mushrooms aren't vegatbles}, { selected: Mushroom is a fungus, not a vegetable.}}
      [x] Brussel Sprout	 {{S: Brussel sprouts are vegetables.}, {u: Brussel sprout is the only vegetable in this list.}}

      {{ ((A*B)) Making a banana split? }}
      {{ ((B*D)) That will make a horrible dessert: a brussel sprout split? }}

      || Hint one.||
      || Hint two. ||
      || Hint three. ||
    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>Select all the fruits from the list</label>
        <choiceresponse>
            <checkboxgroup>
                <choice correct="true">Apple
                    <choicehint selected="true">You're right that apple is a fruit.</choicehint>
                    <choicehint selected="false">Remember that apple is also a fruit.</choicehint>
                </choice>
                <choice correct="false">Mushroom
                    <choicehint selected="true">Mushroom is a fungus, not a fruit.</choicehint>
                    <choicehint selected="false">You're right that mushrooms aren't fruit</choicehint>
                </choice>
                <choice correct="true">Grape
                    <choicehint selected="true">You're right that grape is a fruit</choicehint>
                    <choicehint selected="false">Remember that grape is also a fruit.</choicehint>
                </choice>
                <choice correct="false">Mustang</choice>
                <choice correct="false">Camero
                    <choicehint selected="true">I don't know what a Camero is but it isn't a fruit.</choicehint>
                    <choicehint selected="false">What is a camero anyway?</choicehint>
                </choice>
                <compoundhint value="A*B">You're right that apple is a fruit, but there's one you're missing. Also, mushroom is not a fruit.</compoundhint>
                <compoundhint value="B*C">You're right that grape is a fruit, but there's one you're missing. Also, mushroom is not a fruit.</compoundhint>
            </checkboxgroup>
        </choiceresponse>

        <label>Select all the vegetables from the list</label>
        <choiceresponse>
            <checkboxgroup>
                <choice correct="false">Banana
                    <choicehint selected="true">No, sorry, a banana is a fruit.</choicehint>
                    <choicehint selected="false">poor banana.</choicehint>
                </choice>
                <choice correct="false">Ice Cream</choice>
                <choice correct="false">Mushroom
                    <choicehint selected="true">Mushroom is a fungus, not a vegetable.</choicehint>
                    <choicehint selected="false">You're right that mushrooms aren't vegatbles</choicehint>
                </choice>
                <choice correct="true">Brussel Sprout
                    <choicehint selected="true">Brussel sprouts are vegetables.</choicehint>
                    <choicehint selected="false">Brussel sprout is the only vegetable in this list.</choicehint>
                </choice>
                <compoundhint value="A*B">Making a banana split?</compoundhint>
                <compoundhint value="B*D">That will make a horrible dessert: a brussel sprout split?</compoundhint>
            </checkboxgroup>
        </choiceresponse>

        <demandhint>
            <hint>Hint one.</hint>
            <hint>Hint two.</hint>
            <hint>Hint three.</hint>
        </demandhint>
    </problem>
    """)


describe 'Markdown to xml extended hint multiple choice', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>Select the fruit from the list<<

      () Mushroom	  	 {{ Mushroom is a fungus, not a fruit.}}
      () Potato
      (x) Apple     	 	 {{ OUTSTANDING::Apple is indeed a fruit.}}

      >>Select the vegetables from the list<<

      () Mushroom	  	 {{ Mushroom is a fungus, not a vegetable.}}
      (x) Potato	                 {{ Potato is a root vegetable. }}
      () Apple     	 	 {{ OOPS::Apple is a fruit.}}
    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>Select the fruit from the list</label>
        <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
                <choice correct="false">Mushroom
                    <choicehint>Mushroom is a fungus, not a fruit.</choicehint>
                </choice>
                <choice correct="false">Potato</choice>
                <choice correct="true">Apple
                    <choicehint label="OUTSTANDING">Apple is indeed a fruit.</choicehint>
                </choice>
            </choicegroup>
        </multiplechoiceresponse>

        <label>Select the vegetables from the list</label>
        <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
                <choice correct="false">Mushroom
                    <choicehint>Mushroom is a fungus, not a vegetable.</choicehint>
                </choice>
                <choice correct="true">Potato
                    <choicehint>Potato is a root vegetable.</choicehint>
                </choice>
                <choice correct="false">Apple
                    <choicehint label="OOPS">Apple is a fruit.</choicehint>
                </choice>
            </choicegroup>
        </multiplechoiceresponse>
    </problem>
    """)

  it 'produces xml with demand hints', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        >>Select the fruit from the list<<

        () Mushroom	  	 {{ Mushroom is a fungus, not a fruit.}}
        () Potato
        (x) Apple     	 {{ OUTSTANDING::Apple is indeed a fruit.}}

        || 0) spaces on previous line. ||
        || 1) roses are red. ||

        >>Select the vegetables from the list<<

        () Mushroom	  	 {{ Mushroom is a fungus, not a vegetable.}}
        (x) Potato	     {{ Potato is a root vegetable. }}
        () Apple     	 {{ OOPS::Apple is a fruit.}}

        || 2) where are the lions? ||

      """)
      expect(data).toXMLEqual("""
      <problem>
          <label>Select the fruit from the list</label>
          <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                  <choice correct="false">Mushroom
                      <choicehint>Mushroom is a fungus, not a fruit.</choicehint>
                  </choice>
                  <choice correct="false">Potato</choice>
                  <choice correct="true">Apple
                      <choicehint label="OUTSTANDING">Apple is indeed a fruit.</choicehint>
                  </choice>
              </choicegroup>
          </multiplechoiceresponse>

          <label>Select the vegetables from the list</label>
          <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                  <choice correct="false">Mushroom
                      <choicehint>Mushroom is a fungus, not a vegetable.</choicehint>
                  </choice>
                  <choice correct="true">Potato
                      <choicehint>Potato is a root vegetable.</choicehint>
                  </choice>
                  <choice correct="false">Apple
                      <choicehint label="OOPS">Apple is a fruit.</choicehint>
                  </choice>
              </choicegroup>
          </multiplechoiceresponse>

          <demandhint>
              <hint>0) spaces on previous line.</hint>
              <hint>1) roses are red.</hint>
              <hint>2) where are the lions?</hint>
          </demandhint>
      </problem>
      """)


describe 'Markdown to xml extended hint text input', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>In which country would you find the city of Paris?<<
                    = France		{{ BRAVO::Viva la France! }}

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="France" type="ci">
      <label>In which country would you find the city of Paris?</label>
    <correcthint label="BRAVO">Viva la France!</correcthint>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with or=', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>Where Paris?<<
      = France		{{ BRAVO::hint1}}
      or= USA			{{   meh::hint2  }}

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="France" type="ci">
      <label>Where Paris?</label>
    <correcthint label="BRAVO">hint1</correcthint>
      <additional_answer answer="USA"><correcthint label="meh">hint2</correcthint>
    </additional_answer>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with not=', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>Revenge is a dish best served<<
      = cold {{khaaaaaan!}}
      not= warm {{feedback2}}

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="cold" type="ci">
      <label>Revenge is a dish best served</label>
    <correcthint>khaaaaaan!</correcthint>
      <stringequalhint answer="warm">feedback2</stringequalhint>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with s=', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>q<<
      s= 2 {{feedback1}}

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="2" type="ci">
      <label>q</label>
    <correcthint>feedback1</correcthint>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with = and or= and not=', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>q<<
      = aaa
      or= bbb {{feedback1}}
      not= no {{feedback2}}
      or= ccc

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="aaa" type="ci">
      <label>q</label>
    <additional_answer answer="bbb"><correcthint>feedback1</correcthint>
    </additional_answer>
      <stringequalhint answer="no">feedback2</stringequalhint>
      <additional_answer answer="ccc"/>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with s= and or=', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>q<<
      s= 2 {{feedback1}}
      or= bbb {{feedback2}}
      or= ccc

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="2" type="ci">
      <label>q</label>
    <correcthint>feedback1</correcthint>
      <additional_answer answer="bbb"><correcthint>feedback2</correcthint>
    </additional_answer>
      <additional_answer answer="ccc"/>
      <textline size="20"/>
    </stringresponse>


    </problem>
    """)

  it 'produces xml with each = making a new question', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>q<<
        = aaa
        or= bbb
        s= ccc
    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>q</label>
        <stringresponse answer="aaa" type="ci">
            <additional_answer answer="bbb"></additional_answer>
            <textline size="20"/>
        </stringresponse>
        <stringresponse answer="ccc" type="ci">
            <textline size="20"/>
        </stringresponse>
    </problem>
    """)

  it 'produces xml with each = making a new question amid blank lines and paragraphs', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      paragraph
      >>q<<
      = aaa

      or= bbb
      s= ccc

      paragraph 2

    """)
    expect(data).toXMLEqual("""
    <problem>
        <p>paragraph</p>
        <label>q</label>
        <stringresponse answer="aaa" type="ci">
            <additional_answer answer="bbb"></additional_answer>
            <textline size="20"/>
        </stringresponse>
        <stringresponse answer="ccc" type="ci">
            <textline size="20"/>
        </stringresponse>
        <p>paragraph 2</p>
    </problem>
    """)

  it 'produces xml without a question when or= is just hung out there by itself', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      paragraph
      >>q<<
      or= aaa
      paragraph 2

    """)
    expect(data).toXMLEqual("""
    <problem>
        <p>paragraph</p>
        <label>q</label>
        <p>or= aaa</p>
        <p>paragraph 2</p>
    </problem>
    """)

  it 'produces xml with each = with feedback making a new question', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
      >>q<<
      s= aaa
      or= bbb {{feedback1}}
      = ccc {{feedback2}}

    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>q</label>
        <stringresponse answer="aaa" type="ci">
            <additional_answer answer="bbb">
                <correcthint>feedback1</correcthint>
            </additional_answer>
            <textline size="20"/>
        </stringresponse>
        <stringresponse answer="ccc" type="ci">
            <correcthint>feedback2</correcthint>
            <textline size="20"/>
        </stringresponse>
    </problem>
    """)

  it 'produces xml with demand hints', ->
    data = MarkdownEditingDescriptor.markdownToXml(""">>Where Paris?<<
          = France		{{ BRAVO::hint1 }}

          || There are actually two countries with cities named Paris. ||
          || Paris is the capital of one of those countries. ||

    """)
    expect(data).toXMLEqual("""
    <problem>
    <stringresponse answer="France" type="ci">
      <label>Where Paris?</label>
    <correcthint label="BRAVO">hint1</correcthint>
      <textline size="20"/>
    </stringresponse>

    <demandhint>
      <hint>There are actually two countries with cities named Paris.</hint>
      <hint>Paris is the capital of one of those countries.</hint>
    </demandhint>
    </problem>""")


describe 'Markdown to xml extended hint numeric input', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>Enter the numerical value of Pi:<<
        = 3.14159 +- .02   {{ Pie for everyone!   }}

        >>Enter the approximate value of 502*9:<<
        = 4518 +- 15%  {{PIE:: No pie for you!}}

        >>Enter the number of fingers on a human hand<<
        = 5

    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>Enter the numerical value of Pi:</label>
        <numericalresponse answer="3.14159">
            <responseparam type="tolerance" default=".02"/>
            <formulaequationinput/>
            <correcthint>Pie for everyone!</correcthint>
        </numericalresponse>

        <label>Enter the approximate value of 502*9:</label>
        <numericalresponse answer="4518">
            <responseparam type="tolerance" default="15%"/>
            <formulaequationinput/>
            <correcthint label="PIE">No pie for you!</correcthint>
        </numericalresponse>

        <label>Enter the number of fingers on a human hand</label>
        <numericalresponse answer="5">
            <formulaequationinput/>
        </numericalresponse>
    </problem>
    """)

  # The output xml here shows some of the quirks of how historical markdown parsing does or does not put
  # in blank lines.
  it 'numeric input with hints and demand hints', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>text1<<
        = 1   {{ hint1  }}
        || hintA ||
        >>text2<<
        = 2 {{ hint2 }}

        || hintB ||

    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>text1</label>
        <numericalresponse answer="1">
            <formulaequationinput/>
            <correcthint>hint1</correcthint>
        </numericalresponse>
        <label>text2</label>
        <numericalresponse answer="2">
            <formulaequationinput/>
            <correcthint>hint2</correcthint>
        </numericalresponse>

        <demandhint>
            <hint>hintA</hint>
            <hint>hintB</hint>
        </demandhint>
    </problem>
    """)


describe 'Markdown to xml extended hint with multiline hints', ->
  it 'produces xml', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>Checkboxes<<

        [x] A {{
        selected:  aaa  },
        {unselected:bbb}}
        [ ] B {{U: c}, {
        selected: d.}}

        {{ ((A*B)) A*B hint}}

        >>What is 1 + 1?<<
        = 2  {{ part one, and
                part two
             }}

        >>hello?<<
        = hello {{
        hello
        hint
        }}

        >>multiple choice<<
        (x) AA{{hint1}}
        () BB    {{
             hint2
        }}
        ( )  CC  {{ hint3
        }}

        >>dropdown<<
        [[
           W1  {{
            no }}
           W2	                  {{
           nope}}
           (C1)	 {{ yes
            }}
        ]]

        || aaa ||
        ||bbb||
        ||       ccc      ||

    """)
    expect(data).toXMLEqual("""
    <problem>
        <label>Checkboxes</label>
        <choiceresponse>
            <checkboxgroup>
                <choice correct="true">A
                    <choicehint selected="true">aaa</choicehint>
                    <choicehint selected="false">bbb</choicehint>
                </choice>
                <choice correct="false">B
                    <choicehint selected="true">d.</choicehint>
                    <choicehint selected="false">c</choicehint>
                </choice>
                <compoundhint value="A*B">A*B hint</compoundhint>
            </checkboxgroup>
        </choiceresponse>

        <label>What is 1 + 1?</label>
        <numericalresponse answer="2">
            <formulaequationinput/>
            <correcthint>part one, and part two</correcthint>
        </numericalresponse>

        <label>hello?</label>
        <stringresponse answer="hello" type="ci">
            <correcthint>hello hint</correcthint>
            <textline size="20"/>
        </stringresponse>

        <label>multiple choice</label>
        <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
                <choice correct="true">AA
                    <choicehint>hint1</choicehint>
                </choice>
                <choice correct="false">BB
                    <choicehint>hint2</choicehint>
                </choice>
                <choice correct="false">CC
                    <choicehint>hint3</choicehint>
                </choice>
            </choicegroup>
        </multiplechoiceresponse>

        <label>dropdown</label>
        <optionresponse>
            <optioninput>
                <option correct="False">W1
                    <optionhint>no</optionhint>
                </option>
                <option correct="False">W2
                    <optionhint>nope</optionhint>
                </option>
                <option correct="True">C1
                    <optionhint>yes</optionhint>
                </option>
            </optioninput>
        </optionresponse>

        <demandhint>
            <hint>aaa</hint>
            <hint>bbb</hint>
            <hint>ccc</hint>
        </demandhint>
    </problem>
    """)

describe 'Markdown to xml extended hint with tricky syntax cases', ->
  # I'm entering this as utf-8 in this file.
  # I cannot find a way to set the encoding for .coffee files but it seems to work.
  it 'produces xml with unicode', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>á and Ø<<

        (x) Ø{{Ø}}
        () BB

        || Ø ||

    """)
    expect(data).toXMLEqual("""
    <problem>
        <multiplechoiceresponse>
            <label>á and Ø</label>
            <choicegroup type="MultipleChoice">
                <choice correct="true">Ø
                    <choicehint>Ø</choicehint>
                </choice>
                <choice correct="false">BB</choice>
            </choicegroup>
        </multiplechoiceresponse>

        <demandhint>
            <hint>Ø</hint>
        </demandhint>
    </problem>
    """)

  it 'produces xml with quote-type characters', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>"quotes" aren't `fun`<<
        () "hello" {{ isn't }}
        (x) "isn't"  {{ "hello" }}

    """)
    expect(data).toXMLEqual("""
    <problem>
        <multiplechoiceresponse>
            <label>"quotes" aren't `fun`</label>
            <choicegroup type="MultipleChoice">
                <choice correct="false">"hello"
                    <choicehint>isn't</choicehint>
                </choice>
                <choice correct="true">"isn't"
                    <choicehint>"hello"</choicehint>
                </choice>
            </choicegroup>
        </multiplechoiceresponse>
    </problem>
    """)

  it 'produces xml with almost but not quite multiple choice syntax', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>q1<<
        this (x)
        () a  {{ (hint) }}
        (x) b
        that (y)
    """)
    expect(data).toXMLEqual("""
    <problem>
    <multiplechoiceresponse>
      <label>q1</label>
    <p>this (x)</p>
    <choicegroup type="MultipleChoice">
        <choice correct="false">a <choicehint>(hint)</choicehint>
    </choice>
        <choice correct="true">b</choice>
      </choicegroup>
    <p>that (y)</p>
    </multiplechoiceresponse>


    </problem>
    """)

  # An incomplete checkbox hint passes through to cue the author
  it 'produce xml with almost but not quite checkboxgroup syntax', ->
    data = MarkdownEditingDescriptor.markdownToXml("""
        >>q1<<
        this [x]
        [ ] a [square]
        [x] b {{ this hint passes through }}
        that []
    """)
    expect(data).toXMLEqual("""
    <problem>
    <choiceresponse>
      <label>q1</label>
    <p>this [x]</p>
    <checkboxgroup>
        <choice correct="false">a [square]</choice>
        <choice correct="true">b {{ this hint passes through }}</choice>
      </checkboxgroup>
    <p>that []</p>
    </choiceresponse>


    </problem>
    """)

  # It's sort of a pain to edit DOS line endings without some editor or other "fixing" them
  # for you. Therefore, we construct DOS line endings on the fly just for the test.
  it 'produces xml with DOS \r\n line endings', ->
    markdown = """
           >>q22<<

           [[
              (x) {{ hintx
                  these
                  span
                  }}

              yy	                 {{ meh::hinty }}
              zzz	{{ hintz }}
           ]]
      """
    markdown = markdown.replace(/\n/g, '\r\n')  # make DOS line endings
    data = MarkdownEditingDescriptor.markdownToXml(markdown)
    expect(data).toXMLEqual("""
    <problem>
    <optionresponse>
      <label>q22</label>
    <optioninput>
        <option correct="True">x <optionhint>hintx these span</optionhint>
    </option>
        <option correct="False">yy <optionhint label="meh">hinty</optionhint>
    </option>
        <option correct="False">zzz <optionhint>hintz</optionhint>
    </option>
      </optioninput>
    </optionresponse>


    </problem>
    """)
