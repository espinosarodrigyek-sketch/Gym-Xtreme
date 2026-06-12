#!/usr/bin/env python
"""
Script de diagnóstico para verificar la configuración de email en Django
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.conf import settings
from django.core.mail import EmailMessage
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnosticar_email():
    """Realiza un diagnóstico completo de la configuración de email"""
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE CONFIGURACIÓN DE EMAIL")
    print("="*80 + "\n")
    
    # 1. Verificar configuración básica
    print("1. CONFIGURACIÓN BÁSICA")
    print("-" * 80)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else '❌ NO CONFIGURADO'}")
    print(f"EMAIL_HOST_PASSWORD: {'✓ Configurado' if settings.EMAIL_HOST_PASSWORD else '❌ NO CONFIGURADO'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'No configurado'}")
    
    # 2. Validar credenciales
    print("\n2. VALIDACIÓN DE CREDENCIALES")
    print("-" * 80)
    
    if not settings.EMAIL_HOST_USER:
        print("❌ EMAIL_HOST_USER no está configurado")
        return False
    else:
        print(f"✓ EMAIL_HOST_USER configurado: {settings.EMAIL_HOST_USER}")
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("❌ EMAIL_HOST_PASSWORD no está configurado")
        return False
    else:
        print(f"✓ EMAIL_HOST_PASSWORD configurado (longitud: {len(settings.EMAIL_HOST_PASSWORD)} caracteres)")
    
    # 3. Probar conexión SMTP
    print("\n3. PRUEBA DE CONEXIÓN SMTP")
    print("-" * 80)
    
    try:
        import smtplib
        
        # Intentar conexión manual
        print(f"Intentando conectar a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        
        if settings.EMAIL_USE_TLS:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        
        print(f"✓ Conexión TCP establecida")
        
        # Intentar login
        print(f"Intentando autenticarse con {settings.EMAIL_HOST_USER}...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print(f"✓ Autenticación exitosa")
        server.quit()
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación: {str(e)}")
        print(f"   Verifica que EMAIL_HOST_USER y EMAIL_HOST_PASSWORD sean correctos")
        print(f"   Para Gmail, asegúrate de usar una Contraseña de Aplicación (App Password)")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        print(f"   Verifica que EMAIL_HOST={settings.EMAIL_HOST} sea accesible")
        return False
    
    # 4. Probar envío de correo de prueba
    print("\n4. PRUEBA DE ENVÍO DE CORREO")
    print("-" * 80)
    
    try:
        email = EmailMessage(
            subject='[PRUEBA] Test de Configuración de Email - GYM XTREME',
            body='Este es un correo de prueba para verificar que la configuración de email está funcionando correctamente en GYM XTREME.',
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER]  # Enviar a sí mismo para prueba
        )
        
        result = email.send(fail_silently=False)
        
        if result > 0:
            print(f"✓ Correo de prueba enviado exitosamente")
            print(f"  Correos enviados: {result}")
            return True
        else:
            print(f"❌ El correo no se envió (result={result})")
            return False
            
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = diagnosticar_email()
    
    print("\n" + "="*80)
    if success:
        print("✓ CONFIGURACIÓN CORRECTA - Los correos deberían enviarse correctamente")
    else:
        print("❌ PROBLEMAS ENCONTRADOS - Revisa los errores arriba")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
