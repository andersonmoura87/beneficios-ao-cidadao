{{
  config(
    materialized = 'view',
    schema = 'staging'
  )
}}

with source as (
    select * from {{ source('raw', 'seguro_defeso') }}
),

renamed as (
    select
        registro_id,
        mes_competencia::char(6)                        as mes_competencia,
        left(mes_competencia, 4)::int                   as ano,
        right(mes_competencia, 2)::int                  as mes,
        codigo_municipio_ibge::varchar(7)               as codigo_ibge,
        nome_municipio,
        codigo_regiao,
        nome_regiao,
        upper(trim(uf))::char(2)                        as uf,
        tipo_id,
        tipo_descricao,
        coalesce(valor, 0)::numeric(18, 2)              as valor,
        coalesce(quantidade_beneficiados, 0)::bigint    as quantidade_beneficiados,
        _extracted_at
    from source
    where
        mes_competencia is not null
        and codigo_municipio_ibge is not null
)

select * from renamed
