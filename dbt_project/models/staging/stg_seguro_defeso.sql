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
        ano::smallint                               as ano,
        nis_beneficiario,
        nome_beneficiario,
        cpf_beneficiario,
        municipio,
        upper(trim(uf))::char(2)                   as uf,
        especie_pesqueira,
        coalesce(valor_parcela, 0)::numeric(12,2)  as valor_parcela,
        coalesce(quantidade_parcelas, 0)           as quantidade_parcelas,
        valor_parcela * quantidade_parcelas        as valor_total,
        _extracted_at
    from source
    where ano is not null
)

select * from renamed
