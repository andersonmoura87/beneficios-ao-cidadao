{{
  config(
    materialized = 'table',
    schema = 'marts'
  )
}}

/*
  Mart: Evolução temporal dos gastos por programa em nível nacional.
  Ideal para séries temporais e visualizações de tendência.
*/

with base as (
    select
        ano,
        mes,
        mes_competencia,
        programa,
        sum(valor_total)            as valor_total_nacional,
        sum(total_beneficiarios)    as total_beneficiarios_nacional,
        count(distinct municipio)   as municipios_atendidos
    from {{ ref('mart_beneficios_por_municipio') }}
    group by 1, 2, 3, 4
)

select
    ano,
    mes,
    mes_competencia,
    programa,
    valor_total_nacional,
    total_beneficiarios_nacional,
    municipios_atendidos,
    round(valor_total_nacional / nullif(total_beneficiarios_nacional, 0), 2) as ticket_medio,
    -- variação mês a mês
    lag(valor_total_nacional) over (
        partition by programa order by mes_competencia
    ) as valor_mes_anterior,
    round(
        (valor_total_nacional - lag(valor_total_nacional) over (
            partition by programa order by mes_competencia
        )) / nullif(lag(valor_total_nacional) over (
            partition by programa order by mes_competencia
        ), 0) * 100,
        2
    ) as variacao_pct_mom
from base
order by programa, mes_competencia
