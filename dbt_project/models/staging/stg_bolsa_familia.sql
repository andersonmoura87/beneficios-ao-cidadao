{{
  config(
    materialized = 'view',
    schema = 'staging'
  )
}}

with source as (
    select * from {{ source('raw', 'bolsa_familia') }}
),

renamed as (
    select
        mes_competencia::char(6)                    as mes_competencia,
        left(mes_competencia, 4)::int               as ano,
        right(mes_competencia, 2)::int              as mes,
        codigo_municipio_ibge::varchar(7)           as codigo_ibge,
        nome_municipio,
        upper(trim(uf))::char(2)                    as uf,
        nis_beneficiario,
        nome_beneficiario,
        cpf_beneficiario,
        coalesce(valor_parcela, 0)::numeric(12, 2)  as valor_parcela,
        coalesce(quantidade_beneficiarios, 0)       as quantidade_beneficiarios,
        _extracted_at
    from source
    where
        mes_competencia is not null
        and codigo_municipio_ibge is not null
)

select * from renamed
