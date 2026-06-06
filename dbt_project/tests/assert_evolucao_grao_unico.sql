-- mart_evolucao_temporal deve ter no máximo uma linha
-- por (programa, mes_competencia).
-- Retorna linhas apenas quando o grão é violado (teste falha).

select
    programa,
    mes_competencia,
    count(*) as n
from {{ ref('mart_evolucao_temporal') }}
group by 1, 2
having count(*) > 1
