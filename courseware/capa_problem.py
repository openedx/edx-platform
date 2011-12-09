# For calculator: 
# http://pyparsing.wikispaces.com/file/view/fourFn.py

import random, numpy, math, scipy, sys, StringIO, os, struct, json

from xml.dom.minidom import parse, parseString

class LoncapaProblem():
    def get_state(self):
        ''' Stored per-user session data neeeded to: 
            1) Recreate the problem
            2) Populate any student answers. '''
        return json.dumps({'seed':self.seed, 
                           'answers':self.answers,
                           'correct_map':self.correct_map, 
                           'done':self.done})

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
        print "!!",filename, id
        if state!=None:
            state=json.loads(state)
        else:
            state={}
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

        buf=StringIO.StringIO()
        
        ot=False ## Are we in an outtext context? 

        for e in dom.childNodes:
            if e.localName=='script':
                exec e.childNodes[0].data in g,self.context
            if e.localName=='endouttext':
                ot=False
            if ot:
                e.writexml(buf)
            if e.localName=='startouttext':
                ot=True
            if e.localName in self.handlers:
                problem=self.handlers[e.localName](self,e)
                buf.write(problem)

        self.text=buf.getvalue()
        self.text=self.contextualize_text(self.text)
        self.filename=filename

    done=False
    text=""
    context={}   # Execution context from loncapa/python
    questions={} # Detailed info about questions in problem instance. TODO: Should be by id and not lid. 
    answers={}   # Student answers
    correct_map={}
    seed=None
    gid="" # ID of the problem
    lid=-1 # ID of the field within the problem

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

    def grade_answers(self, answers):
        ''' Takes a map of IDs to answers. Return which ones are correct '''
        self.answers=answers
        correct_map={}
        for key in self.questions:
           id=self.questions[key]['id']
           if id not in answers:
               correct_map[id]='incorrect' # Should always be there
           else:
               correct_map[id]=self.grade_nr(self.questions[key],
                                             self.answers[id])
        self.correct_map=correct_map
        return correct_map


    ## Internal methods
    def number(self,text):
        ''' Convert a number to a float, understanding suffixes '''
        try:
            text.strip()
            suffixes={'%':0.01,'k':1e3,'M':1e6,'G':1e9,'T':1e12,'P':1e15,
                      'E':1e18,'Z':1e21,'Y':1e24,'c':1e-2,'m':1e-3,'u':1e-6,
                      'n':1e-9,'p':1e-12,'f':1e-15,'a':1e-18,'z':1e-21,'y':1e-24}
            if text[-1] in suffixes:
                return float(text[:-1])*suffixes[text[-1]]
            else:
                return float(text)
        except:
            return 0 # TODO: Better error handling? 

    def grade_nr(self, question, answer):
        error = abs(self.number(answer) - question['answer'])
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
        problem={"answer":self.number(self.contextualize_text(answer)),
                 "type":"numericalresponse",
                 "tolerance":self.number(self.contextualize_text(tolerance)),
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

        html='<input type="text" name="input_{id}" id="input_{id}" value="{value}"><span class="ui-icon ui-icon-{icon}" style="display:inline-block;" id="status_{id}"></span> '.format(id=id,value=value,icon=icon)
        return html


    graders={'numericalresponse':grade_nr}
    handlers={'numericalresponse':handle_nr}

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
