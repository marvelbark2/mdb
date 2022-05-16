"""Main front app"""
import streamlit as st
from sqlalchemy.sql import func
import pandas as pd
from model.models import Region,\
                session, CandidatParti, ResultatCondidatParti, ResultatMetaInfo, UrneVote

def get_president_national_annee():
    """Function get_president_national_annee return all meta data related to president national"""
    urne_vote_sql = session\
    .query(
        UrneVote.annee.label('annee'),
        func.sum(ResultatMetaInfo.inscripts).label('total des inscripts'),
        func.sum(ResultatMetaInfo.exprimes).label('total des Éxprimés'),
        func.sum(ResultatMetaInfo.nullparts).label('total des Blancs et nuls'),
        func.sum(ResultatMetaInfo.votants).label('total des Votants'),
    )\
        .join(ResultatMetaInfo)\
            .group_by(UrneVote.annee)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

def get_president_regional_annee():
    urne_vote_sql = session\
    .query(
        UrneVote.annee,
        Region.department_name.label('Region'),
        func.sum(ResultatMetaInfo.inscripts).label('total des inscripts'),
        func.sum(ResultatMetaInfo.exprimes).label('total des Éxprimés'),
        func.sum(ResultatMetaInfo.nullparts).label('total des Blancs et nuls'),
        func.sum(ResultatMetaInfo.votants).label('total des Votants'),
    )\
        .join(Region, Region.department_code == UrneVote.region_id)\
        .join(ResultatMetaInfo)\
            .group_by(UrneVote.annee, Region.department_name)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind, index_col='annee')

def get_president_tendance_annee(final):
    urne_vote_sql = session\
    .query(
        UrneVote.annee,
        CandidatParti.courant,
        func.sum(ResultatCondidatParti.value).label('resultat'),
    )\
        .join(ResultatCondidatParti, ResultatCondidatParti.urne_vote_id == UrneVote.id)\
            .join(CandidatParti, CandidatParti.id == ResultatCondidatParti.candidat_parti)\
             .filter(UrneVote.final_round == final)\
              .group_by(UrneVote.annee, CandidatParti.courant)         
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

def get_president_tendance_region_annee():
    urne_vote_sql = session\
    .query(
        UrneVote.annee,
        Region.department_name.label('Region'),
        CandidatParti.courant,
        func.sum(ResultatCondidatParti.value).label('resultat'),
    )\
        .join(Region, Region.department_code == UrneVote.region_id)\
            .join(ResultatCondidatParti, ResultatCondidatParti.urne_vote_id == UrneVote.id)\
             .join(CandidatParti, CandidatParti.id == ResultatCondidatParti.candidat_parti)\
              .group_by(UrneVote.annee, CandidatParti.courant, Region.department_name)    
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind, index_col='annee')

def get_seuil_per_region():
    sql_statement = """
-- 14 mai 2022 8:33:55 PM
SELECT
  region.department_code,
  uv.annee uv_annee,
  department_name,
  MIN(
    (
      SELECT
        sum(rcc.value) * 100.00 / (
          SELECT
            sum(value)
          FROM
            resultat_candidat rc
            JOIN urne_vote ON rc.urne_vote_id = urne_vote.id
          WHERE
            annee LIKE uv.annee
            AND region_id = uv.region_id
            AND final_round = 0
        )
      FROM
        resultat_candidat rcc
        JOIN urne_vote ON rcc.urne_vote_id = urne_vote.id
      WHERE
        rcc.candidat_parti = cp.id
        AND annee LIKE uv.annee
        AND region_id = uv.region_id
        AND final_round = 0
    )
  ) rs
FROM
  resultat_candidat rc
  JOIN urne_vote uv ON rc.urne_vote_id = uv.id
  JOIN candidat_parti cp ON rc.candidat_parti = cp.id
  JOIN candidat ON cp.candidat_id = candidat.id
  JOIN region ON uv.region_id = region.department_code
WHERE
  uv.final_round = 1
GROUP BY
  department_name,
  uv_annee
    """
    return pd.read_sql(sql = sql_statement, con = session.bind, index_col='department_code')

couleur_parti = {
            "EDroit": "#0A87C3",
            "DROIT": "#51A8E3",
            "CENTRE": "#3E3E3E",
            "GAUCHE": "#EA6274",
            "EGAUCHE": "#DB423F",
            'null': "",
}

if __name__ == "__main__":
    st.title("Election Presidentielle")
    st.header("TP BDM")

    with st.container():
        st.subheader("Participation National par annee")
        df_meta_annee = get_president_national_annee()
        df_meta_annee['resultat'] = df_meta_annee['total des Éxprimés'] * 100 / df_meta_annee['total des Votants']
        st.dataframe(df_meta_annee.set_index('annee'))
        st.vega_lite_chart(df_meta_annee, {
                'mark': {'type': 'bar'},
                'encoding': {
                    'y': {'field': 'resultat', 'type': 'quantitative'},
                    'x': {'field': 'annee', 'type': 'nominal'},
                    'color': {'field': 'annee', 'type': 'nominal'},
                },
            }, width=600)


        st.subheader("Participation Regional par annee")
        df_meta = get_president_regional_annee()
        df_meta['avg'] = df_meta['total des Éxprimés'] * 100 / df_meta['total des Votants']
        st.dataframe(df_meta)

        st.subheader("Participation des tendances politiques par annee")

        with st.expander("1er tour"):
            df_tendance = get_president_tendance_annee(False)
            st.dataframe(df_tendance.set_index('annee'))

            st.vega_lite_chart(df_tendance, {
                'mark': {'type': 'area'},
                'encoding': {
                    'y': {'field': 'resultat', 'type': 'quantitative'},
                    'x': {'field': 'annee', 'type': 'nominal'},
                    'color': {'field': 'courant', 'type': 'nominal', "scale": {
                        "domain": list(couleur_parti.keys()),
                        "range": list(couleur_parti.values()),
                    }},
                },
            }, width=600)

        with st.expander("2eme tour"):
            df_tendance = get_president_tendance_annee(True)
            st.dataframe(df_tendance.set_index('annee'))

            st.vega_lite_chart(df_tendance, {
                'mark': {'type': 'area'},
                'encoding': {
                    'y': {'field': 'resultat', 'type': 'quantitative'},
                    'x': {'field': 'annee', 'type': 'nominal'},
                    'color': {'field': 'courant', 'type': 'nominal', "scale": {
                        "domain": list(couleur_parti.keys()),
                        "range": list(couleur_parti.values()),
                    }},
                },
            }, width=600)

        st.subheader("Participation des tendances politiques par annee et regions")
        st.dataframe(get_president_tendance_region_annee())

        st.subheader("Seuil moyen par regions")
        with st.spinner("Loading"):
            df = get_seuil_per_region()

        st.dataframe(df)

        st.vega_lite_chart(df, {
            'mark': {'type': 'circle', 'tooltip': True},
            'encoding': {
                'y': {'field': 'department_name', 'type': 'nominal'},
                'x': {'field': 'uv_annee', 'type': 'nominal'},
                'size': {'field': 'rs', 'type': 'quantitative'},
                'color': {'field': 'rs', 'type': 'quantitative'},
            },
        })
