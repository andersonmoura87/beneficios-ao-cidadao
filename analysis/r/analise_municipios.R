#!/usr/bin/env Rscript
# Análise por município: rankings, concentração e mapa do Brasil
# Fonte: mart_ranking_municipios (dbt)

source("config.R")

library(tidyverse)
library(scales)
library(ggplot2)

con <- conectar_db()

ranking <- dbGetQuery(con, "
  SELECT
    ano, uf, codigo_ibge, municipio,
    valor_total_ano, beneficiarios_ano,
    programas_recebidos, valor_medio_por_pessoa,
    ranking_nacional, ranking_uf
  FROM marts.mart_ranking_municipios
  ORDER BY ano DESC, ranking_nacional
")

dbDisconnect(con)

ano_ref <- max(ranking$ano)
ranking_ano <- ranking |> filter(ano == ano_ref)

# ─── Top 20 municípios (valor total) ──────────────────────────────────────────
top20 <- ranking_ano |>
  slice_min(ranking_nacional, n = 20) |>
  mutate(label = paste0(municipio, " (", uf, ")"))

p_top20 <- ggplot(top20, aes(x = reorder(label, valor_total_ano), y = valor_total_ano / 1e6)) +
  geom_col(fill = "#1B7A34", alpha = 0.85) +
  geom_text(aes(label = scales::dollar(valor_total_ano / 1e6, prefix = "R$ ", suffix = "M",
                                        big.mark = ".", decimal.mark = ",")),
            hjust = -0.1, size = 3.2) +
  coord_flip() +
  scale_y_continuous(
    labels = label_dollar(prefix = "R$ ", suffix = "M", big.mark = "."),
    expand = expansion(mult = c(0, 0.15))
  ) +
  labs(
    title    = paste0("Top 20 Municípios em Gastos com Benefícios Sociais — ", ano_ref),
    subtitle = "Soma de todos os programas (Bolsa Família, BPC, Auxílio Emergencial, Seguro Defeso)",
    x        = NULL,
    y        = "Valor Total (R$ milhões)",
    caption  = "Fonte: Portal da Transparência / CGU"
  ) +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave("../../data/processed/top20_municipios.png", p_top20, width = 13, height = 9, dpi = 150)
cat("Salvo: top20_municipios.png\n")

# ─── Concentração por UF ──────────────────────────────────────────────────────
por_uf <- ranking_ano |>
  group_by(uf) |>
  summarise(
    valor_total   = sum(valor_total_ano, na.rm = TRUE),
    beneficiarios = sum(beneficiarios_ano, na.rm = TRUE),
    municipios    = n_distinct(municipio),
    .groups = "drop"
  ) |>
  arrange(desc(valor_total))

p_uf <- ggplot(por_uf, aes(x = reorder(uf, valor_total), y = valor_total / 1e9)) +
  geom_col(aes(fill = valor_total), show.legend = FALSE) +
  scale_fill_gradient(low = "#A5D6A7", high = "#1B5E20") +
  scale_y_continuous(labels = label_dollar(prefix = "R$ ", suffix = "B", big.mark = ".")) +
  coord_flip() +
  labs(
    title    = paste0("Gastos com Benefícios por Estado — ", ano_ref),
    x        = "UF",
    y        = "Valor Total (R$ bilhões)",
    caption  = "Fonte: Portal da Transparência / CGU"
  ) +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave("../../data/processed/gastos_por_uf.png", p_uf, width = 10, height = 10, dpi = 150)
cat("Salvo: gastos_por_uf.png\n")

write_csv(por_uf, "../../data/processed/gastos_por_uf.csv")
cat("Salvo: gastos_por_uf.csv\n")
