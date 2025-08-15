import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import gspread
import os
import json
from google.oauth2.service_account import Credentials
import logging
from flask import Flask
from threading import Thread

# ログ設定
logging.basicConfig(level=logging.INFO)

# --- 設定項目 ---
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SPREADSHEET_NAME = os.environ.get('SPREADSHEET_NAME')
GCP_SA_KEY_STR = os.environ.get('GCP_SA_KEY')

# --- Google認証 ---
try:
    if not GCP_SA_KEY_STR:
        raise ValueError("環境変数 'GCP_SA_KEY' が設定されていません。")
    gcp_json_credentials_dict = json.loads(GCP_SA_KEY_STR)
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(gcp_json_credentials_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.sheet1
    logging.info("Googleスプレッドシートへの接続に成功しました。")
except Exception as e:
    logging.error(f"Googleスプレッドシートへの接続に失敗しました: {e}")
    exit()

# --- Discord Bot ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

class ReportModal(Modal, title='報告フォーム'):
    content = TextInput(label='報告内容', style=discord.TextStyle.paragraph, placeholder='報告内容を入力してください')
    async def on_submit(self, interaction: discord.Interaction):
        try:
            worksheet.append_row([interaction.user.display_name, self.content.value])
            await interaction.response.send_message(f'報告を記録しました！', ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f'エラーが発生しました: {e}', ephemeral=True)

@tree.command(name="report", description="報告フォームを開きます。")
async def report_command(interaction: discord.Interaction):
    await interaction.response.send_modal(ReportModal())

@client.event
async def on_ready():
    logging.info(f'{client.user} としてログインしました。')
    await tree.sync()
    logging.info("スラッシュコマンドの同期が完了しました。")

# --- Webサーバー (Railway/Heroku用) ---    # <<< ここからブロックごと追加
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --- ここまで追加 ---

# --- Bot実行 ---
if DISCORD_BOT_TOKEN and SPREADSHEET_NAME and GCP_SA_KEY_STR:
    keep_alive()
    client.run(DISCORD_BOT_TOKEN)
else:

    logging.error("必要な環境変数が設定されていません。")

