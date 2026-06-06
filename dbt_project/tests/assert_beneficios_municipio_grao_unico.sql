-- mart_beneficios_por_municipio deve ter no máximo uma linha
-- por (mes_competencia, codigo_ibge, programa).
-- Retorna linhas apenas quando o grão é violado (teste falha).

select
    mes_competencia,
    codigo_ibge,
    programa,
    count(*) as n
from {{ ref('mart_beneficios_por_municipio') }}
group by 1, 2, 3
having count(*) > 1
