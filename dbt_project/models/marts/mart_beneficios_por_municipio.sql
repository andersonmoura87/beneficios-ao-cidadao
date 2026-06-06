{{
  config(
    materialized = 'table',
    schema = 'marts'
  )
}}

/*
  Mart: Gastos totais por município, por programa e por mês.
  Consolida os 4 benefícios (já agregados na origem por município/mês/tipo)
  em uma única tabela analítica, somando os tipos de cada programa.
*/

with bolsa_familia as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'Bolsa Família'                             as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_bolsa_familia') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

auxilio_brasil as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'Auxílio Brasil'                            as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_auxilio_brasil') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

novo_bolsa_familia as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'Novo Bolsa Família'                        as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_novo_bolsa_familia') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

auxilio as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'Auxílio Emergencial'                       as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_auxilio_emergencial') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

bpc as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'BPC'                                       as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_bpc') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

seguro_defeso as (
    select
        mes_competencia,
        ano,
        mes,
        uf,
        codigo_ibge,
        nome_municipio                              as municipio,
        'Seguro Defeso'                             as programa,
        sum(valor)                                  as valor_total,
        sum(quantidade_beneficiados)                as total_beneficiarios
    from {{ ref('stg_seguro_defeso') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

unificado as (
    select * from bolsa_familia
    union all
    select * from auxilio_brasil
    union all
    select * from novo_bolsa_familia
    union all
    select * from auxilio
    union all
    select * from bpc
    union all
    select * from seguro_defeso
)

select
    mes_competencia,
    ano,
    mes,
    uf,
    codigo_ibge,
    municipio,
    programa,
    valor_total,
    total_beneficiarios,
    round(valor_total / nullif(total_beneficiarios, 0), 2) as valor_medio_por_beneficiario
from unificado
