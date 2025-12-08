# ==================================
#    FINAL WELCOME MODULE (EsproChat)
# ==================================

from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops, ImageFilter
from logging import getLogger
import os
import time
import asyncio
import textwrap

LOGGER = getLogger(__name__)

# --- Directory Setup (Ensure 'downloads' directory exists) ---
DOWNLOADS_DIR = 'downloads'
if not os.path.isdir(DOWNLOADS_DIR):
    try:
        os.makedirs(DOWNLOADS_DIR)
    except Exception as e:
        LOGGER.error(f"Failed to create downloads directory: {e}")
        
# -------------------------------------------------------------

# --- Temporary Storage (Used only for deleting the previous welcome message) ---
class temp:
    """Stores the last sent welcome message for cleanup."""
    last = {}
    # Add cooldown to prevent spam
    cooldown = {}
    
# --- Image Processing Functions ---

def circle(pfp, size=(500, 500), brightness_factor=1.3):
    """Makes the profile picture circular and enhances brightness."""
    try:
        resize_filter = Image.Resampling.LANCZOS
    except AttributeError:
        # Fallback for older Pillow versions
        resize_filter = Image.ANTIALIAS
        
    pfp = pfp.resize(size, resize_filter).convert("RGBA")
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness_factor)
    
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, resize_filter)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    
    pfp.putalpha(mask)
    return pfp

def add_text_with_outline(draw, position, text, font, text_color, outline_color, outline_width=2):
    """Add text with outline for better visibility."""
    x, y = position
    
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=text_color)

def create_member_info_overlay(width, height, user_name, user_id, username, chat_title, member_count):
    """Create a transparent overlay with NEW MEMBER info to place on top of thumbnail."""
    # Create a transparent overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        # Try to load fonts
        font_path = "EsproChat/assets/font.ttf"
        try:
            title_font = ImageFont.truetype(font_path, 48)
            info_font = ImageFont.truetype(font_path, 36)
            value_font = ImageFont.truetype(font_path, 32)
            small_font = ImageFont.truetype(font_path, 28)
        except:
            # Fallback to default fonts
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Position for member info (TOP RIGHT CORNER)
        status_x = width - 420  # Right side with some margin
        status_y = 30
        
        # Create a semi-transparent rounded rectangle background
        bg_width = 400
        bg_height = 200
        bg_x1 = status_x
        bg_y1 = status_y
        bg_x2 = bg_x1 + bg_width
        bg_y2 = bg_y1 + bg_height
        
        # Draw background with rounded corners (gradient-like effect)
        draw.rounded_rectangle(
            [bg_x1, bg_y1, bg_x2, bg_y2],
            radius=25,
            fill=(20, 20, 60, 220)  # Dark blue with transparency
        )
        
        # Add decorative border
        draw.rounded_rectangle(
            [bg_x1-2, bg_y1-2, bg_x2+2, bg_y2+2],
            radius=27,
            outline='#FFD700',  # Gold border
            width=3
        )
        
        # Add title - NEW MEMBER INFO
        title_text = "✨ NEW MEMBER ✨"
        title_x = bg_x1 + (bg_width // 2)
        title_y = bg_y1 + 15
        
        # Center the title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = bg_x1 + (bg_width - title_width) // 2
        
        add_text_with_outline(
            draw=draw,
            position=(title_x, title_y),
            text=title_text,
            font=title_font,
            text_color='#FFD700',  # Gold color
            outline_color='black',
            outline_width=2
        )
        
        # Add user name
        display_name = user_name if len(user_name) < 18 else user_name[:15] + "..."
        name_text = f"👑 {display_name}"
        name_x = bg_x1 + 15
        name_y = bg_y1 + 65
        
        add_text_with_outline(
            draw=draw,
            position=(name_x, name_y),
            text=name_text,
            font=info_font,
            text_color='white',
            outline_color='black',
            outline_width=1
        )
        
        # Add user ID
        id_text = f"🆔: {user_id}"
        id_x = bg_x1 + 15
        id_y = bg_y1 + 105
        
        add_text_with_outline(
            draw=draw,
            position=(id_x, id_y),
            text=id_text,
            font=value_font,
            text_color='#00FFAA',  # Light green
            outline_color='black',
            outline_width=1
        )
        
        # Add username
        user_text = f"👤: @{username}" if username else "👤: No Username"
        user_x = bg_x1 + 15
        user_y = bg_y1 + 140
        
        add_text_with_outline(
            draw=draw,
            position=(user_x, user_y),
            text=user_text,
            font=value_font,
            text_color='#87CEEB',  # Sky blue
            outline_color='black',
            outline_width=1
        )
        
        # Add group member count (bottom left of overlay)
        count_text = f"👥 Members: {member_count}"
        count_x = bg_x1 + 15
        count_y = bg_y1 + 175
        
        add_text_with_outline(
            draw=draw,
            position=(count_x, count_y),
            text=count_text,
            font=small_font,
            text_color='#FFA500',  # Orange
            outline_color='black',
            outline_width=1
        )
        
        # Add decorative elements
        # Top left star
        star_x = bg_x1 - 30
        star_y = bg_y1 + 20
        draw.text((star_x, star_y), "⭐", font=title_font, fill='yellow')
        
        # Bottom right star
        star2_x = bg_x2 + 10
        star2_y = bg_y2 - 40
        draw.text((star2_x, star2_y), "🌟", font=title_font, fill='yellow')
        
    except Exception as e:
        LOGGER.error(f"Error creating member info overlay: {e}")
    
    return overlay

def welcomepic(pic, user_name, chatname, user_id, username, member_count, brightness_factor=1.3):
    """
    Generates the welcome image dynamically.
    Uses 'EsproChat/assets/wel2.png' as the background if available, 
    otherwise uses a solid color. PFP is moved to the left side.
    NEW MEMBER INFO OVERLAYED on top of thumbnail.
    """
    
    BG_WIDTH, BG_HEIGHT = 1280, 720
    try:
        resize_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resize_filter = Image.ANTIALIAS
        
    # --- Background Selection (Using the provided path as a background) ---
    background_path = "EsproChat/assets/wel2.png"
    try:
        # Try loading the provided PNG as background
        background = Image.open(background_path).convert('RGB')
        background = background.resize((BG_WIDTH, BG_HEIGHT), resize_filter)
        
        # Add a slight blur effect to background for better text visibility
        background = background.filter(ImageFilter.GaussianBlur(radius=1))
    except FileNotFoundError:
        LOGGER.warning(f"Background image {background_path} not found. Using solid color.")
        # Fallback to Gradient Color
        background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#1a1a2e') 
        
        # Create gradient effect
        draw_bg = ImageDraw.Draw(background)
        for i in range(BG_HEIGHT):
            r = int(26 + (i/BG_HEIGHT)*50)
            g = int(26 + (i/BG_HEIGHT)*30)
            b = int(46 + (i/BG_HEIGHT)*40)
            draw_bg.line([(0, i), (BG_WIDTH, i)], fill=(r, g, b))
    except Exception as e:
        LOGGER.error(f"Error loading background image: {e}")
        background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#1a1a2e') 
        
    # --- PFP Processing ---
    try:
        pfp = Image.open(pic).convert("RGBA")
        pfp = circle(pfp, brightness_factor=brightness_factor) 
    except Exception as e:
        LOGGER.error(f"Error processing PFP: {e}")
        # Fallback to default PFP
        try:
            pfp = Image.open("EsproChat/assets/upic.png").convert("RGBA")
            pfp = circle(pfp, brightness_factor=brightness_factor)
        except Exception as e2:
            LOGGER.error(f"Failed to load fallback PFP: {e2}")
            # Create a simple colored circle as last resort
            pfp = Image.new('RGBA', (380, 380), color='#4A4AFF')
            pfp = circle(pfp, brightness_factor=brightness_factor)
    
    # PFP size and position
    PFP_SIZE = 380
    pfp = pfp.resize((PFP_SIZE, PFP_SIZE), resize_filter) 
    
    PFP_X = int(BG_WIDTH * 0.10)  
    PFP_Y = (BG_HEIGHT // 2) - (PFP_SIZE // 2)
    pfp_position = (PFP_X, PFP_Y)
    
    draw = ImageDraw.Draw(background)

    # Drawing a beautiful gradient border circle around the PFP
    BORDER_SIZE = PFP_SIZE + 30
    BORDER_X = PFP_X - 15 
    BORDER_Y = PFP_Y - 15 
    
    # Draw gradient border (multiple circles)
    for i in range(5):
        border_width = 5 - i
        color_value = 150 + i * 20
        draw.ellipse((BORDER_X-i, BORDER_Y-i, BORDER_X + BORDER_SIZE+i, BORDER_Y + BORDER_SIZE+i), 
                     outline=(color_value, color_value, 255), width=border_width)
    
    # Paste the PFP
    background.paste(pfp, pfp_position, pfp)
    
    # --- CREATE AND ADD MEMBER INFO OVERLAY ON TOP OF THUMBNAIL ---
    member_info_overlay = create_member_info_overlay(
        width=BG_WIDTH,
        height=BG_HEIGHT,
        user_name=user_name,
        user_id=user_id,
        username=username,
        chat_title=chatname,
        member_count=member_count
    )
    
    # Composite the overlay onto the background (ON TOP OF EVERYTHING)
    background = background.convert('RGBA')
    background = Image.alpha_composite(background, member_info_overlay)
    background = background.convert('RGB')
    
    # Add welcome text (LEFT SIDE, BELOW PFP)
    try:
        # Load font for welcome text
        user_font_path = "EsproChat/assets/font.ttf"
        try:
            welcome_font = ImageFont.truetype(user_font_path, 80)
            chat_font = ImageFont.truetype(user_font_path, 60)
            decorative_font = ImageFont.truetype(user_font_path, 40)
        except:
            welcome_font = ImageFont.load_default()
            chat_font = ImageFont.load_default()
            decorative_font = ImageFont.load_default()
            
        # Create a new draw object for the final image
        final_draw = ImageDraw.Draw(background)
        
        # WELCOME text (big and centered)
        welcome_text = "WELCOME"
        welcome_x = PFP_X + 50
        welcome_y = PFP_Y + PFP_SIZE + 40
        
        add_text_with_outline(
            draw=final_draw,
            position=(welcome_x, welcome_y),
            text=welcome_text,
            font=welcome_font,
            text_color='#FFFFFF',  # White
            outline_color='#FF6B6B',  # Coral red outline
            outline_width=4
        )
        
        # To [Chat Name] text
        chat_display = chatname if len(chatname) < 25 else chatname[:22] + "..."
        to_chat_text = f"to {chat_display}"
        to_chat_x = welcome_x + 30
        to_chat_y = welcome_y + 100
        
        add_text_with_outline(
            draw=final_draw,
            position=(to_chat_x, to_chat_y),
            text=to_chat_text,
            font=chat_font,
            text_color='#00FFFF',  # Cyan
            outline_color='black',
            outline_width=3
        )
        
        # Decorative line under welcome text
        line_start_x = welcome_x - 20
        line_end_x = welcome_x + 500
        line_y = welcome_y + 85
        final_draw.line([(line_start_x, line_y), (line_end_x, line_y)], 
                       fill='#FFD700', width=4)
        
        # Add decorative emojis
        # Left side emoji
        emoji1_x = welcome_x - 60
        emoji1_y = welcome_y + 20
        final_draw.text((emoji1_x, emoji1_y), "🎉", font=decorative_font, fill='yellow')
        
        # Right side emoji
        emoji2_x = welcome_x + 520
        emoji2_y = welcome_y + 20
        final_draw.text((emoji2_x, emoji2_y), "🎊", font=decorative_font, fill='yellow')
        
        # Bottom decorative text
        bottom_text = "We're glad to have you here! 🌟"
        bottom_x = PFP_X + 100
        bottom_y = BG_HEIGHT - 80
        
        add_text_with_outline(
            draw=final_draw,
            position=(bottom_x, bottom_y),
            text=bottom_text,
            font=decorative_font,
            text_color='#98FB98',  # Pale green
            outline_color='black',
            outline_width=2
        )
        
    except Exception as e:
        LOGGER.error(f"Error adding welcome text to image: {e}")
    
    # Add a subtle vignette effect
    try:
        # Create vignette
        vignette = Image.new('L', (BG_WIDTH, BG_HEIGHT), color=255)
        draw_vignette = ImageDraw.Draw(vignette)
        
        # Draw white to black radial gradient
        for i in range(0, max(BG_WIDTH, BG_HEIGHT)//2, 10):
            alpha = int(255 * (i / (max(BG_WIDTH, BG_HEIGHT)//2)))
            draw_vignette.ellipse(
                [BG_WIDTH//2 - i, BG_HEIGHT//2 - i, 
                 BG_WIDTH//2 + i, BG_HEIGHT//2 + i],
                outline=alpha
            )
        
        # Apply vignette
        background = background.convert('RGBA')
        vignette = vignette.resize((BG_WIDTH, BG_HEIGHT))
        background.putalpha(vignette)
        background = background.convert('RGB')
        
    except Exception as e:
        LOGGER.error(f"Error adding vignette effect: {e}")
    
    # Saving file
    file_path = f"{DOWNLOADS_DIR}/welcome#{user_id}_{int(time.time())}.png" 
    try:
        background.save(file_path, quality=95, optimize=True)  # High quality with optimization
    except Exception as e:
        LOGGER.error(f"Error saving welcome image: {e}")
        return None
    return file_path

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group, group=-3)
async def greet_new_member(_, member: ChatMemberUpdated):
    """
    Automatically sends a welcome message when a new member joins.
    """
    # Anti-spam cooldown check
    chat_id = member.chat.id
    current_time = time.time()
    
    # Check if we sent a welcome recently (within 5 seconds)
    if chat_id in temp.cooldown:
        if current_time - temp.cooldown[chat_id] < 5:
            return
    temp.cooldown[chat_id] = current_time
    
    welcomeimg = None
    
    if not (member.new_chat_member and not member.old_chat_member):
        return

    if not member.new_chat_member.user:
        return 
        
    user = member.new_chat_member.user
    user_id = user.id
    chat_title = member.chat.title
    
    # Skip if user is a bot (optional)
    if user.is_bot:
        return
    
    try:
        count = await app.get_chat_members_count(chat_id)
    except Exception as e:
        LOGGER.warning(f"Could not get member count for {chat_title}: {e}")
        count = "Unknown"

    # Download PFP
    pic = None
    try:
        if user.photo and user.photo.big_file_id:
            pic_filename = f"pp{user_id}_{int(time.time())}.jpg" 
            temp_pic_path = os.path.join(DOWNLOADS_DIR, pic_filename) 
            pic = await app.download_media(
                user.photo.big_file_id, file_name=temp_pic_path
            )
        else:
            # No PFP, use default
            pic = "EsproChat/assets/upic.png"
    except Exception as e:
        LOGGER.error(f"Error downloading PFP: {e}")
        pic = "EsproChat/assets/upic.png"
        
    # Delete last welcome message for cleanup (if exists)
    old = temp.last.get(chat_id)
    if old:
        try:
            await old.delete()
        except Exception as e:
            LOGGER.error(f"Error deleting old welcome message: {e}")
            # Don't fail if we can't delete old message

    try:
        # Generate main image WITH MEMBER INFO OVERLAY
        welcomeimg = welcomepic(
            pic=pic,
            user_name=user.first_name or "User",
            chatname=chat_title,
            user_id=user_id,
            username=user.username or "NoUsername",
            member_count=count,
            brightness_factor=1.3
        )
        
        if not welcomeimg:
            LOGGER.error("Failed to generate welcome image")
            # Fallback to simple text welcome
            await send_text_welcome(chat_id, user, chat_title, count)
            return
        
        # Get bot username for the invite link
        bot_username = app.username
        
        # Define invite link
        add_link = f"https://t.me/{bot_username}?startgroup=true"
        
        # Prepare caption (simpler since info is already in image)
        caption = f"""
**🎉 Welcome to {chat_title}! 🎉**

We're excited to have you with us! 

**Member Info:**
• **Name:** {user.mention()}
• **ID:** `{user_id}`
• **Username:** @{user.username or 'Not Set'}
• **Total Members:** `{count}`

Feel free to introduce yourself and enjoy your stay! 🌟
"""
        
        # Send photo 
        msg = await app.send_photo(
            chat_id=chat_id,
            photo=welcomeimg,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🤖 Add Bot to Your Group", url=add_link)],
                [InlineKeyboardButton(text="📢 Join Updates Channel", url="https://t.me/EsproUpdate")],
            ])
        )
        
        # Store the new message for cleanup
        temp.last[chat_id] = msg
        
        # Auto-delete welcome image after sending (optional)
        await asyncio.sleep(3)  # Wait a bit before cleanup
        try:
            os.remove(welcomeimg)
        except Exception as e:
            LOGGER.warning(f"Could not delete welcome image: {e}")
        
    except Exception as e:
        LOGGER.error(f"Error sending welcome message: {e}")
        # Try to send a simple text welcome as fallback
        try:
            await send_text_welcome(chat_id, user, chat_title, count)
        except Exception as e2:
            LOGGER.error(f"Fallback welcome also failed: {e2}")
    finally:
        # Clean up downloaded PFP file after use
        if pic and os.path.exists(pic) and "pp" in os.path.basename(pic):
            try:
                os.remove(pic)
            except Exception as e:
                LOGGER.warning(f"Error deleting temporary PFP file: {e}")

async def send_text_welcome(chat_id, user, chat_title, count):
    """Fallback function to send text-only welcome"""
    bot_username = app.username
    add_link = f"https://t.me/{bot_username}?startgroup=true"
    
    caption = f"""
**🎉 Welcome to {chat_title}! 🎉**

**✨ New Member Details:**
• **Name:** {user.mention()}
• **ID:** `{user.id}`
• **Username:** @{user.username or 'Not Set'}
• **Total Members:** `{count}`

We're glad to have you here! Feel free to introduce yourself. 😊
"""
