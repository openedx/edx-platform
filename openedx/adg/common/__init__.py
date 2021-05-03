"""
This package contains all the ADG apps which are required in both lms and cms. These apps are registered in
both lms and cms. Their unit tests will run twice, once with django settings for lms and once for cms
i.e. --ds=lms.envs.test & --ds=cms.envs.test. skip_unless_lms and skip_unless_cms annotations can be used
to skip any particular test for lms or cms respectively.
"""
