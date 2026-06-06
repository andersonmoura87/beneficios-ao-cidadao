-- Inicialização do banco beneficios_db
-- Executado automaticamente pelo PostgreSQL na primeira inicialização
--
-- Os quatro programas usam endpoints '-por-municipio' do Portal da Transparência,
-- que compartilham o mesmo contrato (BeneficioPorMunicipioDTO). Os dados são
-- AGREGADOS por município / mês / tipo de benefício (sem registros por
-- beneficiário). Por isso as quatro tabelas raw têm estrutura idêntica.

-- ─── Schemas ───────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- ─── Tabelas Raw (dados agregados da API) ──────────────────────────────────

CREATE TABLE IF NOT EXISTS raw.bolsa_familia (
    registro_id              BIGINT          PRIMARY KEY,  -- id único da API
    mes_competencia          CHAR(6)         NOT NULL,     -- YYYYMM consultado
    data_referencia          TEXT,                         -- dataReferencia da API
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.auxilio_brasil (
    registro_id              BIGINT          PRIMARY KEY,
    mes_competencia          CHAR(6)         NOT NULL,
    data_referencia          TEXT,
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.novo_bolsa_familia (
    registro_id              BIGINT          PRIMARY KEY,
    mes_competencia          CHAR(6)         NOT NULL,
    data_referencia          TEXT,
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.auxilio_emergencial (
    registro_id              BIGINT          PRIMARY KEY,
    mes_competencia          CHAR(6)         NOT NULL,
    data_referencia          TEXT,
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.bpc (
    registro_id              BIGINT          PRIMARY KEY,
    mes_competencia          CHAR(6)         NOT NULL,
    data_referencia          TEXT,
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.seguro_defeso (
    registro_id              BIGINT          PRIMARY KEY,
    mes_competencia          CHAR(6)         NOT NULL,
    data_referencia          TEXT,
    codigo_municipio_ibge    VARCHAR(7),
    nome_municipio           TEXT,
    codigo_regiao            VARCHAR(8),
    nome_regiao              TEXT,
    uf                       CHAR(2),
    tipo_id                  INTEGER,
    tipo_descricao           TEXT,
    tipo_descricao_detalhada TEXT,
    valor                    NUMERIC(18, 2),
    quantidade_beneficiados  BIGINT,
    _extracted_at            TIMESTAMPTZ     DEFAULT NOW()
);

-- ─── Índices para performance ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bf_mes   ON raw.bolsa_familia (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_bf_ibge  ON raw.bolsa_familia (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_bf_uf    ON raw.bolsa_familia (uf);

CREATE INDEX IF NOT EXISTS idx_nbf_mes  ON raw.novo_bolsa_familia (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_nbf_ibge ON raw.novo_bolsa_familia (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_nbf_uf   ON raw.novo_bolsa_familia (uf);

CREATE INDEX IF NOT EXISTS idx_ab_mes   ON raw.auxilio_brasil (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_ab_ibge  ON raw.auxilio_brasil (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_ab_uf    ON raw.auxilio_brasil (uf);

CREATE INDEX IF NOT EXISTS idx_ae_mes   ON raw.auxilio_emergencial (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_ae_ibge  ON raw.auxilio_emergencial (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_ae_uf    ON raw.auxilio_emergencial (uf);

CREATE INDEX IF NOT EXISTS idx_bpc_mes  ON raw.bpc (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_bpc_ibge ON raw.bpc (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_bpc_uf   ON raw.bpc (uf);

CREATE INDEX IF NOT EXISTS idx_sd_mes   ON raw.seguro_defeso (mes_competencia);
CREATE INDEX IF NOT EXISTS idx_sd_ibge  ON raw.seguro_defeso (codigo_municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_sd_uf    ON raw.seguro_defeso (uf);
