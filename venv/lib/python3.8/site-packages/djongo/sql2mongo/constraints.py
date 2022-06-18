from djongo.exceptions import NotSupportedError
from djongo import djongo_access_url

print(f'This version of djongo does not support constraints. Visit {djongo_access_url}')
raise NotSupportedError('constraints')
