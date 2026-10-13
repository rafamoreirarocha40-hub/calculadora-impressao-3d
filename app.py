import streamlit as st
import datetime
import urllib.parse
import pandas as pd
import os
import math
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração Inicial da Página
st.set_page_config(
    page_title="Calculadora 3D - Orçamentos",
    page_icon="🖨️",
    layout="centered"
)

CONFIG_FILE = "config.json"

# --- VALORES PADRÃO (INCLUINDO DADOS DE CONFIGURAÇÃO) ---
CONFIG_PADRAO = {
    'custo_filamento_kg': 120.0,
    'potencia_w': 150.0,
    'custo_kwh': 0.85,
    'valor_impressora': 2500.0,
    'vida_util_h': 5000,
    'custo_manutencao_h': 0.50,
    'custo_mao_obra_h': 30.0,
    'taxa_plataforma_pct': 5.0,
    'margem_lucro_pct': 100.0,
    'perda_pct': 5.0,
    'custo_embalagem_padrao': 3.00,
    'senha_admin': "1234"
}

# --- FUNÇÕES PARA CARREGAR E SALVAR CONFIGURAÇÕES PERMANENTES ---
def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg_carregada = json.load(f)
                for k, v in CONFIG_PADRAO.items():
                    if k not in cfg_carregada:
                        cfg_carregada[k] = v
                return cfg_carregada
        except Exception:
            return CONFIG_PADRAO.copy()
    return CONFIG_PADRAO.copy()

def salvar_config(novas_configs):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(novas_configs, f, indent=4)

if 'config' not in st.session_state:
    st.session_state['config'] = carregar_config()

cfg = st.session_state['config']

# --- FUNÇÃO PARA LOCALIZAR ARQUIVO DE LOGO ---
def encontrar_logo():
    extensoes = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.PNG", "Logo.jpg", "LOGO.JPG"]
    for file in extensoes:
        if os.path.exists(file):
            return file
    return None

logo_path = encontrar_logo()

# --- INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA ---
if 'historico_orcamentos' not in st.session_state:
    st.session_state['historico_orcamentos'] = []

# --- INICIALIZAÇÃO DAS VARIÁVEIS DE FORMULÁRIO (INICIAM ZERADAS) ---
if 'f_cliente' not in st.session_state:
    st.session_state['f_cliente'] = ""
if 'f_peca' not in st.session_state:
    st.session_state['f_peca'] = ""
if 'f_peso' not in st.session_state:
    st.session_state['f_peso'] = 0.0
if 'f_th' not in st.session_state:
    st.session_state['f_th'] = 0
if 'f_tm' not in st.session_state:
    st.session_state['f_tm'] = 0
if 'f_cores' not in st.session_state:
    st.session_state['f_cores'] = "1 Cor (Monocolor)"
if 'f_comp' not in st.session_state:
    st.session_state['f_comp'] = "Baixa"
if 'f_ph' not in st.session_state:
    st.session_state['f_ph'] = 0
if 'f_pm' not in st.session_state:
    st.session_state['f_pm'] = 0
if 'f_prazo_prod' not in st.session_state:
    st.session_state['f_prazo_prod'] = 0
if 'f_tem_embalagem' not in st.session_state:
    st.session_state['f_tem_embalagem'] = False
if 'f_embalagem_valor' not in st.session_state:
    st.session_state['f_embalagem_valor'] = float(cfg['custo_embalagem_padrao'])
if 'f_tem_frete' not in st.session_state:
    st.session_state['f_tem_frete'] = False
if 'f_tipo_frete' not in st.session_state:
    st.session_state['f_tipo_frete'] = "Motoboy / Uber Flash (Local)"
if 'f_frete_valor' not in st.session_state:
    st.session_state['f_frete_valor'] = 0.00
if 'f_dias_envio_extra' not in st.session_state:
    st.session_state['f_dias_envio_extra'] = 0

def resetar_orcamento():
    st.session_state['f_cliente'] = ""
    st.session_state['f_peca'] = ""
    st.session_state['f_peso'] = 0.0
    st.session_state['f_th'] = 0
    st.session_state['f_tm'] = 0
    st.session_state['f_cores'] = "1 Cor (Monocolor)"
    st.session_state['f_comp'] = "Baixa"
    st.session_state['f_ph'] = 0
    st.session_state['f_pm'] = 0
    st.session_state['f_prazo_prod'] = 0
    st.session_state['f_tem_embalagem'] = False
    st.session_state['f_embalagem_valor'] = float(cfg['custo_embalagem_padrao'])
    st.session_state['f_tem_frete'] = False
    st.session_state['f_tipo_frete'] = "Motoboy / Uber Flash (Local)"
    st.session_state['f_frete_valor'] = 0.00
    st.session_state['f_dias_envio_extra'] = 0

# --- FUNÇÃO PARA GERAR ORÇAMENTO EM PDF COM INFORMAÇÕES DE FRETE ---
def gerar_pdf_orcamento_simplificado(cliente, peca, preco_sugerido, prazo_total_dias, tipo_entrega_str, custo_frete, tem_frete):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E293B'), alignment=1)
    text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor('#334155'))
    bold_style = ParagraphStyle('BoldStyle', parent=text_style, fontName='Helvetica-Bold')

    elements = []

    if logo_path:
        img = RLImage(logo_path, width=140, height=70)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("<b>ORÇAMENTO DE IMPRESSÃO 3D</b>", title_style))
    elements.append(Spacer(1, 15))
    
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    
    frete_info_str = tipo_entrega_str
    if tem_frete and custo_frete > 0:
        frete_info_str += f" (R$ {custo_frete:.2f})"

    dados_tabela = [
        [Paragraph("<b>Data:</b>", bold_style), Paragraph(data_hoje, text_style)],
        [Paragraph("<b>Cliente:</b>", bold_style), Paragraph(cliente if cliente else "Cliente", text_style)],
        [Paragraph("<b>Peça / Projeto:</b>", bold_style), Paragraph(peca if peca else "Serviço de Impressão 3D", text_style)],
        [Paragraph("<b>Forma de Envio:</b>", bold_style), Paragraph(frete_info_str, text_style)],
        [Paragraph("<b>Prazo Estimado de Entrega:</b>", bold_style), Paragraph(f"{prazo_total_dias} dias úteis", text_style)],
        [Paragraph("<b>Valor Total:</b>", bold_style), Paragraph(f"<b>R$ {preco_sugerido:.2f}</b>", ParagraphStyle('Price', parent=bold_style, fontSize=14, textColor=colors.HexColor('#0F766E')))],
    ]
    
    t = Table(dados_tabela, colWidths=[160, 340])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Condições de Pagamento:</b> Pix ou Cartão de Crédito/Débito.", text_style))
    elements.append(Paragraph("<i>Orçamento válido por 7 dias.</i>", text_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- EXIBIÇÃO DA LOGO NO TOPO ---
if logo_path:
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.image(logo_path, use_container_width=True)

# --- ABAS DA APLICAÇÃO ---
aba_calculadora, aba_admin = st.tabs(["🖨️ Calculadora Rápida", "🔒 Configurações de Custos"])

# ==========================================
# ABA 1: CALCULADORA RÁPIDA (USO DIÁRIO)
# ==========================================
with aba_calculadora:
    st.title("🖨️ Orçamento Rápido")
    st.caption("Preencha as informações do produto e selecione os opcionais.")

    col1, col2 = st.columns(2)
    with col1:
        nome_cliente = st.text_input("Nome do Cliente", key="f_cliente", placeholder="Ex: João Silva")
        nome_peca = st.text_input("Nome / Descrição da Peça", key="f_peca", placeholder="Ex: Suporte de Headset")
        peso_g = st.number_input("Peso Total (g) [do App]", key="f_peso", step=5.0, help="Peso total do filamento informado pelo fatiador.")

        st.markdown("**Tempo de Impressão (do App)**")
        col_th, col_tm = st.columns(2)
        with col_th:
            tempo_h = st.number_input("Horas", key="f_th", min_value=0, step=1)
        with col_tm:
            tempo_m = st.number_input("Minutos", key="f_tm", min_value=0, max_value=59, step=1)

        prazo_producao = st.number_input("Prazo de Produção (Dias Úteis)", key="f_prazo_prod", step=1, help="Tempo de fabricação da peça na impressora.")

    with col2:
        qtd_cores = st.selectbox("Quantidade de Cores", ["1 Cor (Monocolor)", "2 a 3 Cores", "4+ Cores (Multicolor Intenso)"], key="f_cores")
        complexidade = st.selectbox("Nível de Complexidade", ["Baixa", "Média (+10%)", "Alta (+20%)"], key="f_comp")
        
        st.markdown("**Acabamento / Pós-processamento**")
        col_ph, col_pm = st.columns(2)
        with col_ph:
            pos_h = st.number_input("Horas (Pós)", key="f_ph", min_value=0, step=1)
        with col_pm:
            pos_m = st.number_input("Minutos (Pós)", key="f_pm", min_value=0, max_value=59, step=1)

    st.divider()
    st.subheader("📦 Opcionais de Embalagem e Frete")

    col_opt1, col_opt2 = st.columns(2)

    # OPCIONAL DE EMBALAGEM (SIM / NÃO)
    with col_opt1:
        tem_embalagem = st.toggle("Incluir Custo de Embalagem?", key="f_tem_embalagem", help="Marque SIM se for usar caixas de papelão, plástico bolha ou mimos no envio.")
        
        custo_embalagem = 0.0
        if tem_embalagem:
            custo_embalagem = st.number_input("Custo da Embalagem (R$)", key="f_embalagem_valor", step=1.0)

    # OPCIONAL DE FRETE (SIM / NÃO)
    with col_opt2:
        tem_frete = st.toggle("Incluir Frete / Entrega?", key="f_tem_frete", help="Marque SIM se for enviar por aplicativo, Correios ou transportadora.")
        
        custo_frete = 0.0
        dias_envio_extra = 0
        tipo_entrega_str = "Retirada no Local"

        if tem_frete:
            tipo_frete = st.selectbox(
                "Tipo de Entrega",
                [
                    "Motoboy / Uber Flash (Local)",
                    "Correios - SEDEX",
                    "Correios - PAC",
                    "Transportadora / Outros"
                ],
                key="f_tipo_frete"
            )
            
            custo_frete = st.number_input("Valor do Frete (R$)", key="f_frete_valor", step=1.0)

            if tipo_frete == "Motoboy / Uber Flash (Local)":
                dias_envio_extra = 0
                tipo_entrega_str = "Motoboy / Uber Flash"
            elif tipo_frete == "Correios - SEDEX":
                dias_envio_extra = 2
                tipo_entrega_str = "Correios (SEDEX)"
            elif tipo_frete == "Correios - PAC":
                dias_envio_extra = 5
                tipo_entrega_str = "Correios (PAC)"
            else:
                dias_envio_extra = st.number_input("Dias Úteis do Envio", key="f_dias_envio_extra", min_value=0, step=1)
                tipo_entrega_str = "Transportadora / Envio Especial"

    # Prazo Final Combinado
    prazo_total_dias = prazo_producao + dias_envio_extra

    # --- CONVERSÃO DE TEMPO PARA HORAS DECIMAIS ---
    tempo_impressao_h_dec = tempo_h + (tempo_m / 60.0)
    tempo_pos_h_dec = pos_h + (pos_m / 60.0)
    
    str_tempo_imp = f"{tempo_h}h{tempo_m:02d
