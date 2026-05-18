import basedosdados as bd
import pandas as pd
from datetime import datetime
import os
 
# =============================================================================
# CONFIGURAÇÕES — EDITE AQUI
# =============================================================================
 
BILLING_PROJECT_ID = "analise-de-dados-semantic"   # <-- substitua pelo ID do seu projeto GCP
ANO_INICIO        = 2023
ANO_FIM           = 2025
PASTA_SAIDA       = "."                   # pasta onde os CSVs serão salvos
 
# =============================================================================
# CBOs DE TECNOLOGIA DA INFORMAÇÃO
# =============================================================================
#
# Estrutura do CBO no CAGED: 6 dígitos sem hífen (ex: "212405")
# Agrupamos por família (primeiros 4 dígitos) para cobrir todas as variantes.
#
# Família 2123 — Profissionais em pesquisa e desenvolvimento de TI
#   212305  Administrador de banco de dados
#   212310  Administrador de redes
#   212315  Administrador de sistemas operacionais
#   212320  Engenheiro de software
#
# Família 2124 — Analistas de TI (nível superior)
#   212405  Analista de desenvolvimento de sistemas
#   212410  Analista de redes e de comunicação de dados
#   212415  Analista de sistemas de automação
#   212420  Analista de suporte computacional
#
# Família 3171 — Técnicos de desenvolvimento de sistemas (nível técnico)
#   317105  Programador de internet
#   317110  Desenvolvedor de sistemas (técnico)
#   317115  Programador de multimídia
#   317120  Programador de sistemas de informação
#   317125  Programador de máquinas-ferramenta com CNC
#
# Família 3172 — Técnicos de suporte de TI (nível técnico)
#   317205  Técnico de suporte ao usuário de TI
#   317210  Operador de computador
#   317215  Técnico em manutenção de equipamentos de informática
#
# Família 2321 — Instrutores/professores de TI (bônus para análise)
#   232120  Instrutor de cursos livres (informática)
#
 
CBOS_TI = [
    # ── Nível superior — Analistas e Engenheiros ────────────────────────────
    "212305",  # Administrador de banco de dados
    "212310",  # Administrador de redes
    "212315",  # Administrador de sistemas operacionais
    "212320",  # Engenheiro de software
    "212405",  # Analista de desenvolvimento de sistemas
    "212410",  # Analista de redes e de comunicação de dados
    "212415",  # Analista de sistemas de automação
    "212420",  # Analista de suporte computacional
 
    # ── Nível técnico — Programadores e Desenvolvedores ─────────────────────
    "317105",  # Programador de internet
    "317110",  # Desenvolvedor de sistemas de TI (técnico)
    "317115",  # Programador de multimídia
    "317120",  # Programador de sistemas de informação
    "317125",  # Programador de máquinas-ferramenta CNC
 
    # ── Nível técnico — Suporte e Infraestrutura ────────────────────────────
    "317205",  # Técnico de suporte ao usuário de TI
    "317210",  # Operador de computador
    "317215",  # Técnico em manutenção de equipamentos de informática
]
 
# Formata como string SQL para usar no IN (...)
CBOS_SQL = ", ".join(f"'{c}'" for c in CBOS_TI)
 
# =============================================================================
# QUERY — ACRE (arquivo principal do minicurso)
# =============================================================================
 
QUERY_ACRE = f"""
SELECT
    -- Identificação temporal
    ano,
    mes,
 
    -- Localização
    sigla_uf,
    id_municipio,
 
    -- Movimentação
    saldo_movimentacao,          -- 1 = admissão, -1 = desligamento
    tipo_movimentacao,           -- descrição textual
 
    -- Ocupação e setor
    cbo_2002,                    -- código da ocupação (6 dígitos)
    cnae_2_subclasse,            -- setor econômico
 
    -- Perfil do trabalhador (dados brutos, sem tratamento intencional)
    salario_mensal,
    grau_instrucao,              -- código numérico (1–11)
    sexo,                        -- código numérico (1 = M, 3 = F)
    idade,
    raca_cor,                    -- código numérico
    horas_contratuais
 
FROM `basedosdados.br_me_caged.microdados_movimentacao`
 
WHERE
    ano BETWEEN {ANO_INICIO} AND {ANO_FIM}
    AND sigla_uf = 'AC'
    AND cbo_2002 IN ({CBOS_SQL})
    AND salario_mensal IS NOT NULL
    AND salario_mensal > 0
 
ORDER BY
    ano, mes
"""
 
# =============================================================================
# QUERY — BRASIL COMPLETO (para análise comparativa em aula)
# =============================================================================
 
QUERY_BRASIL = f"""
SELECT
    ano,
    mes,
    sigla_uf,
    id_municipio,
    saldo_movimentacao,
    tipo_movimentacao,
    cbo_2002,
    cnae_2_subclasse,
    salario_mensal,
    grau_instrucao,
    sexo,
    idade,
    raca_cor,
    horas_contratuais
 
FROM `basedosdados.br_me_caged.microdados_movimentacao`
 
WHERE
    ano BETWEEN {ANO_INICIO} AND {ANO_FIM}
    AND cbo_2002 IN ({CBOS_SQL})
    AND salario_mensal IS NOT NULL
    AND salario_mensal > 0
 
ORDER BY
    ano, mes, sigla_uf
"""
 
 
# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
 
def extrair(query: str, descricao: str) -> pd.DataFrame:
    """Executa a query na Base dos Dados e retorna um DataFrame."""
    print(f"\n{'='*60}")
    print(f"  Extraindo: {descricao}")
    print(f"{'='*60}")
    print(f"  Período : {ANO_INICIO}–{ANO_FIM}")
    print(f"  CBOs    : {len(CBOS_TI)} ocupações de TI")
    print(f"  Aguarde — pode levar alguns minutos...\n")
 
    df = bd.read_sql(query, billing_project_id=BILLING_PROJECT_ID)
 
    print(f"  ✅ Extração concluída!")
    print(f"     Linhas     : {len(df):,}")
    print(f"     Colunas    : {df.shape[1]}")
    print(f"     Memória    : {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    return df
 
 
def salvar(df: pd.DataFrame, nome_arquivo: str) -> str:
    """Salva o DataFrame como CSV e retorna o caminho."""
    caminho = os.path.join(PASTA_SAIDA, nome_arquivo)
    df.to_csv(caminho, sep=";", encoding="utf-8", index=False)
    tamanho_mb = os.path.getsize(caminho) / 1024**2
    print(f"\n  💾 Salvo em  : {caminho}")
    print(f"     Tamanho   : {tamanho_mb:.1f} MB")
    return caminho
 
 
def resumo(df: pd.DataFrame, label: str):
    """Imprime estatísticas básicas para conferência."""
    print(f"\n  📊 Resumo — {label}")
    print(f"     Linhas                : {len(df):,}")
    print(f"     Período               : {df['ano'].min()} a {df['ano'].max()}")
 
    if "sigla_uf" in df.columns:
        ufs = df["sigla_uf"].nunique()
        print(f"     UFs                   : {ufs}")
 
    print(f"     CBOs distintos        : {df['cbo_2002'].nunique()}")
 
    admissoes = (df["saldo_movimentacao"] == 1).sum()
    deslig    = (df["saldo_movimentacao"] == -1).sum()
    print(f"     Admissões             : {admissoes:,}")
    print(f"     Desligamentos         : {deslig:,}")
 
    sal = df["salario_mensal"]
    print(f"     Salário mediano (R$)  : {sal.median():,.2f}")
    print(f"     Salário mínimo (R$)   : {sal.min():,.2f}")
    print(f"     Salário máximo (R$)   : {sal.max():,.2f}")
    print(f"     Nulos em grau_instrucao: {df['grau_instrucao'].isnull().sum():,}")
 
 
def gerar_relatorio(df_ac: pd.DataFrame, df_br: pd.DataFrame,
                    arquivo_ac: str, arquivo_br: str):
    """Gera um relatório em texto para registrar a extração."""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caminho = os.path.join(PASTA_SAIDA, "relatorio_extracao.txt")
 
    linhas = [
        "=" * 60,
        "  RELATÓRIO DE EXTRAÇÃO — CAGED TI",
        "=" * 60,
        f"  Data/hora     : {agora}",
        f"  Projeto GCP   : {BILLING_PROJECT_ID}",
        f"  Período       : {ANO_INICIO}–{ANO_FIM}",
        f"  CBOs incluídos: {len(CBOS_TI)}",
        "",
        "  CBOs de TI utilizados:",
        *[f"    {c}" for c in CBOS_TI],
        "",
        "─" * 60,
        f"  ARQUIVO ACRE",
        f"    Caminho    : {arquivo_ac}",
        f"    Linhas     : {len(df_ac):,}",
        f"    Admissões  : {(df_ac['saldo_movimentacao'] == 1).sum():,}",
        f"    Desligam.  : {(df_ac['saldo_movimentacao'] == -1).sum():,}",
        f"    Sal. median: R$ {df_ac['salario_mensal'].median():,.2f}",
        "",
        "─" * 60,
        f"  ARQUIVO BRASIL",
        f"    Caminho    : {arquivo_br}",
        f"    Linhas     : {len(df_br):,}",
        f"    UFs        : {df_br['sigla_uf'].nunique()}",
        f"    Admissões  : {(df_br['saldo_movimentacao'] == 1).sum():,}",
        f"    Desligam.  : {(df_br['saldo_movimentacao'] == -1).sum():,}",
        f"    Sal. median: R$ {df_br['salario_mensal'].median():,.2f}",
        "",
        "=" * 60,
        "  Extração concluída com sucesso.",
        "=" * 60,
    ]
 
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
 
    print(f"\n  📄 Relatório salvo em: {caminho}")
 
 
# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
 
if __name__ == "__main__":
 
    # Aviso se o projeto não foi configurado
    if BILLING_PROJECT_ID == "seu-projeto-aqui":
        print("\n⚠️  ATENÇÃO: você precisa configurar o BILLING_PROJECT_ID.")
        print("   Edite a variável no topo deste script com o ID do seu projeto GCP.")
        print("   Acesse: https://console.cloud.google.com/projectcreate\n")
        exit(1)
 
    print("\n" + "=" * 60)
    print("  EXTRAÇÃO CAGED — MERCADO DE TI")
    print("  Minicurso: Semana Acadêmica de TIC")
    print("=" * 60)
 
    # ── 1. Extração Acre ─────────────────────────────────────────────────────
    df_ac = extrair(QUERY_ACRE, "Novo CAGED — TI no Acre (2022–2024)")
    resumo(df_ac, "Acre")
    arquivo_ac = salvar(df_ac, "caged_ti_ac_2022_2024.csv")
 
    # ── 2. Extração Brasil ───────────────────────────────────────────────────
    print("\n" + "-" * 60)
    resp = input("\n  Extrair também a base nacional (Brasil completo)? [s/N] ").strip().lower()
    if resp == "s":
        df_br = extrair(QUERY_BRASIL, "Novo CAGED — TI no Brasil (2022–2024)")
        resumo(df_br, "Brasil")
        arquivo_br = salvar(df_br, "caged_ti_br_2022_2024.csv")
    else:
        print("  Base nacional ignorada.")
        df_br     = df_ac.copy()  # placeholder para o relatório
        arquivo_br = arquivo_ac
 
    # ── 3. Relatório ─────────────────────────────────────────────────────────
    gerar_relatorio(df_ac, df_br, arquivo_ac, arquivo_br)
 
    # ── 4. Mensagem final ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✅ TUDO PRONTO!")
    print("=" * 60)
    print(f"\n  Arquivos gerados em: {os.path.abspath(PASTA_SAIDA)}")
    print(f"  → {arquivo_ac}")
    if resp == "s":
        print(f"  → {arquivo_br}")
    print("\n  Próximos passos:")
    print("  1. Abra o notebook  minicurso_caged_ti.ipynb")
    print("  2. Coloque o CSV na mesma pasta que o notebook")
    print("  3. Distribua o CSV para os participantes (pen drive ou Google Drive)")
    print("  4. O tratamento das colunas será feito ao vivo em aula :)")
    print("=" * 60 + "\n")