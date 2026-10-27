# Página para VER la base de datos como cuadros (una tabla por modelo).
# Abre http://127.0.0.1:8000/base-de-datos mientras haces POST en /docs y se va llenando.
from html import escape

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Actividad, Contrato, Corte

router = APIRouter(tags=["Ver base de datos"])


def tabla(titulo: str, modelo, session: Session) -> str:
    columnas = ["id"] + [c for c in modelo.model_fields.keys() if c != "id"]  # el id primero
    filas = session.exec(select(modelo)).all()
    html = f"<h2>{titulo} ({len(filas)} registros)</h2><table><tr>"
    html += "".join(f"<th>{c}</th>" for c in columnas) + "</tr>"
    for fila in filas:
        clase = "" if fila.activo else ' class="inactivo"'
        html += f"<tr{clase}>" + "".join(f"<td>{escape(str(getattr(fila, c)))}</td>" for c in columnas) + "</tr>"
    if not filas:
        html += f'<tr><td colspan="{len(columnas)}">Sin datos todavía</td></tr>'
    return html + "</table>"


@router.get("/base-de-datos", response_class=HTMLResponse)
def ver_base_de_datos(session: Session = Depends(get_session)):
    estilo = """<style>
      body{font-family:Arial;margin:24px} table{border-collapse:collapse;margin-bottom:20px}
      th,td{border:1px solid #999;padding:6px 10px} th{background:#1f3864;color:white}
      .inactivo{background:#eee;color:#888;text-decoration:line-through}
    </style>"""
    cuerpo = ("<h1>Base de datos: control.db</h1>"
              "<p>Se actualiza sola cada 5 segundos. Las filas tachadas están inactivas (histórico).</p>"
              + tabla("Tabla contrato", Contrato, session)
              + tabla("Tabla actividad", Actividad, session)
              + tabla("Tabla corte", Corte, session))
    return f'<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="5">{estilo}</head><body>{cuerpo}</body></html>'
