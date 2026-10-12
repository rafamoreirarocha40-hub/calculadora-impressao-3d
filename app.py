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

# --- VALORES PADRÃO (SE NÃO EXISTIR FICHEIRO SALVO) ---
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
    'senha_admin': "1234"
}

# --- FUNÇÕES PARA CARREGAR E SALVAR CONFIGURAÇÕES PERMANENTES ---
def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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

# --- FUNÇÃO PARA GERAR ORÇAMENTO EM PDF COM LOGO ---
def gerar_pdf_orcamento(cliente, peca, peso_g, tempo_formatado, cores, complexidade, preco_sugerido, prazo_dias):
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
    
    dados_tabela = [
        [Paragraph("<b>Data:</b>", bold_style), Paragraph(data_hoje, text_style)],
        [Paragraph("<b>Cliente:</b>", bold_style), Paragraph(cliente, text_style)],
        [Paragraph("<b>Peça / Projeto:</b>", bold_style), Paragraph(peca, text_style)],
        [Paragraph("<b>Peso Estimado:</b>", bold_style), Paragraph(f"{peso_g:.1f} g", text_style)],
        [Paragraph("<b>Tempo de Impressão:</b>", bold_style), Paragraph(tempo_formatado, text_style)],
        [Paragraph("<b>Quantidade de Cores:</b>", bold_style), Paragraph(f"{cores}", text_style)],
        [Paragraph("<b>Complexidade:</b>", bold_style), Paragraph(f"{complexidade}", text_style)],
        [Paragraph("<b>Prazo de Entrega:</b>", bold_style), Paragraph(f"{prazo_dias} dias úteis", text_style)],
        [Paragraph("<b>Valor Total:</b>", bold_style), Paragraph(f"<b>R$ {preco_sugerido:.2f}</b>", ParagraphStyle('Price', parent=bold_style, fontSize=14, textColor=colors.HexColor('#0F766E')))],
    ]
    
    t = Table(dados_tabela, colWidths=[150, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
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
    st.caption("Preencha apenas as informações básicas extraídas do app da impressora.")

    col1, col2 = st.columns(2)
    with col1:
        nome_cliente = st.text_input("Nome do Cliente", value="Cliente Exemplo")
        nome_peca = st.text_input("Nome / Descrição da Peça", value="Peça Decorativa 3D")
        peso_g = st.number_input("Peso Total (g) [do App]", value=50.0, step=5.0)

        st.markdown("**Tempo de Impressão (do App)**")
        col_th, col_tm = st.columns(2)
        with col_th:
            tempo_h = st.number_input("Horas", value=1, min_value=0, step=1)
        with col_tm:
            tempo_m = st.number_input("Minutos", value=26, min_value=0, max_value=59, step=1)

    with col2:
        qtd_cores = st.selectbox("Quantidade de Cores", ["1 Cor (Monocolor)", "2 a 3 Cores", "4+ Cores (Multicolor Intenso)"])
        complexidade = st.selectbox("Nível de Complexidade", ["Baixa", "Média (+10%)", "Alta (+20%)"])
        
        st.markdown("**Acabamento / Pós-processamento**")
        col_ph, col_pm = st.columns(2)
        with col_ph:
            pos_h = st.number_input("Horas (Pós)", value=0, min_value=0, step=1)
        with col_pm:
            pos_m = st.number_input("Minutos (Pós)", value=15, min_value=0, max_value=59, step=1)

        prazo_entrega = st.number_input("Prazo de Entrega (Dias Úteis)", value=3, step=1)

    # --- CONVERSÃO DE TEMPO PARA HORAS DECIMAIS ---
    tempo_impressao_h_dec = tempo_h + (tempo_m / 60.0)
    tempo_pos_h_dec = pos_h + (pos_m / 60.0)
    
    str_tempo_imp = f"{tempo_h}h{tempo_m:02d}min"
    str_tempo_pos = f"{pos_h}h{pos_m:02d}min"

    # --- FATORES DE RISCO/COMPLEXIDADE ---
    fator_cores = 0.10 if qtd_cores == "2 a 3 Cores" else (0.25 if qtd_cores == "4+ Cores (Multicolor Intenso)" else 0.0)
    fator_comp = 0.10 if "Média" in complexidade else (0.20 if "Alta" in complexidade else 0.0)

    # --- CÁLCULOS ---
    custo_material = (peso_g / 1000.0) * cfg['custo_filamento_kg'] * (1 + (cfg['perda_pct'] / 100.0))
    custo_energia = (cfg['potencia_w'] / 1000.0) * tempo_impressao_h_dec * cfg['custo_kwh']
    depreciacao_h = cfg['valor_impressora'] / cfg['vida_util_h'] if cfg['vida_util_h'] > 0 else 0
    custo_maquina = (depreciacao_h + cfg['custo_manutencao_h']) * tempo_impressao_h_dec
    custo_mao_obra = tempo_pos_h_dec * cfg['custo_mao_obra_h']

    custo_producao_base = custo_material + custo_energia + custo_maquina + custo_mao_obra
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
    col_res3.metric("Custo Total de Produção", f"R$ {custo_producao_total:.2f}")

    st.divider()

    # --- AÇÕES RÁPIDAS ---
    st.subheader("📲 Ações Rápidas")

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        if st.button("💾 Registrar Orçamento no Histórico"):
            novo_registro = {
                "DataHora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cliente": nome_cliente,
                "Peca": nome_peca,
                "Peso_g": peso_g,
                "TempoImpressao": str_tempo_imp,
                "TempoPosProcessamento": str_tempo_pos,
                "Cores": qtd_cores,
                "Complexidade": complexidade,
                "CustoProducao": round(custo_producao_total, 2),
                "PrecoExato": round(preco_exato, 2),
                "PrecoSugerido": round(preco_sugerido, 2),
                "LucroLiquido": round(lucro_liquido, 2)
            }
            st.session_state['historico_orcamentos'].append(novo_registro)
            st.success("✅ Orçamento gravado no histórico com sucesso!")

        pdf_bytes = gerar_pdf_orcamento(
            nome_cliente, nome_peca, peso_g, str_tempo_imp, 
            qtd_cores, complexidade, preco_sugerido, prazo_entrega
        )
        st.download_button(
            label="📄 Baixar Orçamento em PDF",
            data=pdf_bytes,
            file_name=f"Orcamento_{nome_cliente.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

    with col_act2:
        mensagem_wa = (
            f"Olá *{nome_cliente}*! 👋\n\n"
            f"Segue o orçamento para a impressão da peça *{nome_peca}*:\n"
            f"📌 *Valor Total:* R$ {preco_sugerido:.2f}\n"
            f"🎨 *Especificação:* {qtd_cores} | Complexidade {complexidade}\n"
            f"⏱️ *Prazo de Entrega:* {prazo_entrega} dias úteis\n\n"
            f"Podemos confirmar o pedido?"
        )
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensagem_wa)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 18px; border-radius:5px; cursor:pointer; font-weight:bold; margin-bottom:10px;">💬 Enviar no WhatsApp</button></a>', unsafe_allow_html=True)

    # --- SESSÃO DE HISTÓRICO E EXPORTAÇÃO PARA POWER BI / EXCEL ---
    st.divider()
    st.subheader("📊 Histórico de Orçamentos Registrados")

    if len(st.session_state['historico_orcamentos']) > 0:
        df_historico = pd.DataFrame(st.session_state['historico_orcamentos'])
        st.dataframe(df_historico, use_container_width=True)

        csv_buffer = df_historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Banco de Dados (CSV para Power BI)",
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
    st.caption("Apenas altere estes valores quando houver mudança no preço do filamento, energia ou margens.")

    senha_input = st.text_input("Digite a senha de administrador", type="password")

    if senha_input == cfg['senha_admin']:
        st.success("Acesso liberado!")
        
        # Formulário para guardar as alterações
        with st.form("form_config"):
            novo_custo_filamento = st.number_input("Custo do Filamento (R$/kg)", value=float(cfg['custo_filamento_kg']), step=5.0)
            nova_potencia = st.number_input("Potência Média da Impressora (Watts)", value=float(cfg['potencia_w']), step=10.0)
            novo_custo_kwh = st.number_input("Tarifa de Energia (R$/kWh)", value=float(cfg['custo_kwh']), step=0.05)
            novo_valor_impressora = st.number_input("Valor de Compra da Impressora (R$)", value=float(cfg['valor_impressora']), step=100.0)
            nova_vida_util = st.number_input("Vida Útil Estimada (Horas)", value=int(cfg['vida_util_h']), step=500)
            novo_custo_manutencao = st.number_input("Custo de Manutenção (R$/hora)", value=float(cfg['custo_manutencao_h']), step=0.1)
            novo_custo_mao_obra = st.number_input("Custo da sua Hora de Trabalho (R$/hora)", value=float(cfg['custo_mao_obra_h']), step=5.0)
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
