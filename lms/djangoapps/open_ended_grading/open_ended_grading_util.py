def convert_seconds_to_human_readable(seconds):
    if seconds < 60:
        human_string = "{0} seconds".format(seconds)
    elif seconds < 60 * 60:
        human_string = "{0} minutes".format(round(seconds/60,1))
    elif seconds < (24*60*60):
        human_string = "{0} hours".format(round(seconds/(60*60),1))
    else:
        human_string = "{0} days".format(round(seconds/(60*60*24),1))

    eta_string = "In {0}.".format(human_string)
    return eta_string