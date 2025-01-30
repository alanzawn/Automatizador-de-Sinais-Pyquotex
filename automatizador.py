import os
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from telethon import TelegramClient, events
from quotexapi.config import email, password
from quotexapi.stable_api import Quotex
from multiprocessing.connection import Listener

os.system("pip install telethon")
print("[CLEAR_SCREEN]")


USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

quotex_client = Quotex(email=email, password=password, lang="pt")

# Variáveis de configuração
API_ID = 29960482
API_HASH = '447e76f37431dc029c90f594fd8b1cab'
SALA = 1002310421815  # ID do grupo

# Lendo o nome da sessão do arquivo 'session_name.txt'
session_file = "session_name.txt"

try:
    with open(session_file, "r", encoding="utf-8") as file:
        SESSION_NAME = file.read().strip()  # Remove espaços extras e quebras de linha
except FileNotFoundError:
    print(f"Erro: O arquivo '{session_file}' não foi encontrado. Usando o nome padrão.")
    SESSION_NAME = "alanzawn"  # Nome padrão caso o arquivo não exista

# Contadores globais para vitórias e derrotas consecutivas
num_win_consecutivos = 0
num_loss_consecutivos = 0
total_entradas = 0
total_win = 0
total_loss = 0
soma_lucro_prejuizo = 0




async def get_payout_by_asset(ativo):
    #check_connect, reason = await quotex_client.connect()
    #if check_connect:
    asset_data = quotex_client.get_payout_by_asset(ativo)
    #print(asset_data)
    return asset_data


def atualizar_arquivo_dados():
    """
    Atualiza o arquivo 'dados.txt' com as estatísticas de operações em tempo real.
    """
    global saldo_atual, soma_lucro_prejuizo, total_entradas, total_win, total_loss, num_win_consecutivos, num_loss_consecutivos

    # Garante que o saldo atual está formatado corretamente
    saldo_formatado = f"{saldo_atual:.2f}".replace('.', ',')

    # Salvar os dados no arquivo
    with open("dados.txt", "w", encoding="utf-8") as arquivo:
        arquivo.write("=== Dados das Operações ===\n")
        arquivo.write(f"Saldo Atual: R$ {saldo_formatado}\n")
        arquivo.write(f"Lucro/Prejuízo Total: R$ {soma_lucro_prejuizo:.2f}\n")
        arquivo.write(f"Entradas Totais: {total_entradas}\n")
        arquivo.write(f"Wins: {total_win}\n")
        arquivo.write(f"Losses: {total_loss}\n")
    print("Arquivo de dados atualizado.")



def ler_configuracoes():
    configuracoes = {}

    caminho_arquivo = "configuracoes.txt"

    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()

            for linha in linhas:
                if "=" * 50 in linha or "Configuracoes do Robo de Operacoes" in linha:
                    continue

                linha = linha.strip()

                if not linha:
                    continue

                chave, valor = linha.split(":")
                chave = chave.strip()
                valor = valor.strip()

                if valor.replace('.', '', 1).isdigit():
                    if '.' in valor:
                        configuracoes[chave] = float(valor)
                    else:
                        configuracoes[chave] = int(valor)
                else:
                    configuracoes[chave] = valor

        #print("Configurações carregadas com sucesso!")
        return configuracoes

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return None


async def connect_quotex_client(attempts=5):
    check, reason = await quotex_client.connect()
    if not check:
        for attempt in range(1, attempts + 1):
            if not quotex_client.check_connect():
                check, reason = await quotex_client.connect()
                if check:
                    print("Reconectado com sucesso!!!")
                    break
                print("Erro ao reconectar.")
                if Path("session.json").is_file():
                    Path("session.json").unlink()
                print(f"Tentando reconectar, tentativa {attempt} de {attempts}")
                await asyncio.sleep(5)
            else:
                break
        return check, reason
    print(reason)
    return check, reason


async def buy_simple(ativo, direcao, duracao, lote):
    amount = lote
    asset_name, asset_data = await quotex_client.get_available_asset(ativo, force_open=False)
    if asset_data[2]:
        status, buy_info = await quotex_client.buy(amount, asset_name, direcao, duracao)
        if status:
            is_win = await quotex_client.check_win(buy_info["id"])
            profit = quotex_client.get_profit()
            profit = quotex_client.get_profit()
            if is_win:
                print(f"\nWin!!! Lucro: R$ {profit}")
                return "win", profit
            else:
                print(f"\nLoss!!! Prejuízo: R$ {profit}")
                return "loss", profit
        print("Erro ao realizar a compra.")
        return "error", 0
    print("ERRO: Asset está fechado.")
    return "closed", 0


async def agendar_operacao(ativo, direcao, duracao, horario_entrada):
    """
    Aguarda o horário exato para executar uma operação e tenta até conseguir.
    Retorna o resultado da operação para gerenciamento.
    """
    global saldo_atual, soma_lucro_prejuizo, total_entradas, total_win, total_loss, total_loss, total_win, total_entradas, num_win_consecutivos, num_loss_consecutivos

    config = await extrair_config()  # Obtemos o dicionário diretamente
    if not config:  # Verifica se a configuração falhou
        print("Falha ao carregar configurações.")
        return "error", 0

    # Atributos são extraídos do dicionário quando necessários
    tipo_conta = config["tipo_conta"]
    capital_inicial = config["capital_inicial"]
    saldo_atual = await get_balance(tipo_conta) #config["saldo_atual"]
    payout_minimo = config["payout_minimo"]
    tipo_gerenciamento = config["tipo_gerenciamento"]
    gerenciamento = config["gerenciamento"]
    tipo_takeprofit = config["tipo_takeprofit"]
    take_profit = config["take_profit"]
    take_valor = config["take_valor"]
    tipo_stoploss = config["tipo_stoploss"]
    stop_loss = config["stop_loss"]
    stop_valor = config["stop_valor"]
    valor_operacao = config["valor_operacao"]

    print(f"Operação agendada para {horario_entrada}...")

    while True:
        agora = datetime.now()
        tempo_restante = (horario_entrada - agora).total_seconds()

        if tempo_restante <= 0 or agora.second <= 5:
            print("\nHora da operação! Tentando realizar a entrada...")

            #print(saldo_atual, capital_inicial, take_valor, stop_valor)
            # Verificar se o saldo atingiu o Take Profit ou Stop Loss
            if saldo_atual >= take_valor:  # Take Profit atingido
                print("Saldo atingiu o Take Profit. Encerrando operações...")
                atualizar_arquivo_dados()  # Atualiza os dados no arquivo
                return "take_profit", saldo_atual

            elif saldo_atual <= stop_valor:  # Stop Loss atingido
                print("Saldo atingiu o Stop Loss. Encerrando operações...")
                atualizar_arquivo_dados()  # Atualiza os dados no arquivo
                return "stop_loss", saldo_atual

            try:
                resultado, lucro_prejuizo = await buy_simple(ativo, direcao, duracao, valor_operacao)
            except Exception as e:
                resultado, lucro_prejuizo = await buy_simple(ativo, direcao, duracao, valor_operacao)
                resultado, lucro_prejuizo = "error", 0

            # Atualiza saldo após operação
            saldo_atual += lucro_prejuizo

            if resultado == "win":
                num_win_consecutivos += 1
                num_loss_consecutivos = 0
                total_win += 1  # Incrementa contagem de wins
            elif resultado == "loss":
                num_loss_consecutivos += 1
                num_win_consecutivos = 0
                total_loss += 1  # Incrementa contagem de losses
            elif resultado == 'error':
                raise RuntimeError("Erro ao agendar operação em teste.py")

            # Incrementa o total de entradas e soma de lucro/prejuízo
            total_entradas += 1
            soma_lucro_prejuizo += lucro_prejuizo

            # Atualiza o arquivo dados.txt
            atualizar_arquivo_dados()

            print(f"Saldo atual: R$ {saldo_atual}, Valor da operação: R$ {valor_operacao}")
            return resultado, lucro_prejuizo

        if int(tempo_restante) <= 300:
            print(f"\rAguardando... {int(tempo_restante)} segundos restantes.", end="", flush=True)
            await asyncio.sleep(1)
        else:
            print('Horário inválido')
            break



horarios_agendados = {}
async def processar_sinal(mensagem):
    global horarios_agendados
    if all(char in mensagem for char in ["🚨", "🏆", "⏰", "⏳"]):
        try:
            ativo_inicio = mensagem.index("🏆") + 1
            ativo_fim = mensagem.index("\n", ativo_inicio)
            ativo = mensagem[ativo_inicio:ativo_fim].strip()

            entrada_inicio = mensagem.index("⏰") + len("⏰ ENTRADA")
            entrada_fim = mensagem.index("\n", entrada_inicio)
            horario_entrada = mensagem[entrada_inicio:entrada_fim].strip()

            direcao = "call" if "CALL" in mensagem.upper() else "put"

            expiracao_inicio = mensagem.index("⏳") + len("⏳ Expiração de ")
            expiracao_fim = mensagem.index("minuto", expiracao_inicio)
            expiracao_minutos = int(mensagem[expiracao_inicio:expiracao_fim].strip())

            agora = datetime.now()
            hora_entrada = datetime.strptime(horario_entrada, "%H:%M").replace(
                year=agora.year, month=agora.month, day=agora.day
            )

            if hora_entrada < agora:
                hora_entrada += timedelta(days=1)

            if hora_entrada in horarios_agendados:
                print(f"Sinal ignorado: já existe uma operação agendada para {hora_entrada}.")
                return "ignored", 0

            expiracao_segundos = expiracao_minutos * 60
            print("Novo Sinal Encontrado:")
            print(f"  Ativo: {ativo}")
            print(f"  Direção: {direcao}")
            print(f"  Hora de entrada: {hora_entrada}")
            print(f"  Duração: {expiracao_segundos}s\n")

            config = await extrair_config()  # Obtemos o dicionário diretamente
            if not config:  # Verifica se a configuração falhou
                print("Falha ao carregar configurações.")
                pass

            payout_minimo = config["payout_minimo"]
            if int(await get_payout_by_asset(ativo)) >= int(payout_minimo):
                horarios_agendados[hora_entrada] = ativo
            else:
                print(f"Sinal ignorado, Payout inferior")
                return 'ignored', 0

            resultado, lucro_prejuizo = await agendar_operacao(
                ativo, direcao, expiracao_segundos, hora_entrada
            )
            print(f"Resultado da operação: {resultado}, Valor: {lucro_prejuizo}")

            return resultado, lucro_prejuizo
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")
            return "error", 0
    else:
        # Retorna "ignored" por padrão se a mensagem não conter os caracteres necessários
        return {"status": "ignored", "profit": 0}


async def get_balance(conta=int):
    if conta == 1:
        #print("Saldo corrente: ", round(float(await quotex_client.get_balance()), 2))
        pass
    elif conta == 2:
        quotex_client.change_account("REAL")
        #print("Saldo corrente: ", round(float(await quotex_client.get_balance()), 2))

    banca = round(float(await quotex_client.get_balance()), 2)
    return banca

async def extrair_config():
    configuracoes = ler_configuracoes()

    if configuracoes:
        tipo_conta = configuracoes.get("tipo_conta")
        capital_inicial = await get_balance(tipo_conta)
        saldo_atual = configuracoes.get("capital_inicial")
        payout_minimo = configuracoes.get("payout_minimo")
        tipo_gerenciamento = configuracoes.get("tipo_gerenciamento")
        gerenciamento = configuracoes.get("gerenciamento")
        tipo_takeprofit = configuracoes.get("tipo_takeprofit")
        take_profit = configuracoes.get("take_profit")
        take_valor = configuracoes.get("take_valor")
        tipo_stoploss = configuracoes.get("tipo_stoploss")
        stop_loss = configuracoes.get("stop_loss")
        stop_valor = configuracoes.get("stop_valor")
        usar_martingale = configuracoes.get("usar_martingale")
        usar_trailingStop = configuracoes.get("usar_trailingStop")
        valor_inicial_operacao = configuracoes.get("valor_inicial_operacao")
        valor_operacao = float(valor_inicial_operacao)
        break_cond = configuracoes.get("break")

        if tipo_gerenciamento == 2:
            mao_soros = configuracoes.get("mao_soros")
        elif tipo_gerenciamento == 3:
            porcentagem = configuracoes.get("porcentagem")

        if tipo_takeprofit == 2:
            mao_take = configuracoes.get("mao_take")

        if tipo_stoploss == 2:
            mao_stop = configuracoes.get("mao_stop")

            if tipo_stoploss == 2:  # Caso de "número de losses consecutivos"
                loss_consecutivos = configuracoes.get("loss_concecutivo")

        #print(configuracoes)

        return {
            "tipo_conta": tipo_conta,
            "capital_inicial": capital_inicial,
            "saldo_atual": saldo_atual,
            "payout_minimo": payout_minimo,
            "tipo_gerenciamento": tipo_gerenciamento,
            "gerenciamento": gerenciamento,
            "tipo_takeprofit": tipo_takeprofit,
            "take_profit": take_profit,
            "take_valor": take_valor,
            "tipo_stoploss": tipo_stoploss,
            "stop_loss": stop_loss,
            "stop_valor": stop_valor,
            "usar_martingale": usar_martingale,
            "usar_trailingStop": usar_trailingStop,
            "valor_inicial_operacao": valor_inicial_operacao,
            "valor_operacao": valor_operacao,
            "break_cond": break_cond,
            "mao_soros": locals().get("mao_soros"),
            "porcentagem": locals().get("porcentagem"),
            "win_consecutivos": locals().get("win_consecutivos"),
            "loss_consecutivos": locals().get("loss_consecutivos"),
        }
    else:
        print("Não foi possível carregar as configurações.")
        return None

async def start_telegram_bot():
    """
    Inicializa o cliente do Telegram e configura os event listeners.
    """
    telegram_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await telegram_client.start()
    print("Telegram Client conectado.")

    # Verificar conexão com a Quotex
    check, reason = await quotex_client.connect()
    if not check:
        print(f"Erro ao conectar com a Quotex: {reason}")
        return

    # Carregar configurações
    configuracoes = await extrair_config()
    if not configuracoes:
        print("Erro ao carregar as configurações. Encerrando execução.")
        return

    print("[CLEAR_SCREEN]")  # Limpa o terminal
    print("Automatizador ligado. Aguardando sinais...")

    # Listener para mensagens no grupo
    @telegram_client.on(events.NewMessage(chats=SALA))
    async def handler(event):
        mensagem = event.raw_text
        resultado, valor = await processar_sinal(mensagem)
        if resultado == "win":
            print(f"Operação WIN: Lucro de R$ {valor}")
        elif resultado == "loss":
            print(f"Operação LOSS: Prejuízo de R$ {valor}")
        elif resultado == "ignored":
            print("Sinal ignorado.")
        elif resultado == "error":
            print("Erro ao processar o sinal.")

        # Aguarda 3 segundos para visualizar o resultado e depois limpa o terminal
        await asyncio.sleep(3)
        print("[CLEAR_SCREEN]")  # Limpa o terminal
        print("Automatizador ligado. Aguardando sinais...")
    try:
        await telegram_client.run_until_disconnected()
    finally:
        # Atualizar os dados no encerramento do script
        atualizar_arquivo_dados()
        print("Encerrando script e atualizando arquivo 'dados.txt'...")

if __name__ == "__main__":
    try:
        asyncio.run(start_telegram_bot())
    except Exception as e:
        print(f"Erro no teste.py: {e}")
        sys.exit(1)  # Retorna 1 para indicar falha
    else:
        sys.exit(0)  # Retorna 0 para indicar sucesso
