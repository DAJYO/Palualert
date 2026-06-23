"""
Génération du rapport épidémique au format PDF (via fpdf2).

Le PDF reprend, pour un district et une année :
  - un en-tête (titre, région, date de génération) ;
  - une synthèse (mois en alerte / épidémie, pic prévu) ;
  - la courbe épidémique (image PNG rendue par kaleido) ;
  - le tableau épidémique mensuel, lignes colorées par niveau de risque.

Les polices cœur de fpdf2 sont en Latin-1 : `_latin1` neutralise les
caractères hors de ce jeu (tirets longs, points médians, etc.).
"""

from datetime import date
from io import BytesIO

from fpdf import FPDF

from src import config

# Couleurs (R, G, B) par niveau, dérivées de la config
_HEX = {
    "Épidémie": config.COULEUR_EPIDEMIE,
    "Alerte": config.COULEUR_ALERTE,
    "Normal": config.COULEUR_NORMAL,
    "—": config.COULEUR_INCONNU,
}


def _rgb(hexa):
    h = hexa.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


_REMPL = {"—": "-", "–": "-", "·": "-", "’": "'", "œ": "oe", "→": "->"}


def _latin1(texte):
    """Rend une chaîne sûre pour les polices cœur Latin-1 de fpdf2."""
    s = str(texte)
    for k, v in _REMPL.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


def _image_figure(fig):
    """Convertit une figure Plotly en PNG (bytes) ou None si indisponible."""
    try:
        return fig.to_image(format="png", width=1000, height=520, scale=2)
    except Exception:
        return None


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120)
        self.cell(0, 6, _latin1("Surveillance Palustre - Region de l'Extreme-Nord"),
                  align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120)
        self.cell(0, 6, _latin1(
            "Source : geoBoundaries (ADM3) - Prototype memoire ENSPM Maroua"),
            align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R")
        self.set_text_color(0)


def generer_pdf_rapport(district, annee, fig, tableau, resume):
    """Construit le PDF et retourne ses octets.

    `tableau` : DataFrame avec colonnes
        [Mois, Prédiction, Seuil d'alerte, Seuil épidémique, Niveau].
    `resume`  : liste de couples (libellé, valeur).
    """
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Titre
    pdf.set_font("Helvetica", "B", 17)
    pdf.cell(0, 10, _latin1(f"Rapport epidemique - {district} ({annee})"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110)
    pdf.cell(0, 6, _latin1(f"Genere le {date.today():%d/%m/%Y}"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    pdf.ln(3)

    # Synthèse
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Synthese", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for libelle, valeur in resume:
        pdf.cell(70, 7, _latin1(f"  {libelle}"))
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _latin1(str(valeur)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)

    # Courbe épidémique
    png = _image_figure(fig)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Courbe epidemique", new_x="LMARGIN", new_y="NEXT")
    if png:
        pdf.image(BytesIO(png), w=pdf.epw)  # epw = largeur utile de page
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(150)
        pdf.cell(0, 7, _latin1(
            "[Graphique indisponible : kaleido/Chrome requis]"),
            new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0)
    pdf.ln(3)

    # Tableau
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Tableau epidemique", new_x="LMARGIN", new_y="NEXT")

    colonnes = list(tableau.columns)
    largeurs = [22, 38, 38, 42, 0]  # la dernière colonne prend le reste
    largeurs[-1] = pdf.epw - sum(largeurs[:-1])

    # En-tête de tableau
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230)
    for nom, larg in zip(colonnes, largeurs):
        pdf.cell(larg, 8, _latin1(nom), border=1, align="C", fill=True)
    pdf.ln()

    # Lignes
    pdf.set_font("Helvetica", "", 10)
    for _, ligne in tableau.iterrows():
        niveau = str(ligne[colonnes[-1]])
        r, g, b = _rgb(_HEX.get(niveau, config.COULEUR_INCONNU))
        for nom, larg in zip(colonnes, largeurs):
            val = ligne[nom]
            if isinstance(val, float):
                val = "-" if val != val else f"{val:.0f}"  # val != val => NaN
            if nom == colonnes[-1]:
                pdf.set_fill_color(r, g, b)
                pdf.set_text_color(255)
                pdf.cell(larg, 7, _latin1(val), border=1, align="C", fill=True)
                pdf.set_text_color(0)
            else:
                pdf.cell(larg, 7, _latin1(val), border=1, align="C")
        pdf.ln()

    return bytes(pdf.output())
