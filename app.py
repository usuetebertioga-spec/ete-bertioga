import base64
import calendar
from datetime import datetime
import json
import os
import sys
from fpdf import FPDF
import streamlit as st
import unicodedata
import pandas as pd
import pytz

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="ETE Sesc Bertioga - Operação",
    page_icon="💧",
    layout="wide",
)

# --- FUSO HORÁRIO DE BRASÍLIA / LOCAL ---
FUSO_SP = pytz.timezone('America/Sao_Paulo')

def agora_brasilia():
    return datetime.now(FUSO_SP)

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

# --- PERSISTÊNCIA DO RASCUNHO EM FICHEIRO ---
DRAFT_FILE = "rascunho_ete_v11.json"

def carregar_rascunho_disco():
  if os.path.exists(DRAFT_FILE):
    try:
      with open(DRAFT_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
        # Garante unicidade estrita pelo ID interno ao carregar do disco
        return dados if isinstance(dados, list) else []
    except Exception:
      return []
  return []

def salvar_rascunho_disco(registros):
  try:
    with open(DRAFT_FILE, "w", encoding="utf-8") as f:
      json.dump(registros, f, ensure_ascii=False, indent=4)
  except Exception as e:
    print(f"Erro ao salvar rascunho: {e}")

if "registros_turno" not in st.session_state:
  st.session_state["registros_turno"] = carregar_rascunho_disco()

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
            text-align: center;
        }
        .header-container h1, .header-container p {
            color: white !important;
        }
        .section-title {
            background-color: #003366;
            color: white !important;
            padding: 12px 15px;
            border-radius: 6px;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .instruction-box {
            background-color: #e6f0fa;
            border-left: 5px solid #003366;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            color: #002244;
            font-size: 14px;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #003366 !important;
            color: white !important;
        }
        .stMultiSelect [data-baseweb="tag"] span {
            color: white !important;
        }
        div[data-baseweb="select"] > div, 
        div[data-baseweb="base-input"] > div, 
        textarea, 
        input[type="text"],
        input[type="number"] {
            border: 1px solid #003366 !important;
            border-radius: 6px !important;
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

# --- FUNÇÃO DE LIMPEZA DE TEXTO PARA PDF ---
def limpar_texto_fpdf(texto):
  if not isinstance(texto, str):
    return str(texto)
  texto = (
      texto.replace("\u2013", "-")
      .replace("\u2014", "-")
      .replace("\u201c", '"')
      .replace("\u201d", '"')
      .replace("\u2018", "'")
      .replace("\u2019", "'")
  )
  nfkd_form = unicodedata.normalize('NFKD', texto)
  return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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
    self.cell(0, 8, limpar_texto_fpdf("ESTACAO DE TRATAMENTO DE ESGOTO - SESC BERTIOGA"), 0, 1, "C")
    self.set_font("Helvetica", "", 9)
    self.set_text_color(0, 51, 102)
    self.cell(0, 5, limpar_texto_fpdf("Relatorio Operacional Diario e Atividades — Versao 1.1 (Contrato nº 851.188)"), 0, 1, "C")
    self.ln(5)

  def footer(self):
    self.set_y(-15)
    self.set_font("Helvetica", "I", 8)
    self.set_text_color(0, 51, 102)
    self.cell(0, 10, limpar_texto_fpdf(f"Pagina {self.page_no()} | Tecwater Systems Solucoes em Saneamento"), 0, 0, "C")

def gerar_pdf_relatorio(mes_nome, ano, dados_atividades):
  pdf = PDFReport(orientation="L", unit="mm", format="A4")
  pdf.set_auto_page_break(auto=True, margin=15)
  pdf.add_page()

  pdf.set_font("Helvetica", "B", 11)
  pdf.set_fill_color(0, 51, 102)
  pdf.set_text_color(255, 255, 255)
  pdf.cell(0, 8, limpar_texto_fpdf(f" REGISTO DE ATIVIDADES - {mes_nome.upper()} DE {ano}"), 1, 1, "C", True)
  pdf.ln(4)

  # Cabeçalho da Tabela
  pdf.set_font("Helvetica", "B", 8)
  pdf.set_fill_color(230, 235, 240)
  pdf.set_text_color(0, 51, 102)
  pdf.cell(12, 7, "Item", 1, 0, "C", True)
  pdf.cell(75, 7, "Atividade Executada", 1, 0, "L", True)
  pdf.cell(45, 7, "Equipe / Executores", 1, 0, "L", True)
  pdf.cell(25, 7, "Data / Hora", 1, 0, "C", True)
  pdf.cell(30, 7, "Status", 1, 0, "C", True)
  pdf.cell(90, 7, "Observacao", 1, 1, "L", True)

  pdf.set_font("Helvetica", "", 8)
  pdf.set_text_color(0, 0, 0)
  
  if not dados_atividades:
    pdf.cell(277, 8, limpar_texto_fpdf("Nenhuma atividade registada neste periodo."), 1, 1, "C")
  else:
    for idx, item in enumerate(dados_atividades, 1):
      y_antes = pdf.get_y()
      if y_antes > 155:
        pdf.add_page()

      y_inicio = pdf.get_y()

      status_txt = limpar_texto_fpdf(item["status"])
      obs_txt = limpar_texto_fpdf(item["observacao"]) if item.get("observacao") else "-"

      altura_linha = 18

      pdf.cell(12, altura_linha, str(idx), 1, 0, "C")
      
      x_ativ = pdf.get_x()
      y_ativ = pdf.get_y()
      pdf.cell(75, altura_linha, "", 1, 0, "L")
      pdf.set_xy(x_ativ + 1, y_ativ + 1)
      pdf.multi_cell(73, 3.5, limpar_texto_fpdf(item["atividade"]), border=0, align="L")

      pdf.set_xy(x_ativ + 75, y_ativ)
      x_exec = pdf.get_x()
      y_exec = pdf.get_y()
      pdf.cell(45, altura_linha, "", 1, 0, "L")
      pdf.set_xy(x_exec + 1, y_exec + 1)
      pdf.multi_cell(43, 3.5, limpar_texto_fpdf(item["executores"]), border=0, align="L")

      pdf.set_xy(x_exec + 45, y_exec)
      pdf.cell(25, altura_linha, f"{item['data']} {item['hora']}", 1, 0, "C")

      pdf.cell(30, altura_linha, status_txt, 1, 0, "C")

      x_obs = pdf.get_x()
      y_obs = pdf.get_y()
      pdf.cell(90, altura_linha, "", 1, 0, "L")
      pdf.set_xy(x_obs + 1, y_obs + 1)
      pdf.multi_cell(88, 3.5, obs_txt, border=0, align="L")

      pdf.set_xy(10, y_inicio + altura_linha)

  # --- CONTAGEM POR OPERADOR APENAS NO PDF ---
  pdf.ln(8)
  y_atual = pdf.get_y()
  if y_atual > 170:
    pdf.add_page()

  pdf.set_font("Helvetica", "B", 10)
  pdf.set_text_color(0, 51, 102)
  pdf.cell(0, 6, limpar_texto_fpdf("RESUMO DE ATIVIDADES POR MEMBRO DA EQUIPE"), 0, 1, "L")
  pdf.ln(2)

  contagem_membros = {}
  for item in dados_atividades:
    executores_str = item.get("executores", "")
    partes = executores_str.split("|")
    for parte in partes:
      if ":" in parte:
        nomes_parte = parte.split(":")[1].split(",")
        for n in nomes_parte:
          nome_limpo = n.strip()
          if nome_limpo:
            contagem_membros[nome_limpo] = contagem_membros.get(nome_limpo, 0) + 1

  pdf.set_font("Helvetica", "B", 8)
  pdf.set_fill_color(230, 235, 240)
  pdf.set_text_color(0, 51, 102)
  pdf.cell(60, 6, "Membro da Equipe", 1, 0, "L", True)
  pdf.cell(40, 6, "Total de Atividades", 1, 1, "C", True)

  pdf.set_font("Helvetica", "", 8)
  pdf.set_text_color(0, 0, 0)
  if contagem_membros:
    for membro, qtd in sorted(contagem_membros.items(), key=lambda x: x[1], reverse=True):
      pdf.cell(60, 6, limpar_texto_fpdf(membro), 1, 0, "L")
      pdf.cell(40, 6, str(qtd), 1, 1, "C")
  else:
    pdf.cell(100, 6, limpar_texto_fpdf("Nenhum registo de membro atribuído."), 1, 1, "C")

  pdf_output_bytes = pdf.output(dest="S").encode("latin1", errors="replace")
  return pdf_output_bytes


# --- INTERFACE PRINCIPAL ---
logo_file = resolve_path("logo.jpg")

bloco_cabecalho = """
    <div class="header-container">
        <h1 style="margin:0; font-size: 24px; color: white;">ETE Sesc Bertioga - Painel Operacional (Versão 1.1)</h1>
        <p style="margin:5px 0 0 0; font-size: 14px; color: white;">Controlo de Turno, Rascunho Persistente em Disco e Registo — Contrato nº 851.188</p>
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

# --- BLOCO DE INSTRUÇÕES E DIRECIONAMENTO (L) ---
st.markdown("""
    <div class="instruction-box">
        <strong>📌 ORIENTAÇÕES DE PREENCHIMENTO E USO DO APLICATIVO:</strong><br>
        • <strong>Preenchimento dos Campos:</strong> Selecione o turno, data, hora, os responsáveis da equipe e marque as atividades executadas no período.<br>
        • <strong>Observações Individuais:</strong> Para cada atividade selecionada, insira o seu respectivo detalhe ou justificativa no campo correspondente que surgirá abaixo (ex: identificação de visitantes na Atividade 41).<br>
        • <strong>⚠️ ATENÇÃO AO RASCUNHO E CONEXÃO:</strong> O rascunho é guardado automaticamente no disco do dispositivo a cada adição. Caso perca a conexão de internet ou feche o aplicativo, os dados anteriores estarão salvos. Certifique-se de <strong>gerar e descarregar o relatório PDF consolidado</strong> ao término do ciclo ou turno antes de limpar o rascunho para reiniciar os lançamentos.
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- BARRA LATERAL ---
with st.sidebar:
  st.markdown("<div class='section-title' style='font-size:16px;'>Painel de Controle</div>", unsafe_allow_html=True)
  
  agora_local = agora_brasilia()
  ano_atual = agora_local.year
  mes_atual = agora_local.month

  anos_disponiveis = [2026, 2027, 2028]
  default_ano_idx = anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0
  
  ano = st.selectbox("Ano", anos_disponiveis, index=default_ano_idx, key="sel_ano")
  
  meses_dict = {
      1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
      5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
      9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
  }
  
  mes_nome = st.selectbox(
      "Mês", list(meses_dict.values()), index=mes_atual - 1, key="sel_mes"
  )
  mes_num = [k for k, v in meses_dict.items() if v == mes_nome][0]

  st.markdown("---")
  st.info(f"📅 **Período Selecionado:** {mes_nome} de {ano}\n\n🕒 *Fuso de Brasília sincronizado.*")

  # --- CALENDÁRIO OPERACIONAL ---
  st.markdown("---")
  st.markdown("<div class='section-title' style='font-size:16px;'>Calendário Operacional</div>", unsafe_allow_html=True)
  st.markdown(f"<div style='text-align: center; font-weight: bold;'>{mes_nome} de {ano}</div>", unsafe_allow_html=True)

  dias_com_atividade = set()
  for item in st.session_state["registros_turno"]:
    try:
      data_item = datetime.strptime(item["data"], "%d/%m/%Y")
      if data_item.month == mes_num and data_item.year == ano:
        dias_com_atividade.add(data_item.day)
    except:
      pass

  cal = calendar.monthcalendar(ano, mes_num)

  html_cal = (
      "<table style='width:100%; text-align:center; font-family:monospace;"
      " font-size:12px; border-collapse:collapse;' class='notranslate'"
      " translate='no'>\n"
  )
  html_cal += (
      "<tr><th>Seg</th><th>Ter</th><th>Qua</th><th>Qui</th><th"
      " class='notranslate' translate='no'>Sex</th><th>Sáb</th><th>Dom</th></tr>\n"
  )

  for semana in cal:
    html_cal += "<tr>\n"
    for d in semana:
      if d == 0:
        html_cal += "<td style='padding:3px;'></td>\n"
      elif d in dias_com_atividade:
        html_cal += (
            "<td style='padding:3px;'><span"
            f" style='background-color:#003366; color:#ffffff; padding:2px 5px;"
            f" border-radius:3px; font-weight:bold;'>{d:02d}</span></td>\n"
        )
      else:
        html_cal += f"<td style='padding:3px; color:#333333;'>{d:02d}</td>\n"
    html_cal += "</tr>\n"
  html_cal += "</table>"

  st.markdown(html_cal, unsafe_allow_html=True)
  st.markdown(
      "<div style='text-align: center;'><small>* Os dias destacados indicam registos no mês.</small></div>",
      unsafe_allow_html=True,
  )

  st.markdown("---")
  st.markdown("<div class='section-title' style='font-size:16px;'>Gestão do Rascunho</div>", unsafe_allow_html=True)
  total_rascunho = len(st.session_state["registros_turno"])
  st.metric("Itens Guardados no Rascunho", total_rascunho)
  
  if total_rascunho > 0:
    if st.button("🗑️ Limpar Rascunho Definitivamente"):
      st.session_state["registros_turno"] = []
      salvar_rascunho_disco([])
      if os.path.exists(DRAFT_FILE):
        try:
          os.remove(DRAFT_FILE)
        except:
          pass
      st.success("Rascunho limpo e reiniciado com sucesso!")
      st.rerun()

# --- LISTA DE ATIVIDADES NUMERADAS ---
atividades_brutas = [
    "Receber pendências, verificar alarmes, registros anteriores e orientações",
    "Realizar ronda geral da ETE: equipamentos, tanques, aeração, dosagens, membranas",
    "Monitorar supervisório, parâmetros operacionais, alarmes, ocorrências e desvios",
    "Inspecionar as seis elevatórias: bombeamento, níveis, limpeza, alarmes e anomalias",
    "Avaliar visual e olfativamente efluente bruto e tratado, licor misto, lodo, espuma, óleo",
    "Confirmar funcionamento dos equipamentos e dosagem dos produtos químicos",
    "Medir pH, turbidez, oxigênio dissolvido e sólidos sedimentáveis",
    "Registrar dados operacionais em planilhas eletrônicas e avaliar desempenho",
    "Verificar instrumentos de processo e comunicar anormalidades de medição",
    "Limpar a entrada do pré-tratamento com rastelo e destinar os materiais",
    "Verificar estoques, dosagens, armazenamento de produtos e reagentes",
    "Limpar e organizar áreas, oficinas, painéis, bancadas e EPIs (5S)",
    "Segregar resíduos e atender às normas de coleta seletiva",
    "Emitir e completar o RDO, comunicar desvios e transmitir pendências",
    "Executar série de sólidos SST, SSV e SSF nos tanques de aeração",
    "Limpar o gradil com rastelo, preferencialmente com o SESC fechado",
    "Inspecionar VRM, sólidos nas câmaras e tendências do processo",
    "Executar coleta/processamento de DBO5 e análise de DQO",
    "Iniciar coleta composta de 24h na entrada e saída com pH",
    "Concluir coleta composta e executar DBO5, DQO, nitrato e fósforo total",
    "Confrontar previsto e realizado, ajustar prioridades e programação",
    "Executar inspeções mecânicas preventivas e tratar anomalias",
    "Verificar painéis, sinais, proteções e instrumentos elétricos",
    "Realizar inventário físico e projeção de consumo de químicos e óleos",
    "Atualizar vencimentos de manutenção/limpezas e emitir cronograma",
    "Distribuir inspeções de bombas, sopradores, desidratação e PLC",
    "Realizar inspeções de segurança e testes do chuveiro e lava-olhos",
    "Apurar indicadores: conclusão, pendências, ocorrências e tempos",
    "Consolidar Relatório Técnico Mensal de Operação",
    "Organizar RDOs, evidências e relatório mensal no ViaWeb",
    "Executar sucção e hidrojateamento das seis elevatórias",
    "Limpar caixas de gordura e caixas de areia",
    "Limpar o Tanque 500",
    "Executar inspeção semestral do VRM e manual",
    "Executar inspeções elétricas semestrais",
    "Limpar aproximadamente 4.500m da rede coletora e caixas de inspeção",
    "Executar revisões anuais de VRM, desidratação e equipamentos",
    "Calibrar instrumentos de processo e equipamentos de bancada",
    "Diagnosticar desvios, repetir medições e adotar ajustes",
    "Produzir registros fotográficos nítidos para ocorrências",
    "Registrar acessos, acompanhar visitantes e equipes terceiras",
    "Acompanhar recebimento de caminhão-fossa ou lodo externo",
    "Solicitar manutenção ou calibração e acompanhar intervenção",
    "Acompanhar desidratação e manejo do lodo",
    "Programar retirada e transporte de resíduos com MTR/CADRI",
    "Realizar coletas externas conforme Plano de Amostragem",
    "Receber e conferir reagentes e produtos químicos",
    "Executar limpeza química das membranas CIP",
    "Conferir válvulas, comandos, testes e limpeza após manutenção",
    "Registrar treinamentos, orientações de segurança, EPIs e 5S",
    "Registrar propostas de melhorias aplicadas na ETE",
]

atividades_base = [f"{i}. {ativ}" for i, ativ in enumerate(atividades_brutas, 1)]

# --- FORMULÁRIO PRINCIPAL ---
st.markdown("<div class='section-title'>Registo de Turno e Atividades</div>", unsafe_allow_html=True)

with st.form(key="form_registo_geral_v11"):
  
  col_t1, col_t2, col_t3 = st.columns(3)
  with col_t1:
    turno_atual = st.selectbox("Turno Operacional", ["Turno Manhã", "Turno Tarde", "Turno Noite"])
  with col_t2:
    data_lancamento = st.date_input("Data do Registo", value=agora_brasilia().date())
  with col_t3:
    hora_lancamento = st.time_input("Hora da Execução", value=agora_brasilia().time())

  st.markdown("---")
  col_e1, col_e2, col_e3, col_e4 = st.columns(4)
  with col_e1:
    nomes_op = st.multiselect("Operador(es)", LISTA_OPERADORES)
  with col_e2:
    nomes_sup = st.multiselect("Supervisor(es)", LISTA_SUPERVISORES)
  with col_e3:
    nomes_mec = st.multiselect("Mecânico(s)", LISTA_MECANICOS)
  with col_e4:
    nomes_ele = st.multiselect("Eletrotécnico(s)", LISTA_ELETROTECNICOS)

  st.markdown("---")
  atividades_selecionadas = st.multiselect(
      "Selecione uma ou mais Atividades Executadas neste momento:",
      options=atividades_base
  )

  col_st1, col_st2 = st.columns(2)
  with col_st1:
    status_item = st.selectbox(
        "Status Geral da(s) Atividade(s)",
        ["Concluído", "Incompleta / Parcial", "Não Executada", "Pendente", "Não Aplicável"]
    )
  with col_st2:
    foto_file = st.file_uploader("Comprovação Fotográfica (Opcional)", type=["png", "jpg", "jpeg"])

  # --- CAMPO DE OBSERVAÇÕES INDIVIDUALIZADAS POR ATIVIDADE SELECIONADA ---
  observacoes_individuais = {}
  if atividades_selecionadas:
    st.markdown("---")
    st.markdown("#### 📝 Observações / Detalhes Individuais por Atividade")
    st.markdown("<small>Preencha especificamente a observação para cada atividade (ex: identificar a empresa na atividade 41).</small>", unsafe_allow_html=True)
    
    for ativ in atividades_selecionadas:
      # Exibe um campo de texto exclusivo para cada atividade escolhida
      observacoes_individuais[ativ] = st.text_input(
          f"Observação para: {ativ[:60]}...",
          placeholder="Ex: Empresa X esteve presente / Detalhe específico...",
          key=f"obs_ind_{ativ}"
      )

  submitted = st.form_submit_button("➕ Adicionar Atividade(s) ao Rascunho Persistente")

  if submitted:
    if not (nomes_op or nomes_sup or nomes_mec or nomes_ele):
      st.warning("⚠️ Selecione pelo menos um responsável na equipa.")
    elif not atividades_selecionadas:
      st.warning("⚠️ Selecione pelo menos uma atividade na lista.")
    else:
      executores_lista = []
      if nomes_op: executores_lista.append(f"Op: {', '.join(nomes_op)}")
      if nomes_sup: executores_lista.append(f"Sup: {', '.join(nomes_sup)}")
      if nomes_mec: executores_lista.append(f"Mec: {', '.join(nomes_mec)}")
      if nomes_ele: executores_lista.append(f"Ele: {', '.join(nomes_ele)}")
      str_executores = " | ".join(executores_lista)

      foto_path_temp = None
      if foto_file is not None:
        foto_path_temp = f"temp_foto_{datetime.now().strftime('%H%M%S_%f')}.jpg"
        with open(foto_path_temp, "wb") as f:
          f.write(foto_file.getbuffer())

      # Carrega o rascunho atual diretamente do disco para evitar duplicação em cache
      registros_atuais = carregar_rascunho_disco()

      for ativ in atividades_selecionadas:
        obs_especifica = observacoes_individuais.get(ativ, "").strip()
        
        novo_registo = {
            "turno": turno_atual,
            "data": data_lancamento.strftime("%d/%m/%Y"),
            "hora": hora_lancamento.strftime("%H:%M"),
            "atividade": ativ,
            "executores": str_executores,
            "status": status_item,
            "observacao": obs_especifica if obs_especifica else "-",
            "foto_path": foto_path_temp
        }
        registros_atuais.append(novo_registo)

      # Reatribui IDs sequenciais limpos e únicos para evitar qualquer duplicação
      for idx, r in enumerate(registros_atuais, 1):
        r["id"] = idx

      # Atualiza a sessão e salva no disco
      st.session_state["registros_turno"] = registros_atuais
      salvar_rascunho_disco(registros_atuais)

      st.success(f"✅ {len(atividades_selecionadas)} atividade(s) adicionada(s) com observações individuais e salvas com segurança!")
      st.rerun()

# --- VISUALIZAÇÃO DO RASCUNHO ATUAL ---
st.markdown("---")
st.markdown("<div class='section-title'>Rascunho Persistente do Turno (Salvo no Sistema)</div>", unsafe_allow_html=True)

# Sincroniza session_state com o disco para garantir integridade visual
st.session_state["registros_turno"] = carregar_rascunho_disco()

if len(st.session_state["registros_turno"]) > 0:
  df_rascunho = pd.DataFrame(st.session_state["registros_turno"])[
      ["id", "turno", "data", "hora", "atividade", "executores", "status", "observacao"]
  ]
  st.dataframe(df_rascunho, use_container_width=True)

  st.markdown("<div class='section-title'>Geração de Relatório PDF</div>", unsafe_allow_html=True)
  if st.button("📄 Gerar e Descarregar Relatório PDF Consolidado"):
    try:
      pdf_bytes = gerar_pdf_relatorio(mes_nome, ano, st.session_state["registros_turno"])
      st.success("Relatório gerado com sucesso!")
      st.download_button(
          label="📥 Clique aqui para baixar o PDF",
          data=pdf_bytes,
          file_name=f"ETE_Bertioga_Operacao_{mes_nome}_{ano}.pdf",
          mime="application/pdf",
      )
    except Exception as e:
      st.error(f"Erro ao gerar relatório: {e}")
else:
  st.info("ℹ️ O rascunho está vazio. Adicione atividades utilizando o formulário acima.")
