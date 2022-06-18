from rest_framework.pagination  import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
import math



# 自定义分页类

class MyPagination(PageNumberPagination):
    page_size = 5    # 每页显示多少个
    page_size_query_param = "size" # 默认每页显示3个，可以通过传入pager1/?page=2&size=4,改变默认每页显示的个数
    max_page_size = 500 # 最大页数不超过500
    page_query_param = "page" # 获取页码数的

    def get_total_pages(self):
        """总页数"""
        return math.ceil(self.page.paginator.count / self.page_size)  # 向上取整

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('size', self.page_size),
            ('totalpages', self.get_total_pages()),
            ('success', True),
            ('msg', 'ok'),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
         ]))

