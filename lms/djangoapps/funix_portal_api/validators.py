from abc import ABC, abstractmethod
from common.djangoapps.student.models import User
import logging

NAME = 'name'
USERNAME = 'username'
EMAIL = 'email'
PASSWORD = 'password'

class FunixUserFieldValidationBase(ABC):

    @abstractmethod
    def _default_msg(self):
        pass

    def __init__(self, value):
        self.value = value
        self.errors = []
    
    @abstractmethod
    def validate(self): 
        pass

    def _add_msg(self, msg):
        self.errors.append(msg)

    
class FunixUsernameValidation(FunixUserFieldValidationBase):

    def _default_msg(self):
        return f"Username '{self.value}' is not valid."
    
    def validate(self):
        conflict_username = self._username_already_exists()
        if conflict_username:
            self._add_msg(conflict_username)

        return self.errors
    
    def _username_already_exists(self): 
        try:
            User.objects.get(username=self.value)
            return f"User with username '{self.value}' already exists."
        except User.DoesNotExist:
            return False
        except Exception as e:
            logging.error(str(e))
            return str(e)

class FunixPasswordValidation(FunixUserFieldValidationBase):

    def _default_msg(self):
        return f"Password '{self.value}' is invalid. Password must be at least 8 characters."
    
    def validate(self):
        if len(self.value) < 8:
            self._add_msg(self._default_msg())
        
        return self.errors

class FunixNameValidation(FunixUserFieldValidationBase):

    def _default_msg(self):
        return f"Name '{self.value}' is invalid."
    
    def validate(self):
        return self.errors
    
class FunixEmailValidation(FunixUserFieldValidationBase):

    def _default_msg(self):
        return f"Email '{self.value}' is invalid."
    
    def validate(self):
        if self.value.count('@') != 1:
            self._add_msg(self._default_msg())

        conflict_email = self._email_already_exists()
        if conflict_email:
            self._add_msg(conflict_email)

        return self.errors
    
    def _email_already_exists(self): 
        try:
            User.objects.get(email=self.value)
            return f"User with email '{self.value}' already exists."
        except User.DoesNotExist:
            return False
        except Exception as e:
            logging.error(str(e))
            return str(e)
    
field_validators = {
    NAME: FunixNameValidation,
    USERNAME: FunixUsernameValidation,
    EMAIL: FunixEmailValidation,
    PASSWORD: FunixPasswordValidation,
}

class FunixUserValidation:

    def __init__(self, fields): 
        self.fields = fields

    
    def validate(self, user): 
        validation_errors = {}

        for field in self.fields:
            field_errors = []
            value = user.get(field)

            if value is None:
                field_errors.append("This field is required.")
            else: 
                validator = field_validators.get(field)(value)
                field_errors = validator.validate()
            
            if len(field_errors) > 0:
                validation_errors[field] = field_errors


        return validation_errors

funix_user_validator = FunixUserValidation([NAME, USERNAME, EMAIL, PASSWORD])