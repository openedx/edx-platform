# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0009_auto_20180131_0938'),
    ]

    def insert_instructions(apps, schema_editor):
        instructions = [
            {
                'question_index': 1,
                'question': "What is the Organizational Effectiveness Framework?",
                'answer': """<p>The Organizational Effectiveness Framework (OEF) describes the 10 areas of
                                        organizational
                                        effectiveness, or organizational capacity, which Philanthropy University
                                        believes are essential
                                        to a nonprofit’s success.</p>

                                    <div class="table-wrapper">
                                        <table class="oef-subcategory-table" cellspacing="0" cellpadding="0">
                                            <tbody>
                                            <tr>
                                                <td>
                                                    <h4>Leadership & Governance</h4>
                                                </td>
                                                <td>
                                                    <h4>Program Design & Delivery</h4>
                                                </td>
                                                <td>
                                                    <h4>External Relations and partnerships</h4>
                                                </td>
                                                <td>
                                                    <h4>Financial Management</h4>
                                                </td>
                                                <td>
                                                    <h4>Marketing, Communications & PR</h4>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <h4>Strategy & Planning</h4>
                                                </td>
                                                <td>
                                                    <h4>Measurement, evaluation, and learning</h4>
                                                </td>
                                                <td>

                                                    <h4>Human Resource Management</h4>
                                                </td>
                                                <td>
                                                    <h4>Fundraising & Resource Mobilization</h4>
                                                </td>
                                                <td>
                                                    <h4>Systems, processes, and tools</h4>
                                                </td>

                                            </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                    <p>The OEF is a tool that your organization can use to rate the current state of
                                        your organization’s capacity under each of the 10 areas above.</p>
                                    <p>The OEF describes what an organization looks like in each of these areas as it
                                        develops capacity - a ‘pathway’ to organizational effectiveness.</p>"""
            },{
                'question_index': 2,
                'question': "Do I have to complete it?",
                'answer': """<p>You are not required to complete the OEF in order to access the full course and
                                        community experience on Philanthropy University, but there are a few reasons
                                        that you should!</p>"""
            },{
                'question_index': 3,
                'question': "Why should I complete the OEF for my organization?",
                'answer': """<p>There are four key reasons to complete the OEF:</p>
                                    <ul>
                                        <li>To improve your understanding of your organization’s strengths and areas for
                                            development, and to use this information to make decisions on where to
                                            invest resources in developing capacity.
                                        </li>
                                        <li>To enable Philanthropy University to make recommendations to you and your
                                            organization on Philanthropy University courses and communities you might
                                            like
                                        </li>
                                        <li>To provide you and your organization’s leadership and Board with a view of
                                            changes in your organizational capacity through time.
                                        </li>
                                        <li>To enable Philanthropy University to use data gathered through the tool to
                                            understand how it can serve your organization and other organizations like
                                            yours better.
                                        </li>
                                    </ul>
                                    <p>In order to see how your organization’s capacity changes through time, it is
                                        important that you complete a new OEF each year, even if your organization is no
                                        longer using the Philanthropy University platform.</p>"""
            },{
                'question_index': 4,
                'question': "How is the OEF different from other capacity assessments?",
                'answer': """<p>Your organization may have already assessed its capacity using other tools.</p>
                                    <p>There are three key ways in which the OEF is different from other capacity
                                        assessments:</p>
                                    <ul>
                                        <li>The OEF was designed to be completed by one person with a good understanding
                                            of the organization’s functions and operations.
                                        </li>
                                        <li>The OEF should take less time to complete.</li>
                                        <li>The OEF does not produce a comprehensive capacity development plan.</li>
                                    </ul>
                                    <p>Participatory, in-person capacity assessments are valuable exercises. The OEF
                                        should complement but not replace this more intensive assessment. For example,
                                        you could use your OEF ratings to inform where you focus a more in-depth
                                        capacity assessment process. Similarly, you could use the results of other
                                        capacity assessments your organization has undertaken to inform your OEF
                                        ratings.</p>"""
            },{
                'question_index': 5,
                'question': "Who should complete it?",
                'answer': """<p>The OEF was designed to be completed by one person with a good understanding of
                                        your organization’s functions and operations. This will likely be the same
                                        person as your organization's "Administrator" on Philanthropy University. Your
                                        Administrator should be the most senior person in your organization responsible
                                        for organizational capacity building and learning. In a small organization with
                                        few employees, the Organization Administrator might be the Executive Director or
                                        Chief Executive. In a larger organization, the Organization Administrator might
                                        be the director or manager responsible for staff learning and development and
                                        organizational capacity assessment and development planning.</p>
                                    <p>Your Administrator may be able to provide ratings for most areas without seeking
                                        advice from others, or s/he may need the help of, for example, your
                                        organization’s leadership team on ratings in the Leadership and governance area
                                        or with your organization's’ Development Director on ratings in the Fundraising
                                        and resource mobilization area.</p>"""
            },{
                'question_index': 6,
                'question': "How do I complete the OEF?",
                'answer': """<p>The OEF describes what an organization looks like across the 10 areas of
                                        organizational effectiveness based on four levels of capacity:</p>
                                    <ul>
                                        <li>1. Limited capacity</li>
                                        <li>2. Developing capacity</li>
                                        <li>3. Good capacity</li>
                                        <li>4. High capacity</li>
                                    </ul>
                                    <p>You will provide a rating of between 1 and 4 for each of the 10 areas of
                                        organizational effectiveness by clicking on the box for each area which best
                                        describes the current state of your organization’s capacity for that area. If
                                        you think that your organization’s capacity in any area falls between two
                                        levels, you can select an in-between <span class="circle-text-icon">+/-</span> rating.</p>
                                    <p>You do not need to remember all of these instructions - you will find more
                                        instructions on the tool itself.</p>"""
            },{
                'question_index': 7,
                'question': "How well should I expect my organization to rate on the OEF?",
                'answer': """<p>Most organizations won’t rate as 3s or 4s in all areas in their first OEF. Some
                                        organizations may never rate as 4s in some areas because these areas aren’t as
                                        important to their success. Your organization might want to focus on certain
                                        areas first and develop capacity in those areas before focusing in other
                                        areas.</p>
                                    <p>t is OK for your first OEF ratings to be 1s and 2s. You should use your first OEF
                                        ratings to inform investments of resources in your organization’s capacity and
                                        then focus on how your ratings change through time. Remember that while capacity
                                        improvement is a slow and challenging process, it is incredibly valuable to your
                                        organization's success</p>
                                    <p>In order for your OEF ratings to inform your capacity development work, it is
                                        important that you are honest when assessing your organization’s capacity in
                                        each area - make sure you select the rating that best describes your
                                        organization’s current capacity, rather than the rating that you would like to
                                        achieve in the future.</p>"""
            },{
                'question_index': 8,
                'question': "How long does it take to complete the OEF?",
                'answer': """<p>A person with a good understanding of your organization’s functions and
                                        operations should be able to complete the OEF in 10 to 30 minutes.</p>
                                    <p>You can start the OEF, complete part of it, save it as a draft, and return to
                                        complete it when you have time. There is no deadline for completion.</p>"""
            },{
                'question_index': 9,
                'question': "What if I don’t know how to rate my organization in one or a number of areas?",
                'answer': """<p>You may not know how to rate your organization in some areas and you may want to
                                        talk with your colleagues or your leadership team in order to decide the most
                                        appropriate rating. This may take more time, but will be important in improving
                                        the accuracy of your ratings.</p>"""
            },{
                'question_index': 10,
                'question': "What happens after I complete it?",
                'answer': """<p>After you submit the OEF, you will be able to access it from your organization’s
                                        Dashboard. You will not be able to change a submitted OEF - instead, you can
                                        submit a new OEF once every six months. We will store all your organization’s
                                        past OEFs in your Dashboard, so that you can see how they have changed over
                                        time.</p>
                                    <p>We will contact you one year after you submitted your first OEF to ask you to
                                        return to Philanthropy University and submit a new OEF that shows the changes
                                        your organization has made during the year. We hope that you are able to return
                                        once per year to complete a new OEF, even if you are no longer using
                                        Philanthropy University.</p>"""
            },{
                'question_index': 11,
                'question': "What happens after I complete it?",
                'answer': """<p>A person with good working knowledge of the organization's functions and
                                        operations should be able to complete the OEF
                                        in 10 to 30 minutes. You can start the OEF, complete part of it, save it as a
                                        draft, and return to complete it when you
                                        have time. There is no deadline for completion.</p>"""
            },
        ]
        instruction = apps.get_model('oef', 'Instruction')
        lst = []
        for i in instructions:
            lst.append(instruction(question_index=i['question_index'], question=i['question'], answer=i['answer']))

        instruction.objects.bulk_create(lst)

    operations = [
        migrations.RunPython(insert_instructions),
    ]
