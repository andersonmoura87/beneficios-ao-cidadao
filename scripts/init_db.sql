-- Inicialização do banco beneficios_db
-- Executado automaticamente pelo PostgreSQL na primeira inicialização

-- ─── Schemas ───────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- ─── Tabelas Raw (dados brutos da API) ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.bolsa_familia (
    id                      BIGSERIAL,
    mes_competencia         CHAR(6)         NOT NULL,  -- YYYYMM
    codigo_municipio_ibge   VARCHAR(7)      NOT NULL,
    nome_municipio          TEXT,
    uf                      CHAR(2),
    nis_beneficiario        VARCHAR(11),
    nome_beneficiario       TEXT,
    cpf_beneficiario        VARCHAR(11),
    valor_parcela           NUMERIC(12, 2),
    quantidade_beneficiarios INTEGER,
    _extracted_at           TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (mes_competencia, codigo_municipio_ibge, nis_beneficiario)
);

CREATE TABLE IF NOT EXISTS raw.auxilio_emergencial (
    id                      BIGSERIAL,
    mes_competencia         CHAR(6)         NOT NULL,
    codigo_municipio_ibge   VARCHAR(7)      NOT NULL,
    nome_municipio          TEXT,
    uf                      CHAR(2),
    cpf_beneficiario        VARCHAR(11)     NOT NULL,
    nis_beneficiario        VARCHAR(11),
    nome_beneficiario       TEXT,
    valor_parcela           NUMERIC(12, 2),
    quantidade_parcelas     INTEGER,
    _extracted_at           TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (mes_competencia, codigo_municipio_ibge, cpf_beneficiario)
);

CREATE TABLE IF NOT EXISTS raw.bpc (
    id                      BIGSERIAL,
    mes_competencia         CHAR(6)         NOT NULL,
    uf                      CHAR(2)         NOT NULL,
    municipio               TEXT,
    codigo_municipio_ibge   VARCHAR(7),
    nis_beneficiario        VARCHAR(11)     NOT NULL,
    nome_beneficiario       TEXT,
    cpf_beneficiario        VARCHAR(11),
    tipo_beneficio          TEXT,
    valor_beneficio         NUMERIC(12, 2),
    _extracted_at           TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (mes_competencia, uf, nis_beneficiario)
);

CREATE TABLE IF NOT EXISTS raw.seguro_defeso (
    id                      BIGSERIAL,
    ano                     SMALLINT        NOT NULL,
    nis_beneficiario        VARCHAR(11)     NOT NULL,
    nome_beneficiario       TEXT,
    cpf_beneficiario        VARCHAR(11),
    municipio               TEXT,
    uf                      CHAR(2),
    valor_parcela           NUMERIC(12, 2),
    quantidade_parcelas     INTEGER,
    especie_pesqueira       TEXT,
    _extracted_at           TIMESTAMPTZ     DEFAULT NOW(),
    PRIMARY KEY (ano, nis_beneficiario)
);

-- ─── Índices para performance ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bf_mes        ON raw.bolsa_familia (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_bf_ibge       ON raw.bolsa_familia (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_bf_uf         ON raw.bolsa_familia (uf);

CREATE INDEX IF NOT EXISTS idx_ae_mes        ON raw.auxilio_emergencial (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_ae_ibge       ON raw.auxilio_emergencial (codigo_municipio_ibge);

CREATE INDEX IF NOT EXISTS idx_bpc_mes       ON raw.bpc (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_bpc_uf        ON raw.bpc (uf);

CREATE INDEX IF NOT EXISTS idx_sd_ano        ON raw.seguro_defeso (ano);
CREATE INDEX IF NOT EXISTS idx_sd_uf         ON raw.seguro_defeso (uf);
