import secrets
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import pyperclip
from cryptography.fernet import Fernet
import os
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



# Gera uma chave e salva em um arquivo (execute uma única vez)
def gerar_chave():
    chave = Fernet.generate_key()
    with open("chave.key", "wb") as arquivo_chave:
        arquivo_chave.write(chave)

# Carrega a chave existente
def carregar_chave():
    try:
        return open("chave.key", "rb").read()
    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo de chave não encontrado! Gere uma chave primeiro.")
        return None

# Classe para estatísticas de uso
class Estatisticas:
    def __init__(self):
        self.arquivos_criptografados = 0
        self.arquivos_descriptografados = 0
        self.tamanho_total_criptografado = 0  # em bytes
        self.tamanho_total_descriptografado = 0  # em bytes
        self.operacoes_por_dia = {}  # formato: {'YYYY-MM-DD': {'cripto': N, 'descripto': M}}
        self.tipos_arquivos = {}  # formato: {'.txt': {'cripto': N, 'descripto': M}}
        self.hora_inicio = datetime.datetime.now()

    def registrar_operacao(self, tipo, tamanho=0, extensao=None):
        # Registra operação por tipo
        if tipo == 'criptografar':
            self.arquivos_criptografados += 1
            self.tamanho_total_criptografado += tamanho
        elif tipo == 'descriptografar':
            self.arquivos_descriptografados += 1
            self.tamanho_total_descriptografado += tamanho

        # Registra operação por data
        data_hoje = datetime.datetime.now().strftime('%Y-%m-%d')
        if data_hoje not in self.operacoes_por_dia:
            self.operacoes_por_dia[data_hoje] = {'cripto': 0, 'descripto': 0}

        if tipo == 'criptografar':
            self.operacoes_por_dia[data_hoje]['cripto'] += 1
        elif tipo == 'descriptografar':
            self.operacoes_por_dia[data_hoje]['descripto'] += 1

        # Registra operação por tipo de arquivo
        if extensao:
            if extensao not in self.tipos_arquivos:
                self.tipos_arquivos[extensao] = {'cripto': 0, 'descripto': 0}

            if tipo == 'criptografar':
                self.tipos_arquivos[extensao]['cripto'] += 1
            elif tipo == 'descriptografar':
                self.tipos_arquivos[extensao]['descripto'] += 1

# Instancia objeto de estatísticas
estatisticas = Estatisticas()

# Função para criptografar o texto
def criptografar():
    mensagem = entrada_texto.get("1.0", tk.END).strip()
    if not mensagem:
        messagebox.showwarning("Aviso", "Digite um texto para criptografar!")
        return

    chave = carregar_chave()
    if chave:
        fernet = Fernet(chave)
        mensagem_encriptada = fernet.encrypt(mensagem.encode())
        saida_texto.delete("1.0", tk.END)
        saida_texto.insert(tk.END, mensagem_encriptada.decode())

        # Registrar estatísticas
        estatisticas.registrar_operacao('criptografar', len(mensagem))
        atualizar_estatisticas()

# Função para descriptografar o texto
def descriptografar():
    mensagem_encriptada = entrada_texto.get("1.0", tk.END).strip()
    if not mensagem_encriptada:
        messagebox.showwarning("Aviso", "Digite um texto criptografado para descriptografar!")
        return

    chave = carregar_chave()
    if chave:
        try:
            fernet = Fernet(chave)
            mensagem_decriptada = fernet.decrypt(mensagem_encriptada.encode()).decode()
            saida_texto.delete("1.0", tk.END)
            saida_texto.insert(tk.END, mensagem_decriptada)

            # Registrar estatísticas
            estatisticas.registrar_operacao('descriptografar', len(mensagem_encriptada))
            atualizar_estatisticas()
        except Exception:
            messagebox.showerror("Erro", "Falha ao descriptografar! Verifique a chave ou o texto.")

# Função para limpar os campos de texto
def limpar_texto():
    entrada_texto.delete("1.0", tk.END)
    saida_texto.delete("1.0", tk.END)

# Função para carregar arquivo
def carregar_arquivo():
    arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo",
        filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )

    if arquivo:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                entrada_texto.delete("1.0", tk.END)
                entrada_texto.insert(tk.END, conteudo)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo: {e}")

# Função para salvar resultado em arquivo
def salvar_arquivo():
    conteudo = saida_texto.get("1.0", tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Não há conteúdo para salvar!")
        return

    arquivo = filedialog.asksaveasfilename(
        title="Salvar como",
        defaultextension=".txt",
        filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )

    if arquivo:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo: {e}")

# Função para adicionar informação ao histórico de arquivos
def adicionar_ao_historico(operacao, caminho_arquivo):
    timestamp = tk.Label(frame_historico_arquivos, text=f"{operacao}: {caminho_arquivo}", anchor="w", pady=2)
    timestamp.pack(fill="x", padx=5)

    # Atualiza também a barra de status
    barra_status.config(text=f"{operacao}: {caminho_arquivo}")

    # Rolar para o final para mostrar a entrada mais recente
    canvas_historico.update_idletasks()
    canvas_historico.yview_moveto(1.0)

# Função para criptografar múltiplos arquivos
def criptografar_arquivo():
    arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos para criptografar",
        filetypes=(("Todos os arquivos", "*.*"),)
    )

    if arquivos:
        chave = carregar_chave()
        if not chave:
            return

        fernet = Fernet(chave)
        criar_backup = messagebox.askyesno("Backup", "Deseja criar backups dos arquivos originais?")

        arquivos_processados = 0
        erros = 0
        tamanho_total = 0

        for arquivo in arquivos:
            try:
                # Ler o arquivo em modo binário
                with open(arquivo, "rb") as f:
                    conteudo = f.read()
                    tamanho_arquivo = len(conteudo)
                    tamanho_total += tamanho_arquivo

                conteudo_criptografado = fernet.encrypt(conteudo)

                # Criar backup do arquivo original se solicitado
                if criar_backup:
                    arquivo_backup = arquivo + ".bak"
                    import shutil
                    shutil.copy2(arquivo, arquivo_backup)

                # Sobrescrever o arquivo original com o conteúdo criptografado
                with open(arquivo, "wb") as f:
                    f.write(conteudo_criptografado)

                adicionar_ao_historico("Arquivo criptografado", arquivo)
                arquivos_processados += 1

                # Registrar estatísticas
                _, extensao = os.path.splitext(arquivo)
                estatisticas.registrar_operacao('criptografar', tamanho_arquivo, extensao)

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criptografar o arquivo '{os.path.basename(arquivo)}': {e}")
                erros += 1

        # Mostrar resumo da operação
        if erros == 0:
            messagebox.showinfo("Sucesso", f"{arquivos_processados} arquivo(s) criptografado(s) com sucesso!")
        else:
            messagebox.showwarning("Concluído com erros",
                                   f"{arquivos_processados} arquivo(s) criptografado(s) com sucesso.\n"
                                   f"{erros} arquivo(s) não puderam ser processados.")

        # Atualizar estatísticas
        atualizar_estatisticas()

# Função para descriptografar múltiplos arquivos
def descriptografar_arquivo():
    arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos criptografados",
        filetypes=(("Todos os arquivos", "*.*"),)
    )

    if arquivos:
        chave = carregar_chave()
        if not chave:
            return

        fernet = Fernet(chave)
        arquivos_processados = 0
        erros = 0
        tamanho_total = 0

        for arquivo in arquivos:
            try:
                # Ler o arquivo criptografado
                with open(arquivo, "rb") as f:
                    conteudo_criptografado = f.read()
                    tamanho_arquivo = len(conteudo_criptografado)
                    tamanho_total += tamanho_arquivo

                try:
                    conteudo_descriptografado = fernet.decrypt(conteudo_criptografado)

                    # Sobrescrever o arquivo criptografado com o conteúdo descriptografado
                    with open(arquivo, "wb") as f:
                        f.write(conteudo_descriptografado)

                    adicionar_ao_historico("Arquivo descriptografado", arquivo)
                    arquivos_processados += 1

                    # Registrar estatísticas
                    _, extensao = os.path.splitext(arquivo)
                    estatisticas.registrar_operacao('descriptografar', tamanho_arquivo, extensao)

                except Exception:
                    messagebox.showerror("Erro",
                                         f"Falha ao descriptografar o arquivo '{os.path.basename(arquivo)}'! Verifique a chave ou o arquivo.")
                    erros += 1

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir arquivo '{os.path.basename(arquivo)}': {e}")
                erros += 1

        # Mostrar resumo da operação
        if erros == 0:
            messagebox.showinfo("Sucesso", f"{arquivos_processados} arquivo(s) descriptografado(s) com sucesso!")
        else:
            messagebox.showwarning("Concluído com erros",
                                   f"{arquivos_processados} arquivo(s) descriptografado(s) com sucesso.\n"
                                   f"{erros} arquivo(s) não puderam ser processados.")

        # Atualizar estatísticas
        atualizar_estatisticas()

# Função para criptografar uma pasta inteira
def criptografar_pasta():
    pasta = filedialog.askdirectory(title="Selecione a pasta para criptografar")
    if not pasta:
        return

    chave = carregar_chave()
    if not chave:
        return

    # Perguntar se deve incluir subpastas
    incluir_subpastas = messagebox.askyesno("Subpastas", "Deseja incluir subpastas na criptografia?")

    # Perguntar se deve criar backups
    criar_backup = messagebox.askyesno("Backup", "Deseja criar backups dos arquivos originais?")

    # Perguntar sobre padrões de arquivo para incluir/excluir
    padrao_incluir = simpledialog.askstring(
        "Filtro de Arquivos",
        "Digite extensões para incluir separadas por vírgula (vazio = todos):",
        initialvalue="txt,doc,pdf,jpg,png"
    )

    # Processar os padrões
    padroes_incluir = []
    if padrao_incluir:
        padroes_incluir = [f".{ext.strip().lower()}" for ext in padrao_incluir.split(",")]

    fernet = Fernet(chave)
    arquivos_processados = 0
    erros = 0
    skipped = 0
    tamanho_total = 0

    # Configurar barra de progresso
    barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=100, mode="determinate")
    barra_progresso.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
    barra_status.config(text="Contando arquivos...")
    janela.update()

    # Contar total de arquivos para a barra de progresso
    total_arquivos = 0
    for pasta_atual, subpastas, arquivos in os.walk(pasta):
        if not incluir_subpastas and pasta_atual != pasta:
            continue
        for arquivo in arquivos:
            # Verificar se o arquivo corresponde aos padrões de inclusão
            if padroes_incluir and not any(arquivo.lower().endswith(ext) for ext in padroes_incluir):
                continue
            total_arquivos += 1

    # Iniciar processamento
    barra_status.config(text=f"Processando {total_arquivos} arquivos...")
    janela.update()

    # Função para processar um único arquivo
    def processar_arquivo(caminho_completo):
        nonlocal arquivos_processados, erros, skipped, tamanho_total

        # Verificar se o arquivo corresponde aos padrões de inclusão
        if padroes_incluir and not any(caminho_completo.lower().endswith(ext) for ext in padroes_incluir):
            skipped += 1
            return

        try:
            # Ler o arquivo em modo binário
            with open(caminho_completo, "rb") as f:
                conteudo = f.read()
                tamanho_arquivo = len(conteudo)
                tamanho_total += tamanho_arquivo

            # Verificar se o arquivo já está criptografado
            try:
                # Tentar descriptografar para ver se já está criptografado
                fernet.decrypt(conteudo)
                # Se não der erro, o arquivo já está criptografado
                adicionar_ao_historico("Arquivo já criptografado (pulado)", caminho_completo)
                skipped += 1
                return
            except Exception:
                # O arquivo não está criptografado, prosseguir com a criptografia
                pass

            conteudo_criptografado = fernet.encrypt(conteudo)

            # Criar backup do arquivo original se solicitado
            if criar_backup:
                arquivo_backup = caminho_completo + ".bak"
                import shutil
                shutil.copy2(caminho_completo, arquivo_backup)

            # Sobrescrever o arquivo original com o conteúdo criptografado
            with open(caminho_completo, "wb") as f:
                f.write(conteudo_criptografado)

            adicionar_ao_historico("Arquivo criptografado", caminho_completo)
            arquivos_processados += 1

            # Registrar estatísticas
            _, extensao = os.path.splitext(caminho_completo)
            estatisticas.registrar_operacao('criptografar', tamanho_arquivo, extensao)

        except Exception as e:
            adicionar_ao_historico("Erro ao criptografar", f"{caminho_completo}: {str(e)}")
            erros += 1

    # Percorrer a pasta recursivamente
    current_count = 0
    for pasta_atual, subpastas, arquivos in os.walk(pasta):
        if not incluir_subpastas and pasta_atual != pasta:
            continue

        for arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, arquivo)
            processar_arquivo(caminho_completo)

            # Atualizar a barra de progresso
            current_count += 1
            if total_arquivos > 0:
                progresso = (current_count / total_arquivos) * 100
                barra_progresso.config(value=progresso)
                barra_status.config(text=f"Processando: {current_count}/{total_arquivos}")
                janela.update()

    # Remover a barra de progresso
    barra_progresso.destroy()

    # Mostrar resumo da operação
    messagebox.showinfo("Operação Concluída",
                        f"Operação de criptografia concluída:\n"
                        f"- {arquivos_processados} arquivo(s) criptografado(s)\n"
                        f"- {skipped} arquivo(s) pulado(s)\n"
                        f"- {erros} erro(s)")

    barra_status.config(text="Pronto")

    # Atualizar estatísticas
    atualizar_estatisticas()

# Função para descriptografar uma pasta inteira
def descriptografar_pasta():
    pasta = filedialog.askdirectory(title="Selecione a pasta para descriptografar")
    if not pasta:
        return

    chave = carregar_chave()
    if not chave:
        return

    # Perguntar se deve incluir subpastas
    incluir_subpastas = messagebox.askyesno("Subpastas", "Deseja incluir subpastas na descriptografia?")

    fernet = Fernet(chave)
    arquivos_processados = 0
    erros = 0
    skipped = 0
    tamanho_total = 0

    # Configurar barra de progresso
    barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=100, mode="determinate")
    barra_progresso.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
    barra_status.config(text="Contando arquivos...")
    janela.update()

    # Contar total de arquivos para a barra de progresso
    total_arquivos = 0
    for pasta_atual, subpastas, arquivos in os.walk(pasta):
        if not incluir_subpastas and pasta_atual != pasta:
            continue
        total_arquivos += len(arquivos)

    # Iniciar processamento
    barra_status.config(text=f"Processando {total_arquivos} arquivos...")
    janela.update()

    # Função para processar um único arquivo
    def processar_arquivo(caminho_completo):
        nonlocal arquivos_processados, erros, skipped, tamanho_total

        try:
            # Ignorar arquivos de backup
            if caminho_completo.endswith(".bak"):
                skipped += 1
                return

            # Ler o arquivo em modo binário
            with open(caminho_completo, "rb") as f:
                conteudo_criptografado = f.read()
                tamanho_arquivo = len(conteudo_criptografado)
                tamanho_total += tamanho_arquivo

            try:
                # Tentar descriptografar
                conteudo_descriptografado = fernet.decrypt(conteudo_criptografado)

                # Sobrescrever o arquivo criptografado com o conteúdo descriptografado
                with open(caminho_completo, "wb") as f:
                    f.write(conteudo_descriptografado)

                adicionar_ao_historico("Arquivo descriptografado", caminho_completo)
                arquivos_processados += 1

                # Registrar estatísticas
                _, extensao = os.path.splitext(caminho_completo)
                estatisticas.registrar_operacao('descriptografar', tamanho_arquivo, extensao)

            except Exception:
                # O arquivo não estava criptografado com esta chave
                adicionar_ao_historico("Arquivo não criptografado (pulado)", caminho_completo)
                skipped += 1

        except Exception as e:
            adicionar_ao_historico("Erro ao processar", f"{caminho_completo}: {str(e)}")
            erros += 1

    # Percorrer a pasta recursivamente
    current_count = 0
    for pasta_atual, subpastas, arquivos in os.walk(pasta):
        if not incluir_subpastas and pasta_atual != pasta:
            continue

        for arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, arquivo)
            processar_arquivo(caminho_completo)

            # Atualizar a barra de progresso
            current_count += 1
            if total_arquivos > 0:
                progresso = (current_count / total_arquivos) * 100
                barra_progresso.config(value=progresso)
                barra_status.config(text=f"Processando: {current_count}/{total_arquivos}")
                janela.update()

    # Remover a barra de progresso
    barra_progresso.destroy()

    # Mostrar resumo da operação
    messagebox.showinfo("Operação Concluída",
                        f"Operação de descriptografia concluída:\n"
                        f"- {arquivos_processados} arquivo(s) descriptografado(s)\n"
                        f"- {skipped} arquivo(s) pulado(s)\n"
                        f"- {erros} erro(s)")

    barra_status.config(text="Pronto")

    # Atualizar estatísticas
    atualizar_estatisticas()

# Função para limpar histórico de arquivos
def limpar_historico():
    for widget in frame_historico_arquivos.winfo_children():
        widget.destroy()
    adicionar_ao_historico("Histórico limpo", "")

# Função para atualizar a exibição de estatísticas
def atualizar_estatisticas():
    # Limpar área de estatísticas
    for widget in frame_estatisticas_dados.winfo_children():
        widget.destroy()

    # Converter bytes para unidades legíveis
    def bytes_para_legivel(tamanho_bytes):
        for unidade in ['B', 'KB', 'MB', 'GB']:
            if tamanho_bytes < 1024.0:
                return f"{tamanho_bytes:.2f} {unidade}"
            tamanho_bytes /= 1024.0
        return f"{tamanho_bytes:.2f} TB"

    # Criar labels com estatísticas
    labels = [
        f"Arquivos criptografados: {estatisticas.arquivos_criptografados}",
        f"Arquivos descriptografados: {estatisticas.arquivos_descriptografados}",
        f"Volume total criptografado: {bytes_para_legivel(estatisticas.tamanho_total_criptografado)}",
        f"Volume total descriptografado: {bytes_para_legivel(estatisticas.tamanho_total_descriptografado)}",
    ]

    # Adicionar labels ao frame
    for i, texto in enumerate(labels):
        lbl = tk.Label(frame_estatisticas_dados, text=texto, anchor="w", pady=5)
        lbl.grid(row=i, column=0, sticky="w", padx=10)

    # Atualizar gráficos
    atualizar_graficos()

# Função para atualizar gráficos na aba de estatísticas
def atualizar_graficos():
    # Limpar área de gráficos
    for widget in frame_graficos.winfo_children():
        widget.destroy()

    # Criar figura para os gráficos
    fig = plt.Figure(figsize=(10, 6), dpi=100)

    # Gráfico 1: Comparação entre arquivos criptografados e descriptografados
    ax1 = fig.add_subplot(221)
    labels = ['Criptografados', 'Descriptografados']
    valores = [estatisticas.arquivos_criptografados, estatisticas.arquivos_descriptografados]
    ax1.bar(labels, valores, color=['blue', 'green'])
    ax1.set_title('Total de Arquivos Processados')

    # Gráfico 2: Operações por tipo de arquivo
    ax2 = fig.add_subplot(222)
    extensoes = list(estatisticas.tipos_arquivos.keys())
    cripto = [estatisticas.tipos_arquivos[ext]['cripto'] for ext in extensoes]
    descripto = [estatisticas.tipos_arquivos[ext]['descripto'] for ext in extensoes]

    # Limitar a 5 tipos mais comuns para melhor visualização
    if len(extensoes) > 5:
        # Ordenar por quantidade total
        totais = [(ext, estatisticas.tipos_arquivos[ext]['cripto'] + estatisticas.tipos_arquivos[ext]['descripto'])
                  for ext in extensoes]
        totais.sort(key=lambda x: x[1], reverse=True)

        # Pegar os 5 mais comuns
        top_exts = [item[0] for item in totais[:5]]
        extensoes = top_exts
        cripto = [estatisticas.tipos_arquivos[ext]['cripto'] for ext in extensoes]
        descripto = [estatisticas.tipos_arquivos[ext]['descripto'] for ext in extensoes]

    # Garantir que há pelo menos um valor para plotar
    if extensoes:
        x = range(len(extensoes))
        largura = 0.35
        ax2.bar([i - largura / 2 for i in x], cripto, largura, label='Criptografados', color='blue')
        ax2.bar([i + largura / 2 for i in x], descripto, largura, label='Descriptografados', color='green')
        ax2.set_xticks(x)
        ax2.set_xticklabels(extensoes)
        ax2.set_title('Operações por Tipo de Arquivo')
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, 'Sem dados para exibir', ha='center', va='center')

    # Gráfico 3: Operações por dia (últimos 7 dias ou todos se menos que 7)
    ax3 = fig.add_subplot(212)

    # Obter últimos 7 dias (ou todos disponíveis)
    dias = list(estatisticas.operacoes_por_dia.keys())
    dias.sort()  # Ordenar por data

    if len(dias) > 7:
        dias = dias[-7:]  # Últimos 7 dias

    cripto_por_dia = [estatisticas.operacoes_por_dia[dia]['cripto'] for dia in dias]
    descripto_por_dia = [estatisticas.operacoes_por_dia[dia]['descripto'] for dia in dias]

    # Formatação das datas para o gráfico
    dias_formatados = [dia.split('-')[2] + '/' + dia.split('-')[1] for dia in dias]  # Formato DD/MM

    # Garantir que há pelo menos um dia para plotar
    if dias:
        x = range(len(dias))
        largura = 0.35
        ax3.bar([i - largura / 2 for i in x], cripto_por_dia, largura, label='Criptografados', color='blue')
        ax3.bar([i + largura / 2 for i in x], descripto_por_dia, largura, label='Descriptografados', color='green')
        ax3.set_xticks(x)
        ax3.set_xticklabels(dias_formatados)
        ax3.set_title('Operações por Dia')
        ax3.legend()
    else:
        ax3.text(0.5, 0.5, 'Sem dados para exibir', ha='center', va='center')

    # Ajustar layout
    fig.tight_layout()

    # Exibir na interface
    canvas = FigureCanvasTkAgg(fig, master=frame_graficos)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Função para exportar as estatísticas para um arquivo
def exportar_estatisticas():
    arquivo = filedialog.asksaveasfilename(
        title="Exportar Estatísticas",
        defaultextension=".txt",
        filetypes=(("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )

    if not arquivo:
        return

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            # Cabeçalho
            f.write("RELATÓRIO DE ESTATÍSTICAS DE USO\n")
            f.write("==============================\n\n")

            f.write(f"Data do relatório: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Estatísticas gerais
            f.write("ESTATÍSTICAS GERAIS\n")
            f.write("-----------------\n")
            f.write(f"Arquivos criptografados: {estatisticas.arquivos_criptografados}\n")
            f.write(f"Arquivos descriptografados: {estatisticas.arquivos_descriptografados}\n")

            # Função auxiliar para formatar tamanhos
            def bytes_para_legivel(tamanho_bytes):
                for unidade in ['B', 'KB', 'MB', 'GB']:
                    if tamanho_bytes < 1024.0:
                        return f"{tamanho_bytes:.2f} {unidade}"
                    tamanho_bytes /= 1024.0
                return f"{tamanho_bytes:.2f} TB"

            f.write(f"Volume total criptografado: {bytes_para_legivel(estatisticas.tamanho_total_criptografado)}\n")
            f.write(
                f"Volume total descriptografado: {bytes_para_legivel(estatisticas.tamanho_total_descriptografado)}\n\n")

            # Estatísticas por tipo de arquivo
            f.write("ESTATÍSTICAS POR TIPO DE ARQUIVO\n")
            f.write("------------------------------\n")
            for ext, dados in estatisticas.tipos_arquivos.items():
                f.write(f"Extensão {ext}:\n")
                f.write(f"  - Arquivos criptografados: {dados['cripto']}\n")
                f.write(f"  - Arquivos descriptografados: {dados['descripto']}\n")
            f.write("\n")

            # Estatísticas por dia
            f.write("ESTATÍSTICAS POR DIA\n")
            f.write("-------------------\n")
            dias = list(estatisticas.operacoes_por_dia.keys())
            dias.sort()
            for dia in dias:
                dados = estatisticas.operacoes_por_dia[dia]
                f.write(f"Data {dia}:\n")
                f.write(f"  - Arquivos criptografados: {dados['cripto']}\n")
                f.write(f"  - Arquivos descriptografados: {dados['descripto']}\n")

            messagebox.showinfo("Sucesso", "Estatísticas exportadas com sucesso!")

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível exportar as estatísticas: {e}")

def limpar_dados_estatisticas():
    resposta = messagebox.askyesno("Limpar Dados",
                                   "Tem certeza que deseja limpar todos os dados estatísticos?\nEsta ação não pode ser desfeita.")
    if resposta:
        try:
            # Limpar os dados do objeto estatisticas
            estatisticas.arquivos_criptografados = 0
            estatisticas.arquivos_descriptografados = 0
            estatisticas.tamanho_total_criptografado = 0
            estatisticas.tamanho_total_descriptografado = 0
            estatisticas.tipos_arquivos = {}
            estatisticas.operacoes_por_dia = {}

            # Se você estiver usando um banco de dados ou arquivo, limpe também
            # limpar_registros_db()

            # Limpar a visualização
            detalhes_texto.delete(1.0, tk.END)
            detalhes_texto.insert(tk.END, "Todos os dados estatísticos foram removidos.")

            # Atualizar os gráficos
            atualizar_graficos()

            # Atualizar as estatísticas
            atualizar_estatisticas()

            messagebox.showinfo("Sucesso", "Dados estatísticos limpos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível limpar os dados: {str(e)}")

# Criando a interface gráfica com Tkinter
janela = tk.Tk()
janela.title("CryptographiE")

# Configurar comportamento responsivo
janela.minsize(400, 450)  # Tamanho mínimo da janela
janela.columnconfigure(0, weight=1)  # Faz a coluna principal expandir
janela.rowconfigure(0, weight=1)  # Faz a linha principal expandir

# Criar notebook (sistema de abas)
notebook = ttk.Notebook(janela)
notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Aba 1: Criptografia de Texto
aba_texto = ttk.Frame(notebook)
notebook.add(aba_texto, text="Criptografia de Texto")
aba_texto.columnconfigure(0, weight=1)
aba_texto.rowconfigure(0, weight=40)
aba_texto.rowconfigure(1, weight=1)
aba_texto.rowconfigure(2, weight=40)

# Aba 2: Criptografia de Arquivos
aba_arquivos = ttk.Frame(notebook)
notebook.add(aba_arquivos, text="Criptografia de Arquivos")
aba_arquivos.columnconfigure(0, weight=1)
aba_arquivos.rowconfigure(0, weight=1)

# Aba 3: Estatísticas
aba_estatisticas = ttk.Frame(notebook)
notebook.add(aba_estatisticas, text="Estatísticas")
aba_estatisticas.columnconfigure(0, weight=1)
aba_estatisticas.rowconfigure(0, weight=1)


# Conteúdo da Aba 1: Criptografia de Texto
# Frame para área de entrada de texto
frame_entrada = tk.LabelFrame(aba_texto, text="Entrada", font=("Arial", 10))
frame_entrada.grid(row=0, column=0, sticky="nsew", pady=5)
frame_entrada.columnconfigure(0, weight=1)
frame_entrada.rowconfigure(0, weight=1)

# Área de entrada com ScrolledText
entrada_texto = scrolledtext.ScrolledText(frame_entrada, height=8)
entrada_texto.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Botão para abrir arquivo na área de entrada
btn_abrir = tk.Button(frame_entrada, text="Abrir Arquivo", command=carregar_arquivo)
btn_abrir.grid(row=1, column=0, sticky="e", padx=5, pady=2)

# Frame para botões de operações de texto
frame_botoes_texto = tk.Frame(aba_texto)
frame_botoes_texto.grid(row=1, column=0, sticky="ew", pady=5)
frame_botoes_texto.columnconfigure(0, weight=1)
frame_botoes_texto.columnconfigure(1, weight=1)
frame_botoes_texto.columnconfigure(2, weight=1)
frame_botoes_texto.columnconfigure(3, weight=1)

# Botões responsivos, usando grid para organização
btn_criptografar = tk.Button(frame_botoes_texto, text="Criptografar", command=criptografar, padx=5)
btn_criptografar.grid(row=0, column=0, sticky="ew", padx=2)

btn_descriptografar = tk.Button(frame_botoes_texto, text="Descriptografar", command=descriptografar, padx=5)
btn_descriptografar.grid(row=0, column=1, sticky="ew", padx=2)

btn_limpar = tk.Button(frame_botoes_texto, text="Limpar", command=limpar_texto, bg="lightgray", padx=5)
btn_limpar.grid(row=0, column=2, sticky="ew", padx=2)

btn_salvar = tk.Button(frame_botoes_texto, text="Salvar", command=salvar_arquivo, padx=5)
btn_salvar.grid(row=0, column=3, sticky="ew", padx=2)

# Frame para área de saída de texto
frame_saida = tk.LabelFrame(aba_texto, text="Resultado", font=("Arial", 10))
frame_saida.grid(row=2, column=0, sticky="nsew", pady=5)
frame_saida.columnconfigure(0, weight=1)
frame_saida.rowconfigure(0, weight=1)

# Área de saída com ScrolledText
saida_texto = scrolledtext.ScrolledText(frame_saida, height=8)
saida_texto.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Conteúdo da Aba 2: Criptografia de Arquivos
frame_operacoes_arquivo = tk.LabelFrame(aba_arquivos, text="Operações com Arquivos", font=("Arial", 10))
frame_operacoes_arquivo.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
frame_operacoes_arquivo.columnconfigure(0, weight=1)

# Adicionar explicação
info_label = tk.Label(frame_operacoes_arquivo,
                      text="Selecione as operações de criptografia ou descriptografia para seus arquivos.",
                      wraplength=500, justify="center", pady=10)
info_label.grid(row=0, column=0, sticky="ew")

# Frame para botões de criptografia de arquivos
frame_btns_arquivos = tk.Frame(frame_operacoes_arquivo)
frame_btns_arquivos.grid(row=1, column=0, sticky="nsew", pady=10)
frame_btns_arquivos.columnconfigure(0, weight=1)
frame_btns_arquivos.columnconfigure(1, weight=1)

# Botões grandes e mais espaçados para operações com arquivos
btn_cripto_arq = tk.Button(frame_btns_arquivos, text="Criptografar Arquivo",
                           command=criptografar_arquivo, padx=20, pady=10, font=("Arial", 11))
btn_cripto_arq.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

btn_descripto_arq = tk.Button(frame_btns_arquivos, text="Descriptografar Arquivo",
                              command=descriptografar_arquivo, padx=20, pady=10, font=("Arial", 11))
btn_descripto_arq.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

btn_cripto_pasta = tk.Button(frame_btns_arquivos, text="Criptografar Pasta",
                             command=criptografar_pasta, padx=20, pady=10, font=("Arial", 11))
btn_cripto_pasta.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

btn_descripto_pasta = tk.Button(frame_btns_arquivos, text="Descriptografar Pasta",
                                command=descriptografar_pasta, padx=20, pady=10, font=("Arial", 11))
btn_descripto_pasta.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

# Frame para informações adicionais
frame_info = tk.LabelFrame(frame_operacoes_arquivo, text="Informações Importantes", font=("Arial", 10))
frame_info.grid(row=2, column=0, sticky="ew", pady=10, padx=5)
frame_info.columnconfigure(0, weight=1)

info_texto = tk.Label(frame_info,
                      text="Os arquivos serão substituídos pela sua versão criptografada/descriptografada.\n"
                           "Certifique-se de ter um backup antes de prosseguir.\n",
                      wraplength=500, justify="left", pady=10)
info_texto.grid(row=0, column=0, sticky="w", padx=10)

# Frame para gerenciamento de chave
frame_chave = tk.LabelFrame(frame_operacoes_arquivo, text="Gerenciamento de Chave", font=("Arial", 10))
frame_chave.grid(row=3, column=0, sticky="ew", pady=10, padx=5)
frame_chave.columnconfigure(0, weight=1)

btn_gerar_chave = tk.Button(frame_chave, text="Gerar Nova Chave",
                            command=gerar_chave(), padx=20, pady=5, font=("Arial", 10))
btn_gerar_chave.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

# Frame para histórico de operações com arquivos
frame_historico = tk.LabelFrame(frame_operacoes_arquivo, text="Histórico de Operações", font=("Arial", 10))
frame_historico.grid(row=4, column=0, sticky="ew", pady=5, padx=5)
frame_historico.columnconfigure(0, weight=1)
frame_historico.rowconfigure(0, weight=1)

# Criando um canvas com scrollbar para o histórico
canvas_historico = tk.Canvas(frame_historico, height=5)
canvas_historico.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

scrollbar = tk.Scrollbar(frame_historico, orient="vertical", command=canvas_historico.yview)
scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)

canvas_historico.configure(yscrollcommand=scrollbar.set)

# Frame interno para o conteúdo do histórico
frame_historico_arquivos = tk.Frame(canvas_historico)
canvas_window = canvas_historico.create_window((0, 0), window=frame_historico_arquivos, anchor="nw")

# Função para atualizar o scrollregion quando o frame interno mudar de tamanho
def configurar_scrollregion(event):
    # Atualiza a região de rolagem para refletir o tamanho real do frame interno
    canvas_historico.configure(scrollregion=canvas_historico.bbox("all"))

    # Ajusta a largura do frame interno para preencher o canvas
    canvas_historico.itemconfig(canvas_window, width=canvas_historico.winfo_width())

# Vincular eventos para atualizar a scrollregion
frame_historico_arquivos.bind("<Configure>", configurar_scrollregion)
canvas_historico.bind("<Configure>",
                      lambda e: canvas_historico.itemconfig(canvas_window, width=canvas_historico.winfo_width()))

# Adicionar bindings para a roda do mouse
def _on_mousewheel(event):
    canvas_historico.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas_historico.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/MacOS
canvas_historico.bind_all("<Button-4>", lambda e: canvas_historico.yview_scroll(-1, "units"))  # Linux
canvas_historico.bind_all("<Button-5>", lambda e: canvas_historico.yview_scroll(1, "units"))  # Linux

# Botão para limpar histórico
btn_limpar_historico = tk.Button(frame_historico, text="Limpar Histórico", command=limpar_historico)
btn_limpar_historico.grid(row=1, column=0, sticky="e", padx=5, pady=5)

# Função de exemplo para adicionar itens ao histórico
def adicionar_item_historico(texto):
    label = tk.Label(frame_historico_arquivos, text=texto, anchor="w", justify="left")
    label.pack(fill="x", padx=5, pady=2)
    # Força a atualização do canvas e da scrollregion
    frame_historico_arquivos.update_idletasks()
    canvas_historico.configure(scrollregion=canvas_historico.bbox("all"))
    # Role para mostrar o item mais recente
    canvas_historico.yview_moveto(1.0)

# Conteúdo da Aba 3: Estatísticas
frame_estatisticas_dados = tk.LabelFrame(aba_estatisticas, text="Estatísticas de Uso", font=("Arial", 10))
frame_estatisticas_dados.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
frame_estatisticas_dados.columnconfigure(0, weight=1)
frame_estatisticas_dados.rowconfigure(0, weight=0)  # Título não precisa expandir
frame_estatisticas_dados.rowconfigure(1, weight=1)  # Gráfico expande
frame_estatisticas_dados.rowconfigure(2, weight=0)  # Controles não expandem
frame_estatisticas_dados.rowconfigure(3, weight=0)  # Detalhes expandem

# Adicionar explicação
titulo_estatisticas = tk.Label(frame_estatisticas_dados,
                               text="Estatísticas de uso do sistema de criptografia",
                               wraplength=500, justify="center", pady=10, font=("Arial", 11, "bold"))
titulo_estatisticas.grid(row=0, column=0, sticky="ew")

# Frame para o gráfico
frame_graficos = tk.Frame(frame_estatisticas_dados, bd=1, relief=tk.SUNKEN)
frame_graficos.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

# Frame para controles do gráfico
frame_controles_grafico = tk.Frame(frame_estatisticas_dados)
frame_controles_grafico.grid(row=2, column=0, sticky="ew", pady=5)
frame_controles_grafico.columnconfigure(0, weight=1)
frame_controles_grafico.columnconfigure(1, weight=1)
frame_controles_grafico.columnconfigure(2, weight=1)
frame_controles_grafico.columnconfigure(3, weight=1)
frame_controles_grafico.columnconfigure(4, weight=1)

# Período de análise
lbl_periodo = tk.Label(frame_controles_grafico, text="Período:", padx=5)
lbl_periodo.grid(row=0, column=0, sticky="e")

combo_periodo = ttk.Combobox(frame_controles_grafico,
                             values=["Última semana", "Último mês", "Último ano", "Todo o período"],
                             width=15)
combo_periodo.grid(row=0, column=1, sticky="w", padx=5)
combo_periodo.current(1)  # Seleciona "Último mês" por padrão

# Botão para atualizar estatísticas
btn_atualizar_stats = tk.Button(frame_controles_grafico, text="Atualizar Estatísticas",
                                command=lambda: atualizar_graficos())
btn_atualizar_stats.grid(row=0, column=2, sticky="w", padx=5)

# Botão para exportar estatísticas
btn_exportar_stats = tk.Button(frame_controles_grafico, text="Exportar Estatísticas",
                               command=lambda: exportar_estatisticas())
btn_exportar_stats.grid(row=0, column=3, sticky="w", padx=5)

# Botão para limpar dados
btn_limpar_dados = tk.Button(frame_controles_grafico, text="Limpar Dados",
                             command=lambda: limpar_dados_estatisticas())
btn_limpar_dados.grid(row=0, column=4, sticky="w", padx=5)

# Frame para detalhes estatísticos
frame_detalhes = tk.LabelFrame(frame_estatisticas_dados, text="Detalhes", font=("Arial", 10))
frame_detalhes.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
frame_detalhes.columnconfigure(0, weight=1)
frame_detalhes.rowconfigure(0, weight=1)

# Área de texto para detalhes
detalhes_texto = scrolledtext.ScrolledText(frame_detalhes, height=8)
detalhes_texto.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Função para atualizar a exibição de estatísticas
def atualizar_estatisticas():
    # Limpar área de estatísticas
    detalhes_texto.config(state="normal")
    detalhes_texto.delete(1.0, tk.END)

    # Converter bytes para unidades legíveis
    def bytes_para_legivel(tamanho_bytes):
        for unidade in ['B', 'KB', 'MB', 'GB']:
            if tamanho_bytes < 1024.0:
                return f"{tamanho_bytes:.2f} {unidade}"
            tamanho_bytes /= 1024.0
        return f"{tamanho_bytes:.2f} TB"

    # Inserir cabeçalho
    detalhes_texto.insert(tk.END, "Resumo Estatístico:\n\n")

    # Inserir estatísticas
    detalhes_texto.insert(tk.END, f"• Arquivos criptografados: {estatisticas.arquivos_criptografados}\n")
    detalhes_texto.insert(tk.END, f"• Arquivos descriptografados: {estatisticas.arquivos_descriptografados}\n")
    detalhes_texto.insert(tk.END,
                          f"• Volume total criptografado: {bytes_para_legivel(estatisticas.tamanho_total_criptografado)}\n")
    detalhes_texto.insert(tk.END,
                          f"• Volume total descriptografado: {bytes_para_legivel(estatisticas.tamanho_total_descriptografado)}\n\n")

    # Adicionar informações sobre tipos de arquivos
    detalhes_texto.insert(tk.END, "Tipos de arquivos processados:\n")
    for ext, dados in estatisticas.tipos_arquivos.items():
        total = dados['cripto'] + dados['descripto']
        if total > 0:
            detalhes_texto.insert(tk.END,
                                  f"• {ext}: {total} arquivos ({dados['cripto']} criptografados, {dados['descripto']} descriptografados)\n")

    # Configurar como somente leitura
    detalhes_texto.config(state="disabled")

    # Atualizar gráficos
    atualizar_graficos()

def atualizar_graficos():
    # Limpar área de gráficos
    for widget in frame_graficos.winfo_children():
        widget.destroy()

    # Definir estilo visual moderno
    plt.style.use('ggplot')

    # Configurar cores atraentes
    cores_principal = ['#3498db', '#2ecc71']  # Azul e verde mais vibrantes
    cor_fundo = '#f5f5f5'  # Fundo cinza claro
    cor_texto = '#333333'  # Texto cinza escuro

    # Criar figura principal com tamanho ajustado e layout otimizado
    fig = plt.Figure(figsize=(12, 8), dpi=90, facecolor=cor_fundo, tight_layout=True)

    # Criar GridSpec para melhor controle sobre o posicionamento dos subplots
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1],
                          left=0.05, right=0.95, bottom=0.1, top=0.9,
                          wspace=0.2, hspace=0.3)

    # Gráfico 1: Comparação entre arquivos criptografados e descriptografados
    ax1 = fig.add_subplot(gs[0, 0])
    labels = ['Criptografados', 'Descriptografados']
    valores = [estatisticas.arquivos_criptografados, estatisticas.arquivos_descriptografados]
    total = sum(valores)

    if total > 0:
        wedges, texts, autotexts = ax1.pie(
            valores,
            labels=labels,
            autopct='%1.1f%%',
            colors=cores_principal,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1},
            textprops={'color': cor_texto, 'fontsize': 7}
        )
        # Melhorar visibilidade dos textos
        for text in texts:
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontweight('bold')

        ax1.set_title('Arquivos Processados', fontweight='bold', fontsize=9, pad=5)
        # Adicionar total no centro
        ax1.text(0, 0, f'Total:\n{total}', ha='center', va='center', fontsize=8, fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'Sem dados', ha='center', va='center', fontsize=8)

    ax1.set_aspect('equal')  # Manter o círculo redondo

    # Gráfico 2: Operações por tipo de arquivo
    ax2 = fig.add_subplot(gs[0, 1])
    extensoes = list(estatisticas.tipos_arquivos.keys())
    cripto = [estatisticas.tipos_arquivos[ext]['cripto'] for ext in extensoes]
    descripto = [estatisticas.tipos_arquivos[ext]['descripto'] for ext in extensoes]

    # Limitar a 3 tipos mais comuns para melhor visualização
    if len(extensoes) > 3:
        # Ordenar por quantidade total
        totais = [(ext, estatisticas.tipos_arquivos[ext]['cripto'] + estatisticas.tipos_arquivos[ext]['descripto'])
                  for ext in extensoes]
        totais.sort(key=lambda x: x[1], reverse=True)

        # Pegar os 3 mais comuns
        top_exts = [item[0] for item in totais[:3]]
        extensoes = top_exts
        cripto = [estatisticas.tipos_arquivos[ext]['cripto'] for ext in extensoes]
        descripto = [estatisticas.tipos_arquivos[ext]['descripto'] for ext in extensoes]

    # Garantir que há pelo menos um valor para plotar
    if extensoes:
        x = range(len(extensoes))
        largura = 0.3  # Barras mais estreitas

        # Adicionar borda às barras e usar cores mais vibrantes
        barra1 = ax2.bar([i - largura / 2 for i in x], cripto, largura, label='Cript.',
                         color=cores_principal[0], edgecolor='white', linewidth=0.5)
        barra2 = ax2.bar([i + largura / 2 for i in x], descripto, largura, label='Descrip.',
                         color=cores_principal[1], edgecolor='white', linewidth=0.5)

        # Adicionar valores no topo das barras com fonte menor
        for bar in barra1:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.1, str(int(height)),
                         ha='center', va='bottom', fontsize=6, fontweight='bold')

        for bar in barra2:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.1, str(int(height)),
                         ha='center', va='bottom', fontsize=6, fontweight='bold')

        ax2.set_xticks(x)
        ax2.set_xticklabels([f'.{ext}' if not ext.startswith('.') else ext for ext in extensoes],
                            rotation=30, ha='right', fontsize=7)
        ax2.set_title('Por Tipo de Arquivo', fontweight='bold', fontsize=9, pad=5)
        ax2.legend(framealpha=0.8, fontsize=7, loc='upper right')
        # Remover linhas de grade horizontais para melhor estética
        ax2.grid(axis='x', visible=False)
        # Ajustar tamanho dos ticks
        ax2.tick_params(axis='y', labelsize=6)
    else:
        ax2.text(0.5, 0.5, 'Sem dados', ha='center', va='center', fontsize=8)

    # Gráfico 3: Operações por dia - Usando espaço inferior
    ax3 = fig.add_subplot(gs[1, :])  # Span across both columns

    # Obter últimos 4 dias
    dias = list(estatisticas.operacoes_por_dia.keys())
    dias.sort()  # Ordenar por data

    if len(dias) > 4:
        dias = dias[-4:]  # Últimos 4 dias

    cripto_por_dia = [estatisticas.operacoes_por_dia[dia]['cripto'] for dia in dias]
    descripto_por_dia = [estatisticas.operacoes_por_dia[dia]['descripto'] for dia in dias]

    # Formatação das datas para o gráfico
    dias_formatados = [dia.split('-')[2] + '/' + dia.split('-')[1] for dia in dias]  # Formato DD/MM

    # Garantir que há pelo menos um dia para plotar
    if dias:
        # Usar gráfico de linha para melhor visualização da tendência
        ax3.plot(dias_formatados, cripto_por_dia, 'o-', color=cores_principal[0], linewidth=1.5,
                 label='Criptografados', markersize=5)
        ax3.plot(dias_formatados, descripto_por_dia, 'o-', color=cores_principal[1], linewidth=1.5,
                 label='Descriptografados', markersize=5)

        # Preencher área sob a linha com menos opacidade
        ax3.fill_between(dias_formatados, cripto_por_dia, alpha=0.15, color=cores_principal[0])
        ax3.fill_between(dias_formatados, descripto_por_dia, alpha=0.15, color=cores_principal[1])

        # Adicionar valores nos pontos - fonte menor
        for i, v in enumerate(cripto_por_dia):
            if v > 0:
                ax3.text(i, v + 0.3, str(v), ha='center', fontsize=6, fontweight='bold')

        for i, v in enumerate(descripto_por_dia):
            if v > 0:
                ax3.text(i, v + 0.3, str(v), ha='center', fontsize=6, fontweight='bold')

        ax3.set_title('Operações por Dia', fontweight='bold', fontsize=9, pad=5)
        ax3.legend(loc='upper left', framealpha=0.8, fontsize=7)

        # Adicionar linhas de grade para facilitar a leitura
        ax3.grid(True, linestyle='--', alpha=0.3)  # Grade mais sutil

        # Melhorar aparência dos eixos
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)

        # Adicionar rótulos nos eixos
        ax3.set_xlabel('Data (DD/MM)', fontsize=7, labelpad=5)
        ax3.set_ylabel('Quantidade', fontsize=7, labelpad=5)
        ax3.tick_params(axis='both', labelsize=6)  # Ticks menores

        # Aumentar espaço para valores, mas com menor margem
        y_max = max(max(cripto_por_dia), max(descripto_por_dia)) if cripto_por_dia and descripto_por_dia else 0
        ax3.set_ylim(0, y_max * 1.1)  # Menos espaço extra no topo
    else:
        ax3.text(0.5, 0.5, 'Sem dados', ha='center', va='center', fontsize=8)

    # Ajuste final para eliminar espaços em branco
    fig.tight_layout(pad=1.0)

    # Criação do canvas do Matplotlib dentro do frame_graficos diretamente
    figure_canvas = FigureCanvasTkAgg(fig, master=frame_graficos)
    figure_canvas.draw()
    figure_widget = figure_canvas.get_tk_widget()
    figure_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Barra de ferramentas simples para navegação básica
    toolbar_frame = tk.Frame(frame_graficos, bd=1, relief=tk.RAISED)
    toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
    toolbar = NavigationToolbar2Tk(figure_canvas, toolbar_frame)
    toolbar.update()

    # Função para ajustar automaticamente o gráfico quando o frame for redimensionado
    def on_resize(event):
        # Obter as dimensões atuais do frame
        width = event.width
        height = event.height

        # Calcular novas dimensões para a figura, mantendo proporção mas com tamanho reduzido
        new_width = min(width / 100, 7)  # Converter pixels para polegadas
        new_height = min(height / 100, 4.2)  # Converter pixels para polegadas

        # Atualizar o tamanho da figura
        fig.set_size_inches(new_width, new_height)
        fig.tight_layout(pad=1.0)  # Reajustar o layout interno
        figure_canvas.draw_idle()  # Redesenhar o canvas

    # Associar a função de redimensionamento ao evento de redimensionamento do widget
    frame_graficos.bind('<Configure>', on_resize)

# Função para exportar as estatísticas para um arquivo
def exportar_estatisticas():
    arquivo = filedialog.asksaveasfilename(
        title="Exportar Estatísticas",
        defaultextension=".txt",
        filetypes=(("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*"))
    )

    if not arquivo:
        return

    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            # Cabeçalho
            f.write("RELATÓRIO DE ESTATÍSTICAS DE USO\n")
            f.write("==============================\n\n")


            f.write(f"Data do relatório: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Estatísticas gerais
            f.write("ESTATÍSTICAS GERAIS\n")
            f.write("-----------------\n")
            f.write(f"Arquivos criptografados: {estatisticas.arquivos_criptografados}\n")
            f.write(f"Arquivos descriptografados: {estatisticas.arquivos_descriptografados}\n")

            # Função auxiliar para formatar tamanhos
            def bytes_para_legivel(tamanho_bytes):
                for unidade in ['B', 'KB', 'MB', 'GB']:
                    if tamanho_bytes < 1024.0:
                        return f"{tamanho_bytes:.2f} {unidade}"
                    tamanho_bytes /= 1024.0
                return f"{tamanho_bytes:.2f} TB"

            f.write(f"Volume total criptografado: {bytes_para_legivel(estatisticas.tamanho_total_criptografado)}\n")
            f.write(
                f"Volume total descriptografado: {bytes_para_legivel(estatisticas.tamanho_total_descriptografado)}\n\n")

            # Estatísticas por tipo de arquivo
            f.write("ESTATÍSTICAS POR TIPO DE ARQUIVO\n")
            f.write("------------------------------\n")
            for ext, dados in estatisticas.tipos_arquivos.items():
                f.write(f"Extensão {ext}:\n")
                f.write(f"  - Arquivos criptografados: {dados['cripto']}\n")
                f.write(f"  - Arquivos descriptografados: {dados['descripto']}\n")
            f.write("\n")

            # Estatísticas por dia
            f.write("ESTATÍSTICAS POR DIA\n")
            f.write("-------------------\n")
            dias = list(estatisticas.operacoes_por_dia.keys())
            dias.sort()
            for dia in dias:
                dados = estatisticas.operacoes_por_dia[dia]
                f.write(f"Data {dia}:\n")
                f.write(f"  - Arquivos criptografados: {dados['cripto']}\n")
                f.write(f"  - Arquivos descriptografados: {dados['descripto']}\n")

            messagebox.showinfo("Sucesso", "Estatísticas exportadas com sucesso!")

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível exportar as estatísticas: {e}")

# Inicializar a visualização de estatísticas
atualizar_estatisticas()

# Criar menu
menu_principal = tk.Menu(janela)
janela.config(menu=menu_principal)

# Menu Arquivo
menu_arquivo = tk.Menu(menu_principal, tearoff=0)
menu_principal.add_cascade(label="Arquivo", menu=menu_arquivo)
menu_arquivo.add_command(label="Abrir Arquivo", command=carregar_arquivo)
menu_arquivo.add_command(label="Salvar Resultado", command=salvar_arquivo)
menu_arquivo.add_separator()
menu_arquivo.add_command(label="Sair", command=janela.quit)

# Menu Operações
menu_operacoes = tk.Menu(menu_principal, tearoff=0)
menu_principal.add_cascade(label="Operações", menu=menu_operacoes)
menu_operacoes.add_command(label="Criptografar Texto", command=criptografar)
menu_operacoes.add_command(label="Descriptografar Texto", command=descriptografar)
menu_operacoes.add_separator()
menu_operacoes.add_command(label="Criptografar Arquivo", command=criptografar_arquivo)
menu_operacoes.add_command(label="Descriptografar Arquivo", command=descriptografar_arquivo)
menu_operacoes.add_separator()
menu_operacoes.add_command(label="Gerar Nova Chave", command=gerar_chave())
menu_operacoes.add_separator()
menu_operacoes.add_command(label="Criptografar Pasta", command=criptografar_pasta)
menu_operacoes.add_command(label="Descriptografar Pasta", command=descriptografar_pasta)

# Menu Estatísticas (novo)
menu_estatisticas = tk.Menu(menu_principal, tearoff=0)
menu_principal.add_cascade(label="Estatísticas", menu=menu_estatisticas)
menu_estatisticas.add_command(label="Ver Estatísticas", command=lambda: notebook.select(aba_estatisticas))
menu_estatisticas.add_command(label="Exportar Relatório", command=lambda: messagebox.showinfo("Exportar",
                                                                                              "Funcionalidade de exportação será implementada em breve."))
menu_estatisticas.add_command(label="Limpar Dados", command=lambda: messagebox.askokcancel("Confirmar",
                                                                                           "Deseja realmente limpar todos os dados estatísticos?"))

# Menu Ajuda com ícones e submenu aprimorado
menu_ajuda = tk.Menu(menu_principal, tearoff=0)
menu_principal.add_cascade(label="Ajuda", menu=menu_ajuda)
menu_ajuda.add_command(label="Conteúdo da Ajuda", command=lambda: mostrar_ajuda(), accelerator="F1")
menu_ajuda.add_command(label="Dicas Rápidas", command=lambda: mostrar_dicas(), accelerator="F2")
menu_ajuda.add_command(label="Relatório de Bugs", command=lambda: reportar_bug(), accelerator="F3")
menu_ajuda.add_command(label="Verificar Atualizações", command=lambda: verificar_atualizacoes(), accelerator="F4")
menu_ajuda.add_separator()
menu_ajuda.add_command(label="Sobre", command=lambda: mostrar_sobre(), accelerator="F5")

# Funções para os itens do menu Ajuda
def mostrar_ajuda():
    ajuda = tk.Toplevel(janela)
    ajuda.title("Ajuda - Sistema de Criptografia")
    ajuda.geometry("600x500")
    ajuda.minsize(500, 400)
    ajuda.transient(janela)  # Define a janela principal como parent
    ajuda.grab_set()  # Torna a janela modal

    # Configurações de estilo
    estilo = ttk.Style()
    estilo.configure("Ajuda.TFrame", background="#f0f4f8")
    estilo.configure("Titulo.TLabel", font=("Arial", 14, "bold"), foreground="black")
    estilo.configure("Subtitulo.TLabel", font=("Arial", 12, "bold"), foreground="black")
    estilo.configure("Texto.TLabel", font=("Arial", 10), foreground="black")

    # Frame principal com padding
    frame_principal = ttk.Frame(ajuda, padding=10, style="Ajuda.TFrame")
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título principal
    titulo_frame = ttk.Frame(frame_principal, style="Ajuda.TFrame")
    titulo_frame.pack(fill=tk.X, pady=(0, 10))
    ttk.Label(titulo_frame, text="Sistema de Criptografia - Manual de Ajuda",
              style="Titulo.TLabel").pack(side=tk.LEFT)

    # Criar notebook para organizar a ajuda em abas
    notebook = ttk.Notebook(frame_principal)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Função para formatar o conteúdo de cada aba
    def criar_aba(parent, titulo, conteudo):
        tab = ttk.Frame(parent, style="Ajuda.TFrame")
        notebook.add(tab, text=titulo)

        # Container com scroll
        container = ttk.Frame(tab, style="Ajuda.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        conteudo_frame = ttk.Frame(canvas, style="Ajuda.TFrame")

        conteudo_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=conteudo_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill=tk.BOTH, expand=True)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Formatação do conteúdo
        for secao in conteudo:
            secao_frame = ttk.Frame(conteudo_frame, style="Ajuda.TFrame")
            secao_frame.pack(fill=tk.X, pady=10, padx=5)

            # Título da seção
            titulo_secao = ttk.Label(secao_frame, text=secao["titulo"], style="Subtitulo.TLabel")
            titulo_secao.pack(anchor=tk.W, pady=(0, 5))

            # Separador
            ttk.Separator(secao_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)

            # Descrição
            if "descricao" in secao:
                desc_frame = ttk.Frame(secao_frame, style="Ajuda.TFrame")
                desc_frame.pack(fill=tk.X, padx=10, pady=5)
                desc_label = ttk.Label(desc_frame, text=secao["descricao"],
                                       wraplength=500, justify=tk.LEFT, style="Texto.TLabel")
                desc_label.pack(anchor=tk.W)

            # Lista de itens
            if "itens" in secao:
                itens_frame = ttk.Frame(secao_frame, style="Ajuda.TFrame")
                itens_frame.pack(fill=tk.X, padx=15, pady=5)

                for item in secao["itens"]:
                    item_frame = ttk.Frame(itens_frame, style="Ajuda.TFrame")
                    item_frame.pack(fill=tk.X, pady=3)

                    bullet = ttk.Label(item_frame, text="•", font=("Arial", 12, "bold"),
                                       foreground="#3498db", style="Texto.TLabel")
                    bullet.pack(side=tk.LEFT, padx=(0, 5))

                    if isinstance(item, dict):
                        # Item com título e descrição
                        item_container = ttk.Frame(item_frame, style="Ajuda.TFrame")
                        item_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

                        item_titulo = ttk.Label(item_container, text=item["titulo"],
                                                font=("Arial", 10, "bold"), foreground="black")
                        item_titulo.pack(anchor=tk.W)

                        item_desc = ttk.Label(item_container, text=item["descricao"],
                                              wraplength=460, justify=tk.LEFT, style="Texto.TLabel")
                        item_desc.pack(anchor=tk.W, padx=10)
                    else:
                        # Item simples
                        item_text = ttk.Label(item_frame, text=item, wraplength=480,
                                              justify=tk.LEFT, style="Texto.TLabel")
                        item_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Tabela (para atalhos)
            if "tabela" in secao:
                tabela_frame = ttk.Frame(secao_frame, style="Ajuda.TFrame")
                tabela_frame.pack(fill=tk.X, padx=10, pady=5)

                # Cabeçalho
                header_frame = ttk.Frame(tabela_frame, style="Ajuda.TFrame")
                header_frame.pack(fill=tk.X, pady=2)

                col1 = ttk.Label(header_frame, text=secao["tabela"]["colunas"][0],
                                 width=15, font=("Arial", 10, "bold"), foreground="#2c3e50")
                col1.pack(side=tk.LEFT, padx=5, pady=2)

                col2 = ttk.Label(header_frame, text=secao["tabela"]["colunas"][1],
                                 font=("Arial", 10, "bold"), foreground="#2c3e50")
                col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

                # Separador
                ttk.Separator(tabela_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

                # Linhas
                for linha in secao["tabela"]["linhas"]:
                    linha_frame = ttk.Frame(tabela_frame, style="Ajuda.TFrame")
                    linha_frame.pack(fill=tk.X, pady=1)

                    val1 = ttk.Label(linha_frame, text=linha[0], width=15,
                                     font=("Arial", 10, "bold"), foreground="black")
                    val1.pack(side=tk.LEFT, padx=5, pady=2)

                    val2 = ttk.Label(linha_frame, text=linha[1], style="Texto.TLabel")
                    val2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

                    ttk.Separator(tabela_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)

        return tab

    # Conteúdo para a aba de Introdução
    conteudo_intro = [
        {
            "titulo": "Sistema de Criptografia",
            "descricao": "Bem-vindo ao Sistema de Criptografia CONATUS Technologies, uma ferramenta projetada para proteger seus dados pessoais e arquivos importantes.",
        },
        {
            "titulo": "O que é criptografia?",
            "descricao": "A criptografia é uma técnica essencial para garantir a segurança da informação, protegendo dados contra acessos não autorizados. Ela funciona através da codificação de mensagens, tornando-as ilegíveis para qualquer pessoa que não possua a chave correta para decifrá-las. Nós utilizamos o AES-128 (Advanced Encryption Standard, chave de 128 bits), um dos algoritmos de criptografia mais seguros e amplamente utilizados no mundo. Ele foi padronizado pelo NIST (National Institute of Standards and Technology) e é usado em diversas aplicações, incluindo comunicações seguras, proteção de dados em dispositivos móveis e armazenamento de informações confidenciais em empresas privadas e governamentais. O AES-128 utiliza uma chave de 128 bits, o que significa que existem 340.282.366.920.938.463.463.374.607.431.768.211.456 (ou 340 undecilhões) combinações possíveis para uma chave. Esse espaço é extremamente grande, tornando a força bruta ou outris tipos de cyber-ataques inviáveis com a tecnologia atual e previsível para as próximas décadas.",
        },
        {
            "titulo": "Como começar",
            "descricao": "Navegue pelas abas deste manual para aprender sobre as principais funcionalidades do sistema. Para uma introdução rápida, consulte a seção \"Dicas Rápidas\" no menu Ajuda.",
        }
    ]

    # Conteúdo para a aba de Criptografia de Texto
    conteudo_texto = [
        {
            "titulo": "Criptografia de Texto",
            "descricao": "Na aba \"Criptografia de Texto\", você pode proteger qualquer texto usando nosso algoritmo de criptografia.",
        },
        {
            "titulo": "Operações Disponíveis",
            "itens": [
                {"titulo": "Inserir Texto",
                 "descricao": "Digite diretamente na área de texto ou use o botão \"Carregar\" para importar texto de um arquivo."},
                {"titulo": "Criptografar", "descricao": "Converte seu texto em uma versão criptografada."},
                {"titulo": "Descriptografar",
                 "descricao": "Recupera o texto original a partir da versão criptografada."},
                {"titulo": "Limpar", "descricao": "Remove todo o conteúdo da área de texto."},
                {"titulo": "Salvar", "descricao": "Exporta o resultado para um arquivo de texto."}
            ]
        },
        {
            "titulo": "Dicas",
            "itens": [
                "Para criptografar senhas ou informações sensíveis, tenha backups.",
                "Uma mensagem criptografada aparecerá como uma sequência de caracteres aparentemente aleatórios.",
                "Sempre descriptografe o seu conteúdo antes de gerar uma nova chave, uma vez que uma nova for gerada não será possível descriptografar o conteúdo anterior.",
                "Troque a chave constante para aumentar a segurança e integridade de seus arquivos"
            ]
        }
    ]

    # Conteúdo para a aba de Criptografia de Arquivos
    conteudo_arquivos = [
        {
            "titulo": "Criptografia de Arquivos",
            "descricao": "Na aba \"Criptografia de Arquivos\", você pode proteger arquivos individuais ou pastas inteiras.",
        },
        {
            "titulo": "Operações Disponíveis",
            "itens": [
                {"titulo": "Criptografar Arquivo", "descricao": "Selecione e criptografe um arquivo individual."},
                {"titulo": "Descriptografar Arquivo",
                 "descricao": "Recupere o conteúdo original de um arquivo criptografado."},
                {"titulo": "Criptografar Pasta",
                 "descricao": "Criptografe todos os arquivos dentro de uma pasta selecionada."},
                {"titulo": "Descriptografar Pasta",
                 "descricao": "Recupere todos os arquivos criptografados de uma pasta."},
                {"titulo": "Gerar Nova Chave",
                 "descricao": "Crie uma nova chave de criptografia para aumentar a segurança."}
            ]
        },
        {
            "titulo": "Formatos Suportados",
            "descricao": "O sistema suporta a criptografia de praticamente qualquer tipo de arquivo, incluindo:",
            "itens": [
                "Documentos (.doc, .docx, .pdf, .txt)",
                "Imagens (.jpg, .png, .gif)",
                "Arquivos compactados (.zip, .rar)",
                "E muitos outros"
            ]
        },
        {
            "titulo": "Considerações Importantes",
            "itens": [
                "Os arquivos criptografados manterá a mesma extensão e aparência, tornando-o indistínguel do arquivo original",
                "Mantenha sempre um backup dos seus arquivos originais antes de criptografá-los.",
                "Sempre descriptografe o seu conteúdo antes de gerar uma nova chave, uma vez que uma nova for gerada não será possível descriptografar o conteúdo anterior.",
                "A criptografia de arquivos grandes pode levar alguns minutos."
            ]
        }
    ]

    # Conteúdo para a aba de Estatísticas
    conteudo_stats = [
        {
            "titulo": "Estatísticas de Uso",
            "descricao": "A aba \"Estatísticas\" permite monitorar o uso do sistema e analisar padrões de criptografia.",
        },
        {
            "titulo": "Funcionalidades",
            "itens": [
                {"titulo": "Visualização de Dados",
                 "descricao": "Veja estatísticas sobre o número de arquivos criptografados/descriptografados."},
                {"titulo": "Filtros por Período",
                 "descricao": "Selecione diferentes intervalos de tempo para análise (diário, semanal, mensal)."},
                {"titulo": "Exportação", "descricao": "Salve relatórios de estatísticas em formato de texto ou CSV."},
                {"titulo": "Limpeza de Dados", "descricao": "Reinicie as estatísticas quando necessário."}
            ]
        },
        {
            "titulo": "Benefícios",
            "itens": [
                "Acompanhe o volume de dados processados pelo sistema.",
                "Identifique picos de uso e padrões de utilização.",
                "Mantenha um registro das suas atividades de criptografia."
            ]
        }
    ]

    # Conteúdo para a aba de Atalhos de Teclado
    conteudo_atalhos = [
        {
            "titulo": "Atalhos de Teclado",
            "descricao": "Utilize estes atalhos para navegar e operar o sistema com maior eficiência:",
            "tabela": {
                "colunas": ["Atalho", "Função"],
                "linhas": [
                    ["F1", "Abrir o Manual de Ajuda"],
                    ["F2", "Mostrar Dicas Rápidas"],
                    ["F3", "Reportar Bug"],
                    ["F4", "Verificar Atualizações"],
                    ["F5", "Mostrar Sobre"],
                    ["F6", "Abrir Website"],
                ]
            }
        }
    ]

    # Criar as abas
    criar_aba(notebook, "Introdução", conteudo_intro)
    criar_aba(notebook, "Criptografia de Texto", conteudo_texto)
    criar_aba(notebook, "Criptografia de Arquivos", conteudo_arquivos)
    criar_aba(notebook, "Estatísticas", conteudo_stats)
    criar_aba(notebook, "Atalhos de Teclado", conteudo_atalhos)

    # Botão de fechar com estilo
    botoes_frame = ttk.Frame(ajuda, style="Ajuda.TFrame")
    botoes_frame.pack(fill=tk.X, pady=10)

    botao_fechar = ttk.Button(botoes_frame, text="Fechar", command=ajuda.destroy)
    botao_fechar.pack(side=tk.RIGHT, padx=10)

def mostrar_dicas():
    dicas = tk.Toplevel(janela)
    dicas.title("Dicas Rápidas")
    dicas.geometry("450x350")
    dicas.transient(janela)  # Define a janela principal como parent
    dicas.grab_set()  # Torna a janela modal

    # Estilo
    estilo = ttk.Style()
    estilo.configure("Dica.TFrame", background="#f0f4f8")

    # Frame principal com borda e padding
    frame_principal = ttk.Frame(dicas, padding=15)
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título
    titulo_frame = ttk.Frame(frame_principal)
    titulo_frame.pack(fill=tk.X, pady=(0, 15))

    tk.Label(titulo_frame, text="Dicas Rápidas",
             font=("Arial", 14, "bold"),
             fg="#2c3e50").pack(side=tk.LEFT)

    # Separador
    ttk.Separator(frame_principal, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

    # Frame de dicas com scroll
    container = ttk.Frame(frame_principal)
    container.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    frame_dicas = ttk.Frame(canvas, style="Dica.TFrame")

    frame_dicas.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=frame_dicas, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill=tk.BOTH, expand=True)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Lista de dicas com ícones indicativos
    dicas_lista = [
        ("Segurança", "Sempre faça backup dos seus arquivos antes de criptografá-los."),
        ("Segurança", "Sempre descriptografe o seu conteúdo antes de gerar uma nova chave, uma vez que uma nova for gerada não será possível descriptografar o conteúdo anterior."),
        ("Segurança", "As chaves ficam armazenadas na memória do programa até que uma nova seja gerada."),
        ("Importante", "Os arquivos criptografados só podem ser abertos com a mesma chave usada para criptografá-los."),
        ("Importante", "O programa deve ser utilizado individualmente. Uma única pessoa deve ser responsável pela manutenção dos arquivos."),
        ("Prática", "Para melhor segurança, gere uma nova chave a cada três meses."),
        ("Prática", "Crie uma rotina regular de backup e criptografia para seus dados importantes."),
        ("Eficiência", "Use a função 'Criptografar Pasta' para processar múltiplos arquivos de uma vez."),
        ("Eficiência", "Organize arquivos em pastas por categoria antes de criptografá-los em lote."),
        ("Eficiência", "Confira os atalhos de Tecla."),
        ("Análise", "Confira as estatísticas para acompanhar o uso do sistema e identificar padrões."),
    ]

    # Cores para os diferentes tipos de dicas
    cores = {
        "Segurança": "#e74c3c",
        "Prática": "#3498db",
        "Importante": "#e67e22",
        "Eficiência": "#2ecc71",
        "Análise": "#9b59b6",
        "Atalho": "#34495e"
    }

    # Adicionar cada dica com ícone e formatação
    for idx, (tipo, dica) in enumerate(dicas_lista):
        frame_item = ttk.Frame(frame_dicas, style="Dica.TFrame")
        frame_item.pack(fill=tk.X, pady=5, padx=5, anchor="w")

        # Etiqueta de tipo
        tipo_label = tk.Label(frame_item, text=tipo, font=("Arial", 9, "bold"),
                              bg=cores[tipo], fg="white", width=9, padx=5, pady=2)
        tipo_label.pack(side=tk.LEFT, padx=(0, 10))

        # Texto da dica
        texto_dica = tk.Label(frame_item, text=dica, wraplength=300,
                              justify=tk.LEFT, anchor="w", pady=5)
        texto_dica.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Botões de navegação
    frame_botoes = ttk.Frame(dicas)
    frame_botoes.pack(fill=tk.X, pady=10)

    ttk.Button(frame_botoes, text="Ajuda Completa",
               command=lambda: [dicas.destroy(), mostrar_ajuda()]).pack(side=tk.LEFT, padx=10)

    ttk.Button(frame_botoes, text="Fechar",
               command=dicas.destroy).pack(side=tk.RIGHT, padx=10)

    # Vincular a tecla ESC para fechar a janela
    dicas.bind("<Escape>", lambda event: dicas.destroy())

def reportar_bug():
    bug = tk.Toplevel(janela)
    bug.title("Reportar um problema")
    bug.geometry("500x500")
    bug.transient(janela)
    bug.grab_set()

    # Frame principal
    frame_principal = ttk.Frame(bug, padding=15)
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título
    ttk.Label(frame_principal, text="Reportar um Problema",
              font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 15))

    # Formulário
    ttk.Label(frame_principal, text="Título do problema:").pack(anchor="w", pady=(10, 5))
    titulo_bug = ttk.Entry(frame_principal, width=50)
    titulo_bug.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(frame_principal, text="Descrição detalhada:").pack(anchor="w", pady=(5, 5))
    descricao_bug = scrolledtext.ScrolledText(frame_principal, height=8, wrap=tk.WORD)
    descricao_bug.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    ttk.Label(frame_principal, text="Passos para reproduzir:").pack(anchor="w", pady=(5, 5))
    passos_bug = scrolledtext.ScrolledText(frame_principal, height=5, wrap=tk.WORD)
    passos_bug.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Frame para os botões
    frame_botoes = ttk.Frame(frame_principal)
    frame_botoes.pack(fill=tk.X, pady=(10, 0))

    # Checkbox para anexar logs
    var_logs = tk.BooleanVar(value=True)
    check_logs = ttk.Checkbutton(frame_botoes, text="Anexar logs do sistema", variable=var_logs)
    check_logs.pack(side=tk.LEFT)

    # Botões
    ttk.Button(frame_botoes, text="Cancelar", command=bug.destroy).pack(side=tk.RIGHT, padx=5)
    ttk.Button(frame_botoes, text="Enviar Relatório",
               command=lambda: [tk.messagebox.showinfo("Relatório Enviado",
                                                       "Obrigado! Seu relatório foi enviado com sucesso."),
                                bug.destroy()]).pack(side=tk.RIGHT, padx=5)

def verificar_atualizacoes():
    # Simulação de verificação de atualização
    atualiza = tk.Toplevel(janela)
    atualiza.title("Verificação de Atualizações")
    atualiza.geometry("400x250")
    atualiza.transient(janela)
    atualiza.grab_set()

    # Frame principal
    frame = ttk.Frame(atualiza, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Conteúdo
    ttk.Label(frame, text="Verificando atualizações...",
              font=("Arial", 12, "bold")).pack(pady=(10, 20))

    # Barra de progresso
    progress = ttk.Progressbar(frame, orient="horizontal",
                               length=300, mode="determinate")
    progress.pack(fill=tk.X, pady=10)

    # Status
    status_label = ttk.Label(frame, text="Conectando ao servidor...")
    status_label.pack(pady=10)

    # Função para simular progresso
    def atualizar_progresso(count=0):
        progress["value"] = count
        if count < 100:
            status_label.config(text="Verificando componentes do sistema...")
            atualiza.after(50, lambda: atualizar_progresso(count + 5))
        else:
            status_label.config(text="Você já possui a versão mais recente (1.0.0)")
            ttk.Button(frame, text="Fechar",
                       command=atualiza.destroy).pack(pady=20)

    atualizar_progresso()

def mostrar_sobre():
    sobre = tk.Toplevel(janela)
    sobre.title("Sobre o Sistema de Criptografia")
    sobre.geometry("500x500")
    sobre.resizable(False, False)
    sobre.transient(janela)
    sobre.grab_set()

    # Frame principal com fundo gradiente
    frame_sobre = tk.Frame(sobre, bg="white")
    frame_sobre.pack(fill=tk.BOTH, expand=True)

    # Cabeçalho com gradiente
    header = tk.Frame(frame_sobre, height=100, bg="#2c3e50")
    header.pack(fill=tk.X)

    # Título e versão - agora centralizado
    info_frame = tk.Frame(header, bg="#2c3e50")
    info_frame.pack(side=tk.TOP, pady=15, fill=tk.X)

    tk.Label(info_frame, text="Sistema de Criptografia",
             font=("Arial", 16, "bold"), fg="white", bg="#2c3e50").pack(anchor="center")
    tk.Label(info_frame, text="Versão 1.0.0",
             fg="#bdc3c7", bg="#2c3e50").pack(anchor="center")

    # Separador
    separator = tk.Frame(frame_sobre, height=2, bg="#3498db")
    separator.pack(fill=tk.X, padx=20)

    # Conteúdo central
    content_frame = tk.Frame(frame_sobre, bg="white")
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Notebook para organizar informações
    notebook = ttk.Notebook(content_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Aba de Descrição
    tab_descricao = tk.Frame(notebook, bg="white")
    notebook.add(tab_descricao, text="Descrição")

    descricao_text = """O Sistema de Criptografia é uma aplicação de segurança projetada para proteger seus dados pessoais e arquivos contra acesso não autorizado.

Com uma interface amigável e recursos poderosos, o sistema permite criptografar textos e arquivos usando algoritmos avançados de segurança.

Desenvolvido pensando na facilidade de uso e na máxima proteção, este software é ideal para empresas e usuários individuais que valorizam a privacidade digital."""

    tk.Label(tab_descricao, text=descricao_text, wraplength=400,
             justify=tk.LEFT, bg="white", pady=10, padx=10).pack(fill=tk.BOTH)

    # Aba de Recursos
    tab_recursos = tk.Frame(notebook, bg="white")
    notebook.add(tab_recursos, text="Recursos")

    recursos_frame = tk.Frame(tab_recursos, bg="white")
    recursos_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    recursos = [
        "Criptografia AES-128 de alta segurança",
        "Interface gráfica intuitiva e amigável",
        "Processamento em lote de múltiplos arquivos",
        "Geração de chaves seguras",
        "Estatísticas detalhadas de uso",
        "Compatibilidade com vários formatos de arquivo",
        "Operação em modo offline para maior segurança"
    ]

    for recurso in recursos:
        frame_item = tk.Frame(recursos_frame, bg="white")
        frame_item.pack(fill=tk.X, pady=3, anchor="w")

        tk.Label(frame_item, text="✓", fg="#27ae60", bg="white",
                 font=("Arial", 10, "bold"), width=2).pack(side=tk.LEFT)
        tk.Label(frame_item, text=recurso, bg="white",
                 anchor="w").pack(side=tk.LEFT, fill=tk.X)

    # Aba de Créditos
    tab_creditos = tk.Frame(notebook, bg="white")
    notebook.add(tab_creditos, text="Créditos")

    # Função para abrir links quando clicados
    def abrir_link(url):
        webbrowser.open_new(url)

    # Resto do código para a aba de créditos
    tk.Label(tab_creditos, text="Desenvolvido por:", bg="white",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
    tk.Label(tab_creditos, text="CONATUS Technologies",
             bg="white", justify="left").pack(anchor="w", padx=20)

    # Criando links clicáveis
    linkedin_link = tk.Label(tab_creditos, text="LinkedIn: Lucas Monteiro",
                             bg="white", fg="blue", cursor="hand2")
    linkedin_link.pack(anchor="w", padx=20, pady=2)
    linkedin_link.bind("<Button-1>", lambda e: abrir_link("https://www.linkedin.com/in/lucas-monteiro-67649b233/"))

    github_link = tk.Label(tab_creditos, text="GitHub: Lucas-Monteiro420",
                           bg="white", fg="blue", cursor="hand2")
    github_link.pack(anchor="w", padx=20, pady=2)
    github_link.bind("<Button-1>", lambda e: abrir_link("https://github.com/Lucas-Monteiro420"))

    tk.Label(tab_creditos, text="Design:", bg="white",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
    tk.Label(tab_creditos, text="Departamento de UX/UI",
             bg="white").pack(anchor="w", padx=20)

    tk.Label(tab_creditos, text="Agradecimentos Especiais:", bg="white",
             font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
    tk.Label(tab_creditos,
             text="A todos os usuários e beta-testers que contribuíram\ncom feedback valioso para este projeto.",
             bg="white", justify=tk.LEFT).pack(anchor="w", padx=20)

    # Rodapé
    footer = tk.Frame(frame_sobre, height=50, bg="#2c3e50")
    footer.pack(fill=tk.X)

    tk.Label(footer, text="© 2025 - CONATUS Technologies - Todos os direitos reservados",
             fg="#bdc3c7", bg="#2c3e50").pack(side=tk.LEFT, padx=20, pady=15)

    # Botões de site e contato
    btn_frame = tk.Frame(footer, bg="#2c3e50")
    btn_frame.pack(side=tk.RIGHT, padx=20)

    ttk.Button(btn_frame, text="Website",
               command=lambda: abrir_website()).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Fechar",
               command=sobre.destroy).pack(side=tk.LEFT, padx=5)

def abrir_website():
    # Função para simular abertura do site
    tk.messagebox.showinfo("Website", "Redirecionando para o website...")

# Vincular teclas de atalho
janela.bind("<F1>", lambda event: mostrar_ajuda())
janela.bind("<F2>", lambda event: mostrar_dicas())
janela.bind("<F3>", lambda event: reportar_bug())
janela.bind("<F4>", lambda event: verificar_atualizacoes())
janela.bind("<F5>", lambda event: mostrar_sobre())
janela.bind("<F6>", lambda event: abrir_website())

# Barra de status
barra_status = tk.Label(janela, text="Pronto", bd=1, relief=tk.SUNKEN, anchor=tk.W)
barra_status.grid(row=1, column=0, sticky="ews")

# Adicionar uma primeira entrada ao histórico
adicionar_ao_historico("Sistema iniciado", "Aguardando operações")

# Função para ajustar o tamanho dos widgets quando a janela é redimensionada
def ao_redimensionar(event):
    # Atualizar a largura do frame interno no canvas
    canvas_width = canvas_historico.winfo_width()
    canvas_historico.itemconfig(canvas_historico.find_withtag("all")[0], width=canvas_width)

    # Atualizar a barra de status com informações do tamanho da janela
    barra_status.config(text=f"Tamanho da Janela: {janela.winfo_width()}x{janela.winfo_height()}")

# Vincular a função ao evento de redimensionamento da janela
janela.bind("<Configure>", ao_redimensionar)

# Inicializar a janela com um tamanho padrão
janela.geometry("600x600")

# Iniciando a janela
janela.mainloop()