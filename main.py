# Importações Básicas
import os
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from multiprocessing.connection import Listener
from tkinter import messagebox
from telethon import TelegramClient, events
from quotexapi.config import email, password
from quotexapi.stable_api import Quotex
import customtkinter as ctk
import configparser
import threading
import time
import shutil
import subprocess
import re

# Configurar o CustomTkinter
ctk.set_appearance_mode("Dark")  # Tema escuro para a interface
ctk.set_default_color_theme("blue")  # Cor padrão: azul

# Variáveis Globais (Telegram e Quotex)
API_ID = 29960482
API_HASH = '447e76f37431dc029c90f594fd8b1cab'
SALA = 1002310421815  # ID do grupo Telegram
quotex_client = Quotex(email=email, password=password, lang="pt")

# Inicializações Globais de Operações
saldo_atual = 0
soma_lucro_prejuizo = 0
total_entradas = 0
total_win = 0
total_loss = 0

# Caminho para a configuração e dados
base_dir = Path(__file__).parent
config_path = Path(os.path.join(base_dir, "settings/config.ini"))
dados_path = Path(base_dir / "dados.txt")

# Função para limpar e resetar o arquivo 'dados.txt' ao iniciar
with open(dados_path, "w", encoding="utf-8") as arquivo:
    arquivo.write("=== Dados das Operações ===\n")
    arquivo.write("O arquivo foi resetado no início da execução.\n\n")
print("Arquivo 'dados.txt' foi limpo.")

async def configurar_quotex():
    """
    Tenta conectar ao Quotex e retorna o estado da conexão.
    """
    global quotex_client
    check, reason = await quotex_client.connect()
    if not check:
        print(f"Erro ao conectar ao Quotex: {reason}")
        return False
    print("Conexão com a Quotex estabelecida com sucesso!")
    return True


async def configurar_telegram():
    """
    Inicializa o cliente do Telegram e retorna a instância.
    """
    telegram_client = TelegramClient("session_name", API_ID, API_HASH)
    await telegram_client.start()
    print("Cliente Telegram conectado com sucesso!")
    return telegram_client

async def processar_sinal(telegram_client, mensagem):
    """
    Processa o sinal recebido do Telegram e executa a operação agendada.
    """
    global saldo_atual, soma_lucro_prejuizo, total_entradas, total_win, total_loss

    if "🚨" in mensagem and "⏰" in mensagem:
        try:
            ativo = mensagem.split("🏆")[1].split("\n")[0].strip()
            horario_str = mensagem.split("⏰")[1].split("\n")[0].strip()
            horario_entrada = datetime.strptime(horario_str, "%H:%M").replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )

            # Aguarda o horário correto e executa a operação
            await agendar_operacao(ativo, "call", 5, horario_entrada)
        except Exception as e:
            print(f"Erro ao processar o sinal: {e}")
            return "error", 0
    else:
        return "ignored", 0


async def agendar_operacao(ativo, direcao, duracao, horario_entrada):
    """
    Aguarda o horário exato para executar a operação.
    """
    global saldo_atual, soma_lucro_prejuizo, total_entradas, total_win, total_loss

    print(f"Operação agendada para o ativo {ativo}, direção {direcao}, às {horario_entrada}")
    while True:
        agora = datetime.now()
        if agora >= horario_entrada:
            print("\nExecutando operação no horário agendado.")
            resultado, lucro_prejuizo = await realizar_operacao(ativo, direcao, duracao)
            return resultado, lucro_prejuizo
        await asyncio.sleep(1)


async def realizar_operacao(ativo, direcao, duracao):
    """
    Realiza a operação na Quotex e retorna o resultado (win/loss/erro).
    """
    global saldo_atual, total_entradas, total_win, total_loss
    try:
        status, buy_info = await quotex_client.buy(10, ativo, direcao, duracao)
        if status:
            is_win = await quotex_client.check_win(buy_info["id"])
            profit = buy_info["returnAmount"]
            if is_win:
                total_win += 1
                print(f"Operação WIN. Lucro: {profit}")
                return "win", profit
            else:
                total_loss += 1
                print(f"Operação LOSS. Prejuízo: {profit}")
                return "loss", profit
    except Exception as e:
        print(f"Erro ao realizar operação: {e}")
        return "error", 0

def iniciar_processamento(self):
    """
    Conecta os clientes e inicia o processamento do Telegram/Quotex.
    """
    try:
        # Assegura que a execução será feita em asyncio
        threading.Thread(target=self.executar_bot).start()
    except Exception as e:
        self.saida_text.insert("end", f"Erro ao iniciar processamento: {e}\n")


async def executar_bot(self):
    try:
        # Conecta clientes
        telegram_client = await configurar_telegram()
        conectado = await configurar_quotex()
        if not conectado:
            raise RuntimeError("Falha na conexão com a Quotex.")

        # Ouve mensagens do Telegram e processa sinais
        @telegram_client.on(events.NewMessage(chats=SALA))
        async def handler(event):
            mensagem = event.raw_text
            resultado, valor = await processar_sinal(telegram_client, mensagem)
            self.saida_text.insert("end", f"Resultado: {resultado}, Valor: {valor}\n")

        await telegram_client.run_until_disconnected()
    except Exception as e:
        self.saida_text.insert("end", f"Erro no bot: {e}\n")

def atualizar_saida(self, mensagem):
    """
    Atualiza a saída na interface com a mensagem fornecida.
    """
    self.saida_text.insert("end", f"{mensagem}\n")  # Adiciona uma nova linha com a mensagem
    self.saida_text.see("end")  # Rola automaticamente para a parte inferior

self.botao_iniciar = ctk.CTkButton(
    self,
    text="Iniciar",
    command=self.iniciar_processamento  # Conecta ao método iniciar_processamento
)
self.botao_iniciar.pack(padx=10, pady=10)

@telegram_client.on(events.NewMessage(chats=SALA))
async def handler(event):
    mensagem = event.raw_text
    self.atualizar_saida(f"[Telegram] Nova mensagem recebida: {mensagem}")
    resultado, valor = await processar_sinal(telegram_client, mensagem)

    if resultado == "win":
        self.atualizar_saida(f"✅ Resultado: WIN | Valor: R$ {valor}")
    elif resultado == "loss":
        self.atualizar_saida(f"❌ Resultado: LOSS | Prejuízo: R$ {valor}")
    elif resultado == "ignored":
        self.atualizar_saida("⚠️ Sinal ignorado ou erro no processamento.")
    else:
        self.atualizar_saida(f"Erro ao processar sinal: {resultado}")

def parar_processamento(self):
    """
    Para o bot e desconecta os serviços corretamente.
    """
    try:
        asyncio.get_event_loop().stop()  # Para o loop assíncrono
        self.atualizar_saida("Processamento interrompido.")
    except Exception as e:
        self.atualizar_saida(f"Erro ao parar processamento: {e}")

self.botao_parar = ctk.CTkButton(
    self,
    text="Parar",
    command=self.parar_processamento  # Conecta ao método parar_processamento
)
self.botao_parar.pack(padx=10, pady=10)

