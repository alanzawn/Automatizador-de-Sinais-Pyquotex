import os
os.system("pip install -r requirements.txt")
os.system("pip install customtkinter")
os.system("pip install telethon")
os.system("pip install playwright")
os.system("playwright install")
os.system("cls")

import asyncio
import configparser
import shutil
import subprocess
import threading
import time
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
#from pyquotex import app
import re

# Diretório do arquivo de configuração
base_dir = Path(__file__).parent
config_path = Path(os.path.join(base_dir, "settings/config.ini"))

# Configurar o CustomTkinter
ctk.set_appearance_mode("Dark")  # "Light" ou "Dark"
ctk.set_default_color_theme("blue")  # azul, escuro ou claro

# Limpar o arquivo de dados ao iniciar o script
with open("dados.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write("=== Dados das Operações ===\n")
    arquivo.write("O arquivo foi resetado no início da execução.\n\n")
print("Arquivo 'dados.txt' foi limpo.")

#os.system("python login.py")

# Função para salvar o arquivo de configuração
def save_config(email, password):
    # Criar o diretório "settings" se ele não existir
    config_dir = config_path.parent  # Diretório "settings"
    config_dir.mkdir(exist_ok=True, parents=True)  # Cria o diretório, se necessário

    # Conteúdo do arquivo de configuração
    text_settings = (
        f"[settings]\n"
        f"email={email}\n"
        f"password={password}\n"
    )
    # Salva o arquivo "config.ini" no diretório "settings"
    config_path.write_text(text_settings, encoding="utf-8")


# Classe para a janela de Login
class LoginWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Login Quotex")
        self.root.geometry("400x300")

        # Título
        self.title_label = ctk.CTkLabel(self.root, text="Login Quotex", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # Campo de email
        self.email_label = ctk.CTkLabel(self.root, text="Email:")
        self.email_label.pack(pady=5)
        self.email_entry = ctk.CTkEntry(self.root, width=300)
        self.email_entry.pack(pady=5)

        # Campo de senha
        self.password_label = ctk.CTkLabel(self.root, text="Senha:")
        self.password_label.pack(pady=5)
        self.password_entry = ctk.CTkEntry(self.root, width=300, show="*")
        self.password_entry.pack(pady=5)

        # Botão para entrar
        self.login_button = ctk.CTkButton(self.root, text="Entrar", command=self.login)
        self.login_button.pack(pady=20)

        self.root.mainloop()

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        # Validação dos campos de entrada
        if not email or not password:
            messagebox.showerror("Erro", "Por favor, preencha ambos os campos!")
            return

        # Salva as configurações no arquivo
        save_config(email, password)
        messagebox.showinfo("Sucesso", "Login salvo com sucesso!")
        self.root.destroy()  # Fecha a janela de login
        MainWindow(email=email)  # Abre a janela principal, passando o email

# Classe para a tela principal
class MainWindow:
    def __init__(self, email=None):
        self.root = ctk.CTk()
        self.root.title("Tela Principal")
        self.root.geometry("400x300")

        # Título
        self.title_label = ctk.CTkLabel(self.root, text="Tela Principal", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # Mensagem com o email
        if email:
            self.email_label = ctk.CTkLabel(self.root, text=f"Conectado como {email}", font=ctk.CTkFont(size=14))
            self.email_label.pack(pady=10)

        # Botões
        self.connect_button = ctk.CTkButton(self.root, text="Conectar", command=self.run_conectar)
        self.connect_button.pack(pady=10)

        self.change_account_button = ctk.CTkButton(self.root, text="Trocar Conta", command=self.trocar_conta)
        self.change_account_button.pack(pady=10)

        self.exit_button = ctk.CTkButton(self.root, text="Sair", command=self.sair)
        self.exit_button.pack(pady=10)

        self.root.mainloop()

    def run_conectar(self):
        """Executa a conexão como uma tarefa assíncrona."""
        try:
            asyncio.run(self.conectar())
        except RuntimeError as e:
            messagebox.showerror("Erro", "Erro ao inicializar o sistema de conexão.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    async def conectar(self):
        """Função que lida com a conexão assíncrona."""
        loading_window = LoadingWindow("Conectando...")
        try:
            # Tenta iniciar a conexão (mock do `app.connect`).
            from quotexapi.config import (
                email,
                password
            )
            from quotexapi.stable_api import Quotex
            global client
            client = Quotex(
                email=email,
                password=password,
                lang="pt",  # Default pt -> Português.
            )

            check, reason = await client.connect()

            # Atualiza a mensagem na janela de loading
            if check:
                loading_window.update_message("Conectado com sucesso!")
                loading_window.show_ok_button()  # Habilita o botão "OK" para o usuário

                # Função adicional para abrir AutomatizadorWindow após "OK"
                def abrir_automatizador():
                    loading_window.close()  # Fecha a janela de loading
                    self.root.destroy()  # Fecha a Janela Principal
                    AutomatizadorWindow()  # Abre a nova janela para o Automatizador

                # Substitui o botão "OK" da janela de loading
                loading_window.ok_button.configure(command=abrir_automatizador)
            else:
                # Caso não conectado, mostra erro
                loading_window.update_message(f"Falha na conexão: {reason}")
                loading_window.show_ok_button()  # Permite o usuário fechar após erro
        except Exception as e:
            # Mostra a mensagem de erro no popup
            loading_window.update_message(f"Erro ao conectar: {str(e)}")
            loading_window.show_ok_button()  # Permite o usuário fechar após ver a mensagem de erro

    def trocar_conta(self):
        # Apagar o diretório "settings" com todo o seu conteúdo, se ele existir
        settings_dir = config_path.parent  # Diretório "settings"
        if settings_dir.exists() and settings_dir.is_dir():
            shutil.rmtree(settings_dir)  # Remove o diretório e todo o conteúdo

        # Deleta o arquivo de sessão (session.json)
        session_file_path = base_dir / "session.json"
        if session_file_path.exists():
            session_file_path.unlink()

        # Fecha a janela principal e retorna para a janela de Login
        self.root.destroy()
        LoginWindow()

    def sair(self):
        self.root.destroy()

# Classe da tela de espera de conexão (sim, eu criei uma tela e não um popup ;-;)
class LoadingWindow:
    def __init__(self, initial_message):
        self.window = ctk.CTk()
        self.window.title("Carregando")
        self.window.geometry("300x150")

        # Mensagem inicial
        self.message_label = ctk.CTkLabel(self.window, text=initial_message, font=ctk.CTkFont(size=14))
        self.message_label.pack(pady=20)

        # Botão OK (inicia desabilitado)
        self.ok_button = ctk.CTkButton(self.window, text="OK", command=self.close, state="disabled")
        self.ok_button.pack(pady=20)

        self.window.update()

    def update_message(self, new_message):
        """Atualiza a mensagem exibida no popup."""
        self.message_label.configure(text=new_message)
        self.window.update()

    def show_ok_button(self):
        """Habilita o botão OK para permitir fechar o popup."""
        self.ok_button.configure(state="normal")  # Ativa o botão OK
        self.window.update()

    def close(self):
        """Fecha a janela do LoadingWindow."""
        self.window.update_idletasks()  # Garante que tarefas pendentes sejam concluídas
        self.window.destroy()


async def get_balance(conta=int):
    check_connect, message = await client.connect()
    if check_connect:
        if conta == 1:
            print("Saldo corrente: ", round(float(await client.get_balance()), 2))
        elif conta == 2:
            client.change_account("REAL")
            print("Saldo corrente: ", round(float(await client.get_balance()), 2))

        """print("Saindo...")

        #client.close()"""
        banca = round(float(await client.get_balance()), 2)
        return banca

# Função para salvar as configurações
async def salvar_configuracoes(tipo_conta, payout_minimo, take_profit, stop_loss_1, lote):
    global client
    try:
        # Pegando o valor da conta selecionada pelos radio buttons
        tipo_conta_valor = tipo_conta.get()  # Vai retornar 1 (Demo) ou 2 (Real)
        tipo_conta_valor = int(tipo_conta_valor)
        print(tipo_conta_valor)

        # Verifique o valor retornado pelos radio buttons
        if tipo_conta_valor not in [1, 2]:
            raise ValueError("Tipo de conta inválido! Selecione Conta Demo ou Conta Real.")
        else:
            # Aqui é presumido que "main.get_balance" é parte da sua lógica assíncrona para obter o saldo
            if tipo_conta_valor == 2: # CONTA REAL
                client.change_account("REAL")
                capital = await get_balance(tipo_conta_valor)
            else:
                capital = await get_balance(tipo_conta_valor)

        # Pegando os valores dos campos de entrada e chamando get_balance com o valor correto
        configuracoes = {
            "tipo_conta": tipo_conta_valor,
            "capital_inicial": capital,  # Passa 1 ou 2 aqui
            "payout_minimo": payout_minimo,
            "tipo_gerenciamento": 1,
            "gerenciamento": "mao fixa",
            "tipo_takeprofit": 1,
            "take_profit": take_profit,
            "take_valor": round(capital + float(take_profit), 2),
            "tipo_stoploss": 1,
            "stop_loss": stop_loss_1,
            "stop_valor": round(capital - float(stop_loss_1), 2),
            "usar_martingale": 1,
            "usar_trailingStop": 1,
            "valor_inicial_operacao": lote,
            "break": "false",
        }


        # Conteúdo a ser salvo no arquivo
        conteudo = "==================================================\n"
        conteudo += "Configuracoes do Robo de Operacoes\n"
        conteudo += "==================================================\n"
        for chave, valor in configuracoes.items():
            conteudo += f"{chave}: {valor}\n"
        conteudo += "==================================================\n"

        # Salvando em um arquivo
        with open("configuracoes.txt", "w") as arquivo:
            arquivo.write(conteudo)

        print("Configurações salvas com sucesso!")
        return configuracoes  # Indica sucesso

    except ValueError as e:
        print(f"Erro: {e}")
        return False  # Indica falha
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        return False  # Indica falha


# Função para desativar os inputs após salvar
def desativar_inputs(conta_demo_radio, conta_real_radio, widgets, salvar_button=None):
    """
    Desativa os radio buttons, campos configuráveis e o botão Salvar após salvar.
    """
    # Desativando os radio buttons
    conta_demo_radio.configure(state="disabled")
    conta_real_radio.configure(state="disabled")

    # Desativa os outros widgets (payout_minimo, take_profit, etc.)
    for widget in widgets:
        widget.configure(state="disabled")

    # Desativa o botão "Salvar", se fornecido
    if salvar_button:
        salvar_button.configure(state="disabled")







# Classe para a tela principal do automatizador
class AutomatizadorWindow:
    def __init__(self):
        # Configurações gerais da aplicação
        self.threads_ativas = []
        self.subprocessos = []
        self.dados_path = Path(__file__).parent / "dados.txt"
        #self.saldo_inicial = 0
        self.saldo_atual = 0
        self.labels_valores = {}
        self.tipo_conta = None
        self.payout_minimo_entry = None
        self.take_profit_entry = None
        self.stop_loss_1_entry = None
        self.lote_entry = None
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Criando a janela principal
        self.janela = ctk.CTk()
        self.janela.title("Automatizador de Sinais - Projeto PyquotexBot")
        self.janela.geometry("1000x500")

        # Configurando o evento de fechamento da janela
        self.janela.protocol("WM_DELETE_WINDOW", self.on_close)

        # Título do Projeto
        self.titulo_label = ctk.CTkLabel(self.janela, text="Automatizador Pyquotex", font=("Arial", 24))
        self.titulo_label.pack(pady=10)

        # Área principal da janela (estrutura com 3 frames)
        self.frame_principal = ctk.CTkFrame(self.janela)
        self.frame_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame 1: Configurações (lado esquerdo)
        self.frame_configuracoes()

        # Frame 2: Área central (conteúdo principal)
        self.frame_central()

        # Frame 3: Lado direito (informações adicionais ou saídas)
        self.frame_direito()

        # Exibir a janela
        self.janela.mainloop()

    def limpar_saida(self):
        """
        Limpa o conteúdo da caixa de texto que exibe o output do script.
        """
        self.saida_text.delete("1.0", "end")  # Remove todo conteúdo do widget


    def frame_configuracoes(self):
        """Frame 1: Configurações"""
        self.frame_config = ctk.CTkFrame(self.frame_principal, width=210)
        self.frame_config.pack(side="left", fill="y", padx=10, pady=10)

        # Configurações título
        config_label = ctk.CTkLabel(self.frame_config, text="Configurações", font=("Arial", 16))
        config_label.pack(pady=10)

        # Seletor para Tipo de Conta (demo ou real)
        self.tipo_conta = ctk.IntVar(value=1)  # Valor padrão: 1 (Conta Demo)
        self.conta_demo_radio = ctk.CTkRadioButton(self.frame_config, text="Conta Demo", variable=self.tipo_conta, value=1)
        self.conta_demo_radio.pack(pady=5)
        self.conta_real_radio = ctk.CTkRadioButton(self.frame_config, text="Conta Real", variable=self.tipo_conta, value=2)
        self.conta_real_radio.pack(pady=5)

        # Entradas para Payout, Take Profit, Stop Loss e Lote
        self.payout_minimo_entry = ctk.CTkEntry(self.frame_config, placeholder_text="Payout Mínimo (%)")
        self.payout_minimo_entry.pack(pady=5)

        self.take_profit_entry = ctk.CTkEntry(self.frame_config, placeholder_text="Take Profit (R$)")
        self.take_profit_entry.pack(pady=5)

        self.stop_loss_1_entry = ctk.CTkEntry(self.frame_config, placeholder_text="Stop Loss (R$)")
        self.stop_loss_1_entry.pack(pady=5)

        self.lote_entry = ctk.CTkEntry(self.frame_config, placeholder_text="Valor por Operação (R$)")
        self.lote_entry.pack(pady=5)

        # Botão Salvar Configurações
        self.salvar_button = ctk.CTkButton(self.frame_config, text="SALVAR", command=self.salvar_configuracoes_sync)
        self.salvar_button.pack(pady=10)

        # Label de mensagem de status
        self.mensagem_label = ctk.CTkLabel(self.frame_config, text="", font=("Arial", 12))
        self.mensagem_label.pack(pady=5)

    def frame_central(self):
        """Frame 2: Botão de iniciar e saída de informações"""
        self.frame_central = ctk.CTkFrame(self.frame_principal)
        self.frame_central.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Botão Iniciar
        self.iniciar_button = ctk.CTkButton(self.frame_central, text="Iniciar", command=self.iniciar_processamento)
        self.iniciar_button.pack(pady=20)

        # Widget de texto para exibir a saída do script
        self.saida_text = ctk.CTkTextbox(self.frame_central, width=500, height=300)
        self.saida_text.pack(pady=10, padx=10)

    def frame_direito(self):
        """Frame 3: Informações adicionais atualizadas dinamicamente"""
        self.frame_direita = ctk.CTkFrame(self.frame_principal, width=210)
        self.frame_direita.pack(side="left", fill="y", padx=10, pady=10)

        self.atualizar_saldo_inicial()

        # Título do Frame Direito
        direita_label = ctk.CTkLabel(self.frame_direita, text="Resumo", font=("Arial", 16))
        direita_label.pack(pady=10)

        # Labels associadas às informações do arquivo de dados.
        infos = [
            "Saldo Atual",
            "Lucro/Prejuízo Total",
            "Entradas Totais",
            "Wins",
            "Losses"
        ]

        # Criar as labels no frame direito
        for info in infos:
            # Label título
            titulo_label = ctk.CTkLabel(self.frame_direita, text=info, font=("Arial", 14))
            titulo_label.pack(pady=5)

            # Label valor (inicialmente "0")
            valor_label = ctk.CTkLabel(self.frame_direita, text="0", font=("Arial", 14))
            valor_label.pack(pady=5)

            # Armazena a referência para atualização
            self.labels_valores[info] = valor_label

        # Iniciar o monitoramento do arquivo de dados
        threading.Thread(target=self.monitorar_dados, daemon=True).start()

    def string_para_float(self, valor_str):
        """
        Converte uma string representando um número (em formato brasileiro ou internacional)
        para um número float. Exemplo:
            "1.234,56" -> 1234.56
            "1234.56" -> 1234.56
        :param valor_str:
        :param self: Valor em string a ser convertido.
        :return: Float correspondente ao valor ou None para entradas inválidas.
        """
        try:
            # Remove qualquer caractere que não seja número, vírgula ou ponto
            valor_limpo = re.sub(r"[^\d,\.]", "", valor_str)

            # Se existir tanto vírgula quanto ponto, decide pelo separador decimal
            if ',' in valor_limpo and '.' in valor_limpo:
                # Se o ponto aparece antes da vírgula, o ponto é separador de milhares
                if valor_limpo.index(',') > valor_limpo.index('.'):
                    valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
                else:
                    valor_limpo = valor_limpo.replace(',', '')

            # Se houver apenas vírgula, substitui por ponto (formato brasileiro para float)
            elif ',' in valor_limpo:
                valor_limpo = valor_limpo.replace(',', '.')

            # Converte a string limpa para float
            return float(valor_limpo)
        except ValueError:
            # Retorna None em caso de erro
            print(f"Erro ao converter '{self}' para float.")
            return None

    def atualizar_saldo_inicial(self):
        """Define o saldo inicial com base no arquivo dados.txt."""
        try:
            if not os.path.exists(self.dados_path):
                print(f"Arquivo {self.dados_path} não encontrado.")
                return

            with open(self.dados_path, "r") as arquivo:
                linhas = arquivo.readlines()

            for linha in linhas:
                linha = linha.strip()
                if linha.startswith("Saldo Atual:"):
                    _, valor = linha.split(":", 1)
                    valor = valor.replace("R$", "").strip()  # Remove o prefixo monetário
                    self.saldo_inicial = self.string_para_float(str(valor))  # Converte usando string_para_float
                    self.saldo_atual = self.saldo_inicial  # Inicializa o saldo atual
                    print(f"Saldo inicial definido: {self.saldo_inicial}")
                    break

        except Exception as e:
            print(f"Erro ao inicializar saldo inicial: {e}")

    def monitorar_dados(self):
        """Monitorar alterações no arquivo dados.txt para atualizar os valores das labels."""
        # Dicionário para armazenar os valores anteriores
        valores_atuais = {
            "Saldo Atual": "0",
            "Lucro/Prejuízo Total": "0",
            "Entradas Totais": "0",
            "Wins": "0",
            "Losses": "0"
        }

        while True:
            try:
                # Verifica se o arquivo existe
                if not os.path.exists(self.dados_path):
                    print(f"Arquivo {self.dados_path} não encontrado. Monitorando novamente em 1s...")
                    time.sleep(1)
                    continue

                # Lê o conteúdo do arquivo
                with open(self.dados_path, "r") as arquivo:
                    linhas = arquivo.readlines()

                # Iterar pelas linhas do arquivo para atualizar os valores
                for linha in linhas:
                    linha = linha.strip()  # Remove espaços ao redor da linha

                    # Ignorar o cabeçalho ou linhas vazias
                    if linha.startswith("===") or not linha:
                        continue

                    # Extrai a chave e o valor se a linha contiver ":"
                    if ":" in linha:
                        chave, valor = linha.split(":", 1)  # Divide apenas na primeira ocorrência de ":"
                        chave = chave.strip()
                        valor = valor.replace("R$", "").strip()  # Remove o "R$" dos valores, se presente

                        # Tratar "Saldo Atual" separadamente
                        if chave == "Saldo Atual":
                            # Converte para float usando a função `string_para_float`
                            self.saldo_atual = self.string_para_float(valor)

                            # Log para depuração
                            print(f"Saldo atual atualizado: {self.saldo_atual}")
                            # Atualiza a label correspondente
                            valores_atuais[chave] = f"R${self.saldo_atual:.2f}"
                            self.labels_valores[chave].configure(text=valores_atuais[chave])

                        # Atualizar automaticamente "Lucro/Prejuízo Total"
                        if "Saldo Atual" in valores_atuais and self.saldo_inicial is not None:
                            lucro_prejuizo_total = self.saldo_atual - self.saldo_inicial
                            valores_atuais[
                                "Lucro/Prejuízo Total"] = f"R${lucro_prejuizo_total:.2f}"  # Formatação monetária
                            self.labels_valores["Lucro/Prejuízo Total"].configure(
                                text=valores_atuais["Lucro/Prejuízo Total"]
                            )

                            # Log para depuração
                            print(f"Lucro/Prejuízo Total atualizado: {lucro_prejuizo_total}")

                        # Para qualquer outro campo, simplesmente atualiza a label
                        if chave in valores_atuais:
                            valores_atuais[chave] = valor  # Atualiza o valor atual
                            self.labels_valores[chave].configure(text=valor)  # Atualiza a label na interface

            except Exception as e:
                print(f"Erro ao monitorar dados: {e}")
                exit()

            # Espera 1 segundo antes de verificar novamente
            time.sleep(1)

    # Função para executar o script teste.py
    def iniciar_processamento(self):
        """Executa o script teste.py e captura suas saídas."""
        # Desativa o botão para evitar múltiplos cliques
        self.iniciar_button.configure(state="disabled")

        # Limpa a saída anterior
        self.saida_text.delete("1.0", "end")

        # Executa o script em uma thread separada
        threading.Thread(target=self.executar_script).start()

    def executar_script(self):
        """Roda o script usando subprocess e exibe suas saídas em tempo real."""
        try:
            # Comando para executar o script `teste.py`
            with subprocess.Popen(
                    ["python", "teste.py"],  # Ajuste se necessário (python3 para sistemas UNIX).
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
            ) as processo:
                # Lê cada linha da saída do script em tempo real
                for linha in processo.stdout:
                    if "[CLEAR_SCREEN]" in linha:  # Detecta sinal do comando de 'cls'
                        self.limpar_saida()  # Limpa a caixa de texto
                    else:
                        # Atualiza o widget de texto com a saída
                        self.saida_text.insert("end", linha)
                        self.saida_text.see("end")  # Rola até o final do texto automaticamente

                # Lê as mensagens de erro, se houver
                for linha_erro in processo.stderr:
                    self.saida_text.insert("end", f"ERRO: {linha_erro}")
                    self.saida_text.see("end")  # Rola até o final

                # Verifica o código de saída do processo
                retorno = processo.wait()
                if retorno != 0:  # Se o processo terminou com erro.
                    self.saida_text.insert("end", f"Script terminou com erro. Código: {retorno}\n")
                else:
                    self.saida_text.insert("end", "Script concluído com sucesso.\n")

        except Exception as e:
            # Exibindo erro geral na GUI
            messagebox.showerror("Erro", f"Erro ao executar o script: {e}")
        finally:
            # Ativando novamente o botão após o processo completar
            self.iniciar_button.configure(state="normal")

    def salvar_configuracoes_sync(self):
        """Salva configurações (vinculado ao botão 'Salvar')"""
        try:
            # Pegar os valores inseridos pelo usuário usando `.get()`
            tipo_conta = self.tipo_conta  # RadioButton já retorna o valor
            payout_minimo = self.payout_minimo_entry.get()
            take_profit = self.take_profit_entry.get()
            stop_loss_1 = self.stop_loss_1_entry.get()
            lote = self.lote_entry.get()

            # Executa o salvamento das configurações e captura o dicionário retornado
            configuracoes = asyncio.run(salvar_configuracoes(
                tipo_conta,
                payout_minimo,
                take_profit,
                stop_loss_1,
                lote
            ))

            if configuracoes:
                # Atualizar `self.saldo_inicial` com o valor retornado
                self.saldo_inicial = configuracoes["capital_inicial"]


                # Garante que o saldo atual está formatado corretamente
                saldo_formatado = f"{self.saldo_inicial:.2f}".replace('.', ',')

                # Salvar os dados no arquivo
                with open("dados.txt", "w", encoding="utf-8") as arquivo:
                    arquivo.write("=== Dados das Operações ===\n")
                    arquivo.write(f"Saldo Atual: R$ {saldo_formatado}\n")
                    arquivo.write(f"Lucro/Prejuízo Total: R$ 0,00\n")
                    arquivo.write(f"Entradas Totais: 0\n")
                    arquivo.write(f"Wins: 0\n")
                    arquivo.write(f"Losses: 0\n")
                print("Arquivo de dados atualizado.")

                # Desativa os inputs e mostra mensagem de sucesso
                desativar_inputs(
                    self.conta_demo_radio,  # Agora passando a referência correta
                    self.conta_real_radio,  # Agora passando a referência correta
                    [self.payout_minimo_entry, self.take_profit_entry, self.stop_loss_1_entry, self.lote_entry, self.salvar_button]
                )
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            else:
                messagebox.showerror("Erro", "Falha ao salvar as configurações.")
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

    def on_close(self):
        """Evento disparado ao fechar a janela."""
        if messagebox.askokcancel("Sair", "Tem certeza que deseja fechar a aplicação?"):
            # Finalizar subprocessos
            for processo in self.subprocessos:
                if processo.poll() is None:  # Verifica se o subprocesso ainda está rodando
                    processo.terminate()  # Encerra o processo
                    processo.wait()  # Aguarda o término

            # Encerrar threads de monitoramento
            self.executando = False  # Para o loop das threads
            for thread in self.threads_ativas:
                if thread.is_alive():
                    thread.join()  # Aguarda o término seguro das threads

            # Fechar a janela
            self.janela.destroy()


# Lógica Principal
if __name__ == "__main__":
    # Caminho do arquivo de sessão
    session_file_path = base_dir / "session.json"

    # Definição padrão para credenciais (nula inicialmente)
    email = None
    password = None

    # Verificação: Ambos os arquivos de configuração (config.ini e session.json)
    if config_path.exists():
        # Tenta carregar o conteúdo do config.ini
        config = configparser.ConfigParser(interpolation=None)
        config.read(config_path, encoding="utf-8")

        email = config.get("settings", "email", fallback=None)
        password = config.get("settings", "password", fallback=None)

    # Regra: Se qualquer dos arquivos (config.ini ou session.json) não existe ou as credenciais estão ausentes
    if not config_path.exists() or not session_file_path.exists() or not email or not password:
        # Força a abertura da janela de login
        LoginWindow()
    else:
        # Se tudo estiver correto, inicia a janela principal
        MainWindow(email=email)
