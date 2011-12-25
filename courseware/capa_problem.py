import random, numpy, math, scipy, sys, StringIO, os, struct, json
from dateutil import parser

from xml.dom.minidom import parse, parseString

from calc import evaluator

def strip_dict(d):
    ''' Takes a dict. Returns an identical dict, with all non-word keys stripped out. ''' 
    d=dict([(k, float(d[k])) for k in d if type(k)==str and \
                                           k.isalnum() and \
                                           (type(d[k]) == float or type(d[k]) == int) ])
    return d

class LoncapaProblem():
    def get_state(self):
        ''' Stored per-user session data neeeded to: 
            1) Recreate the problem
            2) Populate any student answers. '''
        return {'seed':self.seed, 
                'answers':self.answers,
                'correct_map':self.correct_map, 
                'done':self.done}

    def get_score(self):
        correct=0
        for key in self.correct_map:
            if self.correct_map[key] == u'correct':
                correct += 1
        if len(self.answers)==0:
            return {'score':0,
                    'total':len(self.questions)}
        else:
            return {'score':correct,
                    'total':len(self.questions)}

    def get_html(self):
        ''' Return the HTML of the question '''
        return self.text

    def __init__(self, filename, id=None, state=None):
        ''' Create a new problem of the type defined in filename. 
            By default, this will generate a random problem. Passing 
            seed will provide the random seed. Alternatively, passing
            context will bypass all script execution, and use the 
            given execution context.  '''
        self.done=False
        self.text=""
        self.context=dict()   # Execution context from loncapa/python
        self.questions=dict() # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
        self.answers=dict()   # Student answers
        self.correct_map=dict()
        self.seed=None
        self.gid="" # ID of the problem
        self.lid=-1 # ID of the field within the problem


        if state==None:
            state=dict()
        self.gid=id

        if 'done' in state:
            self.done=state['done']

        if 'seed' in state and state['seed']!=None and state['seed']!="":
            self.seed=state['seed']
        else:
            # TODO: Check performance of urandom -- depending on
            # implementation, it may slow down to the point of causing
            # performance issues if we deplete the kernel entropy
            # pool.
            self.seed=struct.unpack('i', os.urandom(4))[0] 

        if 'answers' in state:
            self.answers=state['answers']
        if 'correct_map' in state:
            self.correct_map=state['correct_map']
        random.seed(self.seed)
        dom=parse(filename).childNodes[0]

        g={'random':random,'numpy':numpy,'math':math,'scipy':scipy}

        # Buffer stores HTML for problem
        buf=StringIO.StringIO()
        
        ot=False ## Are we in an outtext context? 

        # Loop through the nodes of the problem, and 
        for e in dom.childNodes:
            if e.localName=='script':
                exec e.childNodes[0].data in g,self.context
            elif e.localName=='endouttext':
                ot=False
            elif ot:
                e.writexml(buf)
            elif e.localName=='startouttext':
                ot=True
            elif e.localName in self.handlers:
                problem=self.handlers[e.localName](self,e)
                buf.write(problem)
            elif e.localName==None:
                pass
            else: 
                raise Exception("ERROR: UNRECOGNIZED XML"+e.localName)

        self.text=buf.getvalue()
        self.text=self.contextualize_text(self.text)
        self.filename=filename

    def get_context(self):
        ''' Return the execution context '''
        return self.context

    def get_seed(self):
        ''' Return the random seed used to generate the problem '''
        return self.seed

    def get_correct_map(self):
        return self.correct_map

    def set_answers(self, answers):
        self.answers=answers

    def get_question_answers(self):
        rv = dict()
        for key in self.questions:
            rv[key]=str(self.questions[key]['answer'])
        return rv

    def grade_answers(self, answers):
        ''' Takes a map of IDs to answers. Return which ones are correct '''
        self.answers=answers
        correct_map={}
        for key in self.questions:
           id=self.questions[key]['id']
           if id not in answers:
               correct_map[id]='incorrect' # Should always be there
           else:
               grader=self.graders[self.questions[key]['type']]
               correct_map[id]=grader(self, self.questions[key],
                                      self.answers[id])
        self.correct_map=correct_map
        return correct_map

    def handle_schem(self, element):
        height = element.getAttribute('height')
        width = element.getAttribute('width')
        if height=="":
            height=480
        if width=="":
            width=640
        self.lid+=1
        id=str(self.gid)+'_'+str(self.lid)
        
        html='<input type="hidden" class="schematic" name="input_{id}" '+ \
            'height="{height}" width="{width}" value="{value}" id="input_{id}">'
        html = html.format(height=height, width=width, id=id, value="")

        return html
    
    def grade_schem(self, element):
        return "correct"


    def grade_nr(self, question, answer):
        error = abs(evaluator({},{},answer) - question['answer'])
        allowed_error = abs(question['answer']*question['tolerance'])
        if error <= allowed_error:
            return 'correct'
        else:
            return 'incorrect'

    def handle_nr(self, element):
        answer=element.getAttribute('answer')
        for e in element.childNodes:
            if e.nodeType==1 and e.getAttribute('type')=="tolerance":
                tolerance=e.getAttribute('default')
        self.lid+=1
        id=str(self.gid)+'_'+str(self.lid)
        problem={"answer":evaluator({},{},self.contextualize_text(answer)),
                 "type":"numericalresponse",
                 "tolerance":evaluator({},{},self.contextualize_text(tolerance)),
                 "id":id,
                 "lid":self.lid,
                 }
        self.questions[self.lid]=problem

        if id in self.answers:
            value=self.answers[id]
        else:
            value=""
        icon='bullet'
        if id in self.correct_map and self.correct_map[id]=='correct':
            icon='check'
        if id in self.correct_map and self.correct_map[id]=='incorrect':
            icon='close'

        html='<input type="text" name="input_{id}" id="input_{id}" value="{value}"><span id="answer_{id}"></span><span class="ui-icon ui-icon-{icon}" style="display:inline-block;" id="status_{id}"></span> '.format(id=id,value=value,icon=icon)
        return html

    def grade_fr(self, question, answer):
        correct = True
        for i in range(question['samples_count']):
            instructor_variables = strip_dict(dict(self.context))
            student_variables = dict()
            for var in question['sample_range']:
                value = random.uniform(*question['sample_range'][var])
                instructor_variables[str(var)] = value
                student_variables[str(var)] = value
            instructor_result = evaluator(instructor_variables,{},str(question['answer']))
            student_result = evaluator(student_variables,{},str(answer))
            if math.isnan(student_result) or math.isinf(student_result):
                return "incorrect"
            if abs( student_result - instructor_result ) > question['tolerance']:
                return "incorrect"
 
        return "correct"

    def handle_fr(self, element):
        ## Extract description from element
        samples=element.getAttribute('samples')
        variables=samples.split('@')[0].split(',')
        numsamples=int(samples.split('@')[1].split('#')[1])
        sranges=zip(*map(lambda x:map(float, x.split(",")), samples.split('@')[1].split('#')[0].split(':')))
        answer=element.getAttribute('answer')
        for e in element.childNodes:
            if e.nodeType==1 and e.getAttribute('type')=="tolerance":
                tolerance=e.getAttribute('default')

        # Store element
        self.lid+=1
        id=str(self.gid)+'_'+str(self.lid)
        problem={"answer":self.contextualize_text(answer),
                 "type":"formularesponse",
                 "tolerance":evaluator({},{},self.contextualize_text(tolerance)),
                 "sample_range":dict(zip(variables, sranges)),
                 "samples_count": numsamples,
                 "id":id,
                 "lid":self.lid,
                 }
        self.questions[self.lid]=problem        

        # Generate HTML
        if id in self.answers:
            value=self.answers[id]
        else:
            value=""
        icon='bullet'
        if id in self.correct_map and self.correct_map[id]=='correct':
            icon='check'
        if id in self.correct_map and self.correct_map[id]=='incorrect':
            icon='close'

        html='<input type="text" name="input_{id}" id="input_{id}" value="{value}"><span id="answer_{id}"></span><span class="ui-icon ui-icon-{icon}" style="display:inline-block;" id="status_{id}"></span> '.format(id=id,value=value,icon=icon)
        return html

    graders={'numericalresponse':grade_nr,
             'formularesponse':grade_fr, 
             'schematicresponse':grade_schem}
    handlers={'numericalresponse':handle_nr,
              'formularesponse':handle_fr, 
              'schematicresponse':handle_schem}

    def contextualize_text(self, text):
        ''' Takes a string with variables. E.g. $a+$b. 
            Does a substitution of those variables from the context '''
        for key in sorted(self.context, lambda x,y:cmp(len(y),len(x))):
            text=text.replace('$'+key, str(self.context[key]))
        return text

if __name__=='__main__':  
    p=LoncapaProblem('resistor.xml', seed=-1601461296)

    print p.getHtml()
    print p.getContext()
    print p.getSeed()
