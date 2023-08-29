import os
import glob
import subprocess
import asyncio
import threading
import shutil
from PIL import Image, ImageDraw, ImageFont
import textwrap
import zenhan
import moviepy.editor as mp
import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
  print('起動しました!')


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.attachments:
    for attachment in message.attachments:
      for extension in ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg',
                        '.wma'):
        if attachment.filename.endswith(extension):
          ext = extension
          file_name = attachment.filename
          msg_content = message.content
          msg_time = message.created_at.strftime("%Y%m%d%H%M%S%f")
          unq_name = os.urandom(4).hex() + msg_time
          await attachment.save(unq_name + "_audio" + ext)
          await create_image(message, file_name, msg_content, unq_name, ext)
          await delete_old(message)

async def delete_old(message):
  try:
    delete_ext = [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".png", ".mp4"]
    file_list = []
    for extension in delete_ext:
      file_list.extend(glob.glob(os.path.join("/home/runner/AudioToVideoBot/", f"*{extension}")))
    file_list.sort(key=os.path.getctime)

    # ストレージとプライバシーの観点から、ファイルが90を超えた場合、古いファイルから3つずつ削除
    if len(file_list) > 90:
      files_to_remove = file_list[:3]
      for file_to_remove in files_to_remove:
        try:
          os.remove(file_to_remove)
          print(f"削除: {file_to_remove}")
        except Exception as e:
          print(f"ファイルの削除中にエラーが発生しました: {e}")
          await message.channel.send("エラー1が発生しました。開発者にお問い合わせください。")
  except Exception as e:
    print(f"エラーが発生しました: {e}")
    await message.channel.send("エラー2が発生しました。開発者にお問い合わせください。")

async def create_image(message, file_name, msg_content, unq_name, ext):
  width, height = 256, 256
  background_color = (255, 255, 255)
  image = Image.new("RGB", (width, height), background_color)
  draw = ImageDraw.Draw(image)
  font = ImageFont.truetype("fonts/azuki.ttf", 18)
  text = zenhan.h2z(file_name) + "\n" + zenhan.h2z(msg_content)
  text_x, text_y = 5, 0
  text_color = (0, 0, 0)
  wrapper = textwrap.TextWrapper(width=14)
  wrapped_text = wrapper.fill(text)
  draw.multiline_text((text_x, text_y),
                      wrapped_text,
                      fill=text_color,
                      font=font)
  image.save(f"{unq_name}_img.png")
  await create_video(message, unq_name, ext)


async def create_video(message, unq_name, ext):
  ffmpeg_path = shutil.which('ffmpeg')
  if ffmpeg_path:
    duration = mp.AudioFileClip(f"{unq_name}_audio{ext}").duration + 1
    print("set command correctly")
    command = f'{ffmpeg_path} -loop 1 -r 1 -t {duration} -i {unq_name}_img.png -i {unq_name}_audio{ext} -fs 24.9M -vcodec libx264 -acodec aac -strict experimental -ab 320k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest {unq_name}.mp4'
    await run_command(command, message, unq_name)
  else:
    print('ffmpeg パスが見つかりませんでした。')
    await message.channel.send("エラー3が発生しました。開発者にお問い合わせください。")


async def run_command(command, message, unq_name):
  try:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    print("STDOUT:", stdout)
    print("STDERR:", stderr)

    await send_video(message, unq_name)

  except subprocess.CalledProcessError as e:
    print(f"Error: {e.output}\n")


async def send_video(message, unq_name):
  file_path = f"{unq_name}.mp4"
  try:
    file = discord.File(file_path)
    await message.channel.send(file=file)
  except FileNotFoundError:
    print(f"Error: File not found: {file_path}")
    await message.channel.send("エラー4が発生しました。開発者にお問い合わせください。")


client.run(f"{TOKEN}")
