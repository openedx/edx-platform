from django import forms


# Autocomplete is not working
class TellUsMoreForm(forms.Form):

    EDUCATION_CHOICE = [
        (1, "Doctoral or professional degree"),
        (2, "Master's degree"),
        (3, "Bachelor's degree"),
        (4, "Associate's degree"),
        (5, "Postsecondary nondegree award"),
        (6, "Some college, no degree"),
        (7, "High school diploma or equivalent"),
        (8, "No formal educational credential"),
    ]

    ENGLISH_PROFICIENCY_CHOICE = [
        (1, "No proficiency"),
        (2, "Elementary proficiency"),
        (3, "Limited working proficiency"),
        (4, "Professional working proficiency"),
        (5, "Full professional proficiency"),
        (6, "Native or bilingual proficiency"),
        (7, "High school diploma or equivalent"),
        (8, "No formal educational credential"),
    ]

    birth_date = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Date of Birth'}))

    level_of_education = forms.ChoiceField(
        choices=[(0, "Level of Education")] + EDUCATION_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    native_language = forms.CharField(max_length=25)

    english_language_proficiency = forms.ChoiceField(
        choices=[(0, "English Language Proficiency")] + ENGLISH_PROFICIENCY_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    country = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Country of Residence'}), required=True)
    city = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'City of Residence'}), required=True)
    is_city_or_country_of_employment_diff = forms.BooleanField(
        label='My country or city of employment is different than my country or city of residence.',
        widget=forms.CheckboxInput(),
        required=False
    )

    country_of_employment = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Country of Employment'}), required=False
    )
    city_of_employment = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'City of Employment'}), required=False
    )

# Complete
class InterestForm(forms.Form):
    ORG_CAPACITY_AREA_CHOICE = (
        ("1", "Leadership"),
        ("2", "Finance"),
        ("3", "Programs"),
        ("4", "Administration"),
        ("5", "External Relations"),
        ("6", "Logistics")
    )

    COMMUNITY_TYPES_CHOICE = (
        ("1", "Contribute to my organization's capacity."),
        ("2", "Improve my job prospects.."),
        ("3", "Develop my leadership abilities."),
        ("4", "Build relationship with other nonprofit practitioners."),
        ("5", "Gain new skills.")
    )

    PERSONAL_GOALS_CHOICE = (
        ("1", "A community of learners from my region or country."),
        ("2", "A community of learners interested in the same organizational capacity areas."),
        ("3", "A community learners working for similar organizations."),
    )

    ADD_TO_COMMUNITY_OPTIONS = (
        ("1", "Yes"),
        ("2", "No"),
        ("3", "Ask me later"),
    )

    organizational_capacity_areas = forms.MultipleChoiceField(
        label='Which of these organizational capacity areas are interested to you? (Check all that apply)',
        widget=forms.CheckboxSelectMultiple, choices=ORG_CAPACITY_AREA_CHOICE
    )
    community_types = forms.MultipleChoiceField(
        label='Which of these community types are interested to you? (Check all that apply)',
        widget=forms.CheckboxSelectMultiple, choices=COMMUNITY_TYPES_CHOICE
    )
    permission_to_add_to_communities = forms.ChoiceField(
        label="Would you be automatically added to these kind of communities,"
              " based on the information you provided in your profile.",
        choices=ADD_TO_COMMUNITY_OPTIONS,
        widget=forms.RadioSelect(),
    )

    personal_goals = forms.MultipleChoiceField(
        label='Which is your most important personal goal in using the Philanthropy University platform.',
        widget=forms.CheckboxSelectMultiple, choices=PERSONAL_GOALS_CHOICE
    )


class OrganizationInfoForm(forms.Form):
    ROLE_IN_ORG_CHOICE = [
        (1, "Volunteer"),
        (2, "Entry level"),
        (3, "Associate"),
        (4, "Internship"),
        (5, "Mid-Senior level"),
        (6, "Director"),
        (7, "Executive"),
    ]

    SECTOR_CHOICE = [
        (1, "Academic Institution"),
        (2, "For-Profit Company"),
        (3, "Government Agency"),
        (4, "Grantmaking Foundation"),
        (5, "Non-Profit Organization"),
        (6, "Self-Employed"),
        (7, "Social Enterprise"),
        (8, "Student"),
        (9, "Unemployed"),
        (10, "Other")
    ]

    LEVEL_OF_OPR_CHOICE = [
        (1, "International"),
        (2, "Regional including multiple countries"),
        (3, "National"),
        (4, "Regional including multiple localities within one country"),
        (5, "Local")
    ]

    FOCUS_AREA_CHOICE = [
        (1, "Arts, Culture, Humanities"),
        (2, "Community Development"),
        (3, "Education"),
        (4, "Environment"),
        (5, "Health"),
        (6, "Human and Civil Rights"),
        (7, "Human Services"),
        (8, "International"),
        (9, "Religion"),
        (10, "Research and Public Policy"),
    ]

    TOTAL_EMPLOYEE_AND_VOLUNTEER_CHOICE = [
        (1, "1-10"),
        (2, "11-50"),
        (3, "51-100"),
        (4, "101-500"),
        (5, "501-1,000"),
        (6, "1,000+"),
        (7, "Not applicable")
    ]

    PARTNER_NETWORK_CHOICE = [
        (1, "Mercy Corps"),
        (2, "FHI 360 / FHI Foundation"),
        (3, "+Acumen")
    ]

    role_in_org = forms.ChoiceField(
        choices=[(0, 'Role in the Organization')] + ROLE_IN_ORG_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    start_month_and_year = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Start Month and Year'}))

    country = forms.CharField(max_length=25, label='Country of Organization Headquarters')

    city = forms.CharField(max_length=25)

    organization_website = forms.URLField(
        label='Organization Website', required=True, widget=forms.URLInput(
            attrs={
                'placeholder': 'Organization Website'
            }
        )
    )

    sector = forms.ChoiceField(
        choices=[(0, 'Sector')] + SECTOR_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    level_of_operation = forms.ChoiceField(
        choices=[(0, 'Level of Operation')] + LEVEL_OF_OPR_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    focus_area = forms.ChoiceField(
        choices=[(0, 'Focus Area')] + FOCUS_AREA_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    founding_year = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Founding year'}))

    total_employees = forms.ChoiceField(
        choices=[(0, 'Total Employees')] + TOTAL_EMPLOYEE_AND_VOLUNTEER_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    total_volunteers = forms.ChoiceField(
        choices=[(0, 'Total Volunteers')] + TOTAL_EMPLOYEE_AND_VOLUNTEER_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )

    total_annual_clients_or_beneficiaries = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Total annual clients or beneficiaries'})
    )

    total_annual_revenue_for_last_fiscal_year = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Total annual revenue for last fiscal year '})
    )

    partner_network = forms.ChoiceField(
        choices=[(0, 'Partner Networks')] + PARTNER_NETWORK_CHOICE,
        initial='',
        widget=forms.Select(),
        required=True
    )



