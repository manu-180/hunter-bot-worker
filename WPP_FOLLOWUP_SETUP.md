# Configuracion del WPP Follow-up (Hunter Bot)

## Que es?

Despues de que el Hunter Bot envia un email exitosamente a un contacto, si durante
el scraping del sitio web se encontro un numero de WhatsApp, el bot envia
automaticamente un mensaje de WhatsApp informando que acaba de llegar un correo.

## Variables de entorno requeridas (Railway / .env)

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_api_key_secret
HUNTER_FROM_WPP_NUMBER=whatsapp:+5491125303794
WPP_FOLLOWUP_SID_0=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WPP_FOLLOWUP_SID_1=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WPP_FOLLOWUP_SID_2=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WPP_FOLLOWUP_SID_3=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WPP_FOLLOWUP_SID_4=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

## Migracion Supabase SQL

ALTER TABLE leads ADD COLUMN IF NOT EXISTS wpp_number TEXT DEFAULT NULL;
(ver: sql/add_wpp_number_to_leads.sql)

## Templates sugeridos para Twilio Content Templates (variable {{1}} = nombre empresa)

SID_0: "Hola {{1}}! Les acabo de enviar un correo con informacion sobre como potenciar su presencia digital. Cualquier consulta, estoy disponible por aqui."
SID_1: "Hola {{1}}, recien les enviamos un email con una propuesta para su negocio. Si prefieren coordinar por WhatsApp, estamos a disposicion!"
SID_2: "Buenas {{1}}! Les mande un correo detallando como podemos ayudar a su negocio online. Por si no llego, puede estar en spam. Cualquier duda estamos por aca!"
SID_3: "Hola {{1}}! Les enviamos un mail con detalles sobre nuestros servicios. Si tienen un momento para charlar, con gusto les cuento mas por aca!"
SID_4: "Que tal {{1}}! Justo les deje un email con informacion relevante para su negocio. Si prefieren coordinar por aqui, avisa y lo hacemos!"

## Comportamiento

- Solo se envia si el scraper encontro un numero de WPP en el sitio web del lead
- Los templates rotan automaticamente para evitar deteccion de spam
- Si falla el WPP, el email igual queda como "sent" (no afecta el flujo)
- El numero de WPP se guarda en la columna wpp_number de la tabla leads
- Los envios aparecen en los logs con accion wpp_followup_sent
