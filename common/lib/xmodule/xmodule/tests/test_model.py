
class ModelMetaclassTester(object):
    __metaclass__ = ModelMetaclass

    field_a = Int(scope=Scope.settings)
    field_b = Int(scope=Scope.content)

def test_model_metaclass():
