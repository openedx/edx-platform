.. _JavaScript Input:

JavaScript Input
----------------

The JavaScript Input problem type allows you to create your own learning tool 
using HTML and other standard Internet languages and then add the tool directly 
into Studio. When you use this problem type, Studio embeds your tool in an 
IFrame so that your students can interact with it in the LMS. You can grade
your students' work using JavaScript and some basic Python, and the grading
is integrated into the edX grading system.

This problem type doesn't appear in the menu of advanced problems in Studio. To
create a JavaScript input problem type, you'll create a blank advanced problem,
and then enter your code into the component editor.

.. image:: /Images/JavaScriptInputExample.gif

Create a JavaScript Input Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create your JavaScript application, and then upload all files associated with
   that application to the **Files & Uploads** page.
#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Blank Advanced Problem**.
#. In the component that appears, click **Edit**.
#. Click the **Settings** tab.
#. Set **Maximum Attempts** to a number larger than zero.
#. In the component editor, enter your code.
#. Click **Save**.

To re-create the example problem above, follow these steps.

#. Go to :ref:`Appendix F` and create the following files:

   - webGLDemo.html
   - webGLDemo.js
   - webGLDemo.css
   - three.min.js

#. On the **Files & Uploads** page, upload the four files you just created.
#. Create a new blank advanced problem component.
#. On the **Settings** tab, set **Maximum Attempts** to a number larger than 
   zero.
#. In the problem component editor, paste the code below.
#. Click **Save.**



JavaScript Input Problem Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:: 

    <problem display_name="webGLDemo">
    In the image below, click the cone.  
    
    <script type="loncapa/python">
    import json
    def vglcfn(e, ans):
        '''
        par is a dictionary containing two keys, "answer" and "state"
        The value of answer is the JSON string returned by getGrade
        The value of state is the JSON string returned by getState
        '''
        par = json.loads(ans)
        # We can use either the value of the answer key to grade
        answer = json.loads(par["answer"])
        return answer["cylinder"]  and not answer["cube"]
        # Or we can use the value of the state key
        '''
        state = json.loads(par["state"])
        selectedObjects = state["selectedObjects"]
        return selectedObjects["cylinder"] and not selectedObjects["cube"]
        '''
    </script>
    <customresponse cfn="vglcfn">
        <jsinput
            gradefn="WebGLDemo.getGrade"
            get_statefn="WebGLDemo.getState"
            set_statefn="WebGLDemo.setState"
            width="400"
            height="400"
            html_file="/static/webGLDemo.html"
        />
    </customresponse>
    </problem>
  

**Notes**

- The webGLDemo.js file defines the three JavaScript functions (**WebGLDemo.getGrade**, 
  **WebGLDemo.getState**, and **WebGLDemo.setState**).

- The JavaScript input problem code uses **WebGLDemo.getGrade**, **WebGLDemo.getState**, 
  and **WebGLDemo.setState** to grade, save, or restore a problem. These functions must 
  be global in scope. 

- **WebGLDemo.getState** and **WebGLDemo.setState** are optional. You only have to define
  these functions if you want to conserve the state of the problem.

- **Width** and **height** represent the dimensions of the IFrame that holds the
  application.
  
- When the problem opens, the cone and the cube are both blue, or "unselected." When
  you click either shape once, the shape becomes yellow, or "selected." To unselect
  the shape, click it again. Continue clicking the shape to select and unselect it.

- The response is graded as correct if the cone is selected (yellow) when the user 
  clicks **Check**.
  
- Clicking **Check** or **Save** registers the problem's current state.