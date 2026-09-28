import base64
import calendar
from datetime import datetime
import os
import sys
from fpdf import FPDF
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="ETE Sesc Bertioga - Cronograma e Operação",
    page_icon="💧",
    layout="wide",
)

# --- CONTROLO DE ACESSO POR SENHA ---
def verificar_senha():
    def senha_correta():
        if st.session_state["password"] == "bertioga2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 Acesso Restrito - ETE Sesc Bertioga")
    st.text_input("Digite a palavra-passe de acesso:", type="password", on_change=senha_correta, key="password")
    
    if "password_correct" in st.session_state:
        st.error("😕 Senha incorreta. Tente novamente.")
    return False

if not verificar_senha():
    st.stop()
# ------------------------------------

# --- INICIALIZAÇÃO SEGURA DO SESSION STATE ---
if "registros_atividades" not in st.session_state:
  st.session_state["registros_atividades"] = {}

# --- ESTILIZAÇÃO CSS ---
st.markdown(
    """
    <style>
        .header-container {
            background-color: #003366;
            padding: 20px;
            border-radius: 8px;
            color: white;
            margin-bottom: 20px;
        }
        .header-container h1, .header-container p {
            color: white !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #003366 !important;
            color: white !important;
        }
        .stMultiSelect [data-baseweb="tag"] span {
            color: white !important;
        }
        span[data-baseweb="tag"] {
            background-color: #003366 !important;
        }
        div[data-baseweb="select"] > div:focus-within, 
        div[data-baseweb="select"] > div:hover,
        .stMultiSelect div[data-baseweb="select"] > div {
            border-color: #003366 !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- LOGOTIPO EMBUTIDO ---
LOGO_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAXQAAACAAAAE..."


def resolve_path(path):
  if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
  else:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, path)


logo_path = resolve_path("logo.jpg")
if not os.path.exists(logo_path):
  try:
    with open(logo_path, "wb") as fh:
      fh.write(base64.b64decode(LOGO_BASE64))
  except Exception:
    pass

# --- LISTAS DA EQUIPE ---
LISTA_OPERADORES = ["Ícaro", "Matheus", "Wagner", "Lenine"]
LISTA_MECANICOS = ["Cesar"]
LISTA_ELETROTECNICOS = ["Paulo"]
LISTA_SUPERVISORES = ["Genilson"]

# --- MOTIVOS DE EXCEÇÃO ---
LISTA_MOTIVOS = [
    "Chuvas intensas",
    "Vazão alta",
    "Acompanhamento de limpezas programadas",
    "Falta de carga na estação",
    "Equipamento em manutenção",
    "Outro (Especificar)",
]


# --- CLASSE PARA GERAÇÃO DO PDF EM PAISAGEM ---
class PDFReport(FPDF):

  def header(self):
    logo_file = resolve_path("logo.jpg")
    if os.path.exists(logo_file):
      try:
        self.image(logo_file, 10, 8, 25)
      except Exception:
        pass
    self.set_font("Helvetica", "B", 13)
    self.set_text_color(0, 51, 102)
    self.cell(
        0,
        8,
        "ESTAÇÃO DE TRATAMENTO DE ESGOTO - SESC BERTIOGA",
        0,
        1,
        "C",
    )
    self.set_font("Helvetica", "", 9)
    self.set_text_color(100, 100, 100)
    self.cell(
        0,
        5,
        "Cronograma de Operação, Controlo Diário e Atividades (Contrato nº"
        " 851.188)",
        0,
        1,
        "C",
    )
    self.ln(5)

  def footer(self):
    self.set_y(-15)
    self.set_font("Helvetica", "I", 8)
    self.set_text_color(150, 150, 150)
    self.cell(
        0,
        10,
        (
            "Página "
            f"{self.page_no()} | <span class='notranslate'"
            ' translate="no">Tecwater Systems</span> Soluções em Saneamento'
        ),
        0,
        0,
        "C",
    )


def gerar_pdf_relatorio(mes_nome, ano, dados_atividades):
  pdf = PDFReport(orientation="L", unit="mm", format="A4")
  pdf.set_auto_page_break(auto=True, margin=15)
  pdf.add_page()

  # --- PÁGINA 1: CRONOGRAMA DE ATIVIDADES ---
  pdf.set_font("Helvetica", "B", 11)
  pdf.set_fill_color(0, 51, 102)
  pdf.set_text_color(255, 255, 255)
  pdf.cell(
      0,
      8,
      f" CRONOGRAMA DE OPERAÇÃO - {mes_nome.upper()} DE {ano} (CONTRATO Nº"
      " 851.188)",
      1,
      1,
      "C",
      True,
  )
  pdf.ln(4)

  # Cabeçalho da Tabela
  pdf.set_font("Helvetica", "B", 8)
  pdf.set_fill_color(230, 235, 240)
  pdf.set_text_color(0, 0, 0)
  pdf.cell(75, 7, "Atividade Programada", 1, 0, "L", True)
  pdf.cell(55, 7, "Equipe / Executores", 1, 0, "L", True)
  pdf.cell(32, 7, "Dias Executados", 1, 0, "C", True)
  pdf.cell(55, 7, "Comprovação Fotográfica", 1, 0, "C", True)
  pdf.cell(60, 7, "Status / Motivo", 1, 1, "C", True)

  pdf.set_font("Helvetica", "", 8)
  if not dados_atividades:
    pdf.cell(
        277, 8, "Nenhuma atividade registada neste período.", 1, 1, "C"
    )
  else:
    for item in dados_atividades:
      y_antes = pdf.get_y()
      if y_antes > 155:
        pdf.add_page()
        y_antes = pdf.get_y()

      x_inicio = pdf.get_x()
      y_inicio = pdf.get_y()

      pdf.set_font("Helvetica", "", 7)
      h_ativ = pdf.get_string_width(item["atividade"]) / 75 * 3.5 + 8
      h_exec = pdf.get_string_width(item["executores"]) / 55 * 3.5 + 8
      status_full = item["status"]
      if item["motivo"]:
        status_full += f" ({item['motivo']})"
      h_stat = pdf.get_string_width(status_full) / 60 * 3.5 + 8
      altura_linha = max(22, h_ativ, h_exec, h_stat)

      pdf.rect(x_inicio, y_inicio, 75, altura_linha)
      pdf.set_xy(x_inicio + 1, y_inicio + 1)
      pdf.multi_cell(73, 3.5, item["atividade"], border=0, align="L")

      pdf.rect(x_inicio + 75, y_inicio, 55, altura_linha)
      pdf.set_xy(x_inicio + 76, y_inicio + 1)
      pdf.multi_cell(53, 3.5, item["executores"], border=0, align="L")

      pdf.set_xy(x_inicio + 130, y_inicio)
      pdf.cell(32, altura_linha, item["dias"][:18], 1, 0, "C")

      x_foto = pdf.get_x()
      y_foto = pdf.get_y()
      pdf.cell(55, altura_linha, "", 1, 0, "C")

      if item["foto_path"] and os.path.exists(item["foto_path"]):
        try:
          pdf.image(
              item["foto_path"],
              x=x_foto + 12,
              y=y_foto + 2,
              w=30,
              h=altura_linha - 4,
          )
        except Exception:
          pdf.set_xy(x_foto, y_foto + (altura_linha / 2) - 2)
          pdf.cell(55, 4, "Erro ao carregar", 0, 0, "C")
      else:
        pdf.set_xy(x_foto, y_foto + (altura_linha / 2) - 2)
        pdf.cell(55, 4, "Sem registo fotográfico", 0, 0, "C")

      pdf.rect(x_foto + 55, y_inicio, 60, altura_linha)
      pdf.set_xy(x_foto + 56, y_inicio + 1)
      pdf.multi_cell(58, 3.5, status_full, border=0, align="L")

      pdf.set_xy(10, y_inicio + altura_linha)

  # --- PÁGINA 2: RESUMO ACUMULADO POR OPERADOR E TOTAL GERAL ---
  pdf.add_page()
  pdf.set_font("Helvetica", "B", 11)
  pdf.set_fill_color(0, 51, 102)
  pdf.set_text_color(255, 255, 255)
  pdf.cell(
      0,
      8,
      f" RESUMO ACUMULADO DE ATIVIDADES POR OPERADOR - {mes_nome.upper()} DE"
      f" {ano}",
      1,
      1,
      "C",
      True,
  )
  pdf.ln(4)

  resumo_ops = {op: {"total_dias": 0, "detalhes": []} for op in LISTA_OPERADORES}
  total_geral_atividades_mes = 0

  for item in dados_atividades:
    executores_str = item["executores"]
    dias_str = item["dias"]
    dias_lista = []
    if dias_str and dias_str != "Sem dias marcados":
      dias_lista = [d.strip() for d in dias_str.split(",") if d.strip()]
    qtd_dias = len(dias_lista) if dias_lista else 1

    if "Op:" in executores_str:
      partes = executores_str.split("|")
      for p in partes:
        if "Op:" in p:
          nomes_str = p.replace("Op:", "").strip()
          ops_aqui = [n.strip() for n in nomes_str.split(",") if n.strip()]
          for op in ops_aqui:
            if op in resumo_ops:
              resumo_ops[op]["total_dias"] += qtd_dias
              total_geral_atividades_mes += qtd_dias
              resumo_ops[op]["detalhes"].append(
                  f"- {item['atividade']} (Dias: {dias_str})"
              )

  # Tabela de Resumo no PDF
  pdf.set_font("Helvetica", "B", 9)
  pdf.set_fill_color(230, 235, 240)
  pdf.set_text_color(0, 0, 0)
  pdf.cell(50, 7, "Operador", 1, 0, "L", True)
  pdf.cell(35, 7, "Total Ativ. / Dias", 1, 0, "C", True)
  pdf.cell(192, 7, "Atividades Executadas e Dias", 1, 1, "L", True)

  pdf.set_font("Helvetica", "", 8)
  for op, info in resumo_ops.items():
    y_antes = pdf.get_y()
    detalhes_texto = (
        "\n".join(info["detalhes"])
        if info["detalhes"]
        else "Nenhuma atividade registada"
    )
    # Altura de linha ajustada com espaçamento seguro (6mm por linha) para evitar sobreposição
    num_linhas_detalhe = max(1, len(info["detalhes"]))
    altura_linha = max(12, num_linhas_detalhe * 6 + 4)

    if y_antes + altura_linha > 175:
      pdf.add_page()
      y_antes = pdf.get_y()

    pdf.cell(50, altura_linha, op, 1, 0, "L")
    pdf.cell(35, altura_linha, str(info["total_dias"]), 1, 0, "C")

    x_pos = pdf.get_x()
    y_pos = pdf.get_y()
    pdf.cell(192, altura_linha, "", 1, 0, "L")
    pdf.set_xy(x_pos + 2, y_pos + 2)
    pdf.multi_cell(188, 4.5, detalhes_texto, border=0, align="L")
    pdf.set_xy(10, y_pos + altura_linha)

  # Linha de Total Geral no PDF
  pdf.ln(2)
  pdf.set_font("Helvetica", "B", 9)
  pdf.set_fill_color(240, 240, 240)
  pdf.cell(
      50,
      8,
      "TOTAL GERAL DA EQUIPE",
      1,
      0,
      "L",
      True,
  )
  pdf.cell(
      35,
      8,
      str(total_geral_atividades_mes),
      1,
      0,
      "C",
      True,
  )
  pdf.cell(
      192,
      8,
      "Soma acumulada de todas as execuções e dias no período",
      1,
      1,
      "L",
      True,
  )

  pdf_output_bytes = pdf.output(dest="S").encode("latin1")

  for item in dados_atividades:
    f_path = item.get("foto_path")
    if f_path and os.path.exists(f_path):
      try:
        os.remove(f_path)
      except Exception:
        pass

  return pdf_output_bytes


# --- INTERFACE PRINCIPAL ---
logo_file = resolve_path("logo.jpg")

bloco_cabecalho = """
    <div class="header-container">
        <h1 style="margin:0; font-size: 24px;">ETE Sesc Bertioga - Cronograma e Operação</h1>
        <p style="margin:5px 0 0 0; font-size: 14px;">Controle Diário e Periódico de Atividades — Contrato nº 851.188 | <span class="notranslate" translate="no">Tecwater Systems</span></p>
    </div>
"""

if os.path.exists(logo_file):
  col_logo, col_titulo = st.columns([1, 5])
  with col_logo:
    st.image(logo_file, width="stretch")
  with col_titulo:
    st.markdown(bloco_cabecalho, unsafe_allow_html=True)
else:
  st.markdown(bloco_cabecalho, unsafe_allow_html=True)

st.markdown("---")

# --- BARRA LATERAL ---
with st.sidebar:
  st.markdown("### 💧 Painel de Controle")
  ano = st.selectbox("Ano", [2026, 2027], key="sel_ano")
  meses_dict = {
      1: "Janeiro",
      2: "Fevereiro",
      3: "Março",
      4: "Abril",
      5: "Maio",
      6: "Junho",
      7: "Julho",
      8: "Agosto",
      9: "Setembro",
      10: "Outubro",
      11: "Novembro",
      12: "Dezembro",
  }
  mes_nome = st.selectbox(
      "Mês",
      list(meses_dict.values()),
      index=8 if ano == 2026 else 0,
      key="sel_mes",
  )
  mes_num = [k for k, v in meses_dict.items() if v == mes_nome][0]
  num_dias = calendar.monthrange(ano, mes_num)[1]

  st.markdown("---")
  st.info(f"📅 **Período Selecionado:** {mes_nome} de {ano}")

  # --- CALENDÁRIO OPERACIONAL ---
  st.markdown("---")
  st.markdown("### 📅 Calendário Operacional")
  st.markdown(f"**{mes_nome} de {ano}**")

  dias_com_atividade = set()
  for atv_data in st.session_state["registros_atividades"].values():
    dias_str = atv_data.get("dias", "")
    if dias_str and dias_str != "Sem dias marcados":
      for d_split in dias_str.split(","):
        try:
          dias_com_atividade.add(int(d_split.strip()))
        except:
          pass

  cal = calendar.monthcalendar(ano, mes_num)

  html_cal = (
      "<table style='width:100%; text-align:center; font-family:monospace;"
      " font-size:13px; border-collapse:collapse;' class='notranslate'"
      " translate='no'>\n"
  )
  html_cal += (
      "<tr><th>Seg</th><th>Ter</th><th>Qua</th><th>Qui</th><th"
      " class='notranslate' translate='no'>Sexta</th><th>Sáb</th><th>Dom</th></tr>\n"
  )

  for semana in cal:
    html_cal += "<tr>\n"
    for d in semana:
      if d == 0:
        html_cal += "<td style='padding:4px;'></td>\n"
      elif d in dias_com_atividade:
        html_cal += (
            "<td style='padding:4px;'><span"
            f" style='background-color:#000000; color:#ffffff; padding:2px 6px;"
            f" border-radius:3px; font-weight:bold;'>{d:02d}</span></td>\n"
        )
      else:
        html_cal += f"<td style='padding:4px; color:#333333;'>{d:02d}</td>\n"
    html_cal += "</tr>\n"
  html_cal += "</table>"

  st.markdown(html_cal, unsafe_allow_html=True)
  st.markdown(
      "<small>* Os números com fundo preto indicam dias com atividades"
      " registadas.</small>",
      unsafe_allow_html=True,
  )

st.markdown(
    "📌 *Instruções: Selecione os responsáveis por função, marque os dias"
    " executados, defina o status e envie a foto se necessário. **Atenção: é"
    " obrigatório clicar no botão 'Salvar Registro da Atividade' em cada item"
    " para que os dados sejam salvos e incluídos no relatório PDF!***"
)

# --- LISTA DE ATIVIDADES ---
atividades_base = [
    (
        "Receber pendências, verificar alarmes, registros anteriores e"
        " orientações",
        "Início de cada turno",
        "Operador técnico",
    ),
    (
        "Realizar ronda geral da ETE: equipamentos, tanques, aeração, dosagens,"
        " membranas",
        "Cada turno",
        "Operador técnico",
    ),
    (
        "Monitorar supervisório, parâmetros operacionais, alarmes,"
        " ocorrências e desvios",
        "Contínuo em cada turno",
        "Operador técnico",
    ),
    (
        "Inspecionar as seis elevatórias: bombeamento, níveis, limpeza,"
        " alarmes e anomalias",
        "Diária e por ocorrência",
        "Operador técnico",
    ),
    (
        "Avaliar visual e olfativamente efluente bruto e tratado, licor"
        " misto, lodo, espuma, óleo",
        "Cada turno",
        "Operador técnico",
    ),
    (
        "Confirmar funcionamento dos equipamentos e dosagem dos produtos"
        " químicos",
        "Cada turno",
        "Operador técnico",
    ),
    (
        "Medir pH, turbidez, oxigênio dissolvido e sólidos sedimentáveis",
        "Uma vez por turno",
        "Operador técnico",
    ),
    (
        "Registrar dados operacionais em planilhas eletrônicas e avaliar"
        " desempenho",
        "Diária",
        "Operador técnico",
    ),
    (
        "Verificar instrumentos de processo e comunicar anormalidades de"
        " medição",
        "Durante a rotina",
        "Operador / ELE",
    ),
    (
        "Limpar a entrada do pré-tratamento com rastelo e destinar os materiais",
        "Diária / Conforme necessidade",
        "Operador técnico",
    ),
    (
        "Verificar estoques, dosagens, armazenamento de produtos e reagentes",
        "Diária",
        "Operador técnico",
    ),
    (
        "Limpar e organizar áreas, oficinas, painéis, bancadas e EPIs (5S)",
        "Diária / Após intervenções",
        "Todos os envolvidos",
    ),
    (
        "Segregar resíduos e atender às normas de coleta seletiva",
        "Contínuo",
        "Todos os envolvidos",
    ),
    (
        "Emitir e completar o RDO, comunicar desvios e transmitir pendências",
        "Fim de cada turno",
        "OP / MEC / ELE",
    ),
    (
        "Executar série de sólidos SST, SSV e SSF nos tanques de aeração",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Limpar o gradil com rastelo, preferencialmente com o SESC fechado",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Inspecionar VRM, sólidos nas câmaras e tendências do processo",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Executar coleta/processamento de DBO5 e análise de DQO",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Iniciar coleta composta de 24h na entrada e saída com pH",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Concluir coleta composta e executar DBO5, DQO, nitrato e fósforo total",
        "Semanal",
        "Operador técnico",
    ),
    (
        "Confrontar previsto e realizado, ajustar prioridades e programação",
        "Semanal",
        "Supervisor / SESC",
    ),
    (
        "Executar inspeções mecânicas preventivas e tratar anomalias",
        "Conforme plano",
        "Técnico mecânico",
    ),
    (
        "Verificar painéis, sinais, proteções e instrumentos elétricos",
        "Conforme plano",
        "Técnico eletricista",
    ),
    (
        "Realizar inventário físico e projeção de consumo de químicos e óleos",
        "Mensal / Quinzenal",
        "Supervisor técnico",
    ),
    (
        "Atualizar vencimentos de manutenção/limpezas e emitir cronograma",
        "Mensal",
        "Supervisor / SESC",
    ),
    (
        "Distribuir inspeções de bombas, sopradores, desidratação e PLC",
        "Mensal",
        "MEC / ELE",
    ),
    (
        "Realizar inspeções de segurança e testes do chuveiro e lava-olhos",
        "Mensal",
        "Supervisor / Equipe",
    ),
    (
        "Apurar indicadores: conclusão, pendências, ocorrências e tempos",
        "Mensal",
        "Supervisor técnico",
    ),
    (
        "Consolidar Relatório Técnico Mensal de Operação",
        "Mensal",
        "Supervisor / Eng.",
    ),
    (
        "Organizar RDOs, evidências e relatório mensal no ViaWeb",
        "Mensal",
        "Supervisor técnico",
    ),
    (
        "Executar sucção e hidrojateamento das seis elevatórias",
        "Trimestral / Semestral",
        "Equipe especializada",
    ),
    ("Limpar caixas de gordura e caixas de areia", "Trimestral", "Equipe esp."),
    ("Limpar o Tanque 500", "Semestral / Anual", "Equipe esp. + OP"),
    ("Executar inspeção semestral do VRM e manual", "Semestral", "MEC + ESP"),
    ("Executar inspeções elétricas semestrais", "Semestral", "Eletricista"),
    (
        "Limpar aproximadamente 4.500m da rede coletora e caixas de inspeção",
        "Anual",
        "Equipe esp. + OP",
    ),
    (
        "Executar revisões anuais de VRM, desidratação e equipamentos",
        "Anual",
        "MEC / ELE + ESP",
    ),
    (
        "Calibrar instrumentos de processo e equipamentos de bancada",
        "Anual",
        "Especialista + OP",
    ),
    (
        "Diagnosticar desvios, repetir medições e adotar ajustes",
        "Sob demanda",
        "OP / SUP",
    ),
    (
        "Produzir registros fotográficos nítidos para ocorrências",
        "Por ocorrência",
        "Responsável",
    ),
    (
        "Registrar acessos, acompanhar visitantes e equipes terceiras",
        "Sempre que houver",
        "Operador técnico",
    ),
    (
        "Acompanhar recebimento de caminhão-fossa ou lodo externo",
        "Por ocorrência",
        "Operador técnico",
    ),
    (
        "Solicitar manutenção ou calibração e acompanhar intervenção",
        "Condicional",
        "OP / SUP / ELE",
    ),
    (
        "Acompanhar desidratação e manejo do lodo",
        "Condicional",
        "Operador técnico",
    ),
    (
        "Programar retirada e transporte de resíduos com MTR/CADRI",
        "Condicional",
        "SUP / OP",
    ),
    (
        "Realizar coletas externas conforme Plano de Amostragem",
        "Conforme plano",
        "OP + Laboratório",
    ),
    ("Receber e conferir reagentes e produtos químicos", "Por entrega", "Operador"),
    (
        "Executar limpeza química das membranas CIP",
        "Conforme colmatação",
        "OP + Técnico",
    ),
    (
        "Conferir válvulas, comandos, testes e limpeza após manutenção",
        "Pós-manutenção",
        "Executante + OP",
    ),
    (
        "Registrar treinamentos, orientações de segurança, EPIs e 5S",
        "Periódico",
        "Supervisor",
    ),
    (
        "Registrar propostas de melhorias aplicadas na ETE",
        "Contínuo",
        "Supervisor / Eng.",
    ),
]

for idx, (atividade, frequencia, cargo_sugerido) in enumerate(atividades_base):
  with st.expander(
      f"🔵 {atividade} — [{cargo_sugerido} | {frequencia}]"
  ):
    with st.form(key=f"form_ativ_{idx}"):
      col_f1, col_f2, col_f3, col_f4 = st.columns(4)
      with col_f1:
        st.markdown("**Operador**")
        nomes_op = st.multiselect(
            "Selecionar Operadores",
            LISTA_OPERADORES,
            key=f"nomes_op_{idx}",
            label_visibility="collapsed",
        )
      with col_f2:
        st.markdown("**Supervisor**")
        nomes_sup = st.multiselect(
            "Selecionar Supervisores",
            LISTA_SUPERVISORES,
            key=f"nomes_sup_{idx}",
            label_visibility="collapsed",
        )
      with col_f3:
        st.markdown("**Mecânico**")
        nomes_mec = st.multiselect(
            "Selecionar Mecânicos",
            LISTA_MECANICOS,
            key=f"nomes_mec_{idx}",
            label_visibility="collapsed",
        )
      with col_f4:
        st.markdown("**Eletrotécnico**")
        nomes_ele = st.multiselect(
            "Selecionar Eletrotécnicos",
            LISTA_ELETROTECNICOS,
            key=f"nomes_ele_{idx}",
            label_visibility="collapsed",
        )

      st.markdown("---")
      st.markdown("##### Dias Executados:")
      cols = st.columns(min(num_dias, 10))
      dias_marcados = []
      for d in range(1, num_dias + 1):
        c_idx = (d - 1) % 10
        with cols[c_idx]:
          if st.checkbox(f"Dia {d}", key=f"atv_{idx}d{d}"):
            dias_marcados.append(d)

      col_status, col_foto = st.columns([2, 2])
      with col_status:
        status_item = st.selectbox(
            "Status",
            [
                "Concluído",
                "Incompleta",
                "Não Executada",
                "Pendente",
                "Não Aplicável",
            ],
            key=f"status_{idx}",
        )
      with col_foto:
        foto_file = st.file_uploader(
            "Comprovação Fotográfica",
            type=["png", "jpg", "jpeg"],
            key=f"foto_{idx}",
        )

      motivo_final = ""
      if status_item in ["Incompleta", "Não Executada"]:
        st.markdown("---")
        st.warning(
            f"⚠️ A atividade foi marcada como **{status_item}**. Por favor,"
            " selecione o motivo abaixo:"
        )
        motivo_selecionado = st.selectbox(
            "Motivo da Incompletude / Não Execução",
            LISTA_MOTIVOS,
            key=f"motivo_sel_{idx}",
        )
        if motivo_selecionado == "Outro (Especificar)":
          motivo_final = st.text_input(
              "Especifique o motivo:", key=f"motivo_outro_{idx}"
          )
        else:
          motivo_final = motivo_selecionado

      st.info(
          "⚠️ **Lembrete:** Clique em 'Salvar Registro da Atividade' abaixo"
          " para gravar as informações antes de gerar o PDF."
      )
      submitted = st.form_submit_button("💾 Salvar Registro da Atividade")

      if submitted:
        executores_lista = []
        if nomes_op:
          executores_lista.append(f"Op: {', '.join(nomes_op)}")
        if nomes_sup:
          executores_lista.append(f"Sup: {', '.join(nomes_sup)}")
        if nomes_mec:
          executores_lista.append(f"Mec: {', '.join(nomes_mec)}")
        if nomes_ele:
          executores_lista.append(f"Ele: {', '.join(nomes_ele)}")

        str_executores = (
            " | ".join(executores_lista)
            if executores_lista
            else "Não especificado"
        )
        dias_str = (
            ", ".join(map(str, dias_marcados))
            if dias_marcados
            else "Sem dias marcados"
        )

        foto_path_temp = None
        if foto_file is not None:
          foto_path_temp = f"temp_foto_{idx}.jpg"
          with open(foto_path_temp, "wb") as f:
            f.write(foto_file.getbuffer())

        st.session_state["registros_atividades"][atividade] = {
            "atividade": atividade,
            "executores": str_executores,
            "dias": dias_str,
            "foto_path": foto_path_temp,
            "status": status_item,
            "motivo": motivo_final,
        }
        st.success(
            "Atividade guardada com sucesso! O calendário lateral foi atualizado."
        )
        st.rerun()

st.markdown("---")

# --- SECÇÃO DE GERAÇÃO DO RELATÓRIO PDF ---
st.markdown("### 📥 Geração de Relatório PDF")
st.markdown(
    "Gere o relatório completo em formato paisagem (A4) contendo o cronograma"
    " detalhado nas primeiras páginas e o **resumo acumulado com o total geral"
    " da equipe** na última página."
)

lista_dados_pdf = list(st.session_state["registros_atividades"].values())

if st.button("📄 Gerar e Descarregar Relatório PDF"):
  try:
    pdf_bytes = gerar_pdf_relatorio(mes_nome, ano, lista_dados_pdf)
    st.success("Relatório gerado com sucesso!")
    st.download_button(
        label="📥 Clique aqui para baixar o PDF",
        data=pdf_bytes,
        file_name=f"Cronograma_ETE_Bertioga_{mes_nome}_{ano}.pdf",
        mime="application/pdf",
    )
  except Exception as e:
    st.error(f"Erro ao gerar relatório: {e}")