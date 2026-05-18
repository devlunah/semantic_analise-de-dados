# rode no terminal: streamlit run app.py ─────────────────────────────

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title='Mercado de TI — CAGED', page_icon='💻', layout='wide')

@st.cache_data
def carregar_dados():
    df = pd.read_csv('caged_ti_br_2023_2025.csv', sep=';')
    instrucao_map = {
        1: 'Analfabeto',
        2: 'Até 5ª incompleto',
        3: '5ª Completo Fundamental',
        4: '6ª a 9ª Fundamental',
        5: 'Fundamental completo',
        6: 'Médio incompleto',
        7: 'Médio completo',
        8: 'Superior incompleto',
        9: 'Superior completo',
        80: 'Pós-Graduação Completa',
        10: 'Mestrado',
        11: 'Doutorado',
        99: 'Não identificado'
    }
    df['instrucao_label'] = df['grau_instrucao'].map(instrucao_map)
    df['sexo_label'] = df['sexo'].map({1:'Masculino', 3:'Feminino'})
    df['tipo'] = df['saldo_movimentacao'].map({1:'Admissão', -1:'Desligamento'})
    return df[df['tipo'] == 'Admissão']

df = carregar_dados()

st.title('Mercado de TI Formal no Brasil')
st.markdown('Dados do **Novo CAGED** — Ministério do Trabalho e Emprego')
st.divider()

# Filtros na sidebar
st.sidebar.header('Filtros')
sexo_sel = st.sidebar.multiselect('Gênero:', ['Masculino', 'Feminino'],
                                   default=['Masculino', 'Feminino'])
faixa = st.sidebar.slider('Faixa salarial (R$):', 0, 30000, (0, 15000))
anos_disponiveis = sorted(df['ano'].unique())
ano_sel = st.sidebar.multiselect('Ano:', anos_disponiveis, default=anos_disponiveis)

filtrado = df[
    df['sexo_label'].isin(sexo_sel) &
    df['ano'].isin(ano_sel) &
    df['salario_mensal'].between(faixa[0], faixa[1])
]

# Métricas
c1, c2, c3 = st.columns(3)
c1.metric('Total de Admissões', f'{len(filtrado):,}')
c2.metric('Salário Mediano', f"R$ {filtrado['salario_mensal'].median():,.0f}")
c3.metric('Salário Médio', f"R$ {filtrado['salario_mensal'].mean():,.0f}")
st.divider()

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader('Salário Mediano por Escolaridade')
    ordem = filtrado.groupby('instrucao_label')['salario_mensal'].median().sort_values().index
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(data=filtrado, y='instrucao_label', x='salario_mensal', hue='sexo_label', 
                order=ordem, estimator='median', palette={'Masculino': '#2E86C1', 'Feminino': '#E74C3C'}, ax=ax)
    ax.set_xlabel('R$'); ax.set_ylabel('')
    sns.despine(); st.pyplot(fig); plt.close()

with col2:
    st.subheader('Salário Mediano por Gênero')
    
    medians = filtrado.groupby('sexo_label')['salario_mensal'].median().reset_index()
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(
        data=medians,
        x='sexo_label',
        y='salario_mensal',
        palette={'Masculino': '#2E86C1', 'Feminino': '#E74C3C'},
        ax=ax
    )
    for bar in ax.patches:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 50,
            f"R$ {bar.get_height():,.0f}",
            ha='center', va='bottom', fontsize=12, fontweight='bold'
        )
    ax.set_xlabel('')
    ax.set_ylabel('Salário Mediano (R$)')
    sns.despine()
    st.pyplot(fig)
    plt.close()

with st.expander('Ver dados brutos'):
    st.dataframe(filtrado.head(500))
