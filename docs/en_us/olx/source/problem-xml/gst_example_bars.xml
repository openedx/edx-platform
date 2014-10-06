<vertical>
    <graphical_slider_tool>
      <render>
        <h2>Graphic slider tool: Bar graph example.</h2>

        <p>We can request the API to plot us a bar graph.</p>
        <div style="clear:both">
          <p style="width:60px;float:left;">a</p>
          <slider var='a' style="width:400px;float:left;"/>
          <textbox var='a' style="width:50px;float:left;margin-left:15px;"/>
          <br /><br /><br />
          <p style="width:60px;float:left;">b</p>
          <slider var='b' style="width:400px;float:left;"/>
          <textbox var='b' style="width:50px;float:left;margin-left:15px;"/>
        </div>
          <plot style="clear:left;"/>
      </render>
      <configuration>
        <parameters>
            <param var="a" min="-100" max="100" step="5" initial="25" />
            <param var="b" min="-100" max="100" step="5" initial="50" />
        </parameters>
        <functions>
          <function bar="true" color="blue" label="Men">
            <![CDATA[if (((x>0.9) && (x<1.1)) || ((x>4.9) && (x<5.1))) { return Math.sin(a * 0.01 * Math.PI + 2.952 * x); }
            else {return undefined;}]]>
          </function>
          <function bar="true" color="red" label="Women">
            <![CDATA[if (((x>1.9) && (x<2.1)) || ((x>3.9) && (x<4.1))) { return Math.cos(b * 0.01 * Math.PI + 3.432 * x); }
            else {return undefined;}]]>
          </function>
          <function bar="true" color="green" label="Other 1">
            <![CDATA[if (((x>1.9) && (x<2.1)) || ((x>3.9) && (x<4.1))) { return Math.cos((b - 10 * a) * 0.01 * Math.PI + 3.432 * x); }
            else {return undefined;}]]>
          </function>
          <function bar="true" color="yellow" label="Other 2">
            <![CDATA[if (((x>1.9) && (x<2.1)) || ((x>3.9) && (x<4.1))) { return Math.cos((b + 7 * a) * 0.01 * Math.PI + 3.432 * x); }
            else {return undefined;}]]>
          </function>
        </functions>
        <plot>
          <xrange><min>1</min><max>5</max></xrange>
          <num_points>5</num_points>
          <xticks>0, 0.5, 6</xticks>
          <yticks>-1.5, 0.1, 1.5</yticks>
          <xticks_names>
          <![CDATA[
              {
                  "1.5": "Single", "4.5": "Married"
              }
          ]]>
          </xticks_names>
          <yticks_names>
          <![CDATA[
              {
                  "-1.0": "-100%", "-0.5": "-50%", "0.0": "0%", "0.5": "50%", "1.0": "100%"
              }
          ]]>
          </yticks_names>
          <bar_width>0.4</bar_width>
        </plot>
      </configuration>
    </graphical_slider_tool>
</vertical>
