from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils import timezone
from .models import Rutina
import random
import logging

logger = logging.getLogger(__name__)


def enviar_comprobante_pago(usuario, plan=None, venta=None, total=None, tipo_pago="plan"):
    """
    Envía un comprobante de pago al correo del usuario
    
    Args:
        usuario: El usuario que realizó el pago
        plan: El plan comprado (si es pago de plan)
        venta: La venta realizada (si es pago de producto)
        total: Monto total pagado
        tipo_pago: "plan" o "producto"
        
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    
    if not usuario.email:
        logger.warning(f"[CORREO] Usuario {usuario.username} no tiene email registrado")
        return False, "El usuario no tiene correo electrónico registrado."
    
    # Log de configuración
    logger.info(f"[CORREO] Verificando configuración de email...")
    logger.info(f"[CORREO] EMAIL_HOST: {settings.EMAIL_HOST}")
    logger.info(f"[CORREO] EMAIL_PORT: {settings.EMAIL_PORT}")
    logger.info(f"[CORREO] EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"[CORREO] EMAIL_HOST_USER: {'***' if settings.EMAIL_HOST_USER else 'NO CONFIGURADO'}")
    logger.info(f"[CORREO] EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO'}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.error(f"[CORREO] Credenciales de email no configuradas")
        return False, "El servidor de correo no está configurado. Contacta al administrador."
    
    try:
        logger.info(f"[CORREO] Iniciando envío de comprobante para {usuario.username} ({usuario.email})")
        
        # Determinar información basada en tipo de pago
        if tipo_pago == "plan" and plan:
            nombre_item = plan.nombre
            valor_item = plan.precio
            fecha_item = timezone.now().date()
        elif tipo_pago == "producto" and venta:
            # Obtener el primer producto de la venta para mostrar en el comprobante
            primer_detalle = venta.detalles.first()
            if primer_detalle:
                nombre_item = f"{primer_detalle.producto.nombre} ({venta.detalles.count()} items)"
                valor_item = venta.total
                fecha_item = venta.fecha.date() if venta.fecha else timezone.now().date()
            else:
                nombre_item = "Compra de productos"
                valor_item = total or 0
                fecha_item = timezone.now().date()
        else:
            nombre_item = "Compra"
            valor_item = total or 0
            fecha_item = timezone.now().date()
        
        # Generar número de comprobante
        comprobante_num = f"GYM-{timezone.now().strftime('%Y%m%d')}-{usuario.id:04d}-{random.randint(1000, 9999)}"
        
        # Contenido HTML del correo
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
                .info-item {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; }}
                .info-label {{ font-size: 14px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }}
                .info-value {{ font-size: 18px; font-weight: 600; color: #212529; margin-top: 5px; }}
                .divider {{ height: 1px; background-color: #e9ecef; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
                .btn {{ display: inline-block; background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 20px; }}
                .btn:hover {{ background-color: #218838; }}
                .status-badge {{ display: inline-block; background-color: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: 600; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 Comprobante de Pago</h1>
                    <p>GYM XTREME - Gracias por tu compra</p>
                </div>
                <div class="content">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <span class="status-badge">PAGO EXITOSO</span>
                    </div>
                    
                    <h2>Detalles de la Transacción</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Nombre del Cliente</div>
                            <div class="info-value">{usuario.first_name or usuario.username}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Email</div>
                            <div class="info-value">{usuario.email}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Concepto</div>
                            <div class="info-value">{nombre_item}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Fecha</div>
                            <div class="info-value">{fecha_item.strftime('%d/%m/%Y')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Comprobante #</div>
                            <div class="info-value">{comprobante_num}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Método de Pago</div>
                            <div class="info-value">Simulación (Tarjeta de Crédito)</div>
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div style="text-align: center;">
                        <div class="info-label">Total Pagado</div>
                        <div class="amount">${valor_item:,.2f}</div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #6c757d; font-size: 14px;">
                            Este comprobante sirve como confirmación de pago simulado.<br>
                            Guardelo para sus registros.
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p>GYM XTREME - Transformando cuerpos, cambiando vidas</p>
                    <p>Este es un comprobante de pago simulado generado automáticamente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = EmailMessage(
            f"💰 Comprobante de Pago - {nombre_item}",
            html_content,
            settings.EMAIL_HOST_USER,
            [usuario.email]
        )
        email.content_subtype = "html"
        
        logger.info(f"[CORREO] Construyendo correo para {usuario.email}")
        logger.info(f"[CORREO] Asunto: Comprobante de Pago - {nombre_item}")
        logger.info(f"[CORREO] De: {settings.EMAIL_HOST_USER}")
        logger.info(f"[CORREO] Para: {usuario.email}")
        
        # Intentar enviar el correo
        logger.info(f"[CORREO] Enviando correo...")
        result = email.send(fail_silently=False)
        logger.info(f"[CORREO] Resultado del envío: {result} correos enviados")
        
        if result > 0:
            logger.info(f"[CORREO] ✅ Comprobante enviado exitosamente a {usuario.email}")
            return True, f"Comprobante de pago enviado a {usuario.email}"
        logger.error(f"[CORREO] ❌ No se pudo enviar el correo (result={result})")
        return False, "No se pudo enviar el correo. Intenta de nuevo."
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[CORREO] ❌ Excepción al enviar correo: {error_msg}", exc_info=True)
        
        if "authentication" in error_msg.lower():
            logger.error(f"[CORREO] Error de autenticación - Verifica EMAIL_HOST_USER y EMAIL_HOST_PASSWORD")
            return False, "Error de autenticación del correo. Contacta al administrador."
        elif "connection" in error_msg.lower():
            logger.error(f"[CORREO] Error de conexión - Verifica EMAIL_HOST y EMAIL_PORT")
            return False, "No se pudo conectar al servidor de correo."
        elif "tls" in error_msg.lower() or "ssl" in error_msg.lower():
            logger.error(f"[CORREO] Error de TLS/SSL - Verifica EMAIL_USE_TLS")
            return False, "Error de seguridad (TLS/SSL). Contacta al administrador."
        return False, f"Error al enviar correo: {error_msg}"


def enviar_rutina_correo(usuario, plan, objetivo, rutina_id):
    """
    Envía la rutina asignada al correo del usuario con detalles completos
    
    Args:
        usuario: El usuario que recibe la rutina
        plan: El plan de entrenamiento
        objetivo: El objetivo seleccionado
        rutina_id: ID de la rutina
        
    Returns:
        tuple: (exito: bool, mensaje: str)
    """
    
    if not usuario.email:
        return False, "El usuario no tiene correo electrónico registrado."
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return False, "El servidor de correo no está configurado."
    
    try:
        # Obtener la rutina si existe
        rutina = None
        nombre_rutina = "Tu Rutina de Entrenamiento"
        contenido_ejercicios = ""
        
        if rutina_id:
            try:
                rutina = Rutina.objects.prefetch_related('ejercicios').get(id=rutina_id)
                nombre_rutina = rutina.nombre
                
                # Generar contenido detallado de ejercicios
                ejercicios_por_dia = rutina.get_ejercicios_por_dia()
                
                if ejercicios_por_dia:
                    contenido_ejercicios = """
                    <div style="margin-top: 30px;">
                        <h2 style="color: #1a1a1a; border-bottom: 3px solid #28a745; padding-bottom: 10px; margin-bottom: 20px;">
                            📅 Tu Plan Semanal de Entrenamiento
                        </h2>
                    """
                    
                    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
                    nombres_dias = {
                        'lunes': 'LUNES',
                        'martes': 'MARTES',
                        'miercoles': 'MIÉRCOLES',
                        'jueves': 'JUEVES',
                        'viernes': 'VIERNES',
                        'sabado': 'SÁBADO',
                        'domingo': 'DOMINGO'
                    }
                    
                    iconos_dias = {
                        'lunes': '💪',
                        'martes': '🏋️',
                        'miercoles': '⚡',
                        'jueves': '🔥',
                        'viernes': '🎯',
                        'sabado': '💨',
                        'domingo': '🧘'
                    }
                    
                    for dia in dias_semana:
                        if dia in ejercicios_por_dia:
                            ejercicios_dia = ejercicios_por_dia[dia]
                            contenido_ejercicios += f"""
                            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; margin-bottom: 20px; border-radius: 12px; border-left: 5px solid #28a745;">
                                <h3 style="margin: 0 0 15px 0; color: #1a1a1a; font-size: 18px;">
                                    {iconos_dias.get(dia, '📌')} {nombres_dias.get(dia, dia.upper())}
                                </h3>
                                <div style="border-top: 2px solid #dee2e6; padding-top: 15px;">
                            """
                            
                            for ejercicio in ejercicios_dia:
                                tiempo_descanso_min = ejercicio.descanso // 60
                                tiempo_descanso_seg = ejercicio.descanso % 60
                                
                                if tiempo_descanso_min > 0 and tiempo_descanso_seg > 0:
                                    tiempo_format = f"{tiempo_descanso_min}m {tiempo_descanso_seg}s"
                                elif tiempo_descanso_min > 0:
                                    tiempo_format = f"{tiempo_descanso_min}m"
                                else:
                                    tiempo_format = f"{tiempo_descanso_seg}s"
                                
                                contenido_ejercicios += f"""
                                <div style="background: white; padding: 15px; margin-bottom: 12px; border-radius: 8px; border: 1px solid #dee2e6;">
                                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                        <strong style="color: #28a745; font-size: 16px;">{ejercicio.nombre}</strong>
                                        <span style="background: #e7f5ff; color: #0066cc; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                            #{ejercicio.orden}
                                        </span>
                                    </div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                                        <div style="background: #e7f5ff; padding: 10px; border-radius: 6px; text-align: center;">
                                            <div style="font-size: 12px; color: #0066cc; text-transform: uppercase; font-weight: 600;">Series</div>
                                            <div style="font-size: 20px; font-weight: 700; color: #1a1a1a;">{ejercicio.series}</div>
                                        </div>
                                        <div style="background: #fff3e0; padding: 10px; border-radius: 6px; text-align: center;">
                                            <div style="font-size: 12px; color: #e65100; text-transform: uppercase; font-weight: 600;">Repeticiones</div>
                                            <div style="font-size: 20px; font-weight: 700; color: #1a1a1a;">{ejercicio.repeticiones}</div>
                                        </div>
                                        <div style="background: #f3e5f5; padding: 10px; border-radius: 6px; text-align: center;">
                                            <div style="font-size: 12px; color: #6a1b9a; text-transform: uppercase; font-weight: 600;">Descanso</div>
                                            <div style="font-size: 20px; font-weight: 700; color: #1a1a1a;">{tiempo_format}</div>
                                        </div>
                                    </div>
                                    
                                    {'<div style="background: #f0f0f0; padding: 10px; border-radius: 6px; margin-top: 10px; line-height: 1.6; color: #555; font-size: 14px;">' + f"📝 <strong>Instrucciones:</strong> {ejercicio.descripcion}" + '</div>' if ejercicio.descripcion else ''}
                                </div>
                                """
                            
                            contenido_ejercicios += """
                                </div>
                            </div>
                            """
                        else:
                            # Día sin entrenamiento
                            contenido_ejercicios += f"""
                            <div style="background: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 12px; border-left: 5px solid #6c757d; text-align: center;">
                                <h3 style="margin: 0; color: #6c757d; font-size: 18px;">
                                    😌 {nombres_dias.get(dia, dia.upper())}
                                </h3>
                                <p style="margin: 10px 0 0 0; color: #999; font-size: 14px;">Descanso y recuperación</p>
                            </div>
                            """
                    
                    contenido_ejercicios += """
                    </div>
                    """
                    
                    # Agregar resumen de duración
                    contenido_ejercicios += f"""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 12px; margin-top: 30px;">
                        <div style="text-align: center;">
                            <strong style="font-size: 18px;">⏱️ Duración Total del Programa</strong>
                            <div style="font-size: 28px; font-weight: 700; margin-top: 10px;">{rutina.duracion_dias} días</div>
                            <div style="font-size: 14px; margin-top: 5px; opacity: 0.9;">
                                ({rutina.duracion_dias // 7} semanas aproximadamente)
                            </div>
                        </div>
                    </div>
                    """
                    
            except Rutina.DoesNotExist:
                pass
        
        # Mapeo de nombres para objetivos
        nombres_objetivo = {
            'bajar_peso': '🔥 Bajar de Peso',
            'subir_masa': '💪 Subir Masa Muscular',
            'mantener': '⚖️ Mantener Peso',
            'definir': '🥷 Definir Musculatura',
            'cardio': '❤️ Cardio y Resistencia'
        }
        
        nombre_objetivo = nombres_objetivo.get(objetivo, objetivo)
        
        # Crear contenido del correo
        asunto = f"📋 Tu Rutina Personalizada - {plan.nombre}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    margin: 0; 
                    padding: 20px; 
                }}
                .container {{ 
                    max-width: 700px; 
                    margin: 0 auto; 
                    background-color: white; 
                    border-radius: 15px; 
                    overflow: hidden; 
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                    color: white; 
                    padding: 40px 30px; 
                    text-align: center;
                    border-bottom: 5px solid #1a7934;
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 28px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{ 
                    padding: 30px; 
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 25px;
                }}
                .info-item {{ 
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 20px; 
                    border-radius: 10px;
                    border-left: 4px solid #28a745;
                }}
                .info-item.full {{
                    grid-column: 1 / -1;
                }}
                .label {{ 
                    font-size: 11px; 
                    color: #666; 
                    text-transform: uppercase; 
                    letter-spacing: 1px;
                    font-weight: 600;
                }}
                .value {{ 
                    font-size: 18px; 
                    font-weight: 700; 
                    color: #1a1a1a; 
                    margin-top: 8px;
                }}
                .welcome {{
                    background: #f0f9ff;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    border-left: 4px solid #0066cc;
                    color: #0d3b66;
                }}
                .welcome p {{
                    margin: 0;
                    line-height: 1.6;
                }}
                .section-title {{
                    color: #1a1a1a;
                    font-size: 20px;
                    font-weight: 700;
                    margin-top: 30px;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 3px solid #28a745;
                }}
                .tips {{
                    background: #fff9e6;
                    padding: 20px;
                    border-radius: 10px;
                    margin-top: 20px;
                    border-left: 4px solid #ffb300;
                }}
                .tips h4 {{
                    margin: 0 0 10px 0;
                    color: #ff8c00;
                    font-size: 16px;
                }}
                .tips ul {{
                    margin: 0;
                    padding-left: 20px;
                    color: #666;
                }}
                .tips li {{
                    margin: 8px 0;
                    line-height: 1.5;
                }}
                .footer {{ 
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 25px; 
                    text-align: center; 
                    color: #6c757d; 
                    font-size: 13px;
                    border-top: 2px solid #dee2e6;
                }}
                .footer p {{
                    margin: 5px 0;
                    line-height: 1.6;
                }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 25px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 15px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Tu Rutina Personalizada</h1>
                    <p>¡Estamos listos para ayudarte a alcanzar tus objetivos!</p>
                </div>
                <div class="content">
                    <div class="welcome">
                        <p>¡Hola <strong>{usuario.first_name or usuario.username}</strong>!</p>
                        <p style="margin-top: 10px;">
                            Tu rutina de entrenamiento ha sido asignada exitosamente. A continuación encontrarás todos los detalles 
                            que necesitas para comenzar tu transformación física.
                        </p>
                    </div>
                    
                    <h2 class="section-title">📋 Información de tu Plan</h2>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="label">Plan Contratado</div>
                            <div class="value">{plan.nombre}</div>
                        </div>
                        
                        <div class="info-item">
                            <div class="label">Objetivo</div>
                            <div class="value">{nombre_objetivo}</div>
                        </div>
                        
                        <div class="info-item">
                            <div class="label">Rutina Asignada</div>
                            <div class="value">{nombre_rutina}</div>
                        </div>
                        
                        <div class="info-item">
                            <div class="label">Nivel</div>
                            <div class="value">{rutina.get_nivel_display() if rutina else 'N/A'}</div>
                        </div>
                        
                        <div class="info-item full">
                            <div class="label">Descripción</div>
                            <div class="value" style="font-size: 14px; margin-top: 10px; line-height: 1.6;">
                                {rutina.descripcion if rutina else 'Tu rutina personalizada según tu objetivo y nivel de experiencia.'}
                            </div>
                        </div>
                    </div>
                    
                    {contenido_ejercicios}
                    
                    <div class="tips">
                        <h4>💡 Consejos Importantes</h4>
                        <ul>
                            <li><strong>Calentamiento:</strong> Dedica 5-10 minutos antes de entrenar</li>
                            <li><strong>Hidratación:</strong> Bebe agua constantemente durante el entrenamiento</li>
                            <li><strong>Descanso:</strong> Respeta los tiempos de descanso indicados entre series</li>
                            <li><strong>Técnica:</strong> Prioriza la forma correcta sobre el peso levantado</li>
                            <li><strong>Progresión:</strong> Aumenta gradualmente peso o repeticiones cada semana</li>
                            <li><strong>Alimentación:</strong> Mantén una dieta balanceada acorde a tu objetivo</li>
                            <li><strong>Consistencia:</strong> Sigue la rutina sin saltarte sesiones</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>¡Recuerda!</strong> El éxito está en la consistencia y disciplina.</p>
                    <p>Si tienes preguntas sobre tu rutina, no dudes en contactarnos.</p>
                    <p style="margin-top: 15px; border-top: 1px solid #dee2e6; padding-top: 15px;">
                        💪 GYM XTREME - Transformando cuerpos, cambiando vidas 💪
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email = EmailMessage(
            asunto,
            html_content,
            settings.EMAIL_HOST_USER,
            [usuario.email]
        )
        email.content_subtype = "html"
        
        result = email.send(fail_silently=False)
        
        if result > 0:
            logger.info(f"[CORREO] Rutina enviada exitosamente a {usuario.email}")
            return True, f"Rutina personalizada enviada a {usuario.email}"
        return False, "No se pudo enviar la rutina."
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[CORREO] Error al enviar rutina: {error_msg}")
        if "authentication" in error_msg.lower():
            return False, "Error de autenticación del correo."
        elif "connection" in error_msg.lower():
            return False, "No se pudo conectar al servidor de correo."
        return False, f"Error al enviar la rutina: {error_msg}"


# Funciones auxiliares que se importan en otros módulos
def obtener_frase_motivacional():
    """Retorna una frase motivacional aleatoria"""
    frases = [
        "¡Tu cuerpo es el único que tienes, cuídalo!",
        "El progreso es progreso, sin importar lo pequeño que sea.",
        "La consistencia es la clave del éxito.",
        "Tu futuro depende de lo que hagas hoy.",
        "No es cuestión de poder, es cuestión de querer.",
    ]
    return random.choice(frases)


def obtener_objetivo_usuario(usuario):
    """Obtiene el objetivo principal del usuario"""
    try:
        perfil = usuario.perfil
        return perfil.objetivo if hasattr(perfil, 'objetivo') else "No especificado"
    except:
        return "No especificado"


def analizar_progreso(usuario):
    """Analiza el progreso del usuario"""
    try:
        perfil = usuario.perfil
        if hasattr(perfil, 'peso_actual') and hasattr(perfil, 'peso_inicial'):
            diferencia = perfil.peso_inicial - perfil.peso_actual
            return {
                'diferencia': diferencia,
                'porcentaje': (diferencia / perfil.peso_inicial * 100) if perfil.peso_inicial > 0 else 0
            }
    except:
        pass
    return {'diferencia': 0, 'porcentaje': 0}


def obtener_rutina_activa(usuario):
    """Obtiene la rutina activa del usuario"""
    try:
        rutina = Rutina.objects.filter(usuario=usuario, activa=True).first()
        return rutina
    except:
        return None


# Diccionario de nombres de rutinas
NOMBRES_RUTINA = {
    'principiante': 'Rutina para Principiantes',
    'intermedio': 'Rutina Intermedia',
    'avanzado': 'Rutina Avanzada',
    'fuerza': 'Rutina de Fuerza',
    'resistencia': 'Rutina de Resistencia',
    'hipertrofia': 'Rutina de Hipertrofia',
    'cardio': 'Rutina de Cardio',
}
