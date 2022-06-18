from django_restframework.exceptions import exception
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

class MySerializer(DynamicFieldsMixin,serializers.ModelSerializer):

    pass

class SerializerPlug(object):
    msg_error = "error"
    msg_detail = "field"


    def validation_error(self, serializer):
        """自定义序列化异常"""
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(e)
            d = e.__dict__
            for i, k in d["detail"].items():
                self.msg_detail = i
                self.msg_error = k[0]
                break
            raise exception.myException400({
                "success": False,
                "msg": "{}".format(self.msg_error),
            })
        return None

    def field_errormsg(self,*args,**kwargs):

        field = kwargs.get("field","")

        return {
            "unique": "{}已经被注册。".format(field),
            "required": "{}不能为空。".format(field),
            "min_length": "%s长度不能小于{min_length}。" % field,
            "max_length": "%s长度不能大于{max_length}。" % field,
            "max_value": "确保%s小于或等于{max_value}。" % field,
            "min_value": "确保%s大于或等于{min_value}。" % field,
            "max_digits": "确保%s总共不超过{max_digits}个数字。" % field,
            'invalid': "{}不合法。".format(field),
            'blank': "{}不可以是空白。".format(field),
            'max_string_length': "{}值太大。".format(field),
            'max_whole_digits': "确保%s小数位数不超过{max_decimal_places}。" % field,
            'max_decimal_places': "确保%s小数点前不超过{max_whole_digits}个数字。" % field,
            'overflow': "{}日期时间值超出范围。".format(field),
        }

error_instance = SerializerPlug()



