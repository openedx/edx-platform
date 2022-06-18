from rest_framework_jwt.settings import api_settings




class CreateToken(object):


    def create_token(self,*args,**kwargs):

        user = kwargs["user"]
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return token

createtoken = CreateToken()