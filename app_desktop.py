import customtkinter as ctk
import pandas as pd
import sqlite3
import os
import re
from tkinter import filedialog, messagebox, ttk
from fpdf import FPDF


# ==========================================================
# ================= CONFIGURAÇÕES GERAIS ====================
# ==========================================================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppCustos(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---------------- Janela principal ----------------
        self.title("Sistema de Custos e Rateio")
        self.geometry("1360x820")
        self.minsize(1200, 760)

        # ---------------- Banco / estado ----------------
        self.db_path = "config_precos.db"
        self.ultima_pasta = os.getcwd()

        self.conectar_db()
        self.precos = self.carregar_precos()

        self.dfs_processados = []
        self.df_final = pd.DataFrame()
        self.valor_rateio_5014_0 = 0.0
        self.servicos_lote_atual = []
        self.qtd_arquivos_importados = 0
        self.qtd_pas_encontrados = 0
        self.map_normalizacoes = []

        # ---------------- Layout base ----------------
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.lbl_logo = ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA DE RATEIO",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")

        self.lbl_sub = ctk.CTkLabel(
            self.sidebar,
            text="Custos por PA",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        self.btn_importar = ctk.CTkButton(
            self.sidebar,
            text="Importar arquivos",
            command=self.importar_arquivos,
            height=42
        )
        self.btn_importar.grid(row=2, column=0, padx=20, pady=8, sticky="ew")

        self.btn_calcular = ctk.CTkButton(
            self.sidebar,
            text="Calcular rateio",
            command=self.calcular_tudo,
            height=42,
            fg_color="#1f8b4c",
            hover_color="#16663a"
        )
        self.btn_calcular.grid(row=3, column=0, padx=20, pady=8, sticky="ew")

        self.btn_pdf = ctk.CTkButton(
            self.sidebar,
            text="Exportar relatório PDF",
            command=self.gerar_pdf,
            height=42,
            state="disabled"
        )
        self.btn_pdf.grid(row=4, column=0, padx=20, pady=8, sticky="ew")

        self.btn_limpar = ctk.CTkButton(
            self.sidebar,
            text="Limpar lote atual",
            command=self.limpar_lote_atual,
            height=42,
            fg_color="#444444",
            hover_color="#333333"
        )
        self.btn_limpar.grid(row=5, column=0, padx=20, pady=8, sticky="ew")

        self.lbl_status_sidebar = ctk.CTkLabel(
            self.sidebar,
            text="Nenhum lote importado",
            wraplength=190,
            justify="left"
        )
        self.lbl_status_sidebar.grid(row=6, column=0, padx=20, pady=(20, 8), sticky="w")

        self.btn_sair = ctk.CTkButton(
            self.sidebar,
            text="Sair",
            command=self.destroy,
            fg_color="#8B1E1E",
            hover_color="#6C1717",
            height=40
        )
        self.btn_sair.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Área principal
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_container, corner_radius=16)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="Painel de Custos e Rateio",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.lbl_titulo.grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

        self.lbl_subtitulo = ctk.CTkLabel(
            self.header_frame,
            text="Importe arquivos, revise os valores do lote atual e execute o cálculo.",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_subtitulo.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")

        # Cards resumo
        self.cards_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1)

        self.card_arquivos = self.criar_card_resumo(self.cards_frame, "Arquivos importados", "0", 0)
        self.card_servicos = self.criar_card_resumo(self.cards_frame, "Serviços no lote", "0", 1)
        self.card_pas = self.criar_card_resumo(self.cards_frame, "PAs identificados", "0", 2)
        self.card_pendencias = self.criar_card_resumo(self.cards_frame, "Valores inválidos", "0", 3)

        # Abas
        self.main_area = ctk.CTkTabview(self.main_container)
        self.main_area.grid(row=2, column=0, sticky="nsew")
        self.tab_config = self.main_area.add("Valores do lote")
        self.tab_result = self.main_area.add("Resultados")
        self.tab_log = self.main_area.add("Log de execução")

        # ---------------- Aba Valores ----------------
        self.tab_config.grid_columnconfigure(0, weight=1)
        self.tab_config.grid_rowconfigure(1, weight=1)

        self.info_precos = ctk.CTkFrame(self.tab_config)
        self.info_precos.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        self.info_precos.grid_columnconfigure(0, weight=1)

        self.lbl_info_precos = ctk.CTkLabel(
            self.info_precos,
            text="Nenhum lote carregado.",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_info_precos.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        self.lbl_info_precos2 = ctk.CTkLabel(
            self.info_precos,
            text="Os valores abaixo refletem somente os serviços encontrados no lote atual.",
            justify="left",
            anchor="w"
        )
        self.lbl_info_precos2.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")

        self.scroll_precos = ctk.CTkScrollableFrame(
            self.tab_config,
            label_text="Tabela de valores do lote atual"
        )
        self.scroll_precos.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.inputs_precos = {}
        self.labels_origem_preco = {}

        # ---------------- Aba Resultados ----------------
        self.tab_result.grid_columnconfigure(0, weight=1)
        self.tab_result.grid_rowconfigure(1, weight=1)

        self.result_top = ctk.CTkFrame(self.tab_result)
        self.result_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        self.result_top.grid_columnconfigure(0, weight=1)

        self.lbl_resultado_resumo = ctk.CTkLabel(
            self.result_top,
            text="Nenhum cálculo executado.",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            justify="left"
        )
        self.lbl_resultado_resumo.grid(row=0, column=0, padx=16, pady=(14, 14), sticky="w")

        self.result_split = ctk.CTkFrame(self.tab_result, fg_color="transparent")
        self.result_split.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.result_split.grid_columnconfigure(0, weight=1)
        self.result_split.grid_rowconfigure(1, weight=1)

        self.texto_resultado = ctk.CTkTextbox(
            self.result_split,
            font=("Consolas", 13),
            height=180
        )
        self.texto_resultado.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.texto_resultado.insert("0.0", "Resultado ainda não calculado.")
        self.texto_resultado.configure(state="disabled")

        self.frame_tree = ctk.CTkFrame(self.result_split)
        self.frame_tree.grid(row=1, column=0, sticky="nsew")
        self.frame_tree.grid_columnconfigure(0, weight=1)
        self.frame_tree.grid_rowconfigure(0, weight=1)

        self.tree_resultados = ttk.Treeview(
            self.frame_tree,
            columns=("pa", "qtd", "direto", "rateio", "final"),
            show="headings",
            height=16
        )

        self.tree_resultados.heading("pa", text="PA")
        self.tree_resultados.heading("qtd", text="Qtd")
        self.tree_resultados.heading("direto", text="Custo Direto")
        self.tree_resultados.heading("rateio", text="Rateio 5014_0")
        self.tree_resultados.heading("final", text="Custo Final")

        self.tree_resultados.column("pa", width=360, anchor="w")
        self.tree_resultados.column("qtd", width=80, anchor="center")
        self.tree_resultados.column("direto", width=160, anchor="e")
        self.tree_resultados.column("rateio", width=160, anchor="e")
        self.tree_resultados.column("final", width=160, anchor="e")

        self.tree_scroll_y = ttk.Scrollbar(self.frame_tree, orient="vertical", command=self.tree_resultados.yview)
        self.tree_scroll_x = ttk.Scrollbar(self.frame_tree, orient="horizontal", command=self.tree_resultados.xview)

        self.tree_resultados.configure(
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set
        )

        self.tree_resultados.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # ---------------- Aba Log ----------------
        self.texto_log = ctk.CTkTextbox(self.tab_log)
        self.texto_log.pack(expand=True, fill="both", padx=10, pady=10)
        self.log("Sistema iniciado. Aguardando importação.")

        self.atualizar_cards_resumo()

    # ==========================================================
    # ====================== BANCO SQLITE =======================
    # ==========================================================
    def conectar_db(self):
        self.db = sqlite3.connect(self.db_path)
        self.cursor = self.db.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS precos (
                servico TEXT PRIMARY KEY,
                valor REAL
            )
        """)
        self.db.commit()

    def carregar_precos(self):
        self.cursor.execute("SELECT servico, valor FROM precos")
        dados = self.cursor.fetchall()
        return {servico: valor for servico, valor in dados}

    def salvar_precos(self):
        for servico, entry in self.inputs_precos.items():
            texto = entry.get().replace("R$", "").replace(",", ".").strip()
            try:
                valor = float(texto)
            except Exception:
                valor = 0.0

            self.cursor.execute("""
                INSERT INTO precos (servico, valor)
                VALUES (?, ?)
                ON CONFLICT(servico) DO UPDATE SET valor = excluded.valor
            """, (servico, valor))

        self.db.commit()
        self.precos = self.carregar_precos()
        self.log("Valores do lote atual salvos no banco.")

    # ==========================================================
    # ======================= UTILITÁRIOS =======================
    # ==========================================================
    def log(self, mensagem):
        self.texto_log.configure(state="normal")
        self.texto_log.insert("end", mensagem + "\n")
        self.texto_log.see("end")
        self.texto_log.configure(state="disabled")

    def formatar_moeda(self, valor):
        return f"R$ {valor:,.2f}"

    def criar_card_resumo(self, parent, titulo, valor, coluna):
        frame = ctk.CTkFrame(parent, corner_radius=14)
        frame.grid(row=0, column=coluna, padx=6, sticky="ew")

        lbl_titulo = ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(size=13)
        )
        lbl_titulo.pack(anchor="w", padx=16, pady=(14, 4))

        lbl_valor = ctk.CTkLabel(
            frame,
            text=valor,
            font=ctk.CTkFont(size=26, weight="bold")
        )
        lbl_valor.pack(anchor="w", padx=16, pady=(0, 14))

        return lbl_valor

    def atualizar_cards_resumo(self):
        pendencias = len(self.validar_precos_preenchidos(silencioso=True))
        self.card_arquivos.configure(text=str(self.qtd_arquivos_importados))
        self.card_servicos.configure(text=str(len(self.servicos_lote_atual)))
        self.card_pas.configure(text=str(self.qtd_pas_encontrados))
        self.card_pendencias.configure(text=str(pendencias))

        if self.qtd_arquivos_importados > 0:
            self.lbl_status_sidebar.configure(
                text=(
                    f"Lote atual carregado.\n"
                    f"{self.qtd_arquivos_importados} arquivo(s)\n"
                    f"{len(self.servicos_lote_atual)} serviço(s)\n"
                    f"{self.qtd_pas_encontrados} PA(s)"
                )
            )
        else:
            self.lbl_status_sidebar.configure(text="Nenhum lote importado")

    def limpar_lote_atual(self):
        self.dfs_processados = []
        self.df_final = pd.DataFrame()
        self.valor_rateio_5014_0 = 0.0
        self.servicos_lote_atual = []
        self.qtd_arquivos_importados = 0
        self.qtd_pas_encontrados = 0
        self.map_normalizacoes = []

        for widget in self.scroll_precos.winfo_children():
            widget.destroy()

        self.inputs_precos = {}
        self.labels_origem_preco = {}
        self.btn_pdf.configure(state="disabled")

        self.lbl_info_precos.configure(text="Nenhum lote carregado.")
        self.lbl_info_precos2.configure(
            text="Os valores abaixo refletem somente os serviços encontrados no lote atual."
        )

        self.lbl_resultado_resumo.configure(text="Nenhum cálculo executado.")
        self.texto_resultado.configure(state="normal")
        self.texto_resultado.delete("0.0", "end")
        self.texto_resultado.insert("0.0", "Resultado ainda não calculado.")
        self.texto_resultado.configure(state="disabled")

        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)

        self.atualizar_cards_resumo()
        self.log("Lote atual limpo.")
        self.main_area.set("Valores do lote")

    def normalizar_pa(self, valor):
        if pd.isna(valor):
            return ""

        original = str(valor).strip()
        texto = " ".join(original.split())
        texto = texto.rstrip(".")

        match = re.search(r"(\d+\s*[_-]\s*\d+)", texto)
        if match:
            codigo = match.group(1)
            codigo = re.sub(r"\s+", "", codigo)
            codigo = codigo.replace("-", "_")
            normalizado = f"Cooperativa e PA: {codigo}"
        else:
            normalizado = re.sub(
                r"^Cooperativa\s*e\s*PA\s*:\s*",
                "Cooperativa e PA: ",
                texto,
                flags=re.IGNORECASE
            )

        if normalizado != original:
            self.map_normalizacoes.append((original, normalizado))

        return normalizado

    def extrair_numero_pa(self, texto):
        match = re.search(r"(\d+)[_-](\d+)", str(texto))
        if match:
            try:
                return int(match.group(2))
            except Exception:
                return 999999
        return 999999

    def atualizar_estilo_entry_preco(self, entry, status):
        if status == "positivo_ou_zero":
            entry.configure(border_color=("#2CC985", "#2CC985"))
        elif status == "negativo":
            entry.configure(border_color=("#E6A23C", "#E6A23C"))
        else:
            entry.configure(border_color=("#D9534F", "#D9534F"))

    def ao_alterar_preco(self, event=None):
        for _, entry in self.inputs_precos.items():
            texto = entry.get().replace("R$", "").replace(",", ".").strip()

            try:
                valor = float(texto)
                if valor < 0:
                    self.atualizar_estilo_entry_preco(entry, "negativo")
                else:
                    self.atualizar_estilo_entry_preco(entry, "positivo_ou_zero")
            except Exception:
                self.atualizar_estilo_entry_preco(entry, "invalido")

        self.atualizar_cards_resumo()

    def validar_precos_preenchidos(self, silencioso=False):
        servicos_sem_preco = []

        for servico, entry in self.inputs_precos.items():
            texto = entry.get().replace("R$", "").replace(",", ".").strip()

            try:
                valor = float(texto)
                if valor < 0:
                    self.atualizar_estilo_entry_preco(entry, "negativo")
                else:
                    self.atualizar_estilo_entry_preco(entry, "positivo_ou_zero")
                valido = True
            except Exception:
                self.atualizar_estilo_entry_preco(entry, "invalido")
                valido = False

            if not valido:
                servicos_sem_preco.append(servico)

        if not silencioso:
            self.atualizar_cards_resumo()

        return servicos_sem_preco

    # ==========================================================
    # ======================== INTERFACE ========================
    # ==========================================================
    def criar_campos_preco(self, lista_servicos):
        for widget in self.scroll_precos.winfo_children():
            widget.destroy()

        self.inputs_precos = {}
        self.labels_origem_preco = {}

        if not lista_servicos:
            ctk.CTkLabel(
                self.scroll_precos,
                text="Nenhum serviço encontrado no lote atual."
            ).pack(padx=12, pady=12, anchor="w")
            return

        for i, servico in enumerate(lista_servicos):
            frame_linha = ctk.CTkFrame(self.scroll_precos)
            frame_linha.grid(row=i, column=0, padx=10, pady=6, sticky="ew")
            frame_linha.grid_columnconfigure(0, weight=1)

            frame_info = ctk.CTkFrame(frame_linha, fg_color="transparent")
            frame_info.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="ew")
            frame_info.grid_columnconfigure(0, weight=1)

            lbl_servico = ctk.CTkLabel(
                frame_info,
                text=servico,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            lbl_servico.grid(row=0, column=0, sticky="w")

            origem = "Valor novo"
            valor_atual = self.precos.get(servico, None)
            if valor_atual is not None:
                origem = "Valor carregado do histórico"

            lbl_origem = ctk.CTkLabel(
                frame_info,
                text=origem,
                anchor="w",
                font=ctk.CTkFont(size=11)
            )
            lbl_origem.grid(row=1, column=0, sticky="w", pady=(2, 0))

            entry = ctk.CTkEntry(
                frame_linha,
                width=140,
                height=36,
                justify="right",
                placeholder_text="0.00"
            )
            if valor_atual is not None:
                entry.insert(0, f"{valor_atual:.2f}")
            entry.grid(row=0, column=1, padx=(8, 12), pady=10)

            entry.bind("<KeyRelease>", self.ao_alterar_preco)
            entry.bind("<FocusOut>", self.ao_alterar_preco)

            self.inputs_precos[servico] = entry
            self.labels_origem_preco[servico] = lbl_origem

        self.ao_alterar_preco()

    def popular_tree_resultados(self):
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)

        if self.df_final.empty:
            return

        for _, row in self.df_final.iterrows():
            nome = row["PA"].replace("Cooperativa e PA: ", "")
            self.tree_resultados.insert(
                "",
                "end",
                values=(
                    nome,
                    int(row["Qtd"]),
                    self.formatar_moeda(row["Custo Direto"]),
                    self.formatar_moeda(row["Valor Rateio (5014_0)"]),
                    self.formatar_moeda(row["Custo Final"])
                )
            )

    # ==========================================================
    # ==================== IMPORTAÇÃO / CÁLCULO =================
    # ==========================================================
    def importar_arquivos(self):
        arquivos = filedialog.askopenfilenames(
            initialdir=self.ultima_pasta,
            title="Selecione os arquivos Excel",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )

        if not arquivos:
            return

        self.ultima_pasta = os.path.dirname(arquivos[0])
        self.dfs_processados = []
        self.df_final = pd.DataFrame()
        self.valor_rateio_5014_0 = 0.0
        self.map_normalizacoes = []

        servicos_encontrados = set()
        pas_encontrados = set()
        self.qtd_arquivos_importados = len(arquivos)

        self.log(f"Iniciando leitura de {len(arquivos)} arquivo(s).")

        for caminho in arquivos:
            nome_arq = os.path.basename(caminho)
            try:
                df_header = pd.read_excel(caminho, header=None, nrows=7)
                nome_servico = str(df_header.iloc[5, 1]).strip()
                servicos_encontrados.add(nome_servico)

                df_dados = pd.read_excel(
                    caminho,
                    skiprows=9,
                    header=None,
                    usecols="B"
                )
                df_dados.columns = ["PA_Descricao"]
                df_dados = df_dados.dropna()
                df_dados["PA_Descricao"] = df_dados["PA_Descricao"].apply(self.normalizar_pa)
                df_dados = df_dados[df_dados["PA_Descricao"] != ""]

                pas_encontrados.update(df_dados["PA_Descricao"].unique().tolist())

                contagem = df_dados["PA_Descricao"].value_counts().reset_index()
                contagem.columns = ["PA", "Qtd"]
                contagem["Serviço"] = nome_servico
                contagem["Arquivo"] = nome_arq

                self.dfs_processados.append(contagem)
                self.log(f"Arquivo processado com sucesso: {nome_arq}")

            except Exception as e:
                self.log(f"Erro ao ler {nome_arq}: {e}")

        self.servicos_lote_atual = sorted(servicos_encontrados)
        self.qtd_pas_encontrados = len(pas_encontrados)

        self.criar_campos_preco(self.servicos_lote_atual)

        self.lbl_info_precos.configure(
            text=(
                f"Lote atual com {self.qtd_arquivos_importados} arquivo(s), "
                f"{len(self.servicos_lote_atual)} serviço(s) e "
                f"{self.qtd_pas_encontrados} PA(s)."
            )
        )
        self.lbl_info_precos2.configure(
            text="Somente os serviços identificados neste lote aparecem abaixo. "
                 "Valores salvos anteriormente são usados apenas como sugestão."
        )

        self.btn_pdf.configure(state="disabled")
        self.atualizar_cards_resumo()
        self.main_area.set("Valores do lote")

        if self.map_normalizacoes:
            total_ajustes = len(self.map_normalizacoes)
            exemplos = self.map_normalizacoes[:5]
            self.log(f"{total_ajustes} ajuste(s) de padronização de PA aplicado(s).")
            for original, normalizado in exemplos:
                self.log(f"Normalizado: '{original}' -> '{normalizado}'")
            if total_ajustes > 5:
                self.log("Demais ajustes omitidos no log para não poluir a execução.")

        messagebox.showinfo(
            "Importação concluída",
            "Arquivos importados com sucesso. Revise os valores do lote atual antes de calcular."
        )

    def calcular_tudo(self):
        if not self.dfs_processados:
            messagebox.showwarning("Aviso", "Importe arquivos primeiro.")
            return

        servicos_invalidos = self.validar_precos_preenchidos()
        if servicos_invalidos:
            messagebox.showwarning(
                "Valores pendentes",
                "Existem serviços com valor vazio ou inválido:\n\n- " + "\n- ".join(servicos_invalidos)
            )
            self.log(
                "Cálculo bloqueado por valor ausente/inválido nos serviços: "
                + ", ".join(servicos_invalidos)
            )
            self.main_area.set("Valores do lote")
            return

        self.salvar_precos()

        df_geral = pd.concat(self.dfs_processados, ignore_index=True)
        df_geral["PA"] = df_geral["PA"].apply(self.normalizar_pa)

        df_geral["Valor Unitário"] = df_geral["Serviço"].map(self.precos).fillna(0)
        df_geral["Custo Total"] = df_geral["Qtd"] * df_geral["Valor Unitário"]

        df_resumo = df_geral.groupby("PA").agg({
            "Qtd": "sum",
            "Custo Total": "sum"
        }).reset_index()
        df_resumo.rename(columns={"Custo Total": "Custo Direto"}, inplace=True)

        masc = df_resumo["PA"].str.contains(r"5014_0\b", na=False, regex=True)
        self.valor_rateio_5014_0 = df_resumo.loc[masc, "Custo Direto"].sum()

        df_filiais = df_resumo[~masc].copy()
        total_vol = df_filiais["Qtd"].sum()

        if total_vol > 0:
            df_filiais["% Rateio"] = df_filiais["Qtd"] / total_vol
            df_filiais["Valor Rateio (5014_0)"] = df_filiais["% Rateio"] * self.valor_rateio_5014_0
        else:
            df_filiais["% Rateio"] = 0
            df_filiais["Valor Rateio (5014_0)"] = 0

        df_filiais["Custo Final"] = df_filiais["Custo Direto"] + df_filiais["Valor Rateio (5014_0)"]
        df_filiais["Key"] = df_filiais["PA"].apply(self.extrair_numero_pa)
        df_filiais = df_filiais.sort_values(["Key", "PA"]).drop(columns=["Key"])

        self.df_final = df_filiais

        total_final = df_filiais["Custo Final"].sum()
        qtd_pas_resultado = len(df_filiais)

        texto = f"RESUMO DO CÁLCULO\n{'=' * 70}\n"
        texto += f"Arquivos importados: {self.qtd_arquivos_importados}\n"
        texto += f"Serviços considerados: {len(self.servicos_lote_atual)}\n"
        texto += f"PAs considerados no resultado: {qtd_pas_resultado}\n"
        texto += f"Valor total do rateio 5014_0: {self.formatar_moeda(self.valor_rateio_5014_0)}\n"
        texto += f"Total de volumes para rateio: {int(total_vol)}\n"
        texto += f"Total final distribuído: {self.formatar_moeda(total_final)}\n"
        texto += f"{'=' * 70}\n\n"

        for _, row in df_filiais.iterrows():
            nome = row["PA"].replace("Cooperativa e PA: ", "")
            texto += (
                f"{nome:<20} | "
                f"Qtd: {int(row['Qtd']):<6} | "
                f"Direto: {self.formatar_moeda(row['Custo Direto']):<15} | "
                f"Rateio: {self.formatar_moeda(row['Valor Rateio (5014_0)']):<15} | "
                f"Final: {self.formatar_moeda(row['Custo Final'])}\n"
            )

        self.texto_resultado.configure(state="normal")
        self.texto_resultado.delete("0.0", "end")
        self.texto_resultado.insert("0.0", texto)
        self.texto_resultado.configure(state="disabled")

        self.lbl_resultado_resumo.configure(
            text=(
                f"Cálculo concluído com {qtd_pas_resultado} PA(s) no resultado final | "
                f"Rateio 5014_0: {self.formatar_moeda(self.valor_rateio_5014_0)} | "
                f"Total final: {self.formatar_moeda(total_final)}"
            )
        )

        self.popular_tree_resultados()
        self.btn_pdf.configure(state="normal")
        self.main_area.set("Resultados")

        self.log("Cálculo concluído com sucesso.")
        self.log(f"Rateio 5014_0 apurado: {self.formatar_moeda(self.valor_rateio_5014_0)}")
        self.log(f"Total final consolidado: {self.formatar_moeda(total_final)}")

    # ==========================================================
    # ========================= PDF =============================
    # ==========================================================
    def gerar_pdf(self):
        if self.df_final.empty:
            messagebox.showwarning("Aviso", "Não há dados calculados para exportar.")
            return

        arquivo_pdf = filedialog.asksaveasfilename(
            initialdir=self.ultima_pasta,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Relatorio_Rateio_Confidencial.pdf",
            title="Salvar relatório PDF"
        )

        if not arquivo_pdf:
            return

        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 34)
                self.set_text_color(235, 235, 235)
                self.text(40, 95, "DOCUMENTO")
                self.text(44, 115, "CONFIDENCIAL")
                self.set_font("Arial", "B", 16)
                self.text(112, 129, "Uso Interno")
                self.set_text_color(0, 0, 0)

            def footer(self):
                self.set_y(-12)
                self.set_font("Arial", "I", 8)
                self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

        pdf = PDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_y(18)

        pdf.set_font("Arial", "B", 15)
        pdf.cell(0, 10, "Relatório de Custos e Rateio por PA", ln=True, align="C")
        pdf.ln(3)

        total_final = self.df_final["Custo Final"].sum()
        total_vol = self.df_final["Qtd"].sum()

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, f"Arquivos importados: {self.qtd_arquivos_importados}", ln=True)
        pdf.cell(0, 7, f"Serviços considerados: {len(self.servicos_lote_atual)}", ln=True)
        pdf.cell(0, 7, f"Rateio 5014_0: {self.formatar_moeda(self.valor_rateio_5014_0)}", ln=True)
        pdf.cell(0, 7, f"Total de volumes considerados: {int(total_vol)}", ln=True)
        pdf.cell(0, 7, f"Total final consolidado: {self.formatar_moeda(total_final)}", ln=True)
        pdf.ln(5)

        cols = [
            ("PA (Unidade)", 78),
            ("Qtd", 24),
            ("Custo Direto", 42),
            ("Rateio", 42),
            ("Custo Final", 42)
        ]

        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(225, 225, 225)
        for titulo, largura in cols:
            pdf.cell(largura, 8, titulo, 1, 0, "C", fill=True)
        pdf.ln()

        pdf.set_font("Arial", "", 8.5)
        total_somado = 0

        for _, row in self.df_final.iterrows():
            nome = row["PA"].replace("Cooperativa e PA: ", "")[:45]
            pdf.cell(78, 8, nome, 1)
            pdf.cell(24, 8, str(int(row["Qtd"])), 1, 0, "C")
            pdf.cell(42, 8, self.formatar_moeda(row["Custo Direto"]), 1, 0, "R")
            pdf.cell(42, 8, self.formatar_moeda(row["Valor Rateio (5014_0)"]), 1, 0, "R")
            pdf.cell(42, 8, self.formatar_moeda(row["Custo Final"]), 1, 0, "R")
            pdf.ln()
            total_somado += row["Custo Final"]

        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(210, 210, 210)
        pdf.cell(186, 10, "TOTAL FINAL", 1, 0, "R", fill=True)
        pdf.cell(42, 10, self.formatar_moeda(total_somado), 1, 0, "R", fill=True)

        pdf.output(arquivo_pdf)
        self.log(f"PDF criado: {arquivo_pdf}")
        messagebox.showinfo("Sucesso", "PDF gerado com sucesso.")

    # ==========================================================
    # ======================= ENCERRAMENTO ======================
    # ==========================================================
    def destroy(self):
        try:
            self.db.close()
        except Exception:
            pass
        super().destroy()


if __name__ == "__main__":
    app = AppCustos()
    app.mainloop()