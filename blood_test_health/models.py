"""
Módulo de Modelos de Exames de Sangue

Define os modelos de dados para parâmetros de exames laboratoriais,
faixas de referência e classificações de resultado.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple
from enum import Enum


class Status(Enum):
    """Classificação do status de um parâmetro laboratorial."""
    NORMAL = "Normal"
    BAIXO = "Abaixo do normal"
    ALTO = "Acima do normal"
    CRITICO_BAIXO = "Crítico - muito baixo"
    CRITICO_ALTO = "Crítico - muito alto"


@dataclass
class ValorReferencia:
    """
    Faixa de referência para um parâmetro laboratorial.

    Attributes:
        minimo: Valor mínimo normal
        maximo: Valor máximo normal
        critico_min: Valor crítico inferior (opcional)
        critico_max: Valor crítico superior (opcional)
        unidade: Unidade de medida
    """
    minimo: float
    maximo: float
    unidade: str
    critico_min: Optional[float] = None
    critico_max: Optional[float] = None


@dataclass
class Parametro:
    """
    Parâmetro individual de um exame laboratorial.

    Attributes:
        nome: Nome do parâmetro
        valor: Valor obtido no exame
        referencia: Faixa de referência do parâmetro
        descricao: Descrição clínica do parâmetro
    """
    nome: str
    valor: float
    referencia: ValorReferencia
    descricao: str = ""

    @property
    def status(self) -> Status:
        """Calcula o status do parâmetro em relação à faixa de referência."""
        if self.referencia.critico_min is not None and self.valor < self.referencia.critico_min:
            return Status.CRITICO_BAIXO
        if self.referencia.critico_max is not None and self.valor > self.referencia.critico_max:
            return Status.CRITICO_ALTO
        if self.valor < self.referencia.minimo:
            return Status.BAIXO
        if self.valor > self.referencia.maximo:
            return Status.ALTO
        return Status.NORMAL

    @property
    def dentro_da_faixa(self) -> bool:
        """Retorna True se o valor está dentro da faixa normal."""
        return self.status == Status.NORMAL

    def to_dict(self) -> dict:
        """Converte o parâmetro para dicionário."""
        return {
            "nome": self.nome,
            "valor": self.valor,
            "unidade": self.referencia.unidade,
            "referencia_min": self.referencia.minimo,
            "referencia_max": self.referencia.maximo,
            "status": self.status.value,
            "descricao": self.descricao,
        }


@dataclass
class ResultadoExame:
    """
    Resultado completo de um exame de sangue.

    Attributes:
        paciente: Nome do paciente
        data_coleta: Data de coleta da amostra
        parametros: Lista de parâmetros analisados
        observacoes: Observações adicionais
    """
    paciente: str
    data_coleta: str
    parametros: list = field(default_factory=list)
    observacoes: str = ""

    def adicionar_parametro(self, parametro: Parametro) -> None:
        """Adiciona um parâmetro ao resultado."""
        self.parametros.append(parametro)

    @property
    def parametros_alterados(self) -> list:
        """Retorna apenas os parâmetros fora da faixa de referência."""
        return [p for p in self.parametros if not p.dentro_da_faixa]

    @property
    def parametros_criticos(self) -> list:
        """Retorna parâmetros com valores críticos."""
        return [
            p for p in self.parametros
            if p.status in (Status.CRITICO_BAIXO, Status.CRITICO_ALTO)
        ]

    def resumo_para_ia(self) -> str:
        """
        Gera um resumo textual estruturado para análise pela IA.

        Returns:
            String formatada com todos os parâmetros e seus status
        """
        linhas = [
            f"Paciente: {self.paciente}",
            f"Data da coleta: {self.data_coleta}",
            "",
            "=== RESULTADOS DO EXAME DE SANGUE ===",
        ]

        for p in self.parametros:
            status_icon = "✅" if p.dentro_da_faixa else "⚠️"
            linhas.append(
                f"{status_icon} {p.nome}: {p.valor} {p.referencia.unidade} "
                f"(Ref: {p.referencia.minimo}–{p.referencia.maximo}) — {p.status.value}"
            )

        if self.observacoes:
            linhas += ["", f"Observações: {self.observacoes}"]

        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Faixas de referência padrão (adultos, valores gerais)
# ---------------------------------------------------------------------------

REFERENCIAS_PADRAO: Dict[str, ValorReferencia] = {
    # Hemograma
    "hemoglobina_masculino": ValorReferencia(13.5, 17.5, "g/dL", critico_min=7.0, critico_max=20.0),
    "hemoglobina_feminino": ValorReferencia(12.0, 16.0, "g/dL", critico_min=7.0, critico_max=20.0),
    "hematocrito_masculino": ValorReferencia(40.0, 52.0, "%"),
    "hematocrito_feminino": ValorReferencia(36.0, 46.0, "%"),
    "leucocitos": ValorReferencia(4000.0, 11000.0, "/mm³", critico_min=2000.0, critico_max=30000.0),
    "plaquetas": ValorReferencia(150000.0, 400000.0, "/mm³", critico_min=50000.0, critico_max=1000000.0),
    "vgm": ValorReferencia(80.0, 100.0, "fL"),
    "hgm": ValorReferencia(27.0, 33.0, "pg"),
    "chgm": ValorReferencia(32.0, 36.0, "g/dL"),

    # Glicemia
    "glicose_jejum": ValorReferencia(70.0, 99.0, "mg/dL", critico_min=50.0, critico_max=500.0),
    "hemoglobina_glicada": ValorReferencia(4.0, 5.6, "%"),

    # Lipidograma
    "colesterol_total": ValorReferencia(0.0, 190.0, "mg/dL"),
    "ldl": ValorReferencia(0.0, 130.0, "mg/dL"),
    "hdl_masculino": ValorReferencia(40.0, 9999.0, "mg/dL"),
    "hdl_feminino": ValorReferencia(50.0, 9999.0, "mg/dL"),
    "triglicerideos": ValorReferencia(0.0, 150.0, "mg/dL", critico_max=500.0),
    "vldl": ValorReferencia(0.0, 30.0, "mg/dL"),

    # Função Renal
    "creatinina_masculino": ValorReferencia(0.7, 1.3, "mg/dL"),
    "creatinina_feminino": ValorReferencia(0.5, 1.1, "mg/dL"),
    "ureia": ValorReferencia(15.0, 45.0, "mg/dL"),
    "acido_urico_masculino": ValorReferencia(3.5, 7.2, "mg/dL"),
    "acido_urico_feminino": ValorReferencia(2.6, 6.0, "mg/dL"),

    # Função Hepática
    "tgo_ast": ValorReferencia(5.0, 40.0, "U/L"),
    "tgp_alt": ValorReferencia(5.0, 41.0, "U/L"),
    "ggt": ValorReferencia(8.0, 61.0, "U/L"),
    "fosfatase_alcalina": ValorReferencia(44.0, 147.0, "U/L"),
    "bilirrubina_total": ValorReferencia(0.3, 1.2, "mg/dL"),
    "bilirrubina_direta": ValorReferencia(0.0, 0.3, "mg/dL"),
    "bilirrubina_indireta": ValorReferencia(0.2, 0.8, "mg/dL"),
    "albumina": ValorReferencia(3.5, 5.0, "g/dL"),

    # Tireoide
    "tsh": ValorReferencia(0.4, 4.0, "mUI/L"),
    "t4_livre": ValorReferencia(0.8, 1.8, "ng/dL"),
    "t3_livre": ValorReferencia(2.3, 4.2, "pg/mL"),

    # Ferro e Anemia
    "ferro_serico": ValorReferencia(60.0, 170.0, "μg/dL"),
    "ferritina_masculino": ValorReferencia(22.0, 322.0, "ng/mL"),
    "ferritina_feminino": ValorReferencia(10.0, 291.0, "ng/mL"),
    "vitamina_b12": ValorReferencia(200.0, 900.0, "pg/mL"),
    "vitamina_d": ValorReferencia(30.0, 100.0, "ng/mL"),
    "acido_folico": ValorReferencia(4.6, 18.7, "ng/mL"),

    # Inflamação
    "pcr": ValorReferencia(0.0, 5.0, "mg/L"),
    "vhs_masculino": ValorReferencia(0.0, 15.0, "mm/h"),
    "vhs_feminino": ValorReferencia(0.0, 20.0, "mm/h"),

    # Eletrólitos
    "sodio": ValorReferencia(136.0, 145.0, "mEq/L", critico_min=120.0, critico_max=160.0),
    "potassio": ValorReferencia(3.5, 5.0, "mEq/L", critico_min=2.5, critico_max=6.5),
    "calcio": ValorReferencia(8.5, 10.5, "mg/dL"),
    "magnesio": ValorReferencia(1.7, 2.2, "mg/dL"),
}


DESCRICOES_PARAMETROS: Dict[str, str] = {
    "hemoglobina": "Proteína responsável pelo transporte de oxigênio no sangue.",
    "hematocrito": "Proporção do volume de glóbulos vermelhos em relação ao sangue total.",
    "leucocitos": "Glóbulos brancos responsáveis pela defesa imunológica.",
    "plaquetas": "Células responsáveis pela coagulação sanguínea.",
    "vgm": "Volume Globular Médio — tamanho médio dos glóbulos vermelhos.",
    "hgm": "Hemoglobina Globular Média — quantidade de hemoglobina por eritrócito.",
    "chgm": "Concentração de Hemoglobina Globular Média.",
    "glicose_jejum": "Nível de glicose no sangue em jejum — indicador de diabetes.",
    "hemoglobina_glicada": "Média da glicemia nos últimos 2–3 meses.",
    "colesterol_total": "Soma de todas as frações de colesterol no sangue.",
    "ldl": "Colesterol 'ruim' — associado ao risco cardiovascular.",
    "hdl": "Colesterol 'bom' — efeito protetor cardiovascular.",
    "triglicerideos": "Gorduras circulantes no sangue.",
    "vldl": "Lipoproteína de muito baixa densidade.",
    "creatinina": "Produto do metabolismo muscular — indicador da função renal.",
    "ureia": "Produto do metabolismo proteico — indicador da função renal.",
    "acido_urico": "Produto do metabolismo das purinas.",
    "tgo_ast": "Transaminase oxalacética — enzima hepática e muscular.",
    "tgp_alt": "Transaminase pirúvica — enzima específica do fígado.",
    "ggt": "Gama-glutamil transferase — marcador hepático e de alcoolismo.",
    "fosfatase_alcalina": "Enzima presente no fígado, ossos e intestino.",
    "bilirrubina_total": "Pigmento resultante da degradação da hemoglobina.",
    "albumina": "Principal proteína produzida pelo fígado.",
    "tsh": "Hormônio estimulante da tireoide.",
    "t4_livre": "Tiroxina livre — hormônio tireoidiano ativo.",
    "t3_livre": "Triiodotironina livre — hormônio tireoidiano mais ativo.",
    "ferro_serico": "Ferro circulante no sangue.",
    "ferritina": "Proteína de armazenamento de ferro.",
    "vitamina_b12": "Vitamina essencial para a formação de glóbulos vermelhos.",
    "vitamina_d": "Vitamina essencial para saúde óssea e imunológica.",
    "acido_folico": "Vitamina B9 — essencial para formação de células.",
    "pcr": "Proteína C Reativa — marcador de inflamação.",
    "vhs": "Velocidade de Hemossedimentação — marcador inespecífico de inflamação.",
    "sodio": "Principal eletrólito extracelular.",
    "potassio": "Principal eletrólito intracelular.",
    "calcio": "Mineral essencial para ossos, músculos e nervos.",
    "magnesio": "Mineral essencial para diversas reações enzimáticas.",
}
