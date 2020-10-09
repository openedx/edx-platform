""" Overrides for Docker-based devstack. """

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import
# QINIU_ACCESS_KEY = 'r2KnFulbIQtuq2cyV-6SSLl-Go_36AyImgyg4cae'
# QINIU_SECRET_KEY = '0pZvH505UqqkE8IQVaDpZKJcx0wMUqEMWRvVu3TS'
# QINIU_BUCKET_NAME = 'fengyingbanbo'
# QINIU_BUCKET_DOMAIN = 'qgzocher3.hn-bkt.clouddn.com' 
# QINIU_PIPELINE_NAME = '123456'
# PREFIX_URL = 'http://'



# MEDIA_URL = PREFIX_URL + QINIU_BUCKET_DOMAIN + '/media/' 
# MEDIA_ROOT = QINIU_BUCKET_DOMAIN 
# # 静态文件的url配置
# STATIC_URL = QINIU_BUCKET_DOMAIN + '/static/'
# # 静态文件的存储引擎
# STATICFILES_STORAGE = 'qiniustorage.backends.QiniuStaticStorage'

# VIDEO_IMAGE_SETTINGS = {
#         "DIRECTORY_PREFIX": "video-images/",
#         "STORAGE_KWARGS": {
#             "base_url": STATIC_URL,
#             "location": MEDIA_URL
#         },
#         "VIDEO_IMAGE_MAX_BYTES": 2097152,
#         "VIDEO_IMAGE_MIN_BYTES": 2048
#     }


 