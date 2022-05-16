"""Main front app"""
from tokenize import group
import streamlit as st
from sqlalchemy.sql import func, text
import pandas as pd
from sqlalchemy import desc
from model.models import Candidat, Region,\
                session, CandidatParti, ResultatCondidatParti, ResultatMetaInfo, UrneVote

@st.experimental_memo
def get_departements():
    """DocString"""
    urne_vote_sql = session.query(Region.department_name)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

@st.experimental_memo
def get_president_national_annee(is_final):
    """Function get_president_national_annee return all meta data related to president national"""
    urne_vote_sql = session\
    .query(
        UrneVote.annee.label('annee'),
        func.sum(ResultatMetaInfo.inscripts).label('total des inscripts'),
        func.sum(ResultatMetaInfo.exprimes).label('total des Éxprimés'),
        func.sum(ResultatMetaInfo.nullparts).label('total des Blancs et nuls'),
        func.sum(ResultatMetaInfo.votants).label('total des Votants'),
    )\
        .filter(UrneVote.is_legis == 0, UrneVote.final_round == is_final)\
        .join(ResultatMetaInfo)\
            .group_by(UrneVote.annee)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

@st.experimental_memo
def get_president_regional_annee(is_final):
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
            .filter(UrneVote.is_legis == 0, UrneVote.final_round == is_final)\
            .group_by(UrneVote.annee, Region.department_name)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

@st.experimental_memo
def get_president_tendance_annee(final):
    urne_vote_sql = session\
    .query(
        UrneVote.annee,
        CandidatParti.courant,
        func.sum(ResultatCondidatParti.value).label('resultat'),
    )\
        .join(ResultatCondidatParti, ResultatCondidatParti.urne_vote_id == UrneVote.id)\
            .join(CandidatParti, CandidatParti.id == ResultatCondidatParti.candidat_parti)\
             .filter(UrneVote.final_round == final, UrneVote.is_legis == 0)\
              .group_by(UrneVote.annee, CandidatParti.courant)         
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

@st.experimental_memo
def get_president_tendance_region_annee(is_final):
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
              .filter(UrneVote.is_legis == 0, UrneVote.final_round == is_final)\
              .group_by(UrneVote.annee, CandidatParti.courant, Region.department_name)
    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

@st.experimental_memo
def get_seuil_per_region():
    sql_statement = """
SELECT
  region.department_code,
  uv.annee uv_annee,
  department_name,
  MIN(
    (
      SELECT
        ROUND((sum(rcc.value) * 100.00 / (
          SELECT
            sum(value)
          FROM
            resultat_candidat rc
            JOIN urne_vote
                ON rc.urne_vote_id = urne_vote.id
                AND urne_vote.annee LIKE uv.annee
                AND urne_vote.region_id = uv.region_id
                AND final_round = 0 AND is_legis = 0
        )), 2)
      FROM
        resultat_candidat rcc
        JOIN urne_vote ON rcc.urne_vote_id = urne_vote.id
            AND annee LIKE uv.annee
            AND region_id = uv.region_id
            AND final_round = 0 AND is_legis = 0
      GROUP BY rcc.candidat_parti
      HAVING rcc.candidat_parti = cp.id
    )
  ) rs
FROM
  resultat_candidat rc
  JOIN urne_vote uv ON rc.urne_vote_id = uv.id
  JOIN candidat_parti cp ON rc.candidat_parti = cp.id
  JOIN candidat ON cp.candidat_id = candidat.id
  JOIN region ON uv.region_id = region.department_code
WHERE
  uv.final_round = 1 AND is_legis = 0
GROUP BY
  department_name,
  uv_annee
    """
    return pd.read_sql(sql = sql_statement, con = session.bind, index_col='department_code')

@st.experimental_memo
def get_candidat_med(is_final, candidat_name):
    urne_vote_sql = session\
    .query(
        UrneVote.annee,
        func.avg(ResultatCondidatParti.value).label('resultat'),
        Region.department_name,
    )\
      .select_from(UrneVote)\
      .join(ResultatCondidatParti, ResultatCondidatParti.urne_vote_id == UrneVote.id)\
        .join(Region, Region.department_code == UrneVote.region_id)\
            .join(CandidatParti)\
                .join(Candidat)\
                 .filter(UrneVote.is_legis == 0, Candidat.candidat_name == candidat_name ,UrneVote.final_round == is_final)\
                     .group_by(Region.department_name)\
                         .order_by(desc(text('resultat')))

    return pd.read_sql(sql = urne_vote_sql.statement, con = session.bind)

couleur_parti = {
            "EDroit": "#0A87C3",
            "DROIT": "#51A8E3",
            "CENTRE": "#c961f2",
            "GAUCHE": "#EA6274",
            "EGAUCHE": "#DB423F",
            'null': "#34eba8",
}

if __name__ == "__main__":
    st.title("Election Presidentielle")
    st.header("TP BDM")
    with st.container():
        st.subheader("Participation National par annee")
        fr_col , se_col = st.columns(2)
        with fr_col:
            st.write('1er Tour')
            df_meta_annee = get_president_national_annee(False)
            df_meta_annee['resultat'] = (
                df_meta_annee['total des Éxprimés'] * 100 / df_meta_annee['total des Votants']
            )
            st.vega_lite_chart(df_meta_annee, {
                    'mark': {'type': 'bar', 'tooltip': True},
                    'encoding': {
                        'y': {'field': 'resultat', "scale": {"domain": [90, 100]}, 'type': 'quantitative'},
                        'x': {'field': 'annee', 'type': 'nominal'},
                        'color': {'field': 'annee', 'type': 'nominal'},
                    },
                    "selection": {
                        "zoom_x": {"type": "interval", "bind": "scales", "encodings": ["x"]},
                    }
                })
            with st.expander("Voir details"):
                st.dataframe(df_meta_annee.set_index('annee'))
        
        with se_col:
            st.write('2eme Tour')
            df_meta_annee = get_president_national_annee(True)
            df_meta_annee['resultat'] = (
                df_meta_annee['total des Éxprimés'] * 100 / df_meta_annee['total des Votants']
            )
            st.vega_lite_chart(df_meta_annee, {
                    'mark': {'type': 'bar', 'tooltip': True},
                    'encoding': {
                        'y': {'field': 'resultat', "scale": {"domain": [90, 100]}, 'type': 'quantitative'},
                        'x': {'field': 'annee', 'type': 'nominal'},
                        'color': {'field': 'annee', 'type': 'nominal'},
                    },
                    "selection": {
                        "zoom_x": {"type": "interval", "bind": "scales", "encodings": ["x"]},
                    }
                })
            with st.expander("Voir details"):
                st.dataframe(df_meta_annee.set_index('annee'))

        st.subheader("Participation Regional par annee")
        fr2_col, sec2_col = st.columns(2)
        with fr2_col:
            st.write('1er tour')
            df_meta = get_president_regional_annee(False)
            df_meta['avg'] = df_meta['total des Éxprimés'] * 100 / df_meta['total des Votants']
            region_name_aggr = st.selectbox(
                'Quel departement ?',
                sorted(set(df_meta['Region'])),
                key="FOASW"
            )
            st_meta_aggr = st.empty()
            df_meta_aggr = (
                    df_meta[df_meta['Region'] == region_name_aggr]
                        .groupby(['annee'], as_index=False)
                        .sum()
                )
            st.vega_lite_chart(df_meta_aggr, {
                'mark': {'type': 'bar', 'tooltip': True},
                "selection": {
                    "zoom_x": {"type": "interval", "bind": "scales", "encodings": ["x"]},
                },
                "encoding": {
                    "x": {"field": "annee", "title": f"Annee dans {region_name_aggr}"},
                    "y": {"field": "avg", "scale": {"domain": [90, 100]}, 
                          "type": "quantitative", "title": "% Participation"},
                    "color": {"field": "annee"}
                }
            })

        with sec2_col:
            st.write('2eme tour')
            df_meta = get_president_regional_annee(True)
            df_meta['avg'] = df_meta['total des Éxprimés'] * 100 / df_meta['total des Votants']
            region_name_aggr = st.selectbox(
                'Quel departement ?',
                sorted(set(df_meta['Region'])),
                key="FOA"
            )
            st_meta_aggr = st.empty()
            df_meta_aggr = (
                    df_meta[df_meta['Region'] == region_name_aggr]
                        .groupby(['annee'], as_index=False)
                        .sum()
                )
            st.vega_lite_chart(df_meta_aggr, {
                'mark': {'type': 'bar', 'tooltip': True},
                "selection": {
                    "zoom_x": {"type": "interval", "bind": "scales", "encodings": ["x"]},
                },
                "encoding": {
                    "x": {"field": "annee", "title": f"Annee dans {region_name_aggr}"},
                    "y": {"field": "avg", "scale": {"domain": [90, 100]}, "type": "quantitative", "title": "% Participation"},
                    "color": {"field": "annee"}
                }
            }, use_container_width=True)



        with st.expander('Voir details'):
            st.dataframe(df_meta)

        st.subheader("Participation des tendances politiques par annee")
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("1er tour"):
                df_tendance = get_president_tendance_annee(False)
                st.dataframe(df_tendance.set_index('annee'))

                st.vega_lite_chart(df_tendance, {
                    'mark': {'type': 'area', 'tooltip': True},
                    'encoding': {
                        'y': {'field': 'resultat', 'type': 'quantitative'},
                        'x': {'field': 'annee', 'type': 'nominal'},
                        'color': {'field': 'courant', 'type': 'nominal', "scale": {
                            "domain": list(couleur_parti.keys()),
                            "range": list(couleur_parti.values()),
                        }},
                    },
                })
        with col2:
            with st.expander("2eme tour"):
                df_tendance = get_president_tendance_annee(True)
                st.vega_lite_chart(df_tendance, {
                    'mark': {'type': 'area', 'tooltip': True},
                    'encoding': {
                        'y': {'field': 'resultat', 'type': 'quantitative'},
                        'x': {'field': 'annee', 'type': 'nominal'},
                        'color': {'field': 'courant', 'type': 'nominal', "scale": {
                            "domain": list(couleur_parti.keys()),
                            "range": list(couleur_parti.values()),
                        }},
                    },
                })

        st.subheader("Participation des tendances politiques par annee et regions")
        region_list = get_departements()
        region_name = st.selectbox(
                'Quel departement ?',
                sorted(set(region_list['department_name'])),
                key="TESTCOL1"
            )
        
        fr3_col, sec3_col = st.columns(2)
        with st.form('DD'):
            submitted = st.form_submit_button("Soumettre")
            if submitted:
                with fr3_col:
                    df_president_tendance_region_annee = get_president_tendance_region_annee(False)
                    df_ptra_by_region = (
                        df_president_tendance_region_annee
                            [df_president_tendance_region_annee['Region'] == region_name]
                            .groupby(['annee', 'courant'], sort=False, as_index=False)
                            .sum()
                    ) 
                    st.vega_lite_chart(df_ptra_by_region, {
                        'mark': {'type': 'bar', 'tooltip': True},
                        "encoding": {
                            "x": {"field": "annee"},
                            "y": {"field": "resultat", "type": "quantitative"},
                            "xOffset": {"field": "courant"},
                            "color": {"field": "courant"}
                        }
                    })

                    with st.expander("Voir details"):
                        st.dataframe(df_president_tendance_region_annee.set_index('annee'))
                
                with sec3_col:
                    df_president_tendance_region_annee2 = get_president_tendance_region_annee(True)

                    df_ptra_by_region2 = (
                        df_president_tendance_region_annee2
                            [df_president_tendance_region_annee['Region'] == region_name]
                            .groupby(['annee', 'courant'], sort=False, as_index=False)
                            .sum()
                    )

                    st.vega_lite_chart(df_ptra_by_region2, {
                            'mark': {'type': 'bar', 'tooltip': True},
                            "encoding": {
                                "x": {"field": "annee"},
                                "y": {"field": "resultat", "type": "quantitative"},
                                "xOffset": {"field": "courant"},
                                "color": {"field": "courant"}
                            }
                        })
                    with st.expander("Voir details"):
                        st.dataframe(df_ptra_by_region2.set_index('annee'))
        
        
        st.subheader("Seuil moyen par regions")
        with st.spinner("Loading"):
            df = get_seuil_per_region()

        st.vega_lite_chart(df, {
                    'mark': {'type': 'circle', 'tooltip': True},
                    'encoding': {
                        'y': {'field': 'department_name', 'type': 'nominal'},
                        'x': {'field': 'uv_annee', 'type': 'nominal'},
                        'size': {'field': 'rs', 'type': 'quantitative'},
                        'color': {'field': 'rs', 'type': 'quantitative'},
                    },
                })
        with st.expander('Voir detail'):
            st.dataframe(df)

        st.subheader("Resultat de LAGUILLER par region")
        df_ki = get_candidat_med(False, 'LAGUILLER')
        st.dataframe(df_ki)
