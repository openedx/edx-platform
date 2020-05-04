from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ungettext


class MasterPasswordValidator(object):
    """
    Validate all of the validators given in the validators list.

    Parameters:
        validators (list): the list of validators to validate along with their options.
        min_validations (int): the num of minimum validation must pass for password.

    Raises:
        ValidationError if minimum number of validations is not passed.
    """
    def __init__(self, validators=[], min_validations=0):
        self.check_validators_list(validators, min_validations)
        validators_list = validators
        self.validators = []
        for validator in validators_list:
            try:
                validator_name = validator["NAME"]
            except KeyError:
                raise KeyError("Validator doesn't contain 'NAME'. Please enter valid Validator")
            validator_options = validator.get("OPTIONS", {})
            self.validators.append(import_string(validator_name)(**validator_options))
        self.min_validations = min_validations

    def validate(self, password, user=None):
        errors, passed = [], 0
        for v in self.validators:
            try:
                v.validate(password, user)
            except ValidationError as e:
                errors.append(e)
            else:
                passed += 1
        if passed < self.min_validations:
            errors.insert(0, ValidationError(" Fix at least {} of the following errors: ".format(
                self.min_validations - passed)))
            raise ValidationError(errors, code="too_few_validations",
                                  params={"min_validations": self.min_validations})

    def get_help_text(self):
        text = ungettext(
            "your password must confirm to at least %(min_validations)d of the following:",
            "your password must confirm to at least %(min_validations)d of the followings:",
            self.min_validations
        ) % {"min_validations": self.min_validations}
        for v in self.validators:
            text += v.get_help_text()
        return mark_safe(text)

    def get_instruction_text(self):
        text = ungettext(
            "your password must confirm to at least %(min_validations)d of the following:",
            "your password must confirm to at least %(min_validations)d of the followings:",
            self.min_validations
        ) % {"min_validations": self.min_validations}
        for validator in self.validators:
            if hasattr(validator, 'get_instruction_text'):
                text += validator.get_instruction_text() + ", "
        return mark_safe(text[:-1])

    @staticmethod
    def check_validators_list(validators, min_validations):
        if len(validators) < min_validations:
            raise Exception('Number of Validators in list is lower than the minimum number of required validations.')


class RestrictedSymbolValidator(object):
    """
    Validate whether the password contains any of the restricted symbol.

    Parameters:
        restricted_symbol_list (list): the list of symbols not allowed to use in password.
    """
    def __init__(self, restricted_symbol_list=[]):
        self.restricted_symbol_list = restricted_symbol_list
        self.restricted_symbol_text = self.get_restricted_symbol_text()

    def validate(self, password, user=None):
        if self.validate_restriction_list(password):
            return
        raise ValidationError(
            _("Your password must not contain any of the following symbols: {}".format(self.restricted_symbol_text)),
            code="restricted_symbol_used",
        )

    def get_help_text(self):
        return _(
            "Your password must not contain any of the following symbols: {}".format(self.restricted_symbol_text))

    def get_instruction_text(self):
        if len(self.restricted_symbol_list) > 0:
            return _(
                "your password must not contain any of the following symbols: {}".format(self.restricted_symbol_text))
        return ""

    def validate_restriction_list(self, password):
        for c in password:
            if c in self.restricted_symbol_list:
                return False
        return True

    def get_restricted_symbol_text(self):
        text = ""
        for c in self.restricted_symbol_list:
            if c.isspace():
                text += " Space"
            else:
                text += " " + c
        return text
