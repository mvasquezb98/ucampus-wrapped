from PIL import Image, ImageDraw, ImageFont, ImageFilter
import barcode
from barcode.writer import ImageWriter
from typing import Union, Tuple
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ logger.info("")

# Create barcode from string
def generate_barcode(data: str, filename: str = "barcode.png"):
    CODE128 = barcode.get_barcode_class('code128')
    my_barcode = CODE128(data, writer=ImageWriter())
    full_path = my_barcode.save(filename, options={
        'module_height': 10,
        'font_size': 7,
        'text_distance': 7,
        'quiet_zone': 2,
    })
    img = Image.open(full_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # If pixel is white, make it transparent
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(full_path)
    return full_path

# Draw soft blur shadow text
# def draw_soft_shadow_text(base_img, position, text, font,
#                           text_color="black", shadow_color="black",
#                           shadow_offset=(2, 2), blur_radius=2):
def draw_soft_shadow_text(
    base_img,
    position,
    text,
    font,
    text_color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = "black",
    shadow_color: Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]] = "black",
    shadow_offset: Tuple[int, int] = (2, 2),
    blur_radius = 2
):
    x, y = position
    shadow_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_position = (x + shadow_offset[0], y + shadow_offset[1])
    shadow_draw.text(shadow_position, text, font=font, fill=shadow_color)

    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    base_img.alpha_composite(blurred_shadow)

    draw = ImageDraw.Draw(base_img)
    draw.text((x, y), text, font=font, fill=text_color)

def add_barcode_to_receipt(receipt_img, barcode_path, position=(20, 500)):
    barcode_img = Image.open(barcode_path).convert("RGBA")
    max_width = 300
    aspect_ratio = barcode_img.height / barcode_img.width
    new_height = int(max_width * aspect_ratio - 100)
    barcode_img = barcode_img.resize((max_width, new_height))
    receipt_img.paste(barcode_img, position, barcode_img)

    return receipt_img

# Create the full receipt
def create_receipt_with_shadow_and_barcode(df, texture_path="texture2.jpg", barcode_text="Acta Milagrosa", output_path="receipt.png"):
    # Fixed sizes
    width = 400
    row_height = 40
    header_height = 100
    spacing_after_courses = 20
    avg_block_height = 60
    barcode_height = 70
    padding_bottom = 20

    # Compute total height based on data
    num_rows = len(df)
    height = header_height + num_rows * row_height + spacing_after_courses + avg_block_height + barcode_height + padding_bottom

    # Load your texture
    background = Image.open(texture_path).convert("RGBA")
    background = background.resize((width, height))

    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))

    # Draw on the texture
    img = background.copy()
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font = ImageFont.truetype("IBMPlexMono-Regular.ttf", 16)
        bold_font = ImageFont.truetype("IBMPlexMono-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
        bold_font = font  # fallback if bold font not found
        logger.exception("⚠️ fallback to default fonts. Custom fonts not found in assets.")
    
    # Example placeholder (replace this with your actual value from df or a separate variable)
    title_line1 = "Acta Milagrosa"
    title_line2 = "MA1002 - Introducción al Álgebra"

    # Fonts
    title_font_size = 20

    # Measure line widths
    bbox1 = draw.textbbox((0, 0), title_line1, font=bold_font)
    bbox2 = draw.textbbox((0, 0), title_line2, font=bold_font)

    line1_w = bbox1[2] - bbox1[0]
    line2_w = bbox2[2] - bbox2[0]

    # X positions to center them
    line1_x = (width - line1_w) // 2
    line2_x = (width - line2_w) // 2

    # Y positions (spaced nicely)
    line1_y = 30
    line2_y = line1_y + 30  # Adjust this spacing as needed

    # Draw both lines
    draw_soft_shadow_text(img, (line1_x, line1_y), title_line1, font,
                          text_color="black", shadow_color=(0, 0, 0, 90),
                          shadow_offset=(3, 3), blur_radius=3)
    draw_soft_shadow_text(img, (line2_x, line2_y), title_line2, font,
                          text_color="black", shadow_color=(0, 0, 0, 90),
                          shadow_offset=(3, 3), blur_radius=3)


    # Update y so your content starts below the title
    y = line2_y + 30

    # Draw courses (left course, right grade + year)
    y = header_height
    padding = 20
    for _, row in df.iterrows():
        course = row['Evaluación']
        grade = row['Promedio']
        left_text = course[:30]
        right_text = f"{grade}"

        draw.text((padding, y), left_text, font=font, fill='black')

        # ✅ Set grade color based on value
        grade_color = 'red' if grade < 4.0 else 'black'
        bbox = draw.textbbox((0, 0), right_text, font=font)
        right_w = bbox[2] - bbox[0]
        draw.text((width - right_w - padding, y), right_text, font=font, fill=grade_color)

        y += row_height
    
    # Draw thin line
    line_y = y + 10
    draw.line([(padding, y), (width - padding, y)], fill=(100, 100, 100), width=1)

    exam_text = "Examen"
    exam_series = df.loc[df['Evaluación'] == 'Examen', 'Promedio']
    exam_value = exam_series.iloc[0] if not exam_series.empty else ""

    # Draw text left-aligned
    draw.text((padding, line_y + 10), f"{exam_text}", font=font, fill='black')
    bbox = draw.textbbox((0, 0), f"{exam_value}", font=bold_font)
    exam_w = bbox[2] - bbox[0]
    draw.text((width - exam_w - padding, line_y + 10), f"{exam_value}", font=bold_font, fill='black') #padding + 140

    y = line_y  # update y

    # Draw thin line
    line_y = y + 10
    draw.line([(padding, y), (width - padding, y)], fill=(100, 100, 100), width=1)


    avg_text = "Nota Final"
    avg_series = df.loc[(df['Evaluación']=='Nota Final')|(df['Evaluación']=='Acta'), 'Promedio']
    avg_value = avg_series.iloc[0] if not avg_series.empty else ""

    # Draw text left-aligned
    draw.text((padding, line_y + 10), f"{avg_text}", font=font, fill='black')
    bbox = draw.textbbox((0, 0), f"{avg_value}", font=bold_font)
    avg_w = bbox[2] - bbox[0]
    draw.text((width - avg_w - padding, line_y + 10), f"{avg_value}", font=bold_font, fill='black') #padding + 140

    y = line_y  # update y for barcode position below

    # Barcode
    barcode_path = generate_barcode(barcode_text, "temp_barcode")
    add_barcode_to_receipt(img, barcode_path, position=(50, y + 50))

    img.convert("RGB").save(output_path)
    logger.info(f"💾 Receipt saved at {output_path}")
