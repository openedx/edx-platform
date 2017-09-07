
with open("/Users/muddasserhussain/Documents/ficus_master/edx-platform/lms/djangoapps/onboarding_survey/data/world_countries.txt", encoding="utf-8") as file:
    languages = file.readlines()
    cleaned_list = [language.rstrip("\n") for language in languages ]

    with open("/Users/muddasserhussain/Documents/ficus_master/edx-platform/lms/djangoapps/onboarding_survey/data/world_countries.json", 'w') as outfile:
            import json
            json.dump(cleaned_list[1:-1], outfile)
    from pdb import set_trace; set_trace()
