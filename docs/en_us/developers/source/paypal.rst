1. Create a new paypal app: https://developer.paypal.com/webapps/developer/applications/myapps
Optional: If you are testing, create a sandbox account: https://developer.paypal.com/webapps/developer/applications/accounts
2. Edit edx-platform/lms/envs/common.py and add your paypal details to CC_PROCESSOR:

Here are some example test settings:

    CC_PROCESSOR = {
        'Paypal': {
            'mode': 'sandbox',
            'client_id': 'AQkquBDf1zctJOWGKWUEtKXm6qVhueUEMvXO_-MCI4DQQ4-LWvkDLIN2fGsd',
            'client_secret': 'EL1tVxAjhT7cJimnz5-Nsx9k2reTKSVfErNQF-CmrwJgxRtylkGTKlU4RvrX'
        }
    }
3. Enable paid courses: https://github.com/edx/edx-platform/wiki/Paid-Certificates


You're done!
