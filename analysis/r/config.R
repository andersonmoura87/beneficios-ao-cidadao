# Configuração de conexão ao PostgreSQL e pacotes base

library(DBI)
library(RPostgres)
library(dotenv)

# Carrega variáveis do .env (se existir)
if (file.exists("../../.env")) {
  dotenv::load_dot_env("../../.env")
}

# Conexão com o banco
conectar_db <- function() {
  dbConnect(
    RPostgres::Postgres(),
    host     = Sys.getenv("POSTGRES_HOST", "localhost"),
    port     = as.integer(Sys.getenv("POSTGRES_PORT", "5432")),
    dbname   = Sys.getenv("POSTGRES_DB", "beneficios_db"),
    user     = Sys.getenv("POSTGRES_USER", "beneficios"),
    password = Sys.getenv("POSTGRES_PASSWORD", "beneficios_pass")
  )
}

# Paleta de cores por programa
CORES_PROGRAMAS <- c(
  "Bolsa Família"       = "#1B7A34",
  "Auxílio Brasil"      = "#00897B",
  "Novo Bolsa Família"  = "#43A047",
  "Auxílio Emergencial" = "#E07B00",
  "BPC"                 = "#1565C0",
  "Seguro Defeso"       = "#6A1B9A"
)
