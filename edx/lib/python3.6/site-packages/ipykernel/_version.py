version_info = (5, 1, 0)
__version__ = '.'.join(map(str, version_info[:3]))

# pep440 is annoying, beta/alpha/rc should _not_ have dots or pip/setuptools
# confuses which one between the wheel and sdist is the most recent.
if len(version_info) == 4:
    extra = version_info[3]
    if extra.startswith(('a','b','rc')):
        __version__ = __version__+extra
    else:
        __version__ = __version__+'.'+extra
if len(version_info) > 4:
    raise NotImplementedError

kernel_protocol_version_info = (5, 1)
kernel_protocol_version = '%s.%s' % kernel_protocol_version_info
