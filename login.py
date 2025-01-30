import os
import subprocess
import asyncio
from telethon import TelegramClient

os.system("pip install playwright")
os.system("playwright install")
# Instalação otimizada dos pacotes necessários
def instalar_dependencias():
    pacotes = ["-r requirements.txt", "customtkinter", "telethon"]
    for pacote in pacotes:
        subprocess.run(f"pip install {pacote}", shell=True, check=True)


# Verifica se já existem sessões salvas
def verificar_sessoes():
    return any(arquivo.endswith(".session") for arquivo in os.listdir(".")) or os.path.exists("session.json")


# Salva o nome da sessão em um arquivo .txt
def salvar_session_name(session_name):
    with open("session_name.txt", "w", encoding="utf-8") as file:
        file.write(session_name)


# Faz login no Telegram e salva o nome da sessão
async def login_telegram():
    print("Login Telegram")
    API_ID = 29960482
    API_HASH = '447e76f37431dc029c90f594fd8b1cab'

    session_name = input("Seu nome: ").strip().replace(' ', '_')
    salvar_session_name(session_name)  # Salva o nome da sessão

    telegram_client = TelegramClient(session_name, API_ID, API_HASH)
    await telegram_client.start()


# Função principal para gerenciar o login
async def main():
    if not verificar_sessoes():
        await login_telegram()


# Execução assíncrona do programa com tratamento seguro
if __name__ == "__main__":
    instalar_dependencias()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Encerrando o programa.")
    finally:
        # Cancelar tarefas pendentes antes de fechar o loop
        pending = asyncio.all_tasks(loop=loop)
        for task in pending:
            task.cancel()
            try:
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass
        loop.close()