"""Configuração central: caminhos e catálogo de séries usadas no projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_EXTERNAL = ROOT / "data" / "external"
FIGURES = ROOT / "reports" / "figures"

# Séries do FRED (Federal Reserve Bank of St. Louis). Emprego em milhares,
# dados mensais com ajuste sazonal, originados no BLS / Current Employment Statistics.
FRED_SERIES = {
    "CES6054150001": "Design de sistemas de computação e serviços relacionados",
    "CES5051800001": "Infraestrutura de computação, processamento de dados e hospedagem",
    "CES6054160001": "Consultoria de gestão e técnica",
    "CES5051700001": "Telecomunicações",
    "USINFO": "Setor de Informação (total)",
    "PAYEMS": "Emprego total não agrícola (EUA)",
    "JTU5100JOL": "Vagas abertas no setor de Informação (JOLTS, sem ajuste)",
    "IHLIDXUS": "Indeed: índice de vagas, total (fev/2020 = 100)",
    "IHLIDXUSTPSOFTDEVE": "Indeed: índice de vagas, desenvolvimento de software",
    "IHLIDXUSTPMATH": "Indeed: índice de vagas, matemática",
}

# Séries de emprego (CES) consideradas "núcleo tech" para a modelagem.
TECH_EMPLOYMENT_SERIES = ["CES6054150001", "CES5051800001"]

# Indeed Hiring Lab — repositório público com vagas por setor e país.
INDEED_BASE = "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master"
# Países com série por setor publicada (ES, IT, NL e IE só têm o agregado).
INDEED_COUNTRIES = ["US", "GB", "CA", "AU", "DE", "FR"]
TECH_SECTORS = [
    "Software Development",
    "Data & Analytics",
    "IT Infrastructure, Operations & Support",
    "IT Systems & Solutions",
]

# Eurostat — especialistas em TIC empregados (milhares e % do emprego total).
EUROSTAT_ICT_DATASET = "isoc_sks_itspt"

# Projeções oficiais do BLS (Employment Projections 2025–2035), snapshot local.
BLS_PROJECTIONS_FILE = DATA_EXTERNAL / "bls_projections_2025_2035.csv"
