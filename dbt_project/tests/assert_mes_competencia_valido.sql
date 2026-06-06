-- mes_competencia deve ser um YYYYMM válido: 6 dígitos, mês entre 01 e 12
-- e ano plausível (>= 2004, início do Bolsa Família).
-- Retorna linhas apenas quando há violação.

with todos as (
    select 'bolsa_familia'        as fonte, mes_competencia from {{ ref('stg_bolsa_familia') }}
    union all
    select 'auxilio_brasil'       as fonte, mes_competencia from {{ ref('stg_auxilio_brasil') }}
    union all
    select 'novo_bolsa_familia'   as fonte, mes_competencia from {{ ref('stg_novo_bolsa_familia') }}
    union all
    select 'auxilio_emergencial'  as fonte, mes_competencia from {{ ref('stg_auxilio_emergencial') }}
    union all
    select 'bpc'                  as fonte, mes_competencia from {{ ref('stg_bpc') }}
    union all
    select 'seguro_defeso'        as fonte, mes_competencia from {{ ref('stg_seguro_defeso') }}
)

select *
from todos
where mes_competencia !~ '^[0-9]{6}$'
   or right(mes_competencia, 2)::int not between 1 and 12
   or left(mes_competencia, 4)::int < 2004
