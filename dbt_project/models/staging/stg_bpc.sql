{{
  config(
    materialized = 'view',
    schema = 'staging'
  )
}}

with source as (
    select * from {{ source('raw', 'bpc') }}
),

renamed as (
    select
        mes_competencia::char(6)                    as mes_competencia,
        left(mes_competencia, 4)::int               as ano,
        right(mes_competencia, 2)::int              as mes,
        upper(trim(uf))::char(2)                    as uf,
        municipio,
        codigo_municipio_ibge::varchar(7)           as codigo_ibge,
        nis_beneficiario,
        nome_beneficiario,
        cpf_beneficiario,
        tipo_beneficio,
        coalesce(valor_beneficio, 0)::numeric(12,2) as valor_beneficio,
        _extracted_at
    from source
    where mes_competencia is not null
)

select * from renamed
