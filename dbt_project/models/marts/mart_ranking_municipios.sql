{{
  config(
    materialized = 'table',
    schema = 'marts'
  )
}}

/*
  Mart: Ranking de municípios por valor total recebido (todos os programas).
  Agregação anual para facilitar comparações.
*/

with base as (
    select
        ano,
        uf,
        codigo_ibge,
        municipio,
        sum(valor_total)                as valor_total_ano,
        sum(total_beneficiarios)        as beneficiarios_ano,
        count(distinct programa)        as programas_recebidos
    from {{ ref('mart_beneficios_por_municipio') }}
    where municipio is not null
    group by 1, 2, 3, 4
)

select
    ano,
    uf,
    codigo_ibge,
    municipio,
    valor_total_ano,
    beneficiarios_ano,
    programas_recebidos,
    round(valor_total_ano / nullif(beneficiarios_ano, 0), 2)    as valor_medio_por_pessoa,
    rank() over (partition by ano order by valor_total_ano desc) as ranking_nacional,
    rank() over (partition by ano, uf order by valor_total_ano desc) as ranking_uf
from base
order by ano desc, valor_total_ano desc
