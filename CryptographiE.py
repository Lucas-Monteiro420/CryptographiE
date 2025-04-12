import datetime
import os
import smtplib
import threading
import time
import tkinter as tk
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import matplotlib.pyplot as plt
import numpy as np
import winsound
from cryptography.fernet import Fernet
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy import signal
from scipy.io import wavfile
import serial
import serial.tools.list_ports


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
notebook.add(aba_estatisticas, text="Estatísticas de Criptografia")
aba_estatisticas.columnconfigure(0, weight=1)
aba_estatisticas.rowconfigure(0, weight=1)

# Aba 4: Código Morse
aba_morse = ttk.Frame(notebook)
notebook.add(aba_morse, text="Código Morse")

# Configure o aba_morse para preencher todo o espaço disponível
aba_morse.columnconfigure(0, weight=1)
aba_morse.rowconfigure(0, weight=1)

# Criar um canvas com scrollbar
canvas_morse = tk.Canvas(aba_morse)
canvas_morse.grid(row=0, column=0, sticky="nsew")

scrollbar_morse = ttk.Scrollbar(aba_morse, orient="vertical", command=canvas_morse.yview)
scrollbar_morse.grid(row=0, column=1, sticky="ns")

canvas_morse.configure(yscrollcommand=scrollbar_morse.set)

# Frame para conter os widgets
scrollable_frame = ttk.Frame(canvas_morse)
scrollable_frame_window = canvas_morse.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="scrollable_frame")

# Configure o scrollable_frame para ter a mesma largura que o canvas
def configure_scrollable_frame(event):
    canvas_morse.itemconfig("scrollable_frame", width=event.width)

canvas_morse.bind("<Configure>", configure_scrollable_frame)

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
    ax3 = fig.add_subplot(gs[1, :])

    # Obter últimos 4 dias
    dias = list(estatisticas.operacoes_por_dia.keys())
    dias.sort()

    if len(dias) > 4:
        dias = dias[-4:]

    cripto_por_dia = [estatisticas.operacoes_por_dia[dia]['cripto'] for dia in dias]
    descripto_por_dia = [estatisticas.operacoes_por_dia[dia]['descripto'] for dia in dias]

    # Formatação das datas para o gráfico
    dias_formatados = [dia.split('-')[2] + '/' + dia.split('-')[1] for dia in dias]

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
        new_width = min(width / 100, 7)
        new_height = min(height / 100, 4.2)

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

# Dicionário de conversão Morse
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.', '!': '-.-.--',
    '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...', ':': '---...',
    ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-',
    '"': '.-..-.', '$': '...-..-', '@': '.--.-.'
}

# Inverter o dicionário para decodificação
MORSE_CODE_REVERSE = {value: key for key, value in MORSE_CODE_DICT.items()}

# Conteúdo da Aba 4: Código Morse

# Frame para área de entrada de texto Morse
frame_entrada_morse = tk.LabelFrame(scrollable_frame, text="Entrada", font=("Arial", 10))
frame_entrada_morse.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)
frame_entrada_morse.columnconfigure(0, weight=1)
frame_entrada_morse.rowconfigure(0, weight=1)

# Área de entrada com ScrolledText
entrada_morse = scrolledtext.ScrolledText(frame_entrada_morse, height=8)
entrada_morse.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Botão para abrir arquivo na área de entrada Morse
btn_abrir_morse = tk.Button(frame_entrada_morse, text="Abrir Arquivo",
                            command=lambda: carregar_arquivo_morse())
btn_abrir_morse.grid(row=1, column=0, sticky="e", padx=5, pady=2)

# Frame para botões de operações Morse
frame_botoes_morse = tk.Frame(scrollable_frame)
frame_botoes_morse.grid(row=1, column=0, sticky="ew", pady=5, padx=5)
frame_botoes_morse.columnconfigure(0, weight=1)
frame_botoes_morse.columnconfigure(1, weight=1)
frame_botoes_morse.columnconfigure(2, weight=1)
frame_botoes_morse.columnconfigure(3, weight=1)

# Botões responsivos, usando grid para organização
btn_texto_para_morse = tk.Button(frame_botoes_morse, text="Texto → Morse",
                                 command=lambda: converter_para_morse(), padx=5)
btn_texto_para_morse.grid(row=0, column=0, sticky="ew", padx=2)

btn_morse_para_texto = tk.Button(frame_botoes_morse, text="Morse → Texto",
                                 command=lambda: converter_para_texto(), padx=5)
btn_morse_para_texto.grid(row=0, column=1, sticky="ew", padx=2)

btn_limpar_morse = tk.Button(frame_botoes_morse, text="Limpar",
                             command=lambda: limpar_texto_morse(), bg="lightgray", padx=5)
btn_limpar_morse.grid(row=0, column=2, sticky="ew", padx=2)

btn_salvar_morse = tk.Button(frame_botoes_morse, text="Salvar",
                             command=lambda: salvar_arquivo_morse(), padx=5)
btn_salvar_morse.grid(row=0, column=3, sticky="ew", padx=2)

# Frame para configurações adicionais
frame_config_morse = tk.Frame(scrollable_frame)
frame_config_morse.grid(row=2, column=0, sticky="ew", pady=2, padx=5)
frame_config_morse.columnconfigure(0, weight=1)
frame_config_morse.columnconfigure(1, weight=2)
frame_config_morse.columnconfigure(2, weight=1)
frame_config_morse.columnconfigure(3, weight=2)

# Separadores para código Morse
lbl_separador_letras = tk.Label(frame_config_morse, text="Separador de letras:")
lbl_separador_letras.grid(row=0, column=0, sticky="e", padx=2)

entrada_sep_letras = tk.Entry(frame_config_morse, width=5)
entrada_sep_letras.insert(0, " ")  # Espaço por padrão
entrada_sep_letras.grid(row=0, column=1, sticky="w", padx=2)

lbl_separador_palavras = tk.Label(frame_config_morse, text="Separador de palavras:")
lbl_separador_palavras.grid(row=0, column=2, sticky="e", padx=2)

entrada_sep_palavras = tk.Entry(frame_config_morse, width=5)
entrada_sep_palavras.insert(0, "   ")  # Três espaços por padrão
entrada_sep_palavras.grid(row=0, column=3, sticky="w", padx=2)

# Frame para configurações de som
frame_som_morse = tk.LabelFrame(scrollable_frame, text="Configurações de Som", font=("Arial", 10))
frame_som_morse.grid(row=3, column=0, sticky="ew", pady=5, padx=5)
frame_som_morse.columnconfigure(0, weight=1)
frame_som_morse.columnconfigure(1, weight=1)
frame_som_morse.columnconfigure(2, weight=1)
frame_som_morse.columnconfigure(3, weight=1)

# Configurações de velocidade (WPM - Words Per Minute)
lbl_wpm = tk.Label(frame_som_morse, text="Velocidade (WPM):")
lbl_wpm.grid(row=0, column=0, sticky="e", padx=2, pady=2)

# Variável para armazenar o valor do slider
wpm_var = tk.IntVar()
wpm_var.set(15)  # Valor padrão: 15 WPM

# Slider para ajustar a velocidade
slider_wpm = tk.Scale(frame_som_morse, from_=5, to=30, orient="horizontal",
                      variable=wpm_var, length=150)
slider_wpm.grid(row=0, column=1, sticky="w", padx=2, pady=2)

# Configurações de frequência (Hz)
lbl_freq = tk.Label(frame_som_morse, text="Frequência (Hz):")
lbl_freq.grid(row=0, column=2, sticky="e", padx=2, pady=2)

# Variável para armazenar o valor da frequência
freq_var = tk.IntVar()
freq_var.set(700)  # Valor padrão: 700 Hz

# Slider para ajustar a frequência
slider_freq = tk.Scale(frame_som_morse, from_=500, to=1000, orient="horizontal",
                       variable=freq_var, length=150)
slider_freq.grid(row=0, column=3, sticky="w", padx=2, pady=2)

# Configurações de volume
lbl_volume = tk.Label(frame_som_morse, text="Volume:")
lbl_volume.grid(row=1, column=0, sticky="e", padx=2, pady=2)

# Variável para armazenar o valor do volume
volume_var = tk.DoubleVar()
volume_var.set(0.5)  # Valor padrão: 50%

# Slider para ajustar o volume
slider_volume = tk.Scale(frame_som_morse, from_=0.0, to=1.0, resolution=0.1, orient="horizontal",
                         variable=volume_var, length=150)
slider_volume.grid(row=1, column=1, sticky="w", padx=2, pady=2)

# Frame para botões de reprodução
frame_reprod_morse = tk.Frame(frame_som_morse)
frame_reprod_morse.grid(row=1, column=2, columnspan=2, sticky="ew", padx=2, pady=2)
frame_reprod_morse.columnconfigure(0, weight=1)
frame_reprod_morse.columnconfigure(1, weight=1)

# Botão para reproduzir o código Morse
btn_reproduzir = tk.Button(frame_reprod_morse, text="▶ Reproduzir",
                           command=lambda: reproduzir_morse(), bg="lightgreen")
btn_reproduzir.grid(row=0, column=0, sticky="ew", padx=2)

# Botão para parar a reprodução
btn_parar = tk.Button(frame_reprod_morse, text="■ Parar",
                      command=lambda: parar_reproducao(), bg="lightcoral")
btn_parar.grid(row=0, column=1, sticky="ew", padx=2)

# Frame para área de saída de texto Morse
frame_saida_morse = tk.LabelFrame(scrollable_frame, text="Resultado", font=("Arial", 10))
frame_saida_morse.grid(row=4, column=0, sticky="nsew", pady=5, padx=5)
frame_saida_morse.columnconfigure(0, weight=1)
frame_saida_morse.rowconfigure(0, weight=1)

# Área de saída com ScrolledText
saida_morse = scrolledtext.ScrolledText(frame_saida_morse, height=8)
saida_morse.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Frame para visualização de onda
frame_visual_morse = tk.LabelFrame(scrollable_frame, text="Visualização de Onda", font=("Arial", 10))
frame_visual_morse.grid(row=5, column=0, sticky="nsew", pady=5, padx=5)
frame_visual_morse.columnconfigure(0, weight=1)
frame_visual_morse.rowconfigure(0, weight=1)

# Criar área para a visualização usando matplotlib
fig = Figure(figsize=(10, 2), dpi=80)
ax = fig.add_subplot(111)
ax.set_ylim(-1.2, 1.2)
ax.set_xlim(0, 100)
ax.set_yticks([-1, 0, 1])
ax.set_yticklabels(['', '', ''])
ax.set_xticks([])
ax.grid(True, linestyle='--', alpha=0.7)
line, = ax.plot([], [], lw=2, color='red')

# Adicionar canvas do matplotlib ao frame
canvas = FigureCanvasTkAgg(fig, master=frame_visual_morse)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# Variáveis para controle da visualização
wave_data = []
wave_time = []
max_time_window = 100
wave_active = False
wave_thread = None

# Frame para tabela de referência
frame_ref_morse = tk.LabelFrame(scrollable_frame, text="Tabela de Referência", font=("Arial", 10))
frame_ref_morse.grid(row=6, column=0, sticky="ew", pady=5, padx=5)

# Botão para exibir/ocultar tabela de referência
btn_mostrar_tabela = tk.Button(frame_ref_morse, text="Mostrar Tabela Morse",
                               command=lambda: mostrar_tabela_morse())
btn_mostrar_tabela.pack(fill="x", padx=5, pady=5)

# Variável para controlar a reprodução do som
reproduzindo = False
thread_reproducao = None

# Variáveis globais para controle do Arduino
arduino_serial = None
arduino_conectado = False
arduino_porta = None
thread_arduino = None
transmitindo_arduino = False

# Funções para operações com código Morse
def converter_para_morse():
    """Converte texto normal para código Morse"""
    texto = entrada_morse.get("1.0", tk.END).strip().upper()
    separador_letras = entrada_sep_letras.get()
    separador_palavras = entrada_sep_palavras.get()

    # Se os separadores estiverem vazios, usar os padrões
    if not separador_letras:
        separador_letras = " "
    if not separador_palavras:
        separador_palavras = "   "

    # Converter o texto para código Morse
    resultado = []
    for palavra in texto.split():
        palavra_morse = []
        for caractere in palavra:
            if caractere in MORSE_CODE_DICT:
                palavra_morse.append(MORSE_CODE_DICT[caractere])
        resultado.append(separador_letras.join(palavra_morse))

    morse_final = separador_palavras.join(resultado)

    # Exibir o resultado
    saida_morse.delete("1.0", tk.END)
    saida_morse.insert("1.0", morse_final)

def converter_para_texto():
    """Converte código Morse para texto normal"""
    morse_code = entrada_morse.get("1.0", tk.END).strip()

    # Tentar detectar separadores automaticamente
    sep_letras = entrada_sep_letras.get()
    sep_palavras = entrada_sep_palavras.get()

    # Se não houver separadores definidos, tentar detectar
    if not sep_letras or not sep_palavras:
        # Padrão comum em código Morse: espaço entre símbolos, 3 espaços entre palavras
        sep_letras = " "
        sep_palavras = "   "

    # Tentar processar o código Morse
    resultado = []
    for palavra in morse_code.split(sep_palavras):
        palavra_texto = []
        for simbolo in palavra.split(sep_letras):
            if simbolo in MORSE_CODE_REVERSE:
                palavra_texto.append(MORSE_CODE_REVERSE[simbolo])
            elif simbolo:
                palavra_texto.append("?")
        resultado.append("".join(palavra_texto))

    texto_final = " ".join(resultado)

    # Exibir o resultado
    saida_morse.delete("1.0", tk.END)
    saida_morse.insert("1.0", texto_final)

def limpar_texto_morse():
    """Limpa as áreas de texto da aba Morse"""
    entrada_morse.delete("1.0", tk.END)
    saida_morse.delete("1.0", tk.END)

def carregar_arquivo_morse():
    """Carrega um arquivo de texto na área de entrada Morse"""
    arquivo = filedialog.askopenfilename(
        title="Abrir Arquivo de Texto",
        filetypes=(("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*"))
    )

    if arquivo:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                entrada_morse.delete("1.0", tk.END)
                entrada_morse.insert("1.0", conteudo)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir o arquivo: {e}")

def salvar_arquivo_morse():
    """Salva o conteúdo da área de saída Morse em um arquivo"""
    arquivo = filedialog.asksaveasfilename(
        title="Salvar Como",
        defaultextension=".txt",
        filetypes=(("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*"))
    )

    if arquivo:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                conteudo = saida_morse.get("1.0", tk.END)
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso: {arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

def reproduzir_morse():
    """Reproduz o código Morse como som"""
    global reproduzindo, thread_reproducao

    # Parar reprodução anterior se estiver em andamento
    if reproduzindo:
        parar_reproducao()

    morse_code = saida_morse.get("1.0", tk.END).strip()

    # Se não houver código Morse, tentar converter da entrada
    if not morse_code:
        converter_para_morse()
        morse_code = saida_morse.get("1.0", tk.END).strip()

    if not morse_code:
        messagebox.showwarning("Aviso", "Nenhum código Morse para reproduzir.")
        return

    # Obter configurações de som
    wpm = wpm_var.get()
    frequencia = freq_var.get()
    volume = volume_var.get()

    # Calcular durações com base no WPM
    # Fórmula padrão: dot_duration = 1.2 / WPM (em segundos)
    dot_duration = 1.2 / wpm
    dash_duration = dot_duration * 3
    symbol_space = dot_duration  # Espaço entre símbolos (ponto/traço)
    letter_space = dot_duration * 3  # Espaço entre letras
    word_space = dot_duration * 7  # Espaço entre palavras

    # Iniciar thread de reprodução
    reproduzindo = True
    thread_reproducao = threading.Thread(target=tocar_morse,
                                         args=(morse_code, dot_duration, dash_duration,
                                               symbol_space, letter_space, word_space,
                                               frequencia, volume))
    thread_reproducao.daemon = True
    thread_reproducao.start()

def tocar_morse(morse_code, dot_duration, dash_duration, symbol_space,
                letter_space, word_space, frequencia, volume):
    """Função para tocar o código Morse em uma thread separada e visualizar a onda"""
    global reproduzindo, wave_data, wave_time, wave_active

    # Limpar dados anteriores
    wave_data = []
    wave_time = []
    current_time = 0
    wave_active = True

    # Iniciar thread de visualização
    vis_thread = threading.Thread(target=atualizar_visualizacao)
    vis_thread.daemon = True
    vis_thread.start()

    # Converter duração para milissegundos para o winsound
    dot_ms = int(dot_duration * 1000)
    dash_ms = int(dash_duration * 1000)

    # Verificar se é Windows (para winsound)
    is_windows = hasattr(winsound, 'Beep')

    # Função para tocar um tom e atualizar os dados de visualização
    def tocar_tom(duracao_ms, duracao_s):
        nonlocal current_time
        if is_windows:
            # Adicionar pontos para visualização (onda alta)
            t_start = current_time
            t_end = current_time + duracao_s

            # Adicionar pontos para forma de onda "quadrada"
            num_points = int(duracao_s * 50)  # 50 pontos por segundo para suavidade
            for i in range(num_points):
                t = t_start + (t_end - t_start) * i / num_points
                wave_time.append(t)
                wave_data.append(1)  # Amplitude do sinal alta

            current_time = t_end

            # Tocar o som
            winsound.Beep(frequencia, duracao_ms)
        else:
            # Alternativa para outros sistemas
            # Implementação similar usando outra biblioteca de som
            pass

    # Função para adicionar silêncio na visualização
    def adicionar_silencio(duracao_s):
        nonlocal current_time
        t_start = current_time
        t_end = current_time + duracao_s

        # Adicionar pontos para forma de onda "quadrada"
        num_points = int(duracao_s * 50)  # 50 pontos por segundo para suavidade
        for i in range(num_points):
            t = t_start + (t_end - t_start) * i / num_points
            wave_time.append(t)
            wave_data.append(0)  # Amplitude do sinal baixa (silêncio)

        current_time = t_end
        time.sleep(duracao_s)

    sep_letras = entrada_sep_letras.get() or " "
    sep_palavras = entrada_sep_palavras.get() or "   "

    try:
        for palavra in morse_code.split(sep_palavras):
            for i, letra in enumerate(palavra.split(sep_letras)):
                for j, simbolo in enumerate(letra):
                    if not reproduzindo:
                        break

                    if simbolo == '.':
                        tocar_tom(dot_ms, dot_duration)
                    elif simbolo == '-':
                        tocar_tom(dash_ms, dash_duration)

                    # Espaço entre símbolos dentro da letra
                    if j < len(letra) - 1 and reproduzindo:
                        adicionar_silencio(symbol_space)

                # Espaço entre letras
                if i < len(palavra.split(sep_letras)) - 1 and reproduzindo:
                    adicionar_silencio(letter_space)

            # Espaço entre palavras
            if reproduzindo:
                adicionar_silencio(word_space)

    except Exception as e:
        print(f"Erro na reprodução: {e}")

    finally:
        reproduzindo = False
        # Esperar um pouco antes de desativar a visualização
        time.sleep(0.5)
        wave_active = False

# Função para atualizar a visualização
def atualizar_visualizacao():
    """Atualiza a visualização da onda de forma contínua"""
    global wave_data, wave_time, wave_active

    while wave_active:
        try:
            # Copiar os dados para evitar problemas de concorrência
            current_data = wave_data.copy()
            current_time = wave_time.copy()

            if len(current_time) > 0:
                # Ajustar a escala de tempo para mostrar apenas a janela mais recente
                min_time = max(0, current_time[-1] - max_time_window) if current_time else 0
                max_time = current_time[-1] if current_time else max_time_window

                # Filtrar pontos dentro da janela visível
                visible_indices = [i for i, t in enumerate(current_time) if t >= min_time]
                visible_data = [current_data[i] for i in visible_indices]
                visible_time = [current_time[i] for i in visible_indices]

                # Atualizar o gráfico
                if visible_time:
                    ax.set_xlim(min_time, max_time)
                    line.set_data(visible_time, visible_data)
                    canvas.draw_idle()

            # Curto atraso para não sobrecarregar a CPU
            time.sleep(0.05)

        except Exception as e:
            print(f"Erro ao atualizar visualização: {e}")

    # Limpar visualização ao finalizar
    line.set_data([], [])
    canvas.draw_idle()

# Modificar a função parar_reproducao
def parar_reproducao():
    """Para a reprodução do código Morse e a visualização"""
    global reproduzindo, wave_active
    reproduzindo = False
    wave_active = False
    # Limpar visualização
    line.set_data([], [])
    canvas.draw_idle()
    # Esperar um pouco para garantir que a thread pare
    time.sleep(0.1)

# Adicione esta função para carregar e processar arquivos de áudio Morse
def carregar_audio_morse():
    """Carrega um arquivo de áudio e tenta decodificar código Morse"""
    arquivo = filedialog.askopenfilename(
        title="Abrir Arquivo de Áudio",
        filetypes=(("Arquivos de Áudio WAV", "*.wav"), ("Todos os Arquivos", "*.*"))
    )

    if not arquivo:
        return

    try:
        # Mostrar indicador de processamento
        saida_morse.delete("1.0", tk.END)
        saida_morse.insert("1.0", "Processando áudio, por favor aguarde...")
        saida_morse.update()

        # Carregar o arquivo de áudio
        taxa_amostragem, dados = wavfile.read(arquivo)

        # Se o áudio for estéreo, converter para mono (média dos canais)
        if len(dados.shape) > 1:
            dados = np.mean(dados, axis=1)

        # Normalizar dados para o intervalo [-1, 1]
        dados = dados / np.max(np.abs(dados))

        # Detectar o código Morse do áudio
        codigo_morse = detectar_morse_do_audio(dados, taxa_amostragem)

        # Exibir o código Morse detectado
        entrada_morse.delete("1.0", tk.END)
        entrada_morse.insert("1.0", codigo_morse)

        # Tentar converter para texto
        converter_para_texto()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar o arquivo de áudio: {e}")
        # Limpar mensagem de processamento
        saida_morse.delete("1.0", tk.END)

def detectar_morse_do_audio(dados, taxa_amostragem):
    """Detecta código Morse a partir de dados de áudio"""
    # 1. Pré-processamento do sinal
    # Normalizar dados
    dados = dados / np.max(np.abs(dados))

    # Aplicar filtro passa-banda para frequências típicas de código Morse (500-1000 Hz)
    sos = signal.butter(4, [400, 1200], 'bandpass', fs=taxa_amostragem, output='sos')
    dados_filtrados = signal.sosfilt(sos, dados)

    # Retificar o sinal
    dados_abs = np.abs(dados_filtrados)

    # 2. Envelope do sinal (detecção de amplitude)
    # Filtro de envelope com parâmetro adaptável baseado na taxa de amostragem
    tempo_envelope = 0.03  # 30ms - ajustável para diferentes velocidades de Morse
    tamanho_janela = int(taxa_amostragem * tempo_envelope)
    envelope = signal.convolve(dados_abs, np.ones(tamanho_janela) / tamanho_janela, mode='same')

    # 3. Detecção adaptativa de limiar
    # Usar método de Otsu para achar o limiar ideal (técnica de processamento de imagem adaptada)
    hist, bin_edges = np.histogram(envelope, bins=100)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Método de Otsu simplificado para encontrar o limiar ótimo
    peso1 = np.cumsum(hist)
    peso2 = np.cumsum(hist[::-1])[::-1]
    mean1 = np.cumsum(hist * bin_centers) / (peso1 + 1e-10)
    mean2 = np.cumsum((hist * bin_centers)[::-1])[::-1] / (peso2 + 1e-10)
    variancia = peso1[:-1] * peso2[1:] * (mean1[:-1] - mean2[1:]) ** 2

    if len(variancia) > 0:
        indice_otsu = np.argmax(variancia)
        limiar = bin_centers[indice_otsu]
    else:
        # Fallback para método simples se Otsu falhar
        limiar = np.mean(envelope) + np.std(envelope) * 0.8

    # Aplicar um fator de segurança para evitar falsos positivos
    limiar = limiar * 1.1

    # 4. Binarização do sinal
    sinal_binario = (envelope > limiar).astype(int)

    # 5. Eliminação de pulsos muito curtos (ruídos)
    duracao_minima = int(taxa_amostragem * 0.01)  # 10ms como duração mínima de um pulso

    # Encontrar regiões conectadas
    from scipy import ndimage
    estrutura = np.ones(3)  # Conectividade
    rotulado, num_recursos = ndimage.label(sinal_binario, structure=estrutura)

    # Remover regiões pequenas demais (ruído)
    for i in range(1, num_recursos + 1):
        tamanho = np.sum(rotulado == i)
        if tamanho < duracao_minima:
            sinal_binario[rotulado == i] = 0

    # 6. Encontrar transições com mais precisão
    mudancas = np.diff(sinal_binario)
    inicios = np.where(mudancas == 1)[0]
    fins = np.where(mudancas == -1)[0]

    # Garantir que temos pares completos de início/fim
    if len(inicios) > 0 and len(fins) > 0:
        if inicios[0] > fins[0]:
            fins = fins[1:]
        if len(inicios) > len(fins):
            inicios = inicios[:len(fins)]

    # Se não há transições suficientes, retornar uma string vazia
    if len(inicios) == 0 or len(fins) == 0:
        return ""

    # 7. Calcular durações de sons e silêncios
    duracoes_sons = []
    duracoes_silencios = []

    for i in range(len(inicios)):
        duracao = (fins[i] - inicios[i]) / taxa_amostragem
        duracoes_sons.append(duracao)

    for i in range(len(inicios) - 1):
        duracao = (inicios[i + 1] - fins[i]) / taxa_amostragem
        duracoes_silencios.append(duracao)

    # 8. Usar K-means para classificar duração de sons (pontos e traços)
    from sklearn.cluster import KMeans

    # Se temos sons suficientes para clustering
    if len(duracoes_sons) > 3:
        try:
            # Tentar K-means com 2 clusters (ponto e traço)
            kmeans_sons = KMeans(n_clusters=2, random_state=0).fit(np.array(duracoes_sons).reshape(-1, 1))
            centros_sons = kmeans_sons.cluster_centers_.flatten()

            # O centro menor é o ponto, o maior é o traço
            if centros_sons[0] < centros_sons[1]:
                centro_ponto, centro_traco = centros_sons
            else:
                centro_traco, centro_ponto = centros_sons

            # Limiar entre ponto e traço (média ponderada dos centros)
            limiar_ponto_traco = (centro_ponto * 2 + centro_traco) / 3
        except:
            # Se K-means falhar, usar média simples
            limiar_ponto_traco = np.mean(duracoes_sons)
    else:
        # Poucos sons para clustering, usar heurística
        limiar_ponto_traco = np.median(duracoes_sons) * 1.5

    # 9. Usar K-means para classificar silêncios (entre símbolos, letras e palavras)
    if len(duracoes_silencios) > 4:
        try:
            # Tentar K-means com 2 ou 3 clusters para silêncios
            n_clusters = 3 if len(duracoes_silencios) > 10 else 2
            kmeans_silencios = KMeans(n_clusters=n_clusters, random_state=0).fit(
                np.array(duracoes_silencios).reshape(-1, 1))
            centros_silencios = np.sort(kmeans_silencios.cluster_centers_.flatten())

            if len(centros_silencios) >= 3:
                # Temos 3 clusters: símbolo, letra, palavra
                limiar_simbolo_letra = (centros_silencios[0] + centros_silencios[1]) / 2
                limiar_letra_palavra = (centros_silencios[1] + centros_silencios[2]) / 2
            elif len(centros_silencios) == 2:
                # Temos 2 clusters: usamos valores proporcionais
                limiar_simbolo_letra = centros_silencios[0] * 1.2
                limiar_letra_palavra = centros_silencios[1] * 0.8
            else:
                # Fallback
                limiar_simbolo_letra = np.median(duracoes_silencios) * 1.5
                limiar_letra_palavra = np.median(duracoes_silencios) * 3
        except:
            # Se K-means falhar, usar proporções típicas de Morse
            # Tipicamente: espaço entre símbolos = 1 unidade, entre letras = 3 unidades, entre palavras = 7 unidades
            duracoes_ordenadas = np.sort(duracoes_silencios)
            limiar_simbolo_letra = np.median(duracoes_ordenadas) * 2
            limiar_letra_palavra = np.median(duracoes_ordenadas) * 5
    else:
        # Poucos dados para clustering
        duracoes_ordenadas = np.sort(duracoes_silencios)
        if len(duracoes_ordenadas) > 1:
            # Usar proporções padrão baseadas na mediana
            limiar_simbolo_letra = np.median(duracoes_ordenadas) * 2
            limiar_letra_palavra = np.median(duracoes_ordenadas) * 5
        else:
            # Valores arbitrários baseados em durações típicas
            menor_som = min(duracoes_sons) if duracoes_sons else 0.05
            limiar_simbolo_letra = menor_som * 3
            limiar_letra_palavra = menor_som * 7

    # 10. Construir o código Morse
    codigo_morse = []
    simbolo_atual = []

    # Converter durações em símbolos Morse
    for i, duracao in enumerate(duracoes_sons):
        if duracao < limiar_ponto_traco:
            simbolo_atual.append('.')
        else:
            simbolo_atual.append('-')

        # Verificar se é o último símbolo ou se há um próximo silêncio
        if i < len(duracoes_silencios):
            duracao_silencio = duracoes_silencios[i]

            if duracao_silencio >= limiar_letra_palavra:
                # Fim de palavra
                codigo_morse.append(''.join(simbolo_atual))
                codigo_morse.append('   ')  # Espaço entre palavras
                simbolo_atual = []
            elif duracao_silencio >= limiar_simbolo_letra:
                # Fim de letra
                codigo_morse.append(''.join(simbolo_atual))
                codigo_morse.append(' ')  # Espaço entre letras
                simbolo_atual = []
        elif i == len(duracoes_sons) - 1 and simbolo_atual:
            # Último símbolo
            codigo_morse.append(''.join(simbolo_atual))

    return ''.join(codigo_morse).strip()

# Adicione este trecho após o botão "Abrir Arquivo" na seção de entrada Morse
btn_abrir_audio = tk.Button(frame_entrada_morse, text="Abrir Áudio",
                            command=lambda: carregar_audio_morse())
btn_abrir_audio.grid(row=1, column=0, sticky="w", padx=5, pady=2)

# Função para exportar áudio Morse
def exportar_audio_morse():
    """Exporta o código Morse atual como um arquivo de áudio WAV"""
    global reproduzindo

    # Verificar se há código Morse para exportar
    morse_code = saida_morse.get("1.0", tk.END).strip()

    # Se não houver código Morse, tentar converter da entrada
    if not morse_code:
        converter_para_morse()
        morse_code = saida_morse.get("1.0", tk.END).strip()

    if not morse_code:
        messagebox.showwarning("Aviso", "Nenhum código Morse para exportar.")
        return

    # Solicitar ao usuário onde salvar o arquivo
    arquivo = filedialog.asksaveasfilename(
        title="Exportar Áudio",
        defaultextension=".wav",
        filetypes=(("Arquivo WAV", "*.wav"), ("Todos os Arquivos", "*.*"))
    )

    if not arquivo:
        return

    # Obter configurações de som
    wpm = wpm_var.get()
    frequencia = freq_var.get()
    volume = volume_var.get()

    # Calcular durações com base no WPM
    dot_duration = 1.2 / wpm  # em segundos
    dash_duration = dot_duration * 3
    symbol_space = dot_duration  # Espaço entre símbolos
    letter_space = dot_duration * 3  # Espaço entre letras
    word_space = dot_duration * 7  # Espaço entre palavras

    # Taxa de amostragem para o arquivo de áudio (44.1 kHz é padrão para qualidade CD)
    taxa_amostragem = 44100

    # Gerar o sinal de áudio
    try:
        # Mostrar indicador de processamento
        saida_morse.insert(tk.END, "\n\nGerando áudio, por favor aguarde...")
        saida_morse.update()

        # Criar os dados de áudio
        dados_audio = gerar_dados_audio_morse(morse_code, taxa_amostragem,
                                              dot_duration, dash_duration,
                                              symbol_space, letter_space, word_space,
                                              frequencia, volume)

        # Normalizar para evitar clipping
        if np.max(np.abs(dados_audio)) > 0:
            dados_audio = dados_audio / np.max(np.abs(dados_audio)) * 0.9

        # Converter para o formato de 16 bits
        dados_audio_16bit = (dados_audio * 32767).astype(np.int16)

        # Salvar o arquivo
        wavfile.write(arquivo, taxa_amostragem, dados_audio_16bit)

        # Remover indicador de processamento e mostrar mensagem de sucesso
        saida_morse.delete("1.0", tk.END)
        saida_morse.insert("1.0", morse_code)
        messagebox.showinfo("Sucesso", f"Áudio exportado com sucesso: {arquivo}")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar o áudio: {e}")
        # Remover indicador de processamento
        saida_morse.delete("1.0", tk.END)
        saida_morse.insert("1.0", morse_code)

def gerar_dados_audio_morse(morse_code, taxa_amostragem, dot_duration, dash_duration,
                            symbol_space, letter_space, word_space, frequencia, volume):
    """Gera os dados de áudio para o código Morse fornecido"""

    # Função para gerar um tom senoidal
    def gerar_tom(duracao, freq, vol):
        t = np.linspace(0, duracao, int(taxa_amostragem * duracao), endpoint=False)
        # Adicionar envelope ADSR simples para suavizar o início e fim do som
        envelope = np.ones_like(t)
        attack = int(0.005 * taxa_amostragem)  # 5ms de ataque
        release = int(0.005 * taxa_amostragem)  # 5ms de release

        # Aplicar ataque (rampa linear)
        if len(envelope) > attack:
            envelope[:attack] = np.linspace(0, 1, attack)

        # Aplicar release (rampa linear descendente)
        if len(envelope) > release:
            envelope[-release:] = np.linspace(1, 0, release)

        return vol * np.sin(2 * np.pi * freq * t) * envelope

    # Função para gerar silêncio
    def gerar_silencio(duracao):
        return np.zeros(int(taxa_amostragem * duracao))

    # Processar o código Morse
    dados_audio = np.array([])

    sep_letras = entrada_sep_letras.get() or " "
    sep_palavras = entrada_sep_palavras.get() or "   "

    for palavra in morse_code.split(sep_palavras):
        for i, letra in enumerate(palavra.split(sep_letras)):
            for j, simbolo in enumerate(letra):
                if simbolo == '.':
                    dados_audio = np.append(dados_audio, gerar_tom(dot_duration, frequencia, volume))
                elif simbolo == '-':
                    dados_audio = np.append(dados_audio, gerar_tom(dash_duration, frequencia, volume))

                # Espaço entre símbolos dentro da letra
                if j < len(letra) - 1:
                    dados_audio = np.append(dados_audio, gerar_silencio(symbol_space))

            # Espaço entre letras
            if i < len(palavra.split(sep_letras)) - 1:
                dados_audio = np.append(dados_audio, gerar_silencio(letter_space))

        # Espaço entre palavras
        dados_audio = np.append(dados_audio, gerar_silencio(word_space))

    return dados_audio

# Adicionar botão Exportar na interface de reprodução
btn_exportar = tk.Button(frame_reprod_morse, text="💾 Exportar",
                         command=lambda: exportar_audio_morse(), bg="lightblue")
btn_exportar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

# Atualizar a configuração do grid para acomodar o novo botão
frame_reprod_morse.rowconfigure(1, weight=1)

# Função para listar portas seriais disponíveis
def listar_portas_seriais():
    """Lista todas as portas seriais disponíveis no sistema com informações detalhadas"""
    portas = list(serial.tools.list_ports.comports())

    # Exibir informações detalhadas no console para debug
    print("=== Portas disponíveis ===")
    for p in portas:
        print(f"Dispositivo: {p.device}")
        print(f"Nome: {p.name}")
        print(f"Descrição: {p.description}")
        print(f"HWID: {p.hwid}")
        print(f"VID:PID: {p.vid}:{p.pid}" if hasattr(p, 'vid') and hasattr(p, 'pid') else "VID:PID: N/A")
        print("------------------------")

    return portas

# Função para conectar ao Arduino
def conectar_arduino():
    """Conecta ao Arduino na porta selecionada"""
    global arduino_serial, arduino_conectado, arduino_porta

    porta_completa = combo_portas.get()

    if not porta_completa:
        messagebox.showerror("Erro", "Selecione uma porta serial para conectar.")
        return False

    # Extrair apenas o nome da porta (COM3) da string completa
    if "COM" in porta_completa:
        porta = porta_completa.split(' ')[0]  # Pega apenas a primeira parte (COM3)
    else:
        # Tenta pegar a porta completa como está
        porta = porta_completa

    print(f"Tentando conectar na porta: '{porta}'")  # Debug

    try:
        # Fechar conexão anterior se existir
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.close()

        # Abordagem mais básica para a conexão
        arduino_serial = serial.Serial()
        arduino_serial.port = porta
        arduino_serial.baudrate = 9600
        arduino_serial.timeout = 2
        arduino_serial.open()

        time.sleep(2)  # Aguardar inicialização do Arduino

        # Testar conexão - versão com diagnóstico detalhado
        try:
            # Limpar buffers antes de começar
            arduino_serial.reset_input_buffer()
            arduino_serial.reset_output_buffer()

            print("Enviando comando de teste 'T'...")
            arduino_serial.write(b'T')  # Comando de teste
            time.sleep(1.0)  # Dar mais tempo para resposta

            # Tentar ler a resposta e mostrar o que foi recebido para diagnóstico
            resposta_bytes = arduino_serial.read_all()
            resposta_str = resposta_bytes.decode('utf-8', errors='ignore').strip()

            print(f"Resposta recebida: '{resposta_str}' (bytes: {resposta_bytes})")

            # Verificar se a resposta contém "OK" em qualquer formato
            if "OK" in resposta_str:
                print("Comando OK reconhecido!")
                arduino_conectado = True
                arduino_porta = porta
                atualizar_status_arduino("Conectado", "green")
                messagebox.showinfo("Sucesso", f"Arduino conectado na porta {porta}.")
                return True
            else:
                print("Tentando um segundo comando...")
                # Tentar enviar outro comando como segunda tentativa
                arduino_serial.write(b'\n')
                time.sleep(0.5)

                # Ler qualquer resposta adicional
                resposta_bytes = arduino_serial.read_all()
                resposta_str = resposta_bytes.decode('utf-8', errors='ignore').strip()
                print(f"Segunda resposta: '{resposta_str}'")

                # Se houver qualquer resposta, considerar conectado
                if len(resposta_bytes) > 0:
                    print("Arduino respondeu! Considerando conectado.")
                    arduino_conectado = True
                    arduino_porta = porta
                    atualizar_status_arduino("Conectado", "green")
                    messagebox.showinfo("Sucesso", f"Arduino conectado na porta {porta}.")
                    return True
                else:
                    print("Arduino não respondeu de forma reconhecível")
                    arduino_serial.close()
                    arduino_conectado = False
                    atualizar_status_arduino("Desconectado", "red")
                    messagebox.showerror("Erro", f"Dispositivo não respondeu como esperado. Recebido: '{resposta_str}'")
                    return False

        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
            arduino_serial.close()
            arduino_conectado = False
            atualizar_status_arduino("Desconectado", "red")
            messagebox.showerror("Erro", f"Erro ao testar comunicação com o dispositivo: {e}")
            return False

    except Exception as e:
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.close()
        arduino_conectado = False
        atualizar_status_arduino("Erro", "red")
        messagebox.showerror("Erro", f"Erro ao conectar: {e}")
        return False

# Função para desconectar do Arduino
def desconectar_arduino():
    """Desconecta do Arduino"""
    global arduino_serial, arduino_conectado, transmitindo_arduino

    # Parar transmissão se estiver ativa
    if transmitindo_arduino:
        parar_transmissao_arduino()

    try:
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.write(b'X')  # Comando para desligar LED
            arduino_serial.close()

        arduino_conectado = False
        atualizar_status_arduino("Desconectado", "red")
        messagebox.showinfo("Desconectado", "Arduino desconectado com sucesso.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao desconectar: {e}")

# Função para atualizar status na interface
def atualizar_status_arduino(status, cor):
    """Atualiza o status do Arduino na interface"""
    lbl_status_arduino.config(text=f"Status: {status}", fg=cor)

    # Atualizar estado dos botões
    if status == "Conectado":
        btn_conectar_arduino.config(state=tk.DISABLED)
        btn_desconectar_arduino.config(state=tk.NORMAL)
        btn_atualizar_portas.config(state=tk.DISABLED)
        btn_transmitir_arduino.config(state=tk.NORMAL)
    else:
        btn_conectar_arduino.config(state=tk.NORMAL)
        btn_desconectar_arduino.config(state=tk.DISABLED)
        btn_atualizar_portas.config(state=tk.NORMAL)
        btn_transmitir_arduino.config(state=tk.DISABLED)

    if status == "Transmitindo":
        btn_transmitir_arduino.config(state=tk.DISABLED)
        btn_parar_arduino.config(state=tk.NORMAL)
    else:
        btn_parar_arduino.config(state=tk.DISABLED)
        if status == "Conectado":
            btn_transmitir_arduino.config(state=tk.NORMAL)

# Função para atualizar lista de portas seriais
def atualizar_portas_seriais():
    """Atualiza a lista de portas seriais disponíveis"""
    portas = listar_portas_seriais()

    # Limpar lista atual
    combo_portas['values'] = []

    # Preencher com portas disponíveis
    if portas:
        # Usar apenas o nome da porta para evitar problemas de parsing
        portas_str = [p.device for p in portas]
        combo_portas['values'] = portas_str
        combo_portas.current(0)  # Selecionar primeira porta
    else:
        messagebox.showinfo("Informação", "Nenhuma porta serial encontrada.")

# Função para formatar o código Morse corretamente
def formatar_codigo_morse(morse_code):
    """Formata o código Morse garantindo espaçamento correto para o Arduino"""
    # Obter separadores configurados
    sep_letras = entrada_sep_letras.get() or " "
    sep_palavras = entrada_sep_palavras.get() or "   "

    try:
        # Primeiro dividir por palavras
        palavras = morse_code.split(sep_palavras)
        palavras_formatadas = []

        # Para cada palavra, formatar letras
        for palavra in palavras:
            letras = palavra.split(sep_letras)
            # Filtrar letras vazias
            letras = [letra for letra in letras if letra.strip()]
            # Juntar letras com espaço único entre elas (o Arduino interpretará como separação entre letras)
            palavra_formatada = " ".join(letras)
            palavras_formatadas.append(palavra_formatada)

        # Juntar palavras com três espaços entre elas (o Arduino interpretará como separação entre palavras)
        morse_formatado = "   ".join(palavras_formatadas)

        # Log para diagnóstico
        print(f"Morse formatado para Arduino: '{morse_formatado}'")

        return morse_formatado
    except Exception as e:
        print(f"Erro ao formatar código Morse: {e}")
        # Retornar o código original se houver erro
        return morse_code

# Função para transmitir código Morse pelo Arduino
def transmitir_morse_arduino():
    """Inicia a transmissão do código Morse pelo Arduino"""
    global transmitindo_arduino, thread_arduino

    if not arduino_conectado or not arduino_serial or not arduino_serial.is_open:
        messagebox.showerror("Erro", "Arduino não está conectado.")
        return

    morse_code = saida_morse.get("1.0", tk.END).strip()

    # Se não houver código Morse, tentar converter da entrada
    if not morse_code:
        converter_para_morse()
        morse_code = saida_morse.get("1.0", tk.END).strip()

    if not morse_code:
        messagebox.showwarning("Aviso", "Nenhum código Morse para transmitir.")
        return

    # Formatar o código morse para garantir espaços corretos
    morse_code = formatar_codigo_morse(morse_code)

    # Obter configurações de tempo
    wpm = wpm_var.get()

    # Calcular durações com base no WPM (em milissegundos para o Arduino)
    dot_duration = int((1.2 / wpm) * 1000)
    dash_duration = dot_duration * 3
    symbol_space = dot_duration
    letter_space = dot_duration * 3
    word_space = dot_duration * 7

    # Enviar configurações para o Arduino
    try:
        # Limpar buffer antes de enviar comandos
        arduino_serial.reset_input_buffer()
        arduino_serial.reset_output_buffer()

        # Protocolo: C,dot_duration,dash_duration,symbol_space,letter_space,word_space
        comando = f"C,{dot_duration},{dash_duration},{symbol_space},{letter_space},{word_space}\n"
        print(f"Enviando configuração: {comando.strip()}")
        arduino_serial.write(comando.encode())
        time.sleep(0.5)  # Aumentar pausa para processamento

        # Limpar buffer novamente antes de enviar o código morse
        arduino_serial.reset_input_buffer()

        # Iniciar thread de transmissão
        transmitindo_arduino = True
        atualizar_status_arduino("Transmitindo", "orange")
        thread_arduino = threading.Thread(target=thread_transmissao_arduino,
                                          args=(morse_code,))
        thread_arduino.daemon = True
        thread_arduino.start()

    except Exception as e:
        transmitindo_arduino = False
        atualizar_status_arduino("Conectado", "green")
        messagebox.showerror("Erro", f"Erro ao iniciar transmissão: {e}")

# Thread para transmissão do código Morse
def thread_transmissao_arduino(morse_code):
    """Thread para transmitir o código Morse para o Arduino"""
    global transmitindo_arduino

    try:
        print(f"Iniciando transmissão. Código: '{morse_code}'")

        # Limpar buffer antes de transmitir
        arduino_serial.reset_input_buffer()

        # Enviar o código Morse diretamente como uma única mensagem
        comando = f"M,{morse_code}\n"
        print(f"Enviando comando: {comando.strip()}")
        arduino_serial.write(comando.encode())
        arduino_serial.flush()  # Garantir que todos os dados sejam enviados

        # Aguardar confirmação do Arduino (com timeout)
        inicio = time.time()
        resposta = ""
        while "M OK" not in resposta and (time.time() - inicio) < 180:  # Timeout de 3 minutos
            if arduino_serial.in_waiting:
                try:
                    linha = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        print(f"Resposta durante transmissão: {linha}")
                        resposta = linha
                except:
                    pass
            time.sleep(0.1)  # Pequena pausa para não sobrecarregar a CPU

            if not transmitindo_arduino:
                break

        # Finalizar a transmissão
        transmitindo_arduino = False
        atualizar_status_arduino("Conectado", "green")
        messagebox.showinfo("Concluído", "Transmissão concluída.")

    except Exception as e:
        print(f"Erro na transmissão: {e}")
        transmitindo_arduino = False
        atualizar_status_arduino("Conectado", "green")
        messagebox.showerror("Erro", f"Erro durante transmissão: {e}")

# Função para parar a transmissão
def parar_transmissao_arduino():
    """Para a transmissão do código Morse pelo Arduino"""
    global transmitindo_arduino

    if not arduino_conectado or not arduino_serial or not arduino_serial.is_open:
        return

    try:
        # Enviar comando de parada
        arduino_serial.write(b"S\n")  # S para Stop
        transmitindo_arduino = False
        atualizar_status_arduino("Conectado", "green")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao parar transmissão: {e}")

# Frame para controle do Arduino (inserir após o frame de referência)
frame_arduino = tk.LabelFrame(scrollable_frame, text="Conexão Arduino", font=("Arial", 10))
frame_arduino.grid(row=7, column=0, sticky="ew", pady=5, padx=5)
frame_arduino.columnconfigure(0, weight=1)
frame_arduino.columnconfigure(1, weight=1)
frame_arduino.columnconfigure(2, weight=1)
frame_arduino.columnconfigure(3, weight=1)

# Seleção de porta serial
lbl_porta = tk.Label(frame_arduino, text="Porta Serial:")
lbl_porta.grid(row=0, column=0, padx=5, pady=5, sticky="e")

combo_portas = ttk.Combobox(frame_arduino, width=25)
combo_portas.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Botão para atualizar lista de portas
btn_atualizar_portas = tk.Button(frame_arduino, text="Atualizar Portas",
                                 command=lambda: atualizar_portas_seriais())
btn_atualizar_portas.grid(row=0, column=2, padx=5, pady=5)

# Status da conexão
lbl_status_arduino = tk.Label(frame_arduino, text="Status: Desconectado", fg="red")
lbl_status_arduino.grid(row=0, column=3, padx=5, pady=5)

# Botões de controle do Arduino
frame_ctrl_arduino = tk.Frame(frame_arduino)
frame_ctrl_arduino.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
frame_ctrl_arduino.columnconfigure(0, weight=1)
frame_ctrl_arduino.columnconfigure(1, weight=1)
frame_ctrl_arduino.columnconfigure(2, weight=1)
frame_ctrl_arduino.columnconfigure(3, weight=1)

# Botões de conexão
btn_conectar_arduino = tk.Button(frame_ctrl_arduino, text="Conectar",
                                 command=lambda: conectar_arduino(), bg="lightgreen")
btn_conectar_arduino.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

btn_desconectar_arduino = tk.Button(frame_ctrl_arduino, text="Desconectar",
                                    command=lambda: desconectar_arduino(), bg="lightcoral")
btn_desconectar_arduino.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
btn_desconectar_arduino.config(state=tk.DISABLED)

# Botões de transmissão
btn_transmitir_arduino = tk.Button(frame_ctrl_arduino, text="Transmitir para Arduino",
                                   command=lambda: transmitir_morse_arduino(), bg="lightyellow")
btn_transmitir_arduino.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
btn_transmitir_arduino.config(state=tk.DISABLED)

btn_parar_arduino = tk.Button(frame_ctrl_arduino, text="Parar Transmissão",
                              command=lambda: parar_transmissao_arduino(), bg="lightgray")
btn_parar_arduino.grid(row=0, column=3, padx=2, pady=2, sticky="ew")
btn_parar_arduino.config(state=tk.DISABLED)

# Inicializar a lista de portas ao carregar a aplicação
atualizar_portas_seriais()

def mostrar_tabela_morse():
    """Exibe uma janela com a tabela de referência do código Morse"""
    # Criar uma nova janela
    janela_tabela = tk.Toplevel()
    janela_tabela.title("Tabela de Código Morse")
    janela_tabela.geometry("500x600")
    janela_tabela.minsize(400, 250)

    # Criar um frame para conter a tabela
    frame_tabela = tk.Frame(janela_tabela, padx=10, pady=10)
    frame_tabela.pack(fill="both", expand=True)

    # Criar uma ScrolledText para exibir a tabela
    texto_tabela = scrolledtext.ScrolledText(frame_tabela, wrap=tk.WORD, font=("Courier", 10))
    texto_tabela.pack(fill="both", expand=True)

    # Construir a tabela de referência
    tabela_texto = "TABELA DE CÓDIGO MORSE\n"
    tabela_texto += "=" * 40 + "\n\n"

    # Adicionar letras
    tabela_texto += "LETRAS:\n"
    tabela_texto += "-" * 20 + "\n"
    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        tabela_texto += f"{letra} : {MORSE_CODE_DICT[letra]}\n"

    tabela_texto += "\nNÚMEROS:\n"
    tabela_texto += "-" * 20 + "\n"
    for numero in "0123456789":
        tabela_texto += f"{numero} : {MORSE_CODE_DICT[numero]}\n"

    tabela_texto += "\nSINAIS DE PONTUAÇÃO:\n"
    tabela_texto += "-" * 20 + "\n"
    for sinal, morse in MORSE_CODE_DICT.items():
        if sinal not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            tabela_texto += f"{sinal} : {morse}\n"

    # Adicionar informações sobre regras do código Morse
    tabela_texto += "\nREGRAS BÁSICAS:\n"
    tabela_texto += "-" * 20 + "\n"
    tabela_texto += "• Um traço (-) tem duração de 3 pontos (.)\n"
    tabela_texto += "• O espaço entre partes de uma mesma letra é igual a 1 ponto\n"
    tabela_texto += "• O espaço entre letras é igual a 3 pontos\n"
    tabela_texto += "• O espaço entre palavras é igual a 7 pontos\n"

    # Inserir o texto na área de texto
    texto_tabela.insert("1.0", tabela_texto)
    texto_tabela.config(state="disabled")  # Impedir edição

    # Adicionar botão para fechar a janela
    btn_fechar = tk.Button(janela_tabela, text="Fechar", command=janela_tabela.destroy)
    btn_fechar.pack(pady=10)

# Configurar responsividade da aba
scrollable_frame.columnconfigure(0, weight=1)

# Configurar pesos das linhas para melhor organização vertical
scrollable_frame.rowconfigure(0, weight=1)  # Entrada de texto
scrollable_frame.rowconfigure(1, weight=0)  # Botões de operação
scrollable_frame.rowconfigure(2, weight=0)  # Configurações adicionais
scrollable_frame.rowconfigure(3, weight=0)  # Configurações de som
scrollable_frame.rowconfigure(4, weight=1)  # Saída de texto
scrollable_frame.rowconfigure(5, weight=1)  # Visualização de onda
scrollable_frame.rowconfigure(6, weight=0)  # Tabela de referência

# Função para atualizar o scrollregion do canvas quando os componentes mudam de tamanho
def update_scrollregion(event):
    canvas_morse.configure(scrollregion=canvas_morse.bbox("all"))

scrollable_frame.bind("<Configure>", update_scrollregion)

# Configurar evento de mousewheel para scroll
def _on_mousewheel(event):
    canvas_morse.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas_morse.bind_all("<MouseWheel>", _on_mousewheel)

# Inicialização - Configurar o scrollregion após todos os widgets serem adicionados
scrollable_frame.update_idletasks()
canvas_morse.configure(scrollregion=canvas_morse.bbox("all"))

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
menu_ajuda.add_command(label="Ver Tutorial", command=lambda: mostrar_tutorial(), accelerator="F2")
menu_ajuda.add_command(label="Dicas Rápidas", command=lambda: mostrar_dicas(), accelerator="F3")
menu_ajuda.add_command(label="Relatório de Bugs", command=lambda: reportar_bug(), accelerator="F4")
menu_ajuda.add_command(label="Verificar Atualizações", command=lambda: verificar_atualizacoes(), accelerator="F5")
menu_ajuda.add_separator()
menu_ajuda.add_command(label="Sobre", command=lambda: mostrar_sobre(), accelerator="F6")

# Funções para os itens do menu Ajuda
def mostrar_ajuda():
    ajuda = tk.Toplevel(janela)
    ajuda.title("Ajuda - CryptographiE")
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
    ttk.Label(titulo_frame, text="CryptographiE - Manual de Ajuda",
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
            "titulo": "CryptographiE",
            "descricao": "Bem-vindo ao Sistema de Criptografia - CryptographiE da CONATUS Technologies, uma ferramenta projetada para proteger seus dados pessoais e arquivos importantes.",
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
                "A criptografia de arquivos grandes pode levar alguns minutos e exigir mais da sua CPU."
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
            "titulo": "Operações Disponíveis",
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
                "Mantenha um registro das suas atividades de criptografia.",
                "Opção de exportação dos dados estatísticos"
            ]
        }
    ]

    # Conteúdo para a aba de Código Morse
    conteudo_morse = [
        {
            "titulo": "Código Morse",
            "descricao": "A aba \"Código Morse\" oferece ferramentas completas para tradução e interação com o código morse.",
        },
        {
            "titulo": "Operações Disponíveis",
            "itens": [
                {"titulo": "Tradução Bidirecional",
                 "descricao": "Converta texto para código morse e código morse para texto."},
                {"titulo": "Reprodução de Áudio",
                 "descricao": "Escute o código morse com controle de velocidade, volume e frequência."},
                {"titulo": "Visualização por Onda",
                 "descricao": "Veja a representação visual das ondas sonoras do código morse."},
                {"titulo": "Exportação de Áudio",
                 "descricao": "Salve o código morse como arquivo de áudio em formato .WAV ou .MP3."},
                {"titulo": "Carregamento de Áudio",
                 "descricao": "Importe arquivos de áudio .WAV para tradução automática de código morse."}
            ]
        },
        {
            "titulo": "Benefícios",
            "itens": [
                "Converta mensagens em código Morse para aumentar a privacidade da comunicação.",
                "Traduza mensagens rapidamente entre texto e código morse.",
                "Analise visualmente a estrutura de mensagens em código morse.",
                "Compartilhe e traduza mensagens em morse como arquivos de áudio."
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
                    ["F2", "Ver Tutorial"],
                    ["F3", "Mostrar Dicas Rápidas"],
                    ["F4", "Reportar Bug"],
                    ["F5", "Verificar Atualizações"],
                    ["F6", "Mostrar Sobre"],
                    ["F7", "Abrir Website"],
                ]
            }
        }
    ]

    # Criar as abas
    criar_aba(notebook, "Introdução", conteudo_intro)
    criar_aba(notebook, "Criptografia de Texto", conteudo_texto)
    criar_aba(notebook, "Criptografia de Arquivos", conteudo_arquivos)
    criar_aba(notebook, "Estatísticas", conteudo_stats)
    criar_aba(notebook, "Código Morse", conteudo_morse)
    criar_aba(notebook, "Atalhos de Teclado", conteudo_atalhos)

    # Botão de fechar com estilo
    botoes_frame = ttk.Frame(ajuda, style="Ajuda.TFrame")
    botoes_frame.pack(fill=tk.X, pady=10)

    botao_fechar = ttk.Button(botoes_frame, text="Fechar", command=ajuda.destroy)
    botao_fechar.pack(side=tk.RIGHT, padx=10)

def mostrar_tutorial():
    # Criar nova janela para o tutorial
    tutorial = tk.Toplevel(janela)
    tutorial.title("Tutorial em Vídeo - CryptographiE")
    tutorial.geometry("900x650")
    tutorial.minsize(800, 600)
    tutorial.transient(janela)  # Define a janela principal como parent
    tutorial.grab_set()  # Torna a janela modal
    tutorial.configure(bg="#f5f7fa")  # Cor de fundo mais suave

    # Configurações de estilo
    estilo = ttk.Style()
    estilo.configure("Tutorial.TFrame", background="#f5f7fa")
    estilo.configure("TutorialTitle.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50")
    estilo.configure("TutorialText.TLabel", font=("Segoe UI", 11), foreground="#34495e")
    estilo.configure("TutorialButton.TButton", font=("Segoe UI", 10))
    estilo.configure("ControlButton.TButton", padding=5)

    # Frame principal
    frame_principal = ttk.Frame(tutorial, padding=15, style="Tutorial.TFrame")
    frame_principal.pack(fill=tk.BOTH, expand=True)

    # Título e subtítulo
    frame_titulo = ttk.Frame(frame_principal, style="Tutorial.TFrame")
    frame_titulo.pack(fill=tk.X, pady=(0, 15))

    ttk.Label(frame_titulo, text="Tutorial do CryptographiE",
              style="TutorialTitle.TLabel").pack(anchor=tk.W)
    ttk.Label(frame_titulo, text="Aprenda como utilizar todas as funcionalidades do sistema",
              style="TutorialText.TLabel").pack(anchor=tk.W, pady=(5, 0))

    # Frame para o player de vídeo
    frame_video = ttk.Frame(frame_principal, style="Tutorial.TFrame")
    frame_video.pack(fill=tk.BOTH, expand=True, pady=10)

    # Verificar se a biblioteca está disponível
    video_disponivel = False  # Inicialmente assumimos que não está disponível
    try:
        import cv2
        from PIL import Image, ImageTk
        # Verificar se podemos realmente usar o OpenCV tentando criar um objeto VideoCapture
        test_cap = cv2.VideoCapture()
        if test_cap is not None:
            test_cap.release()
            video_disponivel = True
    except (ImportError, AttributeError, cv2.error):
        video_disponivel = False
        print("Bibliotecas de vídeo não disponíveis ou não funcionando corretamente")

    # Classe para gerenciar tooltips
    class ToolTip:
        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tip_window = None
            self.widget.bind("<Enter>", self.show_tip)
            self.widget.bind("<Leave>", self.hide_tip)

        def show_tip(self, event=None):
            """Exibe o tooltip quando o mouse passa sobre o widget"""
            if self.tip_window or not self.text:
                return

            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25

            # Cria uma janela superior para o tooltip
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)  # Remove a borda da janela
            tw.wm_geometry(f"+{x}+{y}")

            # Cria um label com o texto do tooltip
            label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             font=("Segoe UI", 9, "normal"))
            label.pack(padx=2, pady=2)

        def hide_tip(self, event=None):
            """Esconde o tooltip quando o mouse sai do widget"""
            if self.tip_window:
                self.tip_window.destroy()
                self.tip_window = None

    if video_disponivel:
        # Lista de vídeos tutoriais disponíveis
        videos = [
            {"titulo": "Introdução ao Sistema", "arquivo": "video/Tutorial1.mp4"},
            {"titulo": "Criptografar e Descriptografar Textos", "arquivo": "video/Tutorial2.mp4"},
            {"titulo": "Criptografar e Descriptografar Arquivos", "arquivo": "video/Tutorial3.mp4"},
            {"titulo": "Criptografar e Descriptografar Pastas", "arquivo": "video/Tutorial4.mp4"},
            {"titulo": "Estatísticas e Exportação", "arquivo": "video/Tutorial5.mp4"},
            {"titulo": "Código Morse", "arquivo": "video/Tutorial6.mp4"},
            {"titulo": "Visite nosso site", "arquivo": "video/Tutorial7.mp4"}
        ]

        # Variáveis para controle de reprodução
        reproduzindo = tk.BooleanVar(value=False)
        volume = tk.DoubleVar(value=0.8)
        progresso = tk.DoubleVar(value=0.0)

        # Variáveis globais para o escopo da função
        cap = None
        duracao_total = 0
        frame_atual = 0
        total_frames = 0
        video_selecionado = tk.StringVar(value=videos[0]["arquivo"])

        # Frame de seleção de vídeos
        frame_selecao = ttk.Frame(frame_principal, style="Tutorial.TFrame")
        frame_selecao.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame_selecao, text="Selecione um tutorial:",
                  style="TutorialText.TLabel").pack(side=tk.LEFT, padx=(0, 10))

        combo_videos = ttk.Combobox(frame_selecao, values=[v["titulo"] for v in videos],
                                    width=30, state="readonly")
        combo_videos.current(0)
        combo_videos.pack(side=tk.LEFT)

        # Frame para o vídeo
        video_canvas = tk.Canvas(frame_video, bg="#000000", highlightthickness=0)
        video_canvas.pack(fill=tk.BOTH, expand=True)

        # Frame para informações do vídeo
        info_frame = ttk.Frame(frame_principal, style="Tutorial.TFrame")
        info_frame.pack(fill=tk.X, pady=(10, 5))

        tempo_label = ttk.Label(info_frame, text="00:00 / 00:00",
                                style="TutorialText.TLabel", width=15)
        tempo_label.pack(side=tk.LEFT)

        # Barra de progresso do vídeo
        progresso_frame = ttk.Frame(frame_principal, style="Tutorial.TFrame")
        progresso_frame.pack(fill=tk.X, pady=(0, 10))

        # Função para formatar tempo
        def formatar_tempo(segundos):
            minutos = int(segundos // 60)
            segs = int(segundos % 60)
            return f"{minutos:02d}:{segs:02d}"

        # Função para atualizar label de tempo
        def atualizar_tempo_label():
            if total_frames > 0 and cap is not None and cap.isOpened():
                tempo_atual = (frame_atual / total_frames) * duracao_total
                tempo_label.config(text=f"{formatar_tempo(tempo_atual)} / {formatar_tempo(duracao_total)}")

        # Função para mostrar um frame no canvas
        def mostrar_frame(frame):
            # Converter frame para formato Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            # Redimensionar mantendo proporção
            canvas_width = video_canvas.winfo_width()
            canvas_height = video_canvas.winfo_height()

            if canvas_width > 0 and canvas_height > 0:
                img_width, img_height = img.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)

                # Calcular posição para centralizar
                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2

                # Limpar canvas e mostrar imagem
                video_canvas.delete("all")
                imgtk = ImageTk.PhotoImage(image=img)
                video_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=imgtk)
                video_canvas.image = imgtk

        # Função para atualizar progresso
        def atualizar_progresso(event=None):
            nonlocal frame_atual
            if cap is not None and cap.isOpened() and total_frames > 0:
                novo_frame = int(progresso.get() * total_frames)
                cap.set(cv2.CAP_PROP_POS_FRAMES, novo_frame)
                frame_atual = novo_frame
                atualizar_tempo_label()

                # Atualizar a exibição do frame atual
                ret, frame = cap.read()
                if ret:
                    mostrar_frame(frame)
                    # Voltar para o frame atual para manter a posição
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_atual)

        progresso_barra = ttk.Scale(progresso_frame, from_=0.0, to=1.0,
                                    variable=progresso, orient=tk.HORIZONTAL,
                                    command=lambda x: atualizar_progresso())
        progresso_barra.pack(fill=tk.X, pady=(0, 5))

        # Botões de controle
        controles_frame = ttk.Frame(frame_principal, style="Tutorial.TFrame")
        controles_frame.pack(fill=tk.X, pady=(0, 10))

        # Frame para botões de controle
        botoes_frame = ttk.Frame(controles_frame, style="Tutorial.TFrame")
        botoes_frame.pack(side=tk.LEFT)

        # Função para adicionar tooltip a um botão
        def adicionar_tooltip(widget, texto):
            tooltip = ToolTip(widget, texto)
            return tooltip

        # Função para abrir vídeo
        def abrir_video():
            nonlocal cap, total_frames, duracao_total, frame_atual

            # Fechar vídeo anterior se estiver aberto
            if cap is not None and cap.isOpened():
                cap.release()

            arquivo_video = video_selecionado.get()
            # Verificar se o arquivo existe
            import os
            if not os.path.exists(arquivo_video):
                messagebox.showerror("Erro", f"O arquivo de vídeo não foi encontrado: {arquivo_video}")
                return

            # Abrir novo vídeo
            cap = cv2.VideoCapture(arquivo_video)

            if not cap.isOpened():
                messagebox.showerror("Erro", f"Não foi possível abrir o vídeo: {arquivo_video}")
                return

            # Obter informações do vídeo
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duracao_total = total_frames / fps if fps > 0 else 0
            frame_atual = 0

            # Atualizar interface
            progresso.set(0)
            atualizar_tempo_label()

            # Exibir primeiro frame
            ret, frame = cap.read()
            if ret:
                mostrar_frame(frame)

        # Função para iniciar/pausar o vídeo
        def toggle_play():
            if reproduzindo.get():
                reproduzindo.set(False)
                btn_play.config(text="▶")
            else:
                reproduzindo.set(True)
                btn_play.config(text="⏸")
                reproduzir_video()

        # Função para reproduzir o vídeo
        def reproduzir_video():
            nonlocal frame_atual

            if cap is None or not cap.isOpened():
                return

            def update_frame():
                nonlocal frame_atual

                if not reproduzindo.get():
                    return

                if cap is None or not cap.isOpened():
                    return

                ret, frame = cap.read()
                if ret:
                    # Mostrar frame
                    mostrar_frame(frame)

                    # Atualizar progresso
                    frame_atual += 1
                    if total_frames > 0:
                        progresso.set(frame_atual / total_frames)

                    # Atualizar tempo
                    atualizar_tempo_label()

                    # Agendar próximo frame
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    delay = int(1000 / fps) if fps > 0 else 33  # ~30fps padrão
                    tutorial.after(delay, update_frame)
                else:
                    # Reiniciar o vídeo ao terminar
                    frame_atual = 0
                    progresso.set(0)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    reproduzindo.set(False)
                    btn_play.config(text="▶")

                    # Mostrar primeiro frame novamente
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if ret:
                        mostrar_frame(frame)

            update_frame()

        # Funções para controle de vídeo
        def voltar_10_segundos():
            nonlocal frame_atual
            if cap is not None and cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames_a_voltar = int(fps * 10)
                novo_frame = max(0, frame_atual - frames_a_voltar)

                cap.set(cv2.CAP_PROP_POS_FRAMES, novo_frame)
                frame_atual = novo_frame
                progresso.set(frame_atual / total_frames if total_frames > 0 else 0)

                # Atualizar a exibição
                ret, frame = cap.read()
                if ret:
                    mostrar_frame(frame)
                    # Voltar para manter o frame atual
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_atual)

                atualizar_tempo_label()

        def avancar_10_segundos():
            nonlocal frame_atual
            if cap is not None and cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames_a_avancar = int(fps * 10)
                novo_frame = min(total_frames - 1, frame_atual + frames_a_avancar)

                cap.set(cv2.CAP_PROP_POS_FRAMES, novo_frame)
                frame_atual = novo_frame
                progresso.set(frame_atual / total_frames if total_frames > 0 else 0)

                # Atualizar a exibição
                ret, frame = cap.read()
                if ret:
                    mostrar_frame(frame)
                    # Voltar para manter o frame atual
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_atual)

                atualizar_tempo_label()

        def reiniciar_video():
            nonlocal frame_atual
            if cap is not None and cap.isOpened():
                reproduzindo.set(False)
                frame_atual = 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                progresso.set(0)
                btn_play.config(text="▶")

                # Atualizar a exibição
                ret, frame = cap.read()
                if ret:
                    mostrar_frame(frame)

                atualizar_tempo_label()

        # Função para mudar de vídeo
        def mudar_video(event=None):
            idx = combo_videos.current()
            video_selecionado.set(videos[idx]["arquivo"])
            abrir_video()
            if reproduzindo.get():
                reproduzir_video()

        combo_videos.bind("<<ComboboxSelected>>", mudar_video)

        # Botões de controle
        btn_back10 = ttk.Button(botoes_frame, text="⏪", style="ControlButton.TButton", width=3,
                                command=voltar_10_segundos)
        btn_back10.pack(side=tk.LEFT, padx=2)
        adicionar_tooltip(btn_back10, "Voltar 10 segundos")

        btn_play = ttk.Button(botoes_frame, text="▶", style="ControlButton.TButton", width=3,
                              command=toggle_play)
        btn_play.pack(side=tk.LEFT, padx=2)
        adicionar_tooltip(btn_play, "Reproduzir")

        btn_forward10 = ttk.Button(botoes_frame, text="⏩", style="ControlButton.TButton", width=3,
                                   command=avancar_10_segundos)
        btn_forward10.pack(side=tk.LEFT, padx=2)
        adicionar_tooltip(btn_forward10, "Avançar 10 segundos")

        btn_restart = ttk.Button(botoes_frame, text="⟲", style="ControlButton.TButton", width=3,
                                 command=reiniciar_video)
        btn_restart.pack(side=tk.LEFT, padx=2)
        adicionar_tooltip(btn_restart, "Reiniciar")

        # Controle de volume
        volume_frame = ttk.Frame(controles_frame, style="Tutorial.TFrame")
        volume_frame.pack(side=tk.RIGHT)

        volume_icon = ttk.Label(volume_frame, text="🔊", style="TutorialText.TLabel")
        volume_icon.pack(side=tk.LEFT, padx=(0, 5))

        volume_slider = ttk.Scale(volume_frame, from_=0.0, to=1.0, variable=volume,
                                  orient=tk.HORIZONTAL, length=100)
        volume_slider.pack(side=tk.LEFT)

        # Adaptar quando a janela for redimensionada
        def on_resize(event):
            if cap is not None and cap.isOpened():
                # Salvar frame atual
                atual = frame_atual
                # Obter um frame para redimensionar
                cap.set(cv2.CAP_PROP_POS_FRAMES, atual)
                ret, frame = cap.read()
                if ret:
                    mostrar_frame(frame)
                    # Voltar ao frame atual
                    cap.set(cv2.CAP_PROP_POS_FRAMES, atual)

        video_canvas.bind("<Configure>", on_resize)

        # Inicializar o vídeo após a janela ser criada
        tutorial.update()
        abrir_video()

        # Garantir que o vídeo seja fechado quando a janela for fechada
        def on_close():
            nonlocal cap
            if cap is not None and cap.isOpened():
                cap.release()
            tutorial.destroy()

        tutorial.protocol("WM_DELETE_WINDOW", on_close)

    else:
        # Mensagem de erro e instruções quando as bibliotecas não estão disponíveis
        msg_frame = ttk.Frame(frame_video, style="Tutorial.TFrame")
        msg_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(msg_frame, text="Não foi possível carregar o player de vídeo.",
                  font=("Segoe UI", 14, "bold"), foreground="#e74c3c").pack(pady=(50, 20))

        ttk.Label(msg_frame, text="Para assistir aos tutoriais, siga os passos abaixo:",
                  style="TutorialText.TLabel").pack(pady=(0, 10))

        # Instruções de instalação
        frame_instrucoes = ttk.Frame(msg_frame, style="Tutorial.TFrame")
        frame_instrucoes.pack(pady=10)

        ttk.Label(frame_instrucoes, text="1. Instale as bibliotecas necessárias usando pip:",
                  style="TutorialText.TLabel", justify=tk.LEFT).pack(anchor=tk.W)

        cmd_frame = ttk.Frame(frame_instrucoes, padding=10)
        cmd_frame.pack(fill=tk.X, pady=5)
        cmd_frame.configure(style="Tutorial.TFrame")

        cmd_text = tk.Text(cmd_frame, height=2, font=("Consolas", 10), bg="#f0f0f0",
                           fg="#333333", relief=tk.FLAT, padx=10, pady=10)
        cmd_text.pack(fill=tk.X)
        cmd_text.insert(tk.END, "pip install opencv-python pillow")
        cmd_text.config(state=tk.DISABLED)

        ttk.Label(frame_instrucoes, text="2. Reinicie o programa após a instalação",
                  style="TutorialText.TLabel", justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

        ttk.Label(frame_instrucoes, text="3. Se o problema persistir, acesse o suporte técnico",
                  style="TutorialText.TLabel", justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

        # Botão para copiar comando
        def copiar_comando():
            tutorial.clipboard_clear()
            tutorial.clipboard_append("pip install opencv-python pillow")
            btn_copiar.config(text="✓ Copiado!")
            tutorial.after(2000, lambda: btn_copiar.config(text="Copiar Comando"))

        btn_copiar = ttk.Button(frame_instrucoes, text="Copiar Comando", command=copiar_comando)
        btn_copiar.pack(anchor=tk.W, pady=10)

    # Frame inferior com botões de ação
    frame_acoes = ttk.Frame(frame_principal, style="Tutorial.TFrame")
    frame_acoes.pack(fill=tk.X, pady=(10, 0))

    # Botão para documentação em PDF
    def abrir_documentacao():
        import webbrowser
        import os
        pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs.pdf")
        if os.path.exists(pdf_path):
            webbrowser.open('file://' + pdf_path)
        else:
            messagebox.showinfo("Documentação", "O arquivo de documentação não foi encontrado.")

    btn_documentacao = ttk.Button(frame_acoes, text="📄 Documentação Completa",
                                  command=abrir_documentacao)
    btn_documentacao.pack(side=tk.LEFT, padx=(0, 10))

    # Botão para fechar
    botao_fechar = ttk.Button(frame_acoes, text="Fechar Tutorial", command=tutorial.destroy)
    botao_fechar.pack(side=tk.RIGHT)

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
        ("Importante", "Quanto maior o tamanho do arquivo e/ou pasta, maior é o uso da capacidade do computador."),
        ("Prática", "Para melhor segurança, gere uma nova chave a cada três meses."),
        ("Prática", "Crie uma rotina regular de backup e criptografia para seus dados importantes."),
        ("Prática", "Utilize as funcionalidades do Código Morse para comunicar-se em aúdio com privacidade."),
        ("Eficiência", "Use a função 'Criptografar Pasta' para processar múltiplos arquivos de uma vez."),
        ("Eficiência", "Organize arquivos em pastas por categoria antes de criptografá-los em lote."),
        ("Eficiência", "Confira os atalhos de Tecla."),
        ("Análise", "Acompanhe os seus movimentos de criptografia pelo histórico."),
        ("Análise", "Confira as estatísticas para acompanhar o uso do sistema e identificar padrões."),
        ("Análise", "Exporte os dados estatísticos de criptografia para seu relatório."),
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

    dicas.bind("<Escape>", lambda event: dicas.destroy())

def enviar_email_relatorio(titulo, descricao, passos, incluir_logs, email_usuario=None):
    # Configurações de email
    remetente = "seu_email@gmail.com"
    destinatario = "conatustechlogies@gmail.com"
    senha = "xxxxxxxxxx"

    # Criando a mensagem
    msg = MIMEMultipart()
    msg['From'] = email_usuario if email_usuario else remetente
    msg['To'] = destinatario
    msg['Subject'] = f"Relatório de Bug: {titulo}"

    # Corpo do email
    corpo = f"""
    Relatório de Bug:

    Título: {titulo}

    Descrição:
    {descricao}

    Passos para Reproduzir:
    {passos}

    Enviado por: {email_usuario if email_usuario else "Usuário não identificado"}
    Logs incluídos: {'Sim' if incluir_logs else 'Não'}
    """

    # Se incluir_logs for True, poderia adicionar os logs aqui
    if incluir_logs:
        try:
            corpo += "\n\nLogs do sistema:\n"
        except Exception as e:
            corpo += f"\n\nErro ao obter logs: {str(e)}"

    msg.attach(MIMEText(corpo, 'plain'))

    try:
        # Conectando ao servidor SMTP do Gmail
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha)

        # Enviando email
        texto = msg.as_string()
        servidor.sendmail(remetente, destinatario, texto)
        servidor.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False

# Variáveis globais para armazenar informações de login
usuario_logado = False
email_usuario_logado = ""

def verificar_login(email, senha, janela_login):
    global usuario_logado, email_usuario_logado

    if email and "@" in email and senha:  # Validação básica
        usuario_logado = True
        email_usuario_logado = email
        tk.messagebox.showinfo("Login", "Login realizado com sucesso!")
        janela_login.destroy()
        return True
    else:
        tk.messagebox.showerror("Erro", "Email ou senha inválidos.")
        return False

def mostrar_janela_login(callback):
    login = tk.Toplevel(janela)
    login.title("Login")
    login.geometry("400x250")
    login.transient(janela)
    login.grab_set()

    frame_login = ttk.Frame(login, padding=15)
    frame_login.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame_login, text="Login", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 15))

    ttk.Label(frame_login, text="Email:").pack(anchor="w", pady=(10, 5))
    email_entry = ttk.Entry(frame_login, width=40)
    email_entry.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(frame_login, text="Senha:").pack(anchor="w", pady=(5, 5))
    senha_entry = ttk.Entry(frame_login, width=40, show="*")
    senha_entry.pack(fill=tk.X, pady=(0, 15))

    frame_botoes = ttk.Frame(frame_login)
    frame_botoes.pack(fill=tk.X, pady=(10, 0))

    def processar_login():
        email = email_entry.get()
        senha = senha_entry.get()
        if verificar_login(email, senha, login):
            callback()

    def cancelar():
        login.destroy()

    ttk.Button(frame_botoes, text="Cancelar", command=cancelar).pack(side=tk.RIGHT, padx=5)
    ttk.Button(frame_botoes, text="Entrar", command=processar_login).pack(side=tk.RIGHT, padx=5)

    # Opção para continuar sem login
    ttk.Separator(frame_login, orient="horizontal").pack(fill=tk.X, pady=15)

    def continuar_sem_login():
        login.destroy()
        callback()

    ttk.Button(frame_login, text="Continuar sem login",
               command=continuar_sem_login, style="Link.TButton").pack(pady=5)

def reportar_bug():
    def abrir_formulario_bug():
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

        # Mostrar informação do usuário logado
        if usuario_logado:
            ttk.Label(frame_principal, text=f"Logado como: {email_usuario_logado}",
                      font=("Arial", 10, "italic")).pack(anchor="w", pady=(0, 10))

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

        def processar_envio():
            titulo = titulo_bug.get()
            descricao = descricao_bug.get("1.0", tk.END)
            passos = passos_bug.get("1.0", tk.END)
            incluir_logs = var_logs.get()

            # Verificar se os campos essenciais estão preenchidos
            if not titulo.strip():
                tk.messagebox.showerror("Erro", "Por favor, informe um título para o problema.")
                return

            if not descricao.strip():
                tk.messagebox.showerror("Erro", "Por favor, descreva o problema.")
                return

            # Enviar email, incluindo email do usuário se estiver logado
            email_para_envio = email_usuario_logado if usuario_logado else None
            sucesso = enviar_email_relatorio(titulo, descricao, passos, incluir_logs, email_para_envio)

            if sucesso:
                tk.messagebox.showinfo("Relatório Enviado",
                                       "Obrigado! Seu relatório foi enviado com sucesso.")
                bug.destroy()
            else:
                tk.messagebox.showerror("Erro",
                                        "Não foi possível enviar o email. Verifique as configurações ou tente novamente mais tarde.\n \n Caso o erro persista envie um e-mail para \n conatustechnologies@gmail.com")

        # Botões
        ttk.Button(frame_botoes, text="Cancelar", command=bug.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botoes, text="Enviar Relatório", command=processar_envio).pack(side=tk.RIGHT, padx=5)

    # Primeiro mostra a tela de login, depois abre o formulário
    mostrar_janela_login(abrir_formulario_bug)

# Definir um estilo de botão de link (adicione no início do programa, após inicializar ttk)
def configurar_estilos():
    estilo = ttk.Style()
    estilo.configure("Link.TButton", foreground="blue", background=None, font=("Arial", 9, "underline"))

    configurar_estilos()

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
            status_label.config(text="Você já possui a versão mais recente (1.1.1)")
            ttk.Button(frame, text="Fechar",
                       command=atualiza.destroy).pack(pady=20)

    atualizar_progresso()

def mostrar_sobre():
    sobre = tk.Toplevel(janela)
    sobre.title("Sobre o CryptographiE")
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

    tk.Label(info_frame, text="CryptographiE",
             font=("Arial", 16, "bold"), fg="white", bg="#2c3e50").pack(anchor="center")
    tk.Label(info_frame, text="Versão 1.1.1",
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

    descricao_text = """O CryptographiE é uma aplicação de segurança projetada para proteger seus dados pessoais e arquivos contra acesso não autorizado.

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
        "Interface gráfica prática e intuitiva",
        "Processamento em lote de múltiplos arquivos",
        "Geração de chaves seguras",
        "Estatísticas detalhadas de uso",
        "Compatibilidade com vários formatos de arquivo",
        "Operação em modo offline para maior segurança",
        "Comunicação em aúdio através do Código Morse"
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
    tk.Label(tab_creditos, text="CONATUS Technologies - conatustechnologies@gmail.com",
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

    separador = tk.Frame(tab_creditos, height=2, bg="gray")
    separador.pack(fill="x", padx=20, pady=10)


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
    # URL do site do seu aplicativo
    url = "https://brisashumanas.blogspot.com/" #site provósirio

    try:
        # Abre o URL no navegador padrão
        webbrowser.open(url)
    except Exception as e:
        # Em caso de erro, exibe uma mensagem
        messagebox.showerror("Erro", f"Não foi possível abrir o site: {e}")

# Vincular teclas de atalho
janela.bind("<F1>", lambda event: mostrar_ajuda())
janela.bind("<F2>", lambda event: mostrar_tutorial())
janela.bind("<F3>", lambda event: mostrar_dicas())
janela.bind("<F4>", lambda event: reportar_bug())
janela.bind("<F5>", lambda event: verificar_atualizacoes())
janela.bind("<F6>", lambda event: mostrar_sobre())
janela.bind("<F7>", lambda event: abrir_website())

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
