#!/usr/bin/env python
"""
Validadores personalizados para Django
"""
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator as DjangoEmailValidator
from .email_validator import validate_email_simple, validate_email_strict
import logging

logger = logging.getLogger(__name__)

class RealEmailValidator(DjangoEmailValidator):
    """
    Validador de email que verifica se o email é real
    """
    message = 'Digite um endereço de email válido e real.'
    code = 'invalid_real_email'

    def __init__(self, level='basic', **kwargs):
        """
        Args:
            level: Nível de validação
                - 'basic': Apenas sintaxe + descartáveis (rápido)
                - 'standard': + verificação de domínio (médio)
                - 'strict': + verificação MX + SMTP (lento)
        """
        self.level = level
        super().__init__(**kwargs)

    def __call__(self, value):
        # Primeiro, validação básica do Django
        super().__call__(value)

        # Validação por nível
        if self.level == 'basic':
            is_valid, message = self._validate_basic(value)
        elif self.level == 'standard':
            is_valid, message = self._validate_standard(value)
        else:  # strict
            is_valid, message = validate_email_strict(value)

        if not is_valid:
            raise ValidationError(
                message,
                code=self.code,
                params={'value': value}
            )

    def _validate_basic(self, email):
        """Validação básica: sintaxe + descartáveis"""
        from .email_validator import EmailValidator

        # 1. Verificar sintaxe
        syntax_valid, syntax_msg = EmailValidator.validate_syntax(email)
        if not syntax_valid:
            return False, syntax_msg

        # 2. Verificar domínios descartáveis
        disposable_valid, disposable_msg = EmailValidator.check_disposable_domain(email)
        if not disposable_valid:
            return False, disposable_msg

        return True, "Email válido"

    def _validate_standard(self, email):
        """Validação padrão: básica + domínio"""
        from .email_validator import EmailValidator

        # Validação básica primeiro
        basic_valid, basic_msg = self._validate_basic(email)
        if not basic_valid:
            return False, basic_msg

        # 3. Verificar se domínio existe
        domain_valid, domain_msg = EmailValidator.check_domain_exists(email)
        if not domain_valid:
            return False, domain_msg

        return True, "Email válido"


class DisposableEmailValidator:
    """
    Validador que bloqueia apenas emails descartáveis
    """
    message = 'Emails temporários ou descartáveis não são permitidos.'
    code = 'disposable_email'

    def __call__(self, value):
        from .email_validator import EmailValidator

        is_valid, message = EmailValidator.check_disposable_domain(value)

        if not is_valid:
            raise ValidationError(
                message,
                code=self.code,
                params={'value': value}
            )


class DomainExistsValidator:
    """
    Validador que verifica se o domínio existe
    """
    message = 'O domínio do email não existe.'
    code = 'domain_not_exists'

    def __call__(self, value):
        from .email_validator import EmailValidator

        is_valid, message = EmailValidator.check_domain_exists(value)

        if not is_valid:
            raise ValidationError(
                message,
                code=self.code,
                params={'value': value}
            )


class MXRecordValidator:
    """
    Validador que verifica se o domínio aceita emails (tem registros MX)
    """
    message = 'O domínio não aceita emails.'
    code = 'no_mx_record'

    def __call__(self, value):
        from .email_validator import EmailValidator

        is_valid, message = EmailValidator.check_mx_record(value)

        if not is_valid:
            raise ValidationError(
                message,
                code=self.code,
                params={'value': value}
            )


# Instâncias pré-configuradas para uso fácil
validate_real_email_basic = RealEmailValidator(level='basic')      # Rápido: sintaxe + descartáveis
validate_real_email = RealEmailValidator(level='standard')         # Padrão: + verificação domínio
validate_real_email_strict = RealEmailValidator(level='strict')    # Completo: + MX + SMTP
validate_no_disposable = DisposableEmailValidator()
validate_domain_exists = DomainExistsValidator()
validate_mx_record = MXRecordValidator()
