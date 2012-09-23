class HonorResponse(LoncapaResponse):
    '''
    Grade student code using an external queueing server, called 'xqueue'

    Expects 'xqueue' dict in ModuleSystem with the following keys:
        system.xqueue = { 'interface': XqueueInterface object,
                          'callback_url': Per-StudentModule callback URL where results are posted (string),
                          'default_queuename': Default queuename to submit request (string)
                        }

    External requests are only submitted for student submission grading 
        (i.e. and not for getting reference answers)
    '''

    response_tag = 'honorresponse'
    allowed_inputfields = ['textbox', 'filesubmission']

    def setup_response(self):
        '''
        Configure CodeResponse from XML. Supports both CodeResponse and ExternalResponse XML

        TODO: Determines whether in synchronous or asynchronous (queued) mode
        '''
        xml = self.xml
        self.url = xml.get('url', None) # XML can override external resource (grader/queue) URL
        self.queue_name = xml.get('queuename', self.system.xqueue['default_queuename'])

        # VS[compat]:
        #   Check if XML uses the ExternalResponse format or the generic CodeResponse format
        codeparam = self.xml.find('codeparam')
        if codeparam is None:
            self._parse_externalresponse_xml()
        else:
            self._parse_coderesponse_xml(codeparam)

    def _parse_coderesponse_xml(self,codeparam):
        '''
        Parse the new CodeResponse XML format. When successful, sets:
            self.initial_display
            self.answer (an answer to display to the student in the LMS)
            self.payload
        '''
        # Note that CodeResponse is agnostic to the specific contents of grader_payload
        grader_payload = codeparam.find('grader_payload')
        grader_payload = grader_payload.text if grader_payload is not None else ''
        self.payload = {'grader_payload': grader_payload}

        answer_display = codeparam.find('answer_display')
        if answer_display is not None:
            self.answer = answer_display.text
        else:
            self.answer = 'No answer provided.'

        initial_display = codeparam.find('initial_display')
        if initial_display is not None:
            self.initial_display = initial_display.text
        else:
            self.initial_display = ''

    def _parse_externalresponse_xml(self):
        '''
        VS[compat]: Suppport for old ExternalResponse XML format. When successful, sets:
            self.initial_display
            self.answer (an answer to display to the student in the LMS)
            self.payload
        '''
        answer = self.xml.find('answer')

        if answer is not None:
            answer_src = answer.get('src')
            if answer_src is not None:
                code = self.system.filesystem.open('src/' + answer_src).read()
            else:
                code = answer.text
        else:  # no <answer> stanza; get code from <script>
            code = self.context['script_code']
            if not code:
                msg = '%s: Missing answer script code for coderesponse' % unicode(self)
                msg += "\nSee XML source line %s" % getattr(self.xml, 'sourceline', '<unavailable>')
                raise LoncapaProblemError(msg)

        tests = self.xml.get('tests')

        # Extract 'answer' and 'initial_display' from XML. Note that the code to be exec'ed here is:
        #   (1) Internal edX code, i.e. NOT student submissions, and
        #   (2) The code should only define the strings 'initial_display', 'answer', 'preamble', 'test_program'
        #           following the ExternalResponse XML format
        penv = {}
        penv['__builtins__'] = globals()['__builtins__']
        try:
            exec(code, penv, penv)
        except Exception as err:
            log.error('Error in CodeResponse %s: Error in problem reference code' % err)
            raise Exception(err)
        try:
            self.answer = penv['answer']
            self.initial_display = penv['initial_display']
        except Exception as err:
            log.error("Error in CodeResponse %s: Problem reference code does not define 'answer' and/or 'initial_display' in <answer>...</answer>" % err)
            raise Exception(err)

        # Finally, make the ExternalResponse input XML format conform to the generic exteral grader interface
        #   The XML tagging of grader_payload is pyxserver-specific
        grader_payload  = '<pyxserver>'
        grader_payload += '<tests>' + tests + '</tests>\n'
        grader_payload += '<processor>' + code + '</processor>'
        grader_payload += '</pyxserver>'
        self.payload = {'grader_payload': grader_payload}

    def get_score(self, student_answers):
        try:
            submission = student_answers[self.answer_id] # Note that submission can be a file
        except Exception as err:
            log.error('Error in CodeResponse %s: cannot get student answer for %s; student_answers=%s' %
                (err, self.answer_id, convert_files_to_filenames(student_answers)))
            raise Exception(err)

        # Prepare xqueue request
        #------------------------------------------------------------ 
        qinterface = self.system.xqueue['interface']

        # Generate header
        queuekey = xqueue_interface.make_hashkey(str(self.system.seed)+self.answer_id)
        xheader = xqueue_interface.make_xheader(lms_callback_url=self.system.xqueue['callback_url'],
                                                lms_key=queuekey,
                                                queue_name=self.queue_name)

        # Generate body
        if is_list_of_files(submission):
            self.context.update({'submission': queuekey}) # For tracking. TODO: May want to record something else here
        else:
            self.context.update({'submission': submission})

        contents = self.payload.copy() 

        # Submit request. When successful, 'msg' is the prior length of the queue
        if is_list_of_files(submission):
            contents.update({'student_response': ''}) # TODO: Is there any information we want to send here?
            (error, msg) = qinterface.send_to_queue(header=xheader,
                                                    body=json.dumps(contents),
                                                    files_to_upload=submission)
        else:
            contents.update({'student_response': submission})
            (error, msg) = qinterface.send_to_queue(header=xheader,
                                                    body=json.dumps(contents))

        cmap = CorrectMap() 
        if error:
            cmap.set(self.answer_id, queuekey=None,
                     msg='Unable to deliver your submission to grader. (Reason: %s.) Please try again later.' % msg)
        else:
            # Queueing mechanism flags:
            #   1) Backend: Non-null CorrectMap['queuekey'] indicates that the problem has been queued
            #   2) Frontend: correctness='incomplete' eventually trickles down through inputtypes.textbox 
            #       and .filesubmission to inform the browser to poll the LMS
            cmap.set(self.answer_id, queuekey=queuekey, correctness='incomplete', msg=msg)

        return cmap

    def update_score(self, score_msg, oldcmap, queuekey):

        (valid_score_msg, correct, points, msg) = self._parse_score_msg(score_msg) 
        if not valid_score_msg:
            oldcmap.set(self.answer_id, msg='Error: Invalid grader reply.')
            return oldcmap
        
        correctness = 'correct' if correct else 'incorrect'

        self.context['correct'] = correctness # TODO: Find out how this is used elsewhere, if any

        # Replace 'oldcmap' with new grading results if queuekey matches.
        #   If queuekey does not match, we keep waiting for the score_msg whose key actually matches
        if oldcmap.is_right_queuekey(self.answer_id, queuekey):
            # Sanity check on returned points 
            if points < 0:
                points = 0
            elif points > self.maxpoints[self.answer_id]:
                points = self.maxpoints[self.answer_id]
            oldcmap.set(self.answer_id, npoints=points, correctness=correctness, msg=msg.replace('&nbsp;', '&#160;'), queuekey=None)  # Queuekey is consumed
        else:
            log.debug('CodeResponse: queuekey %s does not match for answer_id=%s.' % (queuekey, self.answer_id))

        return oldcmap

    def get_answers(self):
        anshtml = '<font color="blue"><span class="code-answer"><br/><pre>%s</pre><br/></span></font>' % self.answer
        return {self.answer_id: anshtml}

    def get_initial_display(self):
        return {self.answer_id: self.initial_display}

    def _parse_score_msg(self, score_msg):
        '''
         Grader reply is a JSON-dump of the following dict
           { 'correct': True/False,
             'score': # TODO -- Partial grading
             'msg': grader_msg }

        Returns (valid_score_msg, correct, score, msg):
            valid_score_msg: Flag indicating valid score_msg format (Boolean)
            correct:         Correctness of submission (Boolean)
            score:           # TODO: Implement partial grading
            msg:             Message from grader to display to student (string)
        '''
        fail = (False, False, -1, '')
        try:
            score_result = json.loads(score_msg)
        except (TypeError, ValueError):
            return fail
        if not isinstance(score_result, dict):
            return fail
        for tag in ['correct', 'score', 'msg']:
            if not score_result.has_key(tag):
                return fail
        return (True, score_result['correct'], score_result['score'], score_result['msg'])
        
