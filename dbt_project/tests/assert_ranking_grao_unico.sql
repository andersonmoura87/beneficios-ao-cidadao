-- mart_ranking_municipios deve ter no máximo uma linha
-- por (ano, codigo_ibge).
-- Retorna linhas apenas quando o grão é violado (teste falha).

select
    ano,
    codigo_ibge,
    count(*) as n
from {{ ref('mart_ranking_municipios') }}
group by 1, 2
having count(*) > 1
