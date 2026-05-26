{{
  config(
    materialized = 'table',
    schema = 'marts'
  )
}}

/*
  Mart: Gastos totais por município, por programa e por mês.
  Consolida os 4 benefícios em uma única tabela analítica.
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
        sum(valor_parcela)                          as valor_total,
        sum(quantidade_beneficiarios)               as total_beneficiarios
    from {{ ref('stg_bolsa_familia') }}
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
        sum(valor_parcela)                          as valor_total,
        count(*)                                    as total_beneficiarios
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
        municipio,
        'BPC'                                       as programa,
        sum(valor_beneficio)                        as valor_total,
        count(*)                                    as total_beneficiarios
    from {{ ref('stg_bpc') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

seguro_defeso as (
    select
        cast(ano || '01' as char(6))                as mes_competencia,
        ano,
        1                                           as mes,
        uf,
        null::varchar(7)                            as codigo_ibge,
        municipio,
        'Seguro Defeso'                             as programa,
        sum(valor_total)                            as valor_total,
        count(*)                                    as total_beneficiarios
    from {{ ref('stg_seguro_defeso') }}
    group by 1, 2, 3, 4, 5, 6, 7
),

unificado as (
    select * from bolsa_familia
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
