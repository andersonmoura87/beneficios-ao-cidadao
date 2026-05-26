# Benefícios ao Cidadão — ELT Pipeline

Pipeline ELT robusto para extração, carga e transformação de dados de benefícios sociais do [Portal da Transparência](https://portaldatransparencia.gov.br/), orquestrado pelo Apache Airflow.

## Programas cobertos

| Programa | Período disponível | Endpoint API |
|---|---|---|
| Bolsa Família | jan/2004 – atual | `bolsa-familia-por-municipio` |
| Auxílio Emergencial | abr/2020 – out/2021 | `auxilio-emergencial-por-municipio` |
| BPC (Benefício de Prestação Continuada) | jan/2004 – atual | `bpc` |
| Seguro Defeso | 2013 – atual | `seguro-defeso-codigo` |

## Arquitetura

```
Portal da Transparência API
        │  Extract (Python + rate limiting + retry)
        ▼
   MinIO (S3 local)  ◄── raw layer (Parquet particionado)
        │  Load (psycopg2 + upsert idempotente)
        ▼
  PostgreSQL — schema raw
        │  Transform (dbt)
        ▼
  PostgreSQL — schema staging (views)
        │
  PostgreSQL — schema marts (tabelas analíticas)
        │
  Apache Airflow ◄── orquestra todas as etapas via DAGs
        │
  Análise em R (ggplot2) / Jupyter
```

## Estrutura do projeto

```
.
├── docker-compose.yml          # Airflow + PostgreSQL + MinIO
├── requirements.txt
├── .env                        # variáveis de ambiente (não versionado)
├── .env.example                # template público
│
├── extractors/                 # camada E do ELT
│   ├── base_extractor.py       # rate limiting, retry, paginação, checkpoint
│   ├── bolsa_familia.py
│   ├── auxilio_emergencial.py
│   ├── bpc.py
│   ├── seguro_defeso.py
│   └── municipios.py           # lista IBGE com cache
│
├── loaders/                    # camada L do ELT
│   ├── minio_loader.py         # upload Parquet → MinIO
│   └── postgres_loader.py      # upsert idempotente → PostgreSQL
│
├── dbt_project/                # camada T do ELT
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # views de limpeza/normalização
│       │   ├── stg_bolsa_familia.sql
│       │   ├── stg_auxilio_emergencial.sql
│       │   ├── stg_bpc.sql
│       │   └── stg_seguro_defeso.sql
│       └── marts/              # tabelas analíticas finais
│           ├── mart_beneficios_por_municipio.sql
│           ├── mart_evolucao_temporal.sql
│           └── mart_ranking_municipios.sql
│
├── dags/                       # orquestração Airflow
│   ├── dag_bolsa_familia.py    # mensal automático
│   ├── dag_bpc_seguro_defeso.py# mensal automático
│   ├── dag_auxilio_emergencial.py # trigger manual (histórico)
│   └── dag_carga_historica.py  # carga inicial completa (trigger manual)
│
├── scripts/
│   └── init_db.sql             # criação de schemas e tabelas
│
├── analysis/
│   └── r/
│       ├── config.R
│       ├── analise_evolucao.R  # séries temporais
│       └── analise_municipios.R# rankings e mapas
│
└── data/                       # gerado localmente (não versionado)
    ├── raw/
    ├── processed/
    └── municipios/
```

## Como executar

### 1. Pré-requisitos

- Docker Desktop instalado e rodando
- Git

### 2. Configuração inicial

```bash
# Clone e entre no projeto
git clone <url-do-repo>
cd beneficios-ao-cidadao

# Copie e edite as variáveis de ambiente
cp .env.example .env
# Edite .env com sua chave da API e senhas desejadas
```

### 3. Subir os serviços

```bash
docker compose up airflow-init     # inicializa o banco do Airflow (aguarde concluir)
docker compose up -d               # sobe todos os serviços em background
```

### 4. Acessar as interfaces

| Serviço | URL | Credenciais padrão |
|---|---|---|
| Airflow Webserver | http://localhost:8080 | admin / admin123 |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| PostgreSQL | localhost:5432 | beneficios / beneficios_pass |

### 5. Executar a carga histórica

No Airflow (http://localhost:8080):
1. Ative a DAG `elt_carga_historica_completa`
2. Clique em **Trigger DAG** (botão play)
3. Aguarde — a carga completa pode levar horas dependendo do volume

As DAGs `elt_bolsa_familia` e `elt_bpc_seguro_defeso` rodam automaticamente todo dia 10 do mês.

### 6. Análise em R

```r
# Instale os pacotes necessários
install.packages(c("DBI", "RPostgres", "tidyverse", "scales", "dotenv"))

# Execute as análises
setwd("analysis/r")
source("analise_evolucao.R")
source("analise_municipios.R")
```

## Rate limits da API

| Horário | Endpoints normais | Endpoints restritos |
|---|---|---|
| 00h–06h | 700 req/min | 180 req/min |
| 06h–24h | 400 req/min | 180 req/min |

O pipeline respeita automaticamente esses limites via `RateLimiter` com token bucket e ajuste dinâmico por horário.

## Contribuição

Projeto de extensão universitária — UEM (Universidade Estadual de Maringá).
