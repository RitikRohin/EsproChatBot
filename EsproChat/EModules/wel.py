# ==================================
#    WELCOME MODULE (EsproChat)
# ==================================

from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
import os
import time
import asyncio
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

# --- Directory Setup ---
DOWNLOADS_DIR = 'downloads'
if not os.path.isdir(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# Create assets directory if not exists
ASSETS_DIR = 'EsproChat/assets'
if not os.path.isdir(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# --- Temporary Storage ---
class temp:
    last = {}
    cooldown = {}

# --- Image Processing Functions ---

def circle(pfp, size=(500, 500)):
    """Makes the profile picture circular."""
    try:
        pfp = pfp.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    except AttributeError:
        pfp = pfp.resize(size, Image.ANTIALIAS).convert("RGBA")
    
    # Create circular mask
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    
    # Apply mask
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
        # Scale up default font
        try:
            font_large.size = 40
            font_medium.size = 30
            font_small.size = 25
        except:
            pass
    
    # ========== FIXED POSITIONS FOR BETTER LAYOUT ==========
    
    # Box position - CURRENT (थोड़ा नीचे)
    box_width = 600
    box_height = 180
    box_x = (width - box_width) // 2  # Center horizontally
    box_y = 80  # थोड़ा नीचे (पहले 50 था, अब 80)
    
    # Profile Picture position (LEFT SIDE)
    pfp_x = 50
    pfp_y = 150  # Box के नीचे
    
    # Welcome text position
    welcome_y = 380
    
    # ========== ADD PROFILE PICTURE ==========
    try:
        if os.path.exists(pfp_path):
            pfp = Image.open(pfp_path).convert("RGBA")
            pfp = circle(pfp, size=(200, 200))
            
            # Add PFP
            image.paste(pfp, (pfp_x, pfp_y), pfp)
            
            # Add glowing border around PFP
            for i in range(3):
                border_size = 3 - i
                draw.ellipse(
                    [pfp_x-5-i, pfp_y-5-i, pfp_x+205+i, pfp_y+205+i],
                    outline='#FFD700',
                    width=border_size
                )
            
    except Exception as e:
        LOGGER.error(f"Error adding PFP: {e}")
        # Draw placeholder if PFP fails
        draw.ellipse([pfp_x, pfp_y, pfp_x+200, pfp_y+200], fill='#4a4aff', outline='#FFD700', width=3)
        draw.text((pfp_x+70, pfp_y+85), "USER", fill='white', font=font_medium)
    
    # ========== CREATE MEMBER INFO BOX ==========
    # Create info box with shadow effect
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=25,  # More rounded corners
        fill='#2d2d44',
        outline='#FFD700',
        width=3
    )
    
    # Add box title with gradient effect
    title = "✨ NEW MEMBER ✨"
    
    # Calculate title position (center)
    if hasattr(draw, 'textbbox'):
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
    else:
        # Fallback for older PIL
        title_width = draw.textlength(title, font=font_large)
    
    title_x = box_x + (box_width - title_width) // 2
    
    # Title with shadow
    draw.text((title_x+2, box_y + 17), title, fill='#000000', font=font_large)  # Shadow
    draw.text((title_x, box_y + 15), title, fill='#FFD700', font=font_large)   # Main text
    
    # Add decorative line under title
    line_y = box_y + 65
    draw.line([(box_x + 40, line_y), (box_x + box_width - 40, line_y)], 
              fill='#FFD700', width=3)
    
    # Add member information (TWO COLUMNS WITH BETTER SPACING)
    info_start_y = box_y + 80
    
    # COLUMN 1 (Left side - 40% width)
    # Name with icon
    name_icon = "👤"
    draw.text((box_x + 30, info_start_y), name_icon, fill='white', font=font_medium)
    
    # Truncate long names
    display_name = user_name
    if len(user_name) > 18:
        display_name = user_name[:15] + "..."
    draw.text((box_x + 70, info_start_y), display_name, fill='white', font=font_medium)
    
    # ID with icon
    id_icon = "🆔"
    draw.text((box_x + 30, info_start_y + 45), id_icon, fill='#00ffaa', font=font_medium)
    draw.text((box_x + 70, info_start_y + 45), str(user_id), fill='#00ffaa', font=font_medium)
    
    # COLUMN 2 (Right side - 40% width)
    # Username with icon
    username_icon = "📱"
    draw.text((box_x + 320, info_start_y), username_icon, fill='#87ceeb', font=font_medium)
    
    username_text = f"@{username[:12]}" if username else "No Username"
    draw.text((box_x + 360, info_start_y), username_text, fill='#87ceeb', font=font_medium)
    
    # Members count with icon
    members_icon = "👥"
    draw.text((box_x + 320, info_start_y + 45), members_icon, fill='#ffa500', font=font_medium)
    draw.text((box_x + 360, info_start_y + 45), str(member_count), fill='#ffa500', font=font_medium)
    
    # Add vertical separator line between columns
    separator_x = box_x + 300
    draw.line([(separator_x, info_start_y-5), (separator_x, info_start_y + 90)], 
              fill='#555555', width=1)
    
    # ========== WELCOME TEXT (BIG AND BOLD) ==========
    # Welcome text with shadow effect
    welcome_text = "WELCOME"
    draw.text((52, welcome_y+2), welcome_text, fill='#000000', font=font_large)  # Shadow
    draw.text((50, welcome_y), welcome_text, fill='#FFD700', font=font_large)    # Main text
    
    # Add chat name with gradient
    chat_display = chat_name
    if len(chat_name) > 30:
        chat_display = chat_name[:27] + "..."
    chat_text = f"to {chat_display}"
    draw.text((52, welcome_y + 52), chat_text, fill='#000000', font=font_medium)  # Shadow
    draw.text((50, welcome_y + 50), chat_text, fill='#FFFFFF', font=font_medium)  # Main text
    
    # Add decorative arrow
    arrow_x = pfp_x + 220
    arrow_y = pfp_y + 100
    draw.text((arrow_x, arrow_y), "➡️", fill='#FFD700', font=font_large)
    
    # ========== DECORATIVE ELEMENTS ==========
    # Top decorative corners
    draw.text((box_x - 35, box_y + 25), "⭐", fill='#FFD700', font=font_medium)
    draw.text((box_x + box_width + 5, box_y + 25), "🌟", fill='#FFD700', font=font_medium)
    
    # Bottom decorative line with pattern
    for i in range(0, 900, 30):
        draw.line([(50+i, 470), (65+i, 470)], fill='#FFD700', width=3)
    
    # Add timestamp at bottom (centered)
    timestamp = time.strftime("%d %b %Y • %I:%M %p")
    
    if hasattr(draw, 'textbbox'):
        timestamp_bbox = draw.textbbox((0, 0), timestamp, font=font_small)
        timestamp_width = timestamp_bbox[2] - timestamp_bbox[0]
    else:
        timestamp_width = draw.textlength(timestamp, font=font_small)
    
    timestamp_x = (width - timestamp_width) // 2
    draw.text((timestamp_x, 480), timestamp, fill='#888888', font=font_small)
    
    # Add footer text
    footer = "Welcome to our community! 🌟"
    
    if hasattr(draw, 'textbbox'):
        footer_bbox = draw.textbbox((0, 0), footer, font=font_small)
        footer_width = footer_bbox[2] - footer_bbox[0]
    else:
        footer_width = draw.textlength(footer, font=font_small)
    
    footer_x = (width - footer_width) // 2
    draw.text((footer_x, 455), footer, fill='#aaaaaa', font=font_small)
    
    # Save image with high quality
    output_path = f"{DOWNLOADS_DIR}/welcome_{user_id}_{int(time.time())}.jpg"
    image.save(output_path, quality=95, optimize=True)
    
    LOGGER.info(f"Created welcome image: {output_path}")
    return output_path

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group)
async def greet_new_member(client, member: ChatMemberUpdated):
    """Automatically sends a welcome message when a new member joins."""
    
    # Check if it's a new member joining
    if not member.new_chat_member or member.old_chat_member:
        return
    
    # Check if user exists
    user = member.new_chat_member.user
    if not user:
        return
    
    chat = member.chat
    
    # Skip bots
    if user.is_bot:
        return
    
    # Debug log
    LOGGER.info(f"New member joined: {user.first_name} in {chat.title}")
    
    # Cooldown check (5 seconds)
    current_time = time.time()
    if chat.id in temp.cooldown:
        if current_time - temp.cooldown[chat.id] < 5:
            return
    
    temp.cooldown[chat.id] = current_time
    
    try:
        # Get member count
        try:
            count = await client.get_chat_members_count(chat.id)
        except Exception as e:
            LOGGER.error(f"Error getting member count: {e}")
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
                default_path = "EsproChat/assets/upic.png"
                if not os.path.exists(default_path):
                    # Create default image
                    default_img = Image.new('RGB', (200, 200), color='#4a4aff')
                    draw_default = ImageDraw.Draw(default_img)
                    draw_default.ellipse([20, 20, 180, 180], fill='#2d2d44')
                    draw_default.text((70, 85), "USER", fill='white')
                    os.makedirs("EsproChat/assets", exist_ok=True)
                    default_img.save(default_path)
                
                pfp_path = default_path
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
                raise Exception(f"Image creation failed: {image_path}")
            
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
            except Exception as e:
                LOGGER.warning(f"Error deleting old welcome: {e}")
        
        # Get bot info for button
        try:
            me = await client.get_me()
            bot_username = me.username
            bot_name = me.first_name
        except Exception as e:
            LOGGER.error(f"Error getting bot info: {e}")
            bot_username = "unknown_bot"
            bot_name = "EsproChat"
        
        # Prepare caption
        caption = f"""
**🎉 Welcome to {chat.title}! 🎉**

**✨ New Member Details:**
• **Name:** {user.mention()}
• **ID:** `{user.id}`
• **Username:** @{user.username or 'Not Set'}
• **Total Members:** `{count}`

Enjoy your stay! Feel free to introduce yourself. 😊
"""
        
        # Send welcome message
        try:
            message = await client.send_photo(
                chat_id=chat.id,
                photo=image_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🤖 Add Bot to Group", 
                        url=f"https://t.me/{bot_username}?startgroup=true"
                    )],
                    [InlineKeyboardButton(
                        "📢 Updates Channel", 
                        url="https://t.me/EsproUpdate"
                    )]
                ])
            )
            
            temp.last[chat.id] = message
            LOGGER.info(f"Welcome sent successfully for {user.first_name}")
            
        except Exception as e:
            LOGGER.error(f"Error sending photo: {e}")
            # Try text message as fallback
            await send_text_welcome(client, chat.id, user, chat.title, count)
        
        # Cleanup temporary files
        try:
            # Delete downloaded PFP if it's temporary
            if pfp_path and "temp_pp_" in pfp_path and os.path.exists(pfp_path):
                os.remove(pfp_path)
            
            # Delete welcome image after delay
            await asyncio.sleep(10)  # Wait 10 seconds before cleanup
            if os.path.exists(image_path):
                os.remove(image_path)
                LOGGER.info(f"Cleaned up image: {image_path}")
                
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
            bot_username = "unknown_bot"
        
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
                [InlineKeyboardButton(
                    "🤖 Add Bot to Group", 
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )],
                [InlineKeyboardButton(
                    "📢 Updates Channel", 
                    url="https://t.me/EsproUpdate"
                )]
            ])
        )
        
        temp.last[chat_id] = message
        LOGGER.info(f"Text welcome sent for {user.first_name}")
        
    except Exception as e:
        LOGGER.error(f"Error sending text welcome: {e}")

# Test command for manual welcome
@app.on_message(filters.command("testwelcome") & filters.group & filters.user("self"))
async def test_welcome_command(client, message):
    """Test command to trigger welcome manually (bot owner only)."""
    try:
        # Simulate new member join with command sender
        from pyrogram.types import ChatMember
        
        fake_member = ChatMemberUpdated(
            chat=message.chat,
            from_user=message.from_user,
            date=int(time.time()),
            old_chat_member=None,
            new_chat_member=ChatMember(
                user=message.from_user,
                status=enums.ChatMemberStatus.MEMBER,
                joined_date=int(time.time()),
                until_date=None
            )
        )
        
        await greet_new_member(client, fake_member)
        
        # Delete the test command
        try:
            await message.delete()
        except:
            pass
            
    except Exception as e:
        LOGGER.error(f"Test welcome error: {e}")
        await message.reply(f"❌ Error: {str(e)[:100]}")

# Ping command to check if bot is alive
@app.on_message(filters.command("ing"))
async def ping_command(client, message):
    """Simple ping command."""
    start_time = time.time()
    msg = await message.reply("🏓 Pong!")
    end_time = time.time()
    await msg.edit(f"🏓 Pong! `{round((end_time - start_time) * 1000, 2)}ms`")

LOGGER.info("Welcome module loaded successfully!")
