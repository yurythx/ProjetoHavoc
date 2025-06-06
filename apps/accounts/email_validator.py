#!/usr/bin/env python
"""
Sistema avançado de validação de email
"""
import re
import socket
import smtplib
import dns.resolver
from email.mime.text import MIMEText
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailValidator:
    """Validador avançado de emails"""
    
    # Lista de domínios de email temporário/descartável
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.org', 'temp-mail.org', 'throwaway.email',
        'yopmail.com', 'maildrop.cc', 'sharklasers.com',
        'grr.la', 'guerrillamailblock.com', 'pokemail.net',
        'spam4.me', 'bccto.me', 'chacuo.net', 'dispostable.com',
        'emailondeck.com', 'fakeinbox.com', 'hide.biz.st',
        'mytrashmail.com', 'nobulk.com', 'sogetthis.com',
        'spamherelots.com', 'superrito.com', 'zoemail.org',
        'mailnesia.com', 'trashmail.com', '33mail.com',
        'amilegit.com', 'byom.de', 'crazymailing.com',
        'deadaddress.com', 'despammed.com', 'dontreg.com',
        'e4ward.com', 'emailias.com', 'emailinfive.com',
        'emailsensei.com', 'emailtemporar.ro', 'emailto.de',
        'emz.net', 'fakemail.fr', 'fastacura.com',
        'filzmail.com', 'fleckens.hu', 'get2mail.fr',
        'getairmail.com', 'getnada.com', 'h8s.org',
        'haltospam.com', 'imails.info', 'inboxalias.com',
        'jetable.org', 'koszmail.pl', 'kurzepost.de',
        'lifebyfood.com', 'lroid.com', 'mail-temporaire.fr',
        'mail.by', 'mailbidon.com', 'mailcatch.com',
        'maileater.com', 'mailexpire.com', 'mailforspam.com',
        'mailfreeonline.com', 'mailguard.me', 'mailin8r.com',
        'mailme.lv', 'mailmetrash.com', 'mailmoat.com',
        'mailnull.com', 'mailshell.com', 'mailsiphon.com',
        'mailtemp.info', 'mailtothis.com', 'mailzilla.com',
        'mbx.cc', 'mega.zik.dj', 'meltmail.com', 'mierdamail.com',
        'mintemail.com', 'mt2009.com', 'mx0.wwwnew.eu',
        'myspaceinc.com', 'myspaceinc.net', 'myspaceinc.org',
        'myspacepimpedup.com', 'myspamless.com', 'mytrashmail.com',
        'no-spam.ws', 'noclickemail.com', 'nogmailspam.info',
        'nomail.xl.cx', 'nomail2me.com', 'nospam.ze.tc',
        'nospam4.us', 'nospamfor.us', 'nowmymail.com',
        'objectmail.com', 'obobbo.com', 'odnorazovoe.ru',
        'oneoffemail.com', 'onewaymail.com', 'ordinaryamerican.net',
        'otherinbox.com', 'ovpn.to', 'owlpic.com', 'pancakemail.com',
        'pjkh.com', 'plexolan.de', 'pookmail.com', 'proxymail.eu',
        'rcpt.at', 'receiveee.com', 'recursor.net', 'regbypass.com',
        'rmqkr.net', 'rppkn.com', 'rtrtr.com', 'sharklasers.com',
        'shieldedmail.com', 'shitmail.me', 'shortmail.net',
        'sibmail.com', 'skeefmail.com', 'slopsbox.com',
        'smashmail.de', 'smellfear.com', 'snakemail.com',
        'sneakemail.com', 'snkmail.com', 'sofort-mail.de',
        'sogetthis.com', 'soodonims.com', 'spam.la', 'spamavert.com',
        'spambob.net', 'spambob.org', 'spambog.com', 'spambog.de',
        'spambog.ru', 'spambox.us', 'spamcannon.com', 'spamcannon.net',
        'spamcero.com', 'spamcon.org', 'spamcorptastic.com',
        'spamcowboy.com', 'spamcowboy.net', 'spamcowboy.org',
        'spamday.com', 'spamex.com', 'spamfree24.com', 'spamfree24.de',
        'spamfree24.eu', 'spamfree24.net', 'spamfree24.org',
        'spamgoes.com', 'spamgourmet.com', 'spamgourmet.net',
        'spamgourmet.org', 'spamhole.com', 'spamify.com',
        'spaminator.de', 'spamkill.info', 'spaml.com', 'spaml.de',
        'spammotel.com', 'spamobox.com', 'spamspot.com',
        'spamstack.net', 'spamthis.co.uk', 'spamthisplease.com',
        'spamtrail.com', 'spamtroll.net', 'speed.1s.fr',
        'spoofmail.de', 'stuffmail.de', 'super-auswahl.de',
        'supergreatmail.com', 'supermailer.jp', 'superrito.com',
        'superstachel.de', 'suremail.info', 'tagyourself.com',
        'teewars.org', 'teleworm.com', 'teleworm.us', 'temp-mail.org',
        'temp-mail.ru', 'tempalias.com', 'tempe-mail.com',
        'tempemail.biz', 'tempemail.com', 'tempinbox.co.uk',
        'tempinbox.com', 'tempmail.eu', 'tempmail2.com',
        'tempmaildemo.com', 'tempmailer.com', 'tempmailer.de',
        'tempmailaddress.com', 'tempthe.net', 'thanksnospam.info',
        'thankyou2010.com', 'thecloudindex.com', 'thisisnotmyrealemail.com',
        'thismail.net', 'throwawayemailaddresses.com', 'tilien.com',
        'tmail.ws', 'tmailinator.com', 'toiea.com', 'tradermail.info',
        'trash-amil.com', 'trash-mail.at', 'trash-mail.com',
        'trash-mail.de', 'trash2009.com', 'trashdevil.com',
        'trashemail.de', 'trashmail.at', 'trashmail.com',
        'trashmail.de', 'trashmail.me', 'trashmail.net',
        'trashmail.org', 'trashmail.ws', 'trashmailer.com',
        'trashymail.com', 'trashymail.net', 'trbvm.com',
        'turual.com', 'twinmail.de', 'tyldd.com', 'uggsrock.com',
        'umail.net', 'upliftnow.com', 'uplipht.com', 'venompen.com',
        'veryrealemail.com', 'viditag.com', 'viewcastmedia.com',
        'viewcastmedia.net', 'viewcastmedia.org', 'vomoto.com',
        'vpn.st', 'vsimcard.com', 'vubby.com', 'walala.org',
        'walkmail.net', 'webemail.me', 'webm4il.info', 'wh4f.org',
        'whyspam.me', 'willselfdestruct.com', 'winemaven.info',
        'wronghead.com', 'wuzup.net', 'wuzupmail.net', 'www.e4ward.com',
        'www.gishpuppy.com', 'www.mailinator.com', 'wwwnew.eu',
        'x.ip6.li', 'xagloo.com', 'xemaps.com', 'xents.com',
        'xmaily.com', 'xoxy.net', 'yapped.net', 'yeah.net',
        'yep.it', 'yogamaven.com', 'yopmail.com', 'yopmail.fr',
        'yopmail.net', 'yourdomain.com', 'ypmail.webredirect.org',
        'yuurok.com', 'zehnminuten.de', 'zehnminutenmail.de',
        'zetmail.com', 'zippymail.info', 'zoemail.com', 'zoemail.net',
        'zoemail.org', 'zomg.info'
    }
    
    # Regex para validação de sintaxe
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @classmethod
    def validate_syntax(cls, email: str) -> Tuple[bool, str]:
        """Valida sintaxe do email"""
        if not email or not isinstance(email, str):
            return False, "Email não fornecido"
        
        email = email.strip().lower()
        
        if len(email) > 254:
            return False, "Email muito longo (máximo 254 caracteres)"
        
        if not cls.EMAIL_REGEX.match(email):
            return False, "Formato de email inválido"
        
        local, domain = email.split('@')
        
        if len(local) > 64:
            return False, "Parte local do email muito longa (máximo 64 caracteres)"
        
        if len(domain) > 253:
            return False, "Domínio muito longo (máximo 253 caracteres)"
        
        return True, "Sintaxe válida"
    
    @classmethod
    def check_disposable_domain(cls, email: str) -> Tuple[bool, str]:
        """Verifica se é um domínio de email temporário"""
        try:
            domain = email.split('@')[1].lower()
            
            if domain in cls.DISPOSABLE_DOMAINS:
                return False, f"Email temporário/descartável não permitido ({domain})"
            
            return True, "Domínio válido"
        except:
            return False, "Erro ao verificar domínio"
    
    @classmethod
    def check_domain_exists(cls, email: str) -> Tuple[bool, str]:
        """Verifica se o domínio existe"""
        try:
            domain = email.split('@')[1]
            
            # Verificar se domínio resolve
            socket.gethostbyname(domain)
            return True, "Domínio existe"
            
        except socket.gaierror:
            return False, f"Domínio não existe ou não resolve"
        except Exception as e:
            logger.warning(f"Erro ao verificar domínio: {e}")
            return True, "Não foi possível verificar domínio (assumindo válido)"
    
    @classmethod
    def check_mx_record(cls, email: str) -> Tuple[bool, str]:
        """Verifica se domínio tem registro MX (aceita emails)"""
        try:
            domain = email.split('@')[1]
            
            # Verificar registros MX
            mx_records = dns.resolver.resolve(domain, 'MX')
            
            if mx_records:
                return True, f"Domínio aceita emails ({len(mx_records)} servidores MX)"
            else:
                return False, "Domínio não aceita emails (sem registros MX)"
                
        except dns.resolver.NXDOMAIN:
            return False, "Domínio não existe"
        except dns.resolver.NoAnswer:
            return False, "Domínio não tem registros MX"
        except Exception as e:
            logger.warning(f"Erro ao verificar MX: {e}")
            return True, "Não foi possível verificar MX (assumindo válido)"
    
    @classmethod
    def validate_email_comprehensive(cls, email: str, check_smtp: bool = False) -> Dict[str, Any]:
        """
        Validação completa do email
        
        Args:
            email: Email para validar
            check_smtp: Se deve fazer verificação SMTP (mais lenta)
        
        Returns:
            Dict com resultado da validação
        """
        result = {
            'email': email,
            'is_valid': False,
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # 1. Validar sintaxe
        syntax_valid, syntax_msg = cls.validate_syntax(email)
        result['checks']['syntax'] = {'valid': syntax_valid, 'message': syntax_msg}
        
        if not syntax_valid:
            result['errors'].append(syntax_msg)
            return result
        
        email = email.strip().lower()
        
        # 2. Verificar domínios descartáveis
        disposable_valid, disposable_msg = cls.check_disposable_domain(email)
        result['checks']['disposable'] = {'valid': disposable_valid, 'message': disposable_msg}
        
        if not disposable_valid:
            result['errors'].append(disposable_msg)
            return result
        
        # 3. Verificar se domínio existe
        domain_valid, domain_msg = cls.check_domain_exists(email)
        result['checks']['domain'] = {'valid': domain_valid, 'message': domain_msg}
        
        if not domain_valid:
            result['errors'].append(domain_msg)
            return result
        
        # 4. Verificar registros MX
        mx_valid, mx_msg = cls.check_mx_record(email)
        result['checks']['mx'] = {'valid': mx_valid, 'message': mx_msg}
        
        if not mx_valid:
            result['errors'].append(mx_msg)
            return result
        
        # 5. Verificação SMTP (opcional - mais lenta)
        if check_smtp:
            smtp_valid, smtp_msg = cls.check_smtp_deliverable(email)
            result['checks']['smtp'] = {'valid': smtp_valid, 'message': smtp_msg}
            
            if not smtp_valid:
                result['warnings'].append(f"SMTP: {smtp_msg}")
        
        # Se chegou até aqui, email é válido
        result['is_valid'] = True
        
        return result
    
    @classmethod
    def check_smtp_deliverable(cls, email: str) -> Tuple[bool, str]:
        """
        Verifica se email é entregável via SMTP
        ATENÇÃO: Pode ser lento e alguns servidores bloqueiam
        """
        try:
            domain = email.split('@')[1]
            
            # Obter servidor MX
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_server = str(mx_records[0].exchange)
            
            # Conectar ao servidor SMTP
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_server, 25)
            server.helo('localhost')
            server.mail('test@localhost')
            
            # Verificar se email é aceito
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True, "Email é entregável"
            else:
                return False, f"Email rejeitado pelo servidor (código {code})"
                
        except Exception as e:
            logger.warning(f"Erro na verificação SMTP: {e}")
            return True, "Não foi possível verificar via SMTP (assumindo válido)"


def validate_email_simple(email: str) -> Tuple[bool, str]:
    """
    Validação simples e rápida de email
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem)
    """
    result = EmailValidator.validate_email_comprehensive(email, check_smtp=False)
    
    if result['is_valid']:
        return True, "Email válido"
    else:
        return False, "; ".join(result['errors'])


def validate_email_strict(email: str) -> Tuple[bool, str]:
    """
    Validação rigorosa de email (inclui verificação SMTP)
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem)
    """
    result = EmailValidator.validate_email_comprehensive(email, check_smtp=True)
    
    if result['is_valid']:
        warnings = "; ".join(result['warnings']) if result['warnings'] else ""
        return True, f"Email válido{' (' + warnings + ')' if warnings else ''}"
    else:
        return False, "; ".join(result['errors'])
