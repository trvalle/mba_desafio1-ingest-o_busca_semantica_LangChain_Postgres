"""
Aplicativo de Organização de Exames de Sangue

API REST para organizar exames de sangue e gerar gráficos de evolução dos
níveis de saúde, com análise de impacto a curto, médio e longo prazo.

Compatível com Android e iPhone via PWA (Progressive Web App).

Para executar:
    uvicorn blood_tests_app:app --reload --host 0.0.0.0 --port 8080

Acesse no navegador do celular:
    http://<seu-ip>:8080
"""

import os
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Configuração do banco de dados (SQLite — sem infraestrutura extra)
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./blood_tests.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Modelos SQLAlchemy
# ---------------------------------------------------------------------------
class ExameSangue(Base):
    """Representa um conjunto de exames realizados numa mesma data/laboratório."""

    __tablename__ = "exames_sangue"

    id = Column(Integer, primary_key=True, index=True)
    data_exame = Column(Date, nullable=False)
    laboratorio = Column(String(200), default="")
    observacoes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    resultados = relationship(
        "ResultadoExame",
        back_populates="exame",
        cascade="all, delete-orphan",
    )


class ResultadoExame(Base):
    """Representa o resultado de um biomarcador individual num exame."""

    __tablename__ = "resultados_exame"

    id = Column(Integer, primary_key=True, index=True)
    exame_id = Column(Integer, ForeignKey("exames_sangue.id"), nullable=False)
    biomarcador = Column(String(100), nullable=False)
    valor = Column(Float, nullable=False)
    unidade = Column(String(50), default="")
    ref_min = Column(Float, nullable=True)
    ref_max = Column(Float, nullable=True)

    exame = relationship("ExameSangue", back_populates="resultados")


Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------
class ResultadoCreate(BaseModel):
    biomarcador: str
    valor: float
    unidade: str = ""
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None


class ExameCreate(BaseModel):
    data_exame: date
    laboratorio: str = ""
    observacoes: str = ""
    resultados: List[ResultadoCreate] = []


class ResultadoOut(BaseModel):
    id: int
    biomarcador: str
    valor: float
    unidade: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    status: str  # "normal" | "atencao" | "critico" | "indefinido"

    class Config:
        from_attributes = True


class ExameOut(BaseModel):
    id: int
    data_exame: date
    laboratorio: str
    observacoes: str
    resultados: List[ResultadoOut]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Aplicativo FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Saúde Track — Exames de Sangue",
    description="Organize exames de sangue e acompanhe a evolução da sua saúde.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def calcular_status(
    valor: float,
    ref_min: Optional[float],
    ref_max: Optional[float],
) -> str:
    """Retorna 'normal', 'atencao', 'critico' ou 'indefinido'."""
    if ref_min is None and ref_max is None:
        return "indefinido"
    if ref_min is not None and valor < ref_min:
        pct = (ref_min - valor) / abs(ref_min) if ref_min != 0 else abs(ref_min - valor)
        return "critico" if pct > 0.20 else "atencao"
    if ref_max is not None and valor > ref_max:
        pct = (valor - ref_max) / abs(ref_max) if ref_max != 0 else abs(valor - ref_max)
        return "critico" if pct > 0.20 else "atencao"
    return "normal"


def _format_resultado(r: ResultadoExame) -> dict:
    return {
        "id": r.id,
        "biomarcador": r.biomarcador,
        "valor": r.valor,
        "unidade": r.unidade or "",
        "ref_min": r.ref_min,
        "ref_max": r.ref_max,
        "status": calcular_status(r.valor, r.ref_min, r.ref_max),
    }


def _format_exame(exame: ExameSangue) -> dict:
    return {
        "id": exame.id,
        "data_exame": exame.data_exame.isoformat(),
        "laboratorio": exame.laboratorio or "",
        "observacoes": exame.observacoes or "",
        "resultados": [_format_resultado(r) for r in exame.resultados],
    }


def _calcular_tendencia(medicoes: list) -> dict:
    """Calcula a tendência de um biomarcador num conjunto de medições."""
    if len(medicoes) < 2:
        return {
            "tendencia": "insuficiente",
            "variacao_pct": 0,
            "valor_inicial": medicoes[0]["valor"] if medicoes else None,
            "valor_atual": medicoes[-1]["valor"] if medicoes else None,
            "num_medicoes": len(medicoes),
            "status": "indefinido",
        }

    primeiro = medicoes[0]["valor"]
    ultimo = medicoes[-1]["valor"]
    variacao_pct = ((ultimo - primeiro) / primeiro * 100) if primeiro != 0 else 0

    ref_min = medicoes[-1].get("ref_min")
    ref_max = medicoes[-1].get("ref_max")
    status = calcular_status(ultimo, ref_min, ref_max)

    if abs(variacao_pct) < 5:
        tendencia = "estavel"
    elif variacao_pct > 0:
        tendencia = "aumentando"
    else:
        tendencia = "diminuindo"

    return {
        "tendencia": tendencia,
        "variacao_pct": round(variacao_pct, 1),
        "valor_inicial": primeiro,
        "valor_atual": ultimo,
        "num_medicoes": len(medicoes),
        "status": status,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", response_class=FileResponse, include_in_schema=False)
def root():
    """Serve o aplicativo web (PWA)."""
    return FileResponse(os.path.join("static", "index.html"))


@app.post("/api/exames", response_model=ExameOut, tags=["Exames"])
def criar_exame(exame: ExameCreate, db: Session = Depends(get_db)):
    """Cria um novo conjunto de exames de sangue."""
    db_exame = ExameSangue(
        data_exame=exame.data_exame,
        laboratorio=exame.laboratorio,
        observacoes=exame.observacoes,
    )
    db.add(db_exame)
    db.flush()

    for r in exame.resultados:
        db.add(
            ResultadoExame(
                exame_id=db_exame.id,
                biomarcador=r.biomarcador,
                valor=r.valor,
                unidade=r.unidade,
                ref_min=r.ref_min,
                ref_max=r.ref_max,
            )
        )

    db.commit()
    db.refresh(db_exame)
    return _format_exame(db_exame)


@app.get("/api/exames", response_model=List[ExameOut], tags=["Exames"])
def listar_exames(db: Session = Depends(get_db)):
    """Lista todos os exames ordenados por data."""
    exames = db.query(ExameSangue).order_by(ExameSangue.data_exame).all()
    return [_format_exame(e) for e in exames]


@app.get("/api/exames/{exame_id}", response_model=ExameOut, tags=["Exames"])
def buscar_exame(exame_id: int, db: Session = Depends(get_db)):
    """Retorna um exame pelo ID."""
    exame = db.query(ExameSangue).filter(ExameSangue.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado")
    return _format_exame(exame)


@app.delete("/api/exames/{exame_id}", tags=["Exames"])
def deletar_exame(exame_id: int, db: Session = Depends(get_db)):
    """Remove um exame e todos os seus resultados."""
    exame = db.query(ExameSangue).filter(ExameSangue.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado")
    db.delete(exame)
    db.commit()
    return {"message": "Exame removido com sucesso"}


@app.get("/api/evolucao", tags=["Análise"])
def evolucao_biomarcadores(db: Session = Depends(get_db)):
    """Retorna a série temporal de cada biomarcador para geração de gráficos."""
    rows = (
        db.query(ResultadoExame, ExameSangue.data_exame)
        .join(ExameSangue)
        .order_by(ExameSangue.data_exame)
        .all()
    )

    evolucao: dict = {}
    for resultado, data_exame in rows:
        b = resultado.biomarcador
        if b not in evolucao:
            evolucao[b] = {
                "datas": [],
                "valores": [],
                "unidade": resultado.unidade or "",
                "ref_min": resultado.ref_min,
                "ref_max": resultado.ref_max,
            }
        evolucao[b]["datas"].append(str(data_exame))
        evolucao[b]["valores"].append(resultado.valor)

    return evolucao


@app.get("/api/analise_impacto", tags=["Análise"])
def analise_impacto(db: Session = Depends(get_db)):
    """
    Analisa o impacto nos níveis de saúde a curto (3 meses),
    médio (12 meses) e longo prazo (todo o histórico).
    """
    hoje = date.today()
    corte_curto = hoje - timedelta(days=90)
    corte_medio = hoje - timedelta(days=365)

    rows = (
        db.query(ResultadoExame, ExameSangue.data_exame)
        .join(ExameSangue)
        .order_by(ExameSangue.data_exame)
        .all()
    )

    # Agrupa medições por biomarcador
    biomarcadores: dict = {}
    for resultado, data_exame in rows:
        b = resultado.biomarcador
        if b not in biomarcadores:
            biomarcadores[b] = []
        biomarcadores[b].append(
            {
                "data": data_exame,
                "valor": resultado.valor,
                "ref_min": resultado.ref_min,
                "ref_max": resultado.ref_max,
            }
        )

    analise = {}
    for biomarcador, medicoes in biomarcadores.items():
        analise[biomarcador] = {
            "curto_prazo": _calcular_tendencia(
                [m for m in medicoes if m["data"] >= corte_curto]
            ),
            "medio_prazo": _calcular_tendencia(
                [m for m in medicoes if m["data"] >= corte_medio]
            ),
            "longo_prazo": _calcular_tendencia(medicoes),
        }

    return analise


# ---------------------------------------------------------------------------
# Arquivos estáticos (frontend PWA)
# ---------------------------------------------------------------------------
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
