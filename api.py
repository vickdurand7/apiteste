import mysql.connector
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
from telegram.ext.filters import Command
import os

# Seu ID
SEU_ID = 7575436926

# Configuração do banco de dados MySQL
db_config = {
    "host": "sql210.infinityfree.com",
    "user": "if0_38751056",
    "password": "6MVZQhHqYzol",
    "database": "if0_38751056_acessos_db"
}

# Função para criar a tabela de usuários se não existir
def criar_tabela_usuarios():
    con = mysql.connector.connect(**db_config)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id BIGINT PRIMARY KEY
        )
    ''')
    con.commit()
    con.close()

def adicionar_usuario(user_id):
    con = mysql.connector.connect(**db_config)
    cur = con.cursor()
    cur.execute("INSERT IGNORE INTO usuarios (user_id) VALUES (%s)", (user_id,))
    con.commit()
    con.close()
    print(f"Usuário {user_id} adicionado com sucesso!")

def remover_usuario(user_id):
    con = mysql.connector.connect(**db_config)
    cur = con.cursor()
    cur.execute("DELETE FROM usuarios WHERE user_id = %s", (user_id,))
    con.commit()
    con.close()

def is_usuario_autorizado(user_id):
    con = mysql.connector.connect(**db_config)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE user_id = %s", (user_id,))
    autorizado = cur.fetchone()
    con.close()

    print(f"Verificando autorização do usuário {user_id}: {'Autorizado' if autorizado else 'Não autorizado'}")

    return autorizado is not None

usuarios_em_espera = {}

async def is_user_in_group(update: Update, group_chat_id: int):
    user_id = update.effective_user.id
    try:
        chat_member = await update.effective_chat.get_member(user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Consulta no banco MySQL - com LIKE
def consultar_url(keyword):
    con = mysql.connector.connect(**db_config)
    cur = con.cursor()
    cur.execute("SELECT url, email, senha FROM acessos WHERE url LIKE %s", ('%' + keyword + '%',))
    resultados = cur.fetchall()
    con.close()

    if resultados:
        resposta = "🔐 Logins encontrados:\n"
        for url, email, senha in resultados:
            resposta += f"\nURL: {url}\nEmail: {email}\nSenha: {senha}\n"
        with open("resposta.txt", "w", encoding="utf-8") as file:
            file.write(resposta)
        return "Arquivo com os logins encontrados:", "resposta.txt"
    else:
        return "❌ Nenhum login encontrado para essa palavra-chave.", None

# --- DEMAIS FUNÇÕES (iguais às suas) ---
# Copie aqui as funções url, meuid, adicionar, remover, start, comandos_invalidos e main como estão.
# NÃO PRECISA modificar essas funções, pois elas usam as funções acima que já foram adaptadas.

# Coloque aqui as funções do jeito que estão no seu código original
# Apenas a parte de banco de dados foi alterada

# Comando /url
async def url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Verifica se o usuário está autorizado a usar o bot
    if not is_usuario_autorizado(user_id):
        await update.message.reply_text("🚫 Você não tem permissão para usar este bot.")
        return

    group_chat_id = -100123456789  # Coloque o ID do grupo aqui

    if not await is_user_in_group(update, group_chat_id):
        await update.message.reply_text("🚫 Você não tem permissão para usar este bot.")
        return

    agora = time.time()
    if user_id in usuarios_em_espera and agora - usuarios_em_espera[user_id] < 10:
        await update.message.reply_text("⏳ Espere alguns segundos antes de tentar novamente.")
        return
    usuarios_em_espera[user_id] = agora

    if context.args:
        keyword = context.args[0].lower()  # Usa a palavra-chave fornecida pelo usuário
        mensagem, arquivo = consultar_url(keyword)
        
        if arquivo:
            # Envia o arquivo de texto
            with open(arquivo, "rb") as file:
                await update.message.reply_document(document=file)
            os.remove(arquivo)  # Exclui o arquivo após o envio
        else:
            await update.message.reply_text(mensagem)
    else:
        await update.message.reply_text("❗ Use assim: /url palavra-chave (ex: /url netflix)")

# Comando opcional para pegar seu ID
async def meuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Qualquer usuário pode consultar seu próprio ID
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Seu ID é: {user_id}")

# Comando para adicionar um usuário
async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != SEU_ID:  # Apenas o dono do bot pode adicionar usuários
        await update.message.reply_text("🚫 Apenas o administrador pode adicionar usuários.")
        return

    if context.args:
        try:
            novo_usuario_id = int(context.args[0])
            adicionar_usuario(novo_usuario_id)
            await update.message.reply_text(f"✅ Usuário {novo_usuario_id} adicionado com sucesso.")
        except ValueError:
            await update.message.reply_text("❌ ID inválido. Certifique-se de enviar um número válido.")
    else:
        await update.message.reply_text("❗ Use assim: /adicionar <ID do usuário>")
# Comando para remover um usuário
async def remover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != SEU_ID:  # Apenas o dono do bot pode remover usuários
        await update.message.reply_text("🚫 Apenas o administrador pode remover usuários.")
        return

    if context.args:
        try:
            usuario_id = int(context.args[0])
            remover_usuario(usuario_id)
            await update.message.reply_text(f"✅ Usuário {usuario_id} removido com sucesso.")
        except ValueError:
            await update.message.reply_text("❌ ID inválido. Certifique-se de enviar um número válido.")
    else:
        await update.message.reply_text("❗ Use assim: /remover <ID do usuário>")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    "👋 *Olá! Eu sou o bot de Logs do Kyzer!*\n\n"
    "🔍 *Modo de Uso:*"
    "\n\nUse o comando `/url <palavra-chave>` para consultar logins."
    "\n\n_Exemplo:_ `/url netflix`\n\n"
    "👨‍💻 *Desenvolvido por:* @kyze3r\n"
    "📢 *Canal:* [t.me/eukyzer](https://t.me/eukyzer)\n\n"
    "📌 *Comandos disponíveis:*\n"
    "`\n\n/start` - Inicia o bot"
    "`\n\n/url <palavra-chave>` - Consulta informações de login"
    "`\n\n/meuid` - Mostra seu ID"
    "`\n\n/adicionar <ID>` - Adiciona um usuário autorizado (apenas admin)"
    "`\n\n/remover <ID>` - Remove um usuário autorizado (apenas admin)\n\n"
, parse_mode="Markdown")


# Função para enviar mensagem padrão de comandos inválidos
async def comandos_invalidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❗ Comando inválido! Comandos válidos:\n"
        
        "\n/start - Inicia o bot\n"

        "\n/url <palavra-chave> - Consulta informações de login\n"

        "\n/meuid - Mostra seu ID\n"

        "\n/adicionar <ID> - Adiciona um usuário autorizado (apenas admin)\n"

        "\n/remover <ID> - Remove um usuário autorizado (apenas admin)\n"
    )

# Inicialização do bot
def main():
    # Cria a tabela de usuários, se não existir
    criar_tabela_usuarios()

    # Adiciona seu ID se ainda não estiver na lista de usuários
    adicionar_usuario(SEU_ID)

    app = ApplicationBuilder().token("7365551459:AAHrJ3TMtJJvKcTww3ixkW5BsGtXAzKa1es").build()

    # Adicionando os handlers
    app.add_handler(CommandHandler("url", url))
    app.add_handler(CommandHandler("meuid", meuid))  # Qualquer usuário pode consultar seu ID
    app.add_handler(CommandHandler("adicionar", adicionar))  # Adicionando o handler para /adicionar
    app.add_handler(CommandHandler("remover", remover))  # Adicionando o handler para /remover
    app.add_handler(CommandHandler("start", start))  # Adicionando o handler para /start
    app.add_handler(MessageHandler(Command(), comandos_invalidos))  # Adicionando handler para comandos inválidos

    print("🤖 Bot iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()
