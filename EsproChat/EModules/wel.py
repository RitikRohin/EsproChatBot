# ==================================
#    SIMPLE WORKING WELCOME MODULE
# ==================================

from EsproChat import app
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from logging import getLogger
import os
import time
import asyncio

LOGGER = getLogger(__name__)

# --- Directory Setup ---
DOWNLOADS_DIR = 'downloads'
if not os.path.isdir(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# --- Temporary Storage ---
class temp:
    last = {}
    cooldown = {}

# --- Image Processing Functions ---

def circle(pfp, size=(500, 500)):
    """Makes the profile picture circular."""
    try:
        pfp = pfp.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    except:
        pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    
    try:
        mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    except:
        mask = mask.resize(pfp.size, Image.ANTIALIAS)
    
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def create_simple_welcome_image(pfp_path, user_name, user_id, username, chat_name, member_count):
    """Create a simple welcome image with member info."""
    
    # Create image
    width, height = 1000, 500
    image = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(image)
    
    # Try to load font
    try:
        font_large = ImageFont.truetype("EsproChat/assets/font.ttf", 40)
        font_medium = ImageFont.truetype("EsproChat/assets/font.ttf", 30)
        font_small = ImageFont.truetype("EsproChat/assets/font.ttf", 25)
    except:
        # Use default fonts if custom font not found
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add profile picture
    try:
        if os.path.exists(pfp_path):
            pfp = Image.open(pfp_path).convert("RGBA")
            pfp = circle(pfp, size=(200, 200))
            
            # Add PFP to image
            image.paste(pfp, (50, 150), pfp)
            
            # Add border around PFP
            draw.ellipse([45, 145, 255, 355], outline='#FFD700', width=3)
    except Exception as e:
        LOGGER.error(f"Error adding PFP: {e}")
    
    # Add WELCOME text
    draw.text((300, 50), "WELCOME", fill='#FFD700', font=font_large)
    draw.text((300, 100), f"to {chat_name[:30]}", fill='white', font=font_medium)
    
    # Add member info box
    info_y = 170
    draw.rectangle([300, info_y, 950, info_y + 250], fill='#2d2d44', outline='#FFD700', width=2)
    
    # Add member information
    draw.text((320, info_y + 20), f"👤 Name: {user_name[:25]}", fill='white', font=font_medium)
    draw.text((320, info_y + 70), f"🆔 ID: {user_id}", fill='#00ffaa', font=font_medium)
    
    if username:
        draw.text((320, info_y + 120), f"📱 Username: @{username[:20]}", fill='#87ceeb', font=font_medium)
    else:
        draw.text((320, info_y + 120), "📱 Username: Not Set", fill='#87ceeb', font=font_medium)
    
    draw.text((320, info_y + 170), f"👥 Members: {member_count}", fill='#ffa500', font=font_medium)
    
    # Add decorative line
    draw.line([(300, info_y + 220), (950, info_y + 220)], fill='#FFD700', width=3)
    
    # Add timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    draw.text((320, info_y + 218), f"Joined: {timestamp}", fill='#aaaaaa', font=font_small)
    
    # Save image
    output_path = f"{DOWNLOADS_DIR}/welcome_{user_id}_{int(time.time())}.jpg"
    image.save(output_path, quality=95)
    
    return output_path

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group)
async def greet_new_member(client, member: ChatMemberUpdated):
    """Automatically sends a welcome message when a new member joins."""
    
    # Check if it's a new member joining
    if not member.new_chat_member or member.old_chat_member:
        return
    
    # Check if user exists
    if not member.new_chat_member.user:
        return
    
    user = member.new_chat_member.user
    chat = member.chat
    
    # Skip bots
    if user.is_bot:
        return
    
    # Debug log
    LOGGER.info(f"New member joined: {user.first_name} in {chat.title}")
    
    # Cooldown check
    current_time = time.time()
    if chat.id in temp.cooldown:
        if current_time - temp.cooldown[chat.id] < 3:
            return
    
    temp.cooldown[chat.id] = current_time
    
    try:
        # Get member count
        try:
            count = await client.get_chat_members_count(chat.id)
        except:
            count = "Unknown"
        
        # Download profile picture
        pfp_path = None
        try:
            if user.photo and user.photo.big_file_id:
                pfp_path = f"{DOWNLOADS_DIR}/temp_pp_{user.id}.jpg"
                await client.download_media(
                    user.photo.big_file_id,
                    file_name=pfp_path
                )
                LOGGER.info(f"Downloaded PFP to: {pfp_path}")
            else:
                # Use default image
                pfp_path = "EsproChat/assets/upic.png"
                if not os.path.exists(pfp_path):
                    # Create a simple default image
                    default_img = Image.new('RGB', (200, 200), color='#4a4aff')
                    draw = ImageDraw.Draw(default_img)
                    draw.ellipse([20, 20, 180, 180], fill='#2d2d44')
                    draw.text((70, 85), "USER", fill='white', font=ImageFont.load_default())
                    os.makedirs("EsproChat/assets", exist_ok=True)
                    default_img.save(pfp_path)
                LOGGER.info(f"Using default PFP: {pfp_path}")
        except Exception as e:
            LOGGER.error(f"Error downloading PFP: {e}")
            pfp_path = "EsproChat/assets/upic.png"
        
        # Create welcome image
        try:
            image_path = create_simple_welcome_image(
                pfp_path=pfp_path,
                user_name=user.first_name or "User",
                user_id=user.id,
                username=user.username,
                chat_name=chat.title,
                member_count=count
            )
            
            if not os.path.exists(image_path):
                raise Exception("Image creation failed")
            
            LOGGER.info(f"Created welcome image: {image_path}")
            
        except Exception as e:
            LOGGER.error(f"Error creating image: {e}")
            # Fallback to text message
            await send_text_welcome(client, chat.id, user, chat.title, count)
            return
        
        # Delete previous welcome message
        if chat.id in temp.last:
            try:
                await temp.last[chat.id].delete()
            except:
                pass
        
        # Prepare caption
        caption = f"""
**🎉 Welcome to {chat.title}! 🎉**

**👤 New Member:** {user.mention()}
**🆔 ID:** `{user.id}`
**📱 Username:** @{user.username or 'Not Set'}
**👥 Total Members:** `{count}`

Enjoy your stay! 😊
"""
        
        # Get bot username for button
        try:
            me = await client.get_me()
            bot_username = me.username
        except:
            bot_username = app.username if hasattr(app, 'username') else "unknown_bot"
        
        # Send welcome message
        try:
            message = await client.send_photo(
                chat_id=chat.id,
                photo=image_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 Add Bot", url=f"https://t.me/{bot_username}?startgroup=true")],
                    [InlineKeyboardButton("🌟 Support", url="https://t.me/EsproSupport")]
                ])
            )
            
            temp.last[chat.id] = message
            LOGGER.info(f"Welcome sent successfully for {user.first_name}")
            
        except Exception as e:
            LOGGER.error(f"Error sending photo: {e}")
            # Try text message as fallback
            await send_text_welcome(client, chat.id, user, chat.title, count)
        
        # Cleanup
        try:
            # Delete downloaded PFP if it's temporary
            if pfp_path and "temp_pp_" in pfp_path and os.path.exists(pfp_path):
                os.remove(pfp_path)
            
            # Delete welcome image after delay
            await asyncio.sleep(5)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            LOGGER.warning(f"Cleanup error: {e}")
            
    except Exception as e:
        LOGGER.error(f"Error in welcome handler: {e}")

async def send_text_welcome(client, chat_id, user, chat_title, count):
    """Send text-only welcome as fallback."""
    try:
        # Get bot username
        try:
            me = await client.get_me()
            bot_username = me.username
        except:
            bot_username = app.username if hasattr(app, 'username') else "unknown_bot"
        
        caption = f"""
**🎉 Welcome to {chat_title}! 🎉**

**✨ New Member Information:**
• **Name:** {user.mention()}
• **ID:** `{user.id}`
• **Username:** @{user.username or 'Not Set'}
• **Total Members:** `{count}`

We're glad to have you here! Feel free to introduce yourself. 😊
"""
        
        # Delete previous welcome
        if chat_id in temp.last:
            try:
                await temp.last[chat_id].delete()
            except:
                pass
        
        message = await client.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Add Bot", url=f"https://t.me/{bot_username}?startgroup=true")],
                [InlineKeyboardButton("🌟 Support", url="https://t.me/EsproSupport")]
            ])
        )
        
        temp.last[chat_id] = message
        LOGGER.info(f"Text welcome sent for {user.first_name}")
        
    except Exception as e:
        LOGGER.error(f"Error sending text welcome: {e}")

# Debug command to test welcome
@app.on_message(filters.command("testwelcome") & filters.group)
async def test_welcome_command(client, message):
    """Test command to trigger welcome manually."""
    try:
        # Simulate a new member joining (using the command sender)
        fake_member = ChatMemberUpdated(
            chat=message.chat,
            from_user=message.from_user,
            date=message.date,
            old_chat_member=None,
            new_chat_member=types.ChatMember(
                user=message.from_user,
                status=enums.ChatMemberStatus.MEMBER,
                until_date=None
            )
        )
        
        await greet_new_member(client, fake_member)
        await message.delete()
        
    except Exception as e:
        LOGGER.error(f"Test welcome error: {e}")
        await message.reply(f"Error: {e}")
