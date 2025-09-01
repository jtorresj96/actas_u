from pdf_extractor import extract_text_pdf
import os, streamlit as st
from openai_transcription import transcribe_to_docx, TranscriptionConfig
from core import db
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_html_email(to_email, subject, html_content, docx_path=None):
    # Credenciales (mejor si las lees de variables de entorno)
    email_address = "j.torresj96@falconcol.com"
    email_password = "zyrl gojq ltcz srty"  # Contraseña de aplicación

    # Armar mensaje
    msg = MIMEMultipart()
    msg["From"] = email_address      # si quieres: 'DocuIA <j.torresj96@falconcol.com>'
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # Adjuntar .docx (opcional)
    if docx_path and os.path.isfile(docx_path):
        with open(docx_path, "rb") as f:
            part = MIMEApplication(
                f.read(),
                _subtype="vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        part.add_header("Content-Disposition", "attachment", filename=os.path.basename(docx_path))
        msg.attach(part)

    # Enviar
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, to_email, msg.as_string())
        print("Correo enviado exitosamente.")
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False





def process_audio(file,id,email):
    """Procesa un archivo de audio usando la función de transcripción de OpenAI."""
    os.environ["OPENAI_API_KEY"] = "sk-proj-CjQkWMjZvol64oYpyyB8T3BlbkFJeOUgIl5INMIFljg3KeZg"  # o config.openai_api_key

    cfg = TranscriptionConfig(
        chunk_minutes=10,
        overlap_seconds=2,
        amplify_db=6,
        force_language="es",           # None para autodetect
        export_mp3=True,               # para evitar 413
        model="whisper-1",             # cambia si usas otro
        include_timestamps=False,      # salida sin timestamps
    )

    out_path, blocks, duration = transcribe_to_docx(
        audio_file = file,
        output_docx=f"outputs/{id}_acta.docx",
        config=cfg,
    )

    print("DOCX:", out_path, "Bloques:", blocks)
    db.update_document_status(id, "completado", out_path, duration)
    html_content = f"""
<!-- Preheader (texto de vista previa en bandeja) -->
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
  ¡Acta lista! La transcripción de {file} quedó brutal. Tu acta está fresquita para compartir. 🚀
</div>

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f8ff;padding:24px 12px;">
  <tr>
    <td align="center">
      <table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0" style="max-width:640px;background:#ffffff;border:1px solid #e6eefb;border-radius:16px;overflow:hidden;font-family:Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;">
        <!-- Header azul -->
        <tr>
          <td style="padding:22px 24px;background:#1d4ed8;color:#ffffff;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
              <tr>
                <td width="44" valign="top" style="padding-right:12px;">
                  <div style="width:40px;height:40px;line-height:40px;text-align:center;background:#ffffff22;border-radius:50%;font-weight:800;">✔</div>
                </td>
                <td>
                  <h1 style="margin:0;font-size:22px;line-height:1.25;">¡Acta lista! 🎉</h1>
                  <p style="margin:6px 0 0;opacity:.95;">
                    La transcripción de <strong>{file}</strong> quedó <span style="font-weight:700;">brutal</span>. Tu acta está fresquita para compartir 🚀
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Cuerpo -->
        <tr>
          <td style="padding:18px 24px;">
            <!-- Tarjeta de datos -->
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px dashed #dbe7ff;background:#f8fbff;border-radius:12px;">
              <tr>
                <td style="padding:14px;">
                  <div style="margin:6px 0;">
                    <span style="display:inline-block;min-width:96px;padding:4px 8px;border-radius:999px;background:#e5efff;color:#1e40af;font-weight:700;font-size:12px;">Archivo</span>
                    <span style="font-weight:600;">{file}</span>
                  </div>
                  <div style="margin:6px 0;">
                    <span style="display:inline-block;min-width:96px;padding:4px 8px;border-radius:999px;background:#e5efff;color:#1e40af;font-weight:700;font-size:12px;">Estado</span>
                    <span style="font-weight:700;color:#059669;">Completado ✅</span>
                  </div>
                </td>
              </tr>
            </table>

            <!-- Espacio -->
            <div style="height:14px;line-height:14px;">&nbsp;</div>
            <!-- Nota -->
            <p style="margin:16px 0 0;font-size:13px;color:#334155;">
              Échale un ojo a los puntos, decisiones y compromisos. ¿Quieres ajustes? ¡Regenera el acta y pa’ delante! ✨
            </p>
          </td>
        </tr>

        <!-- Footer clarito -->
        <tr>
          <td style="padding:14px 24px;background:#f8fbff;color:#496581;font-size:12px;text-align:center;border-top:1px solid #e6eefb;">
            Hecho con 💙 para que tu equipo siga en sintonía.
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

    """

    send_html_email(
        to_email=email,
        subject="Acta generada",
        html_content=html_content,
        docx_path=out_path
    )

    return out_path, duration


def process_pdf(file):
    """Procesa un archivo PDF extrayendo su texto."""
    return extract_text_pdf(file)


def process_txt(file):
    """Procesa un archivo de texto decodificándolo a UTF-8."""
    return file.read().decode('utf-8')





