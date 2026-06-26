"""Page « Charger un fichier » : modèle de saisie, import validé, mise à jour."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config
from src.data_validation import (
    COLONNES_ATTENDUES,
    lire_et_valider,
    modele_csv,
    modele_xlsx,
)


def render(panel, P, epi, alerte):
    st.header("Charger un fichier")
    districts = sorted(panel["district"].unique())

    # --- Modèle de saisie (template) ---
    st.subheader("1. Télécharger le modèle de saisie")
    st.caption(
        "Format attendu : "
        "`district, date, temp_moy, temp_max, humidite, precip_mensuel, cas`. "
        f"Les {len(districts)} districts sont pré-remplis ; complétez les valeurs."
    )
    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Modèle Excel (.xlsx)",
        data=modele_xlsx(districts),
        file_name="modele_saisie_palualert.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    c2.download_button(
        "⬇️ Modèle CSV (.csv)",
        data=modele_csv(districts),
        file_name="modele_saisie_palualert.csv",
        mime="text/csv",
    )

    # --- Import + validation ---
    st.subheader("2. Importer un fichier rempli")
    fichier = st.file_uploader(
        "Choisir un fichier Excel ou CSV", type=["xls", "xlsx", "csv"]
    )

    if fichier is not None:
        df_new, erreurs, avert = lire_et_valider(fichier, districts)
        for a in avert:
            st.warning(a)
        if erreurs:
            st.error("Le fichier ne peut pas être intégré :")
            for e in erreurs:
                st.write("• " + e)
        elif df_new is not None:
            st.success(
                f"Fichier valide : {len(df_new)} lignes, "
                f"{df_new['district'].nunique()} districts."
            )
            st.dataframe(df_new.head(10), width="stretch", hide_index=True)
            if st.button("Ajouter au panel et recalculer"):
                fusion = pd.concat(
                    [panel[COLONNES_ATTENDUES], df_new], ignore_index=True
                )
                fusion = fusion.drop_duplicates(
                    subset=["district", "date"], keep="last"
                ).sort_values(["district", "date"])
                fusion.to_csv(config.PANEL_PATH, index=False)
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("Panel mis à jour. L'application se recharge…")
                st.rerun()

        st.info(
            "ℹ️ En ligne (Streamlit Cloud), la mise à jour est **temporaire** : "
            "le système de fichiers est réinitialisé aux redémarrages. Pour une "
            "mise à jour permanente, modifiez le CSV dans le dépôt GitHub."
        )

    # --- Diagnostic du panel courant ---
    st.subheader("Informations sur les données")
    manq = int(panel.isna().sum().sum())
    info = pd.DataFrame(
        {
            "Indicateur": [
                "Colonnes", "Lignes", "Valeurs manquantes", "Valeurs non manquantes",
            ],
            "Valeur": [
                panel.shape[1], panel.shape[0], manq, int(panel.size - manq),
            ],
        }
    )
    fig = go.Figure(
        go.Bar(
            x=info["Indicateur"], y=info["Valeur"], text=info["Valeur"],
            textposition="outside",
            marker_color=["#1f6fb2", "#5a9bd4", "#d62728", "#2ca02c"],
        )
    )
    fig.update_layout(
        height=380, yaxis_title="Valeur", margin=dict(l=10, r=10, t=20, b=10)
    )
    st.plotly_chart(fig, width="stretch")
