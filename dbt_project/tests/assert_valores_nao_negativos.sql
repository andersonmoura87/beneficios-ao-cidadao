-- Valores monetários e quantidades de beneficiados não podem ser negativos
-- em nenhum dos programas. Retorna linhas apenas quando há violação.

with todos as (
    select 'bolsa_familia'        as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_bolsa_familia') }}
    union all
    select 'auxilio_brasil'       as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_auxilio_brasil') }}
    union all
    select 'novo_bolsa_familia'   as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_novo_bolsa_familia') }}
    union all
    select 'auxilio_emergencial'  as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_auxilio_emergencial') }}
    union all
    select 'bpc'                  as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_bpc') }}
    union all
    select 'seguro_defeso'        as fonte, registro_id, valor, quantidade_beneficiados from {{ ref('stg_seguro_defeso') }}
)

select *
from todos
where valor < 0
   or quantidade_beneficiados < 0
