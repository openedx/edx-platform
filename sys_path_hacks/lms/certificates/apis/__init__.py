import warnings
warnings.warn("Importing certificates.apis instead of lms.djangoapps.certificates.apis is deprecated", stacklevel=2)

from lms.djangoapps.certificates.apis import *
