"""# Generate a sorted list of unique language names from pycountry """
import pycountry

LANGUAGE_CHOICES = sorted({lang.name for lang in pycountry.languages if hasattr(lang, 'alpha_2')})
