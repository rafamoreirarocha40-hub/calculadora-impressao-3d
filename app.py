import streamlit as st
import datetime
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração Inicial da Página
st.set_page_config(
    page_title="Calculadora 3D - Orçamentos",
    page_icon="🖨️",
    layout="centered"
)

# --- VALORES PADRÃO (SEGUNDO PLANO / CONFIGURAÇÕES OCULTAS) ---
if 'config' not in st.session_state:
    st.session_state['config'] = {
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

cfg = st.session_state['config']

# --- FUNÇÃO PARA GERAR ORÇAMENTO EM PDF ---
def gerar_pdf_orcamento(cliente, peca, peso_g, tempo_h, cores, complexidade, preco_final, prazo_dias):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1E293B'), alignment=1)
    text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor('#334155'))
    bold_style = ParagraphStyle('BoldStyle', parent=text_style, fontName='Helvetica-Bold')

    elements = []
    
    elements.append(Paragraph("<b>ORÇAMENTO DE IMPRESSÃO 3D</b>", title_style))
    elements.append(Spacer(1, 15))
    
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    
    dados_tabela = [
        [Paragraph("<b>Data:</b>", bold_style), Paragraph(data_hoje, text_style)],
        [Paragraph("<b>Cliente:</b>", bold_style), Paragraph(cliente, text_style)],
        [Paragraph("<b>Peça / Projeto:</b>", bold_style), Paragraph(peca, text_style)],
        [Paragraph("<b>Peso Estimado:</b>", bold_style), Paragraph(f"{peso_g:.1f} g", text_style)],
        [Paragraph("<b>Tempo de Impressão:</b>", bold_style), Paragraph(f"{tempo_h:.1f} horas", text_style)],
        [Paragraph("<b>Quantidade de Cores:</b>", bold_style), Paragraph(f"{cores}", text_style)],
        [Paragraph("<b>Complexidade:</b>", bold_style), Paragraph(f"{complexidade}", text_style)],
        [Paragraph("<b>Prazo de Entrega:</b>", bold_style), Paragraph(f"{prazo_dias} dias úteis", text_style)],
        [Paragraph("<b>Valor Total:</b>", bold_style), Paragraph(f"<b>R$ {preco_final:.2f}</b>", ParagraphStyle('Price', parent=bold_style, fontSize=14, textColor=colors.HexColor('#0F766E')))],
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
        tempo_impressao_h = st.number_input("Tempo de Impressão (Horas) [do App]", value=3.0, step=0.5)

    with col2:
        qtd_cores = st.selectbox("Quantidade de Cores", ["1 Cor (Monocolor)", "2 a 3 Cores", "4+ Cores (Multicolor Intenso)"])
        complexidade = st.selectbox("Nível de Complexidade", ["Baixa", "Média (+10%)", "Alta (+20%)"])
        tempo_pos_h = st.number_input("Acabamento / Pós-processamento (Horas)", value=0.2, step=0.1)
        prazo_entrega = st.number_input("Prazo de Entrega (Dias Úteis)", value=3, step=1)

    # --- FACTORES DE MULTIPLICAÇÃO DE RISCO/COMPLEXIDADE ---
    fator_cores = 0.0
    if qtd_cores == "2 a 3 Cores":
        fator_cores = 0.10  # +10%
    elif qtd_cores == "4+ Cores (Multicolor Intenso)":
        fator_cores = 0.25  # +25%

    fator_comp = 0.0
    if "Média" in complexidade:
        fator_comp = 0.10   # +10%
    elif "Alta" in complexidade:
        fator_comp = 0.20   # +20%

    # --- CÁLCULOS EM SEGUNDO PLANO ---
    custo_material = (peso_g / 1000.0) * cfg['custo_filamento_kg'] * (1 + (cfg['perda_pct'] / 100.0))
    custo_energia = (cfg['potencia_w'] / 1000.0) * tempo_impressao_h * cfg['custo_kwh']
    depreciacao_h = cfg['valor_impressora'] / cfg['vida_util_h'] if cfg['vida_util_h'] > 0 else 0
    custo_maquina = (depreciacao_h + cfg['custo_manutencao_h']) * tempo_impressao_h
    custo_mao_obra = tempo_pos_h * cfg['custo_mao_obra_h']

    # Custo base de produção
    custo_producao_base = custo_material + custo_energia + custo_maquina + custo_mao_obra

    # Aplicação dos adicionais de cores e complexidade
    adicional_risco = custo_producao_base * (fator_cores + fator_comp)
    custo_producao_total = custo_producao_base + adicional_risco

    # Preço final ajustado com margem e taxa do cartão
    margem_fator = 1 + (cfg['margem_lucro_pct'] / 100.0)
    taxa_fator = 1 - (cfg['taxa_plataforma_pct'] / 100.0)
    preco_venda = (custo_producao_total * margem_fator) / taxa_fator if taxa_fator > 0 else custo_producao_total * margem_fator
    taxa_valor = preco_venda * (cfg['taxa_plataforma_pct'] / 100.0)
    lucro_liquido = preco_venda - custo_producao_total - taxa_valor

    st.divider()

    # --- EXIBIÇÃO DO PREÇO FINAL ---
    st.subheader("💡 Resultado do Orçamento")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Preço de Venda Final", f"R$ {preco_venda:.2f}")
    col_res2.metric("Lucro Líquido Estimado", f"R$ {lucro_liquido:.2f}")
    col_res3.metric("Taxas/Adicionais de Risco", f"R$ {adicional_risco:.2f}")

    st.divider()

    # --- AÇÕES: PDF E WHATSAPP ---
    st.subheader("📲 Ações Rápidas")

    pdf_bytes = gerar_pdf_orcamento(
        nome_cliente, nome_peca, peso_g, tempo_impressao_h, 
        qtd_cores, complexidade, preco_venda, prazo_entrega
    )
    st.download_button(
        label="📄 Baixar Orçamento em PDF",
        data=pdf_bytes,
        file_name=f"Orcamento_{nome_cliente.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

    mensagem_wa = (
        f"Olá *{nome_cliente}*! 👋\n\n"
        f"Segue o orçamento para a impressão da peça *{nome_peca}*:\n"
        f"📌 *Valor Total:* R$ {preco_venda:.2f}\n"
        f"🎨 *Especificação:* {qtd_cores} | Complexidade {complexidade}\n"
        f"⏱️ *Prazo de Entrega:* {prazo_entrega} dias úteis\n\n"
        f"Podemos confirmar o pedido?"
    )
    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensagem_wa)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">💬 Enviar no WhatsApp</button></a>', unsafe_allow_html=True)

# ==========================================
# ABA 2: CONFIGURAÇÕES OCULTAS (PROTEGIDA)
# ==========================================
with aba_admin:
    st.title("🔒 Área Restrita de Custos")
    st.caption("Apenas altere estes valores quando houver mudança no preço do filamento, energia ou margens.")

    senha_input = st.text_input("Digite a senha de administrador", type="password")

    if senha_input == cfg['senha_admin']:
        st.success("Acesso liberado!")
        
        cfg['custo_filamento_kg'] = st.number_input("Custo do Filamento (R$/kg)", value=cfg['custo_filamento_kg'], step=5.0)
        cfg['potencia_w'] = st.number_input("Potência Média da Impressora (Watts)", value=cfg['potencia_w'], step=10.0)
        cfg['custo_kwh'] = st.number_input("Tarifa de Energia (R$/kWh)", value=cfg['custo_kwh'], step=0.05)
        cfg['valor_impressora'] = st.number_input("Valor de Compra da Impressora (R$)", value=cfg['valor_impressora'], step=100.0)
        cfg['vida_util_h'] = st.number_input("Vida Útil Estimada (Horas)", value=cfg['vida_util_h'], step=500)
        cfg['custo_manutencao_h'] = st.number_input("Custo de Manutenção (R$/hora)", value=cfg['custo_manutencao_h'], step=0.1)
        cfg['custo_mao_obra_h'] = st.number_input("Custo da sua Hora de Trabalho (R$/hora)", value=cfg['custo_mao_obra_h'], step=5.0)
        cfg['taxa_plataforma_pct'] = st.number_input("Taxa de Cartão / Maquininha (%)", value=cfg['taxa_plataforma_pct'], step=0.5)
        cfg['margem_lucro_pct'] = st.number_input("Margem de Lucro Desejada (%)", value=cfg['margem_lucro_pct'], step=5.0)
        cfg['perda_pct'] = st.number_input("Margem para Falhas / Perdas (%)", value=cfg['perda_pct'], step=1.0)
        
        st.info("As alterações são aplicadas imediatamente nos cálculos da calculadora.")
    elif senha_input != "":
        st.error("Senha incorreta!")
