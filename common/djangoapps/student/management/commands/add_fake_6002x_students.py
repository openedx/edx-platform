# creates users named johndoen with emails of jdn@edx.org
# they are enrolled in 600x and have fake grades with

from optparse import make_option
import json
import random
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment
from courseware.models import StudentModule


class Command(BaseCommand):

    args = '<>'
    help = """
    Add fake students and grades to db.
    """

    # option_list = BaseCommand.option_list + (
    #     make_option('--course_id',
    #                 action='store',
    #                 dest='course_id',
    #                 help='Specify a particular course.'),
    #     make_option('--exam_series_code',
    #                 action='store',
    #                 dest='exam_series_code',
    #                 default=None,
    #                 help='Specify a particular exam, using the Pearson code'),
    #     make_option('--accommodation_pending',
    #                 action='store_true',
    #                 dest='accommodation_pending',
    #                 default=False,
    #                 ),
    # )

    @transaction.autocommit
    def _create_jd(self, seed_num):
        print (20 * "\n") + ("creating johndoe%s" % seed_num) + (20 * "\n")

        course_id = 'MITx/6.002x/2013_Spring'
        email = 'jd%s@edx.org' % seed_num
        password = '1234'

        user = User(username='johndoe%s' % seed_num, email=email, password=password)
        user.save()

        def get_year_of_birth():
            if random.random() > 0.9:
                return None
            else:
                return random.triangular(UserProfile.this_year - 100, UserProfile.this_year, UserProfile.this_year - 22)

        profile = UserProfile(user=User.objects.filter(email=email)[0], name='John Doe %s' % seed_num)
        profile.language = random.choice(["English", "English", "English", "English", "English", "English", "English", "English", "English", "French", "french", "Esperanto"])
        profile.year_of_birth = get_year_of_birth()
        # TODO why don't gender and level_of_educationin fail validation when switched to invalids?
        profile.gender = random.choice([(None, None)] + list(profile.GENDER_CHOICES))[0]
        profile.level_of_education = random.choice([(None, None)] + list(profile.LEVEL_OF_EDUCATION_CHOICES))[0]
        profile.goals = random.choice([None, "Learn EE", "Conquer the world", "Find myself", "Explore the possiblity of becoming a well-rounded college application."])
        profile.mailing_address = random.choice([None, "159 Hubler, Dr", "Ye ol' hunton", "44 poplar", "603 Small Apt., 02341"])
        profile.save()

        enrollment = CourseEnrollment(user=user, course_id=course_id)
        enrollment.save()

        for state_key in MODULE_STATE_KEYS:
            # WARN: state and grade/max_grade are completely made up
            smod = StudentModule(
                module_type='problem',
                module_state_key=state_key,
                student=user,
                course_id=course_id,
                state={},
                grade=random.choice(range(100+1)),
                max_grade=100,
                done='na')
            smod.save()

    def _create_n_jds(self, number_to_add):
        print "adding fake users"

        seed_num = 1
        while number_to_add > 0:
            if len(User.objects.filter(username='johndoe%s' % seed_num)) > 0:
                seed_num += 1
            else:
                self._create_jd(seed_num)
                number_to_add -= 1

    def _delete_all_jds(self):
        [student.delete() for student in User.objects.filter(username__contains="johndoe")]

    def handle(self, *args, **options):
        new_jds = int(args[0])

        if 'delete' in args:
            self._delete_all_jds()

        if 'nocreate' in args:
            pass
        else:
            self._create_n_jds(new_jds)


# set([sm.module_state_key for sm in SM.objects.filter(module_type='problem')])
MODULE_STATE_KEYS = set([
    u'i4x://MITx/6.002x/problem/S14E4_Fall_Time',
    u'i4x://MITx/6.002x/problem/S20E3_LCR_voltage_divider',
    u'i4x://MITx/6.002x/problem/First-order_Transients',
    u'i4x://MITx/6.002x/problem/H5P2_Source_Follower_Large_Signal',
    u'i4x://MITx/6.002x/problem/S3E3_Circuit_Variables_are_Superpositions_of_values_due_to_each_source_separately',
    u'i4x://MITx/6.002x/problem/S2E1_Circuit_Topology',
    u'i4x://MITx/6.002x/problem/Resonance',
    u'i4x://MITx/6.002x/problem/S5E2_Switch_Model',
    u'i4x://MITx/6.002x/problem/S11E1_Small-Signal_MOSFET_Model',
    u'i4x://MITx/6.002x/problem/S8E0_Dependent_Source',
    u'i4x://MITx/6.002x/problem/H2P3_Logic_Circuits',
    u'i4x://MITx/6.002x/problem/Second-order_Circuits',
    u'i4x://MITx/6.002x/problem/S12E4_First-Order_Capacitor_Examples',
    u'i4x://MITx/6.002x/problem/S14E1_Response_to_step_down',
    u'i4x://MITx/6.002x/problem/H10P3_An_L_Network',
    u'i4x://MITx/6.002x/problem/S17E1_Particular_Solution',
    u'i4x://MITx/6.002x/problem/S7E2_Graphs',
    u'i4x://MITx/6.002x/problem/H11P2_Scope_Probe',
    u'i4x://MITx/6.002x/problem/S12E5_Neon_Relaxation_Oscillator',
    u'i4x://MITx/6.002x/problem/S16E1_Charging_and_Discharging',
    u'i4x://MITx/6.002x/problem/H9P1_Response_to_a_Delayed_Impulse',
    u'i4x://MITx/6.002x/problem/S1E1_Various_V-I_characteristics',
    u'i4x://MITx/6.002x/problem/Impedance_Frequency_Response',
    u'i4x://MITx/6.002x/problem/S13E4_First-Order_Inductor_Examples',
    u'i4x://MITx/6.002x/problem/S10E2_two_terminal_connection',
    u'i4x://MITx/6.002x/problem/Propagation_Delay',
    u'i4x://MITx/6.002x/problem/H2P2_Solar_Power',
    u'i4x://MITx/6.002x/problem/H3P4_Diode_Limiter',
    u'i4x://MITx/6.002x/problem/S7E1_Linearization',
    u'i4x://MITx/6.002x/problem/S18E2_Homogenous_Equation_Solution',
    u'i4x://MITx/6.002x/problem/S2E2_Associated_Reference_Directions',
    u'i4x://MITx/6.002x/problem/S22E1_Which_output_',
    u'i4x://MITx/6.002x/problem/H12P1_Current_Source',
    u'i4x://MITx/6.002x/problem/S6E0_Thevenin_isolates_nonlinear_element',
    u'i4x://MITx/6.002x/problem/S24E4_Generalization_to_impedances',
    u'i4x://MITx/6.002x/problem/S16E2_Time_to_Decay',
    u'i4x://MITx/6.002x/problem/S1E2_Power_copy',
    u'i4x://MITx/6.002x/problem/Curve_Tracer',
    u'i4x://MITx/6.002x/problem/H9P3_Designing_a_Shock_Absorber',
    u'i4x://MITx/6.002x/problem/H4P2_Zener_Regulator',
    u'i4x://MITx/6.002x/problem/S1E1.5_Simple_Power',
    u'i4x://MITx/6.002x/problem/S26E1_Power_and_Energy_Review',
    u'i4x://MITx/6.002x/problem/S6E3_Piecewise_Linear',
    u'i4x://MITx/6.002x/problem/S1E6_KVL',
    u'i4x://MITx/6.002x/problem/S15E5_Initial_Conditions',
    u'i4x://MITx/6.002x/problem/Capacitors_and_Energy_Storage',
    u'i4x://MITx/6.002x/problem/H3P3_Solar_Cell',
    u'i4x://MITx/6.002x/problem/H11P1_LC_Tank',
    u'i4x://MITx/6.002x/problem/Logic_Gate_Implementation',
    u'i4x://MITx/6.002x/problem/S14E2_Rise_Time',
    u'i4x://MITx/6.002x/problem/S12E3_Norton_Capacitor_Circuit',
    u'i4x://MITx/6.002x/problem/S4E2_Boolean_Functions',
    u'i4x://MITx/6.002x/problem/H10P2_New_Impedances',
    u'i4x://MITx/6.002x/problem/S24E1_Summing_Amplifier',
    u'i4x://MITx/6.002x/problem/S9E1_MOSFET_model',
    u'i4x://MITx/6.002x/problem/S17E4_An_LC_circuit',
    u'i4x://MITx/6.002x/problem/S2E6_Modeling',
    u'i4x://MITx/6.002x/problem/S12E1_Scaling_Capacitors',
    u'i4x://MITx/6.002x/problem/H8P1_Impulse',
    u'i4x://MITx/6.002x/problem/S1E5_KVL-0',
    u'i4x://MITx/6.002x/problem/S9E3_MOSFET_Amplifier_2',
    u'i4x://MITx/6.002x/problem/S23E2_Inverting_Amplifier_analysis',
    u'i4x://MITx/6.002x/problem/S3E4_Simple_Thevenin',
    u'i4x://MITx/6.002x/problem/Q6Final2012',
    u'i4x://MITx/6.002x/problem/S15E1_Review_A_Step_Up',
    u'i4x://MITx/6.002x/problem/S17E3_Matching_Initial_Conditions',
    u'i4x://MITx/6.002x/problem/H1P2_KCL-KVL_vs_Node_Method',
    u'i4x://MITx/6.002x/problem/Lab_0_Using_the_Tools',
    u'i4x://MITx/6.002x/problem/S21E3_Thevenin_Tank',
    u'i4x://MITx/6.002x/problem/S14E3_Fall_Time_Constant',
    u'i4x://MITx/6.002x/problem/Q2Final2012',
    u'i4x://MITx/6.002x/problem/ex_practice_limited_checks',
    u'i4x://MITx/6.002x/problem/H7P2_Time_Constants',
    u'i4x://MITx/6.002x/problem/S15E3_Review_A_Pulse_is_Step_Up_then_Step_Down',
    u'i4x://MITx/6.002x/problem/S1E2_Power',
    u'i4x://MITx/6.002x/problem/S19E4_Magnitudes_and_Angles',
    u'i4x://MITx/6.002x/problem/S19E1_Trigonometry_Isn_t_So_Bad',
    u'i4x://MITx/6.002x/problem/S2E5_Node_Method',
    u'i4x://MITx/6.002x/problem/S13E1_Scaling_Inductors',
    u'i4x://MITx/6.002x/problem/ex_practice_limited_checks_3',
    u'i4x://MITx/6.002x/problem/S3E6_Norton_Model',
    u'i4x://MITx/6.002x/problem/MTQ6',
    u'i4x://MITx/6.002x/problem/H12P2_Linear_Regulator',
    u'i4x://MITx/6.002x/problem/S1E8_KCL',
    u'i4x://MITx/6.002x/problem/Sample_Algebraic_Problem',
    u'i4x://MITx/6.002x/problem/S26E2_Energy_Sourced_in_T1',
    u'i4x://MITx/6.002x/problem/S13E3_Thevenin_Inductor_Circuit',
    u'i4x://MITx/6.002x/problem/H6P2_Phase_Inverter',
    u'i4x://MITx/6.002x/problem/H7P1_Series_and_Parallel_Inductors',
    u'i4x://MITx/6.002x/problem/S6E2_Load_Line',
    u'i4x://MITx/6.002x/problem/H11P3_Branch_Voltages',
    u'i4x://MITx/6.002x/problem/S20E1_Inductor_Impedance',
    u'i4x://MITx/6.002x/problem/S15E4_Area',
    u'i4x://MITx/6.002x/problem/S12E2_Capacitors_Store_Energy',
    u'i4x://MITx/6.002x/problem/Sample_Numeric_Problem',
    u'i4x://MITx/6.002x/problem/S21E2_LR_filter',
    u'i4x://MITx/6.002x/problem/H5P3_Source_Follower_Small_Signal',
    u'i4x://MITx/6.002x/problem/S18E1_Particular_Solution',
    u'i4x://MITx/6.002x/problem/L2Node0',
    u'i4x://MITx/6.002x/problem/L2Node1',
    u'i4x://MITx/6.002x/problem/L2Node2',
    u'i4x://MITx/6.002x/problem/S1E9_Battery_Model',
    u'i4x://MITx/6.002x/problem/S25E2_Relaxation_Oscillator_Frequency',
    u'i4x://MITx/6.002x/problem/MTQ3',
    u'i4x://MITx/6.002x/problem/MTQ2',
    u'i4x://MITx/6.002x/problem/MTQ1',
    u'i4x://MITx/6.002x/problem/H6P3_Series_and_Parallel_Capacitors',
    u'i4x://MITx/6.002x/problem/MTQ5',
    u'i4x://MITx/6.002x/problem/MTQ4',
    u'i4x://MITx/6.002x/problem/S10E3_Small_Signal_Amplifier',
    u'i4x://MITx/6.002x/problem/H10P1_Magnitude_and_Angle',
    u'i4x://MITx/6.002x/problem/Q5Final2012',
    u'i4x://MITx/6.002x/problem/Resistor_Divider',
    u'i4x://MITx/6.002x/problem/H5P1_Zero-Offset_Amplifier',
    u'i4x://MITx/6.002x/problem/Lab2b_Mixing_Two_Signals',
    u'i4x://MITx/6.002x/problem/H2P1_Voltage-Divider_Design',
    u'i4x://MITx/6.002x/problem/S17E5_An_ILC_circuit',
    u'i4x://MITx/6.002x/problem/S24E3_Inverting_Amplifier_Generalized',
    u'i4x://MITx/6.002x/problem/S19E3_Complex_Numbers',
    u'i4x://MITx/6.002x/problem/H1P3_Poor_Workmanship',
    u'i4x://MITx/6.002x/problem/S1E3_AC_power',
    u'i4x://MITx/6.002x/problem/S9E2_Amplifier_1',
    u'i4x://MITx/6.002x/problem/S2E4_Series_and_Parallel',
    u'i4x://MITx/6.002x/problem/S8E2_Dependent_Voltage_Source',
    u'i4x://MITx/6.002x/problem/S11E2_Small-Signal_Model_of_Diode-Connected_MOSFET',
    u'i4x://MITx/6.002x/problem/H3P1_A_Logic_Family',
    u'i4x://MITx/6.002x/problem/S3E1_Node_Equation_Review',
    u'i4x://MITx/6.002x/problem/H12P3_Opamps_and_Filter_Design',
    u'i4x://MITx/6.002x/problem/H4P1_Vacuum_Diode',
    u'i4x://MITx/6.002x/problem/Q4Final2012',
    u'i4x://MITx/6.002x/problem/S24E2_Difference_Amplifier',
    u'i4x://MITx/6.002x/problem/H9P2_SOC',
    u'i4x://MITx/6.002x/problem/S5E1_Logic_with_Switches',
    u'i4x://MITx/6.002x/problem/S23E3_L23AmplifierInputResistance',
    u'i4x://MITx/6.002x/problem/S25E1_Positive_Feedback_Gain',
    u'i4x://MITx/6.002x/problem/Circuit_Sandbox',
    u'i4x://MITx/6.002x/problem/S3E2_Circuit_Voltages_and_Currents_are_Linear_Combinations_of_Source_Strengths',
    u'i4x://MITx/6.002x/problem/S5E3_SR_Model',
    u'i4x://MITx/6.002x/problem/S11E3_Source_Follower_Again_',
    u'i4x://MITx/6.002x/problem/S21E4_AM_Radio_Tuning',
    u'i4x://MITx/6.002x/problem/Mosfet_Amplifier',
    u'i4x://MITx/6.002x/problem/H4P3_Dependent_Source_Circuit',
    u'i4x://MITx/6.002x/problem/Q1Final2012',
    u'i4x://MITx/6.002x/problem/S20E2_RC_voltage_divider',
    u'i4x://MITx/6.002x/problem/S1E7_KCL-0',
    u'i4x://MITx/6.002x/problem/H8P2_Physiological_Model',
    u'i4x://MITx/6.002x/problem/H8P3_Memory',
    u'i4x://MITx/6.002x/problem/ex_practice_2',
    u'i4x://MITx/6.002x/problem/ex_practice_3',
    u'i4x://MITx/6.002x/problem/H6P1_The_NewFET_device',
    u'i4x://MITx/6.002x/problem/S8E1_Dependent_Current_Source',
    u'i4x://MITx/6.002x/problem/S18E3_Total_Solution',
    u'i4x://MITx/6.002x/problem/H3P2_Graphical_Model_of_Inverter',
    u'i4x://MITx/6.002x/problem/S23E1_Non-Inverting_Amplifier',
    u'i4x://MITx/6.002x/problem/S22E2_The_filter_is_ringing',
    u'i4x://MITx/6.002x/problem/S21E1_Second-order_impedance',
    u'i4x://MITx/6.002x/problem/S20E4_LCR_voltage_divider_frequency_limits',
    u'i4x://MITx/6.002x/problem/S15E2_Review_A_Step_Down',
    u'i4x://MITx/6.002x/problem/S3E5_Thevenin_Model',
    u'i4x://MITx/6.002x/problem/S4E3_Truth_Table',
    u'i4x://MITx/6.002x/problem/S7E3_Linearization',
    u'i4x://MITx/6.002x/problem/S2E3_Using_KVL_KCL_and_VI_constraints',
    u'i4x://MITx/6.002x/problem/H7P3_The_Curse_of_Lead_Inductance',
    u'i4x://MITx/6.002x/problem/S13E2_Inductors_Store_Energy',
    u'i4x://MITx/6.002x/problem/S26E3_A_Hot_Processor',
    u'i4x://MITx/6.002x/problem/S1E1.5_Simple_Power_copy',
    u'i4x://MITx/6.002x/problem/S6E1_A_Nonlinear_Element',
    u'i4x://MITx/6.002x/problem/S19E2_Exponentials_are_Nice',
    u'i4x://MITx/6.002x/problem/S10E1_Incremental_Voltage',
    u'i4x://MITx/6.002x/problem/Op_Amps',
    u'i4x://MITx/6.002x/problem/S24E5_Generalization_to_nonlinear_elements',
    u'i4x://MITx/6.002x/problem/Q3Final2012',
    u'i4x://MITx/6.002x/problem/S17E2_Characteristic_Equation',
    u'i4x://MITx/6.002x/problem/H1P1_Resistor_Combinations',
    u'i4x://MITx/6.002x/problem/S1E1_Various_V-I_characteristics_copy'])

