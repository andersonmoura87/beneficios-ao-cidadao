#!/usr/bin/env Rscript
# Análise da evolução temporal dos gastos por programa social
# Fonte: mart_evolucao_temporal (dbt)

source("config.R")

library(tidyverse)
library(scales)
library(ggplot2)

con <- conectar_db()

# ─── Leitura ──────────────────────────────────────────────────────────────────
evolucao <- dbGetQuery(con, "
  SELECT
    ano,
    mes,
    mes_competencia,
    programa,
    valor_total_nacional,
    total_beneficiarios_nacional,
    ticket_medio,
    variacao_pct_mom
  FROM marts.mart_evolucao_temporal
  ORDER BY mes_competencia
")

dbDisconnect(con)

evolucao <- evolucao |>
  mutate(
    data = as.Date(paste0(mes_competencia, "01"), "%Y%m%d"),
    valor_bi = valor_total_nacional / 1e9
  )

# ─── Gráfico 1: Evolução do valor total por programa ─────────────────────────
p1 <- ggplot(evolucao, aes(x = data, y = valor_bi, color = programa)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 1.2, alpha = 0.6) +
  scale_color_manual(values = CORES_PROGRAMAS) +
  scale_y_continuous(labels = label_dollar(prefix = "R$ ", suffix = "B", big.mark = ".")) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y") +
  labs(
    title    = "Gastos com Benefícios Sociais ao Cidadão — Brasil",
    subtitle = "Valor total mensal por programa (em bilhões de R$)",
    x        = NULL,
    y        = "Valor total (R$ bilhões)",
    color    = "Programa",
    caption  = "Fonte: Portal da Transparência / CGU"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    legend.position  = "bottom",
    axis.text.x      = element_text(angle = 45, hjust = 1),
    plot.title       = element_text(face = "bold")
  )

ggsave("../../data/processed/evolucao_total.png", p1, width = 14, height = 7, dpi = 150)
cat("Salvo: evolucao_total.png\n")

# ─── Gráfico 2: Beneficiários ao longo do tempo ───────────────────────────────
p2 <- ggplot(evolucao, aes(x = data, y = total_beneficiarios_nacional / 1e6, fill = programa)) +
  geom_area(alpha = 0.7, position = "stack") +
  scale_fill_manual(values = CORES_PROGRAMAS) +
  scale_y_continuous(labels = label_number(suffix = "M")) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y") +
  labs(
    title    = "Total de Beneficiários por Programa Social",
    subtitle = "Série histórica — Brasil",
    x        = NULL,
    y        = "Beneficiários (milhões)",
    fill     = "Programa",
    caption  = "Fonte: Portal da Transparência / CGU"
  ) +
  theme_minimal(base_size = 13) +
  theme(legend.position = "bottom", plot.title = element_text(face = "bold"))

ggsave("../../data/processed/evolucao_beneficiarios.png", p2, width = 14, height = 7, dpi = 150)
cat("Salvo: evolucao_beneficiarios.png\n")

# ─── Tabela resumo ────────────────────────────────────────────────────────────
resumo <- evolucao |>
  group_by(programa) |>
  summarise(
    periodo_inicio      = min(data),
    periodo_fim         = max(data),
    valor_total_bi      = sum(valor_bi, na.rm = TRUE),
    media_mensal_bi     = mean(valor_bi, na.rm = TRUE),
    pico_valor_bi       = max(valor_bi, na.rm = TRUE),
    .groups = "drop"
  ) |>
  arrange(desc(valor_total_bi))

print(resumo)
write_csv(resumo, "../../data/processed/resumo_programas.csv")
cat("Salvo: resumo_programas.csv\n")
