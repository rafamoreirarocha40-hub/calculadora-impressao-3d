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
    
    str_tempo_imp = str(tempo_h) + "h" + str(tempo_m) + "min"
    str_tempo_pos = str(pos_h) + "h" + str(pos_m) + "min"

    # --- FATORES DE RISCO/COMPLEXIDADE ---
    fator_cores = 0.10 if qtd_cores == "2 a 3 Cores" else (0.25 if qtd_cores == "4+ Cores (Multicolor Intenso)" else 0.0)
    fator_comp = 0.10 if "Média" in complexidade else (0.20 if "Alta" in complexidade else 0.0)

    # --- CÁLCULOS ---
    custo_material = (peso_g / 1000.0) * cfg['custo_filamento_kg'] * (1 + (cfg['perda_pct'] / 100.0))
    custo_energia = (cfg['potencia_w'] / 1000.0) * tempo_impressao_h_dec * cfg['custo_kwh']
    depreciacao_h = cfg['valor_impressora'] / cfg['vida_util_h'] if cfg['vida_util_h'] > 0 else 0
    custo_maquina = (depreciacao_h + cfg['custo_manutencao_h']) * tempo_impressao_h_dec
    custo_mao_obra = tempo_pos_h_dec * cfg['custo_mao_obra_h']

    # Custo Base acumulando Embalagem e Frete
    custo_producao_base = custo_material + custo_energia + custo_maquina + custo_mao_obra + custo_embalagem + custo_frete
    adicional_risco = custo_producao_base * (fator_cores + fator_comp)
    custo_producao_total = custo_producao_base + adicional_risco

    margem_fator = 1 + (cfg['margem_lucro_pct'] / 100.0)
    taxa_fator = 1 - (cfg['taxa_plataforma_pct'] / 100.0)
    
    preco_exato = (custo_producao_total * margem_fator) / taxa_fator if taxa_fator > 0 else custo_producao_total * margem_fator
    preco_sugerido = float(math.ceil(preco_exato))
    
    taxa_valor = preco_sugerido * (cfg['taxa_plataforma_pct'] / 100.0)
    lucro_liquido = preco_sugerido - custo_producao_total - taxa_valor

    st.divider()

    # --- EXIBIÇÃO DO PREÇO FINAL ---
    st.subheader("💡 Resultado do Orçamento")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Preço Sugerido (Arredondado)", f"R$ {preco_sugerido:.2f}", delta=f"Exato: R$ {preco_exato:.2f}")
    col_res2.metric("Lucro Líquido Estimado", f"R$ {lucro_liquido:.2f}")
    col_res3.metric("Prazo Total Estimado", f"{prazo_total_dias} dias úteis", delta=f"Produção: {prazo_producao}d + Envio: {dias_envio_extra}d")

    st.divider()

    # --- AÇÕES RÁPIDAS ---
    st.subheader("📲 Ações Rápidas")

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        if st.button("💾 Registrar Orçamento no Histórico"):
            novo_registro = {
                "DataHora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cliente": nome_cliente if nome_cliente else "Cliente Exemplo",
                "Peca": nome_peca if nome_peca else "Peça 3D",
                "Peso_g": peso_g,
                "TempoImpressao": str_tempo_imp,
                "Embalagem_R$": custo_embalagem,
                "Frete_R$": custo_frete,
                "TipoEntrega": tipo_entrega_str,
                "PrazoTotalDias": prazo_total_dias,
                "CustoProducao": round(custo_producao_total, 2),
                "PrecoExato": round(preco_exato, 2),
                "PrecoSugerido": round(preco_sugerido, 2),
                "LucroLiquido": round(lucro_liquido, 2)
            }
            st.session_state['historico_orcamentos'].append(novo_registro)
            st.success("✅ Orçamento gravado no histórico!")

        pdf_bytes = gerar_pdf_orcamento_simplificado(
            nome_cliente, nome_peca, preco_sugerido, prazo_total_dias, tipo_entrega_str, custo_frete, tem_frete
        )
        st.download_button(
            label="📄 Baixar Orçamento em PDF",
            data=pdf_bytes,
            file_name=f"Orcamento_{nome_cliente.replace(' ', '_') if nome_cliente else 'Cliente'}.pdf",
            mime="application/pdf"
        )

    with col_act2:
        info_frete_wa = f"🚚 *Envio:* {tipo_entrega_str} (R$ {custo_frete:.2f})\n" if tem_frete and custo_frete > 0 else f"🚚 *Envio:* {tipo_entrega_str}\n"
        mensagem_wa = (
            f"Olá *{nome_cliente if nome_cliente else 'Cliente'}*! 👋\n\n"
            f"Segue o orçamento para a impressão da peça *{nome_peca if nome_peca else 'Peça 3D'}*:\n"
            f"📌 *Valor Total:* R$ {preco_sugerido:.2f}\n"
            f"{info_frete_wa}"
            f"⏱️ *Prazo Estimado de Entrega:* {prazo_total_dias} dias úteis\n\n"
            f"Podemos confirmar o pedido?"
        )
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensagem_wa)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 18px; border-radius:5px; cursor:pointer; font-weight:bold; margin-bottom:10px;">💬 Enviar no WhatsApp</button></a>', unsafe_allow_html=True)

        if st.button("🧹 Criar Novo Orçamento (Zerar Tela)", use_container_width=True):
            resetar_orcamento()
            st.rerun()

    # --- SESSÃO DE HISTÓRICO E EXPORTAÇÃO ---
    st.divider()
    st.subheader("📊 Histórico de Orçamentos Registrados")

    if len(st.session_state['historico_orcamentos']) > 0:
        df_historico = pd.DataFrame(st.session_state['historico_orcamentos'])
        st.dataframe(df_historico, use_container_width=True)

        csv_buffer = df_historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Histórico (CSV para Power BI / Excel)",
            data=csv_buffer,
            file_name=f"historico_orcamentos_3d_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum orçamento registrado no histórico ainda. Clique em '💾 Registrar Orçamento no Histórico' acima para salvar os dados.")

# ==========================================
# ABA 2: CONFIGURAÇÕES OCULTAS (PROTEGIDA)
# ==========================================
with aba_admin:
    st.title("🔒 Área Restrita de Custos")
    st.caption("Altere aqui os custos padrão de insumos, hora, embalagem e margens.")

    senha_input = st.text_input("Digite a senha de administrador", type="password")

    if senha_input == cfg['senha_admin']:
        st.success("Acesso liberado!")
        
        with st.form("form_config"):
            st.markdown("### ⚙️ Custos Operacionais e Maquinário")
            novo_custo_filamento = st.number_input("Custo do Filamento (R$/kg)", value=float(cfg['custo_filamento_kg']), step=5.0)
            nova_potencia = st.number_input("Potência Média da Impressora (Watts)", value=float(cfg['potencia_w']), step=10.0)
            novo_custo_kwh = st.number_input("Tarifa de Energia (R$/kWh)", value=float(cfg['custo_kwh']), step=0.05)
            novo_valor_impressora = st.number_input("Valor de Compra da Impressora (R$)", value=float(cfg['valor_impressora']), step=100.0)
            nova_vida_util = st.number_input("Vida Útil Estimada (Horas)", value=int(cfg['vida_util_h']), step=500)
            novo_custo_manutencao = st.number_input("Custo de Manutenção (R$/hora)", value=float(cfg['custo_manutencao_h']), step=0.1)
            novo_custo_mao_obra = st.number_input("Custo da sua Hora de Trabalho (R$/hora)", value=float(cfg['custo_mao_obra_h']), step=5.0)
            
            st.markdown("### 📦 Custos Padrão de Embalagem")
            novo_custo_embalagem = st.number_input("Custo de Embalagem Padrão (R$)", value=float(cfg['custo_embalagem_padrao']), step=0.5, help="Custo padrão pré-carregado ao ligar o botão de embalagem.")

            st.markdown("### 📊 Margens e Taxas")
            nova_taxa_plataforma = st.number_input("Taxa de Cartão / Maquininha (%)", value=float(cfg['taxa_plataforma_pct']), step=0.5)
            nova_margem_lucro = st.number_input("Margem de Lucro Desejada (%)", value=float(cfg['margem_lucro_pct']), step=5.0)
            nova_perda = st.number_input("Margem para Falhas / Perdas (%)", value=float(cfg['perda_pct']), step=1.0)
            nova_senha = st.text_input("Nova Senha de Administrador", value=str(cfg['senha_admin']), type="password")
            
            btn_salvar = st.form_submit_button("💾 Salvar Configurações Permanentemente")
            
            if btn_salvar:
                novas_configs = {
                    'custo_filamento_kg': novo_custo_filamento,
                    'potencia_w': nova_potencia,
                    'custo_kwh': novo_custo_kwh,
                    'valor_impressora': novo_valor_impressora,
                    'vida_util_h': nova_vida_util,
                    'custo_manutencao_h': novo_custo_manutencao,
                    'custo_mao_obra_h': novo_custo_mao_obra,
                    'taxa_plataforma_pct': nova_taxa_plataforma,
                    'margem_lucro_pct': nova_margem_lucro,
                    'perda_pct': nova_perda,
                    'custo_embalagem_padrao': novo_custo_embalagem,
                    'senha_admin': nova_senha
                }
                salvar_config(novas_configs)
                st.session_state['config'] = novas_configs
                st.success("✅ Configurações salvas permanentemente com sucesso!")

        st.divider()
        st.subheader("🖼️ Upload da Logo")
        
        uploaded_logo = st.file_uploader("Enviar ou atualizar imagem da Logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            with open("logo.png", "wb") as f:
                f.write(uploaded_logo.getbuffer())
            st.success("Logo atualizada com sucesso! Recarregue a página para visualizar.")

    elif senha_input != "":
        st.error("Senha incorreta!")
