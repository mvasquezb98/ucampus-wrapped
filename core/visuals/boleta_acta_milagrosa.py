from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.ImageFont import FreeTypeFont
import barcode
from barcode.writer import ImageWriter
from typing import Union, Tuple, Literal
import logging
from config.logger import setup_logger
import pandas as pd

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Create barcode from string
def generate_barcode(
    data: str,
    filename: str = "barcode.png"
) -> str:
    """
    Generate a barcode image from a string and save it with transparent background.

    Args:
        data (str): The text to encode as a barcode.
        filename (str, optional): The filename to save the barcode image. 
            Defaults to "barcode.png".

    Returns:
        str: The full path of the saved barcode image.

    Raises:
        Exception: If the barcode generation or image processing fails.
    """
    logger.info("🚀 Generando código de barras...")
    logger.debug(f"ℹ️️ Parámetros: data='{data}', filename='{filename}'")
    
    try:
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
        logger.info(f"💾 Código de barras guardado en: {full_path}")
        return full_path
    except Exception as e:
        logger.exception("❌ Error al generar el código de barras")
        raise

def draw_soft_shadow_text(
    base_img: Image.Image,
    position: tuple[float, Literal[30, 60]],
    text: str,
    font: Union[FreeTypeFont, ImageFont.ImageFont],
    text_color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]] = "black",
    shadow_color: Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]] = "black",
    shadow_offset: Tuple[int, int] = (2, 2),
    blur_radius: int = 2
) -> None:
    """
    Draw text with a soft blurred shadow on an image.

    This function creates a shadow layer behind the text, applies a Gaussian
    blur to soften the shadow, composites it over the base image, and then
    draws the main text in the specified color.

    Args:
        base_img (PIL.Image.Image): The base image where the text will be drawn.
        position (tuple[float, Literal[30, 60]]): The (x, y) coordinates for 
            the text placement.
        text (str): The text string to render.
        font (Union[FreeTypeFont, ImageFont.ImageFont]): The font object used
            to render the text.
        text_color (Union[str, Tuple[int, int, int], Tuple[int, int, int, int]], optional):
            Color of the main text. Can be a string (e.g., "black"), an RGB
            tuple, or an RGBA tuple. Defaults to "black".
        shadow_color (Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int]], optional):
            Color of the shadow text. Can be a string, integer grayscale, RGB,
            or RGBA value. Defaults to "black".
        shadow_offset (Tuple[int, int], optional): Offset (dx, dy) applied to
            the shadow relative to the text position. Defaults to (2, 2).
        blur_radius (int, optional): Radius for the Gaussian blur applied to
            the shadow. Higher values produce a softer shadow. Defaults to 2.

    Returns:
        None: The function modifies the base image in place.
    """
    logger.debug(f"🖊️ Dibujando texto con sombra: '{text}' en posición {position}")
    x, y = position
    shadow_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_position = (x + shadow_offset[0], y + shadow_offset[1])
    shadow_draw.text(shadow_position, text, font=font, fill=shadow_color)

    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    base_img.alpha_composite(blurred_shadow)

    draw = ImageDraw.Draw(base_img)
    draw.text((x, y), text, font=font, fill=text_color)
    logger.debug("✅ Texto con sombra dibujado")

def add_barcode_to_receipt(
    receipt_img: Image.Image,
    barcode_path: str,
    position: Tuple[int,int] = (20, 500)
) -> Image.Image:
    """
    Insert a barcode image into a receipt image at a specified position.

    The function loads a barcode from the given file path, converts it to RGBA,
    resizes it while maintaining its aspect ratio (with a fixed maximum width),
    and pastes it onto the receipt image at the provided coordinates.

    Args:
        receipt_img (PIL.Image.Image): The base receipt image where the barcode
            will be inserted.
        barcode_path (str): Path to the image file containing the barcode.
        position (Tuple[int, int], optional): (x, y) coordinates in the receipt
            image where the barcode will be placed. Defaults to (20, 500).

    Returns:
        PIL.Image.Image: The updated receipt image with the barcode inserted.

    Raises:
        Exception: If there is an error loading, resizing, or pasting the barcode.
    """
    logger.info(f"ℹ️ Insertando código de barras en el recibo desde: {barcode_path}")
    try:
        barcode_img = Image.open(barcode_path).convert("RGBA")
        max_width = 300
        aspect_ratio = barcode_img.height / barcode_img.width
        new_height = int(max_width * aspect_ratio - 100)
        barcode_img = barcode_img.resize((max_width, new_height))
        receipt_img.paste(barcode_img, position, barcode_img)
        logger.info(f"✅ Código de barras insertado en posición {position}")
        return receipt_img
    except Exception as e:
        logger.exception(f"❌ Error al añadir el código de barras al recibo: {e}")
        raise

# Create the full receipt
def create_receipt_with_shadow_and_barcode(
    df: pd.DataFrame,
    texture_path: str = "texture2.jpg",
    barcode_text: str = "Acta Milagrosa",
    output_path: str = "receipt.png"
) -> None:
    """
    Create a receipt image with shadowed text, course grades, and a barcode.

    The function generates a styled receipt image using a textured background,
    draws course evaluations and their corresponding grades from a DataFrame,
    highlights exam and final grades, and appends a generated barcode at the
    bottom. Titles are drawn with soft shadows for improved readability, and
    grades below 4.0 are displayed in red to indicate failure.

    Args:
        df (pandas.DataFrame): DataFrame containing evaluation results with at
            least two columns:
            - "Evaluación" (str): Name of the evaluation (e.g., "Examen").
            - "Promedio" (float): Grade or score associated with the evaluation.
        texture_path (str, optional): Path to the texture image used as the
            background of the receipt. Defaults to "texture2.jpg".
        barcode_text (str, optional): Text to encode into a barcode that will be
            inserted at the bottom of the receipt. Defaults to "Acta Milagrosa".
        output_path (str, optional): Path where the final receipt image will be
            saved. Defaults to "receipt.png".

    Returns:
        None: The function saves the generated receipt image to the specified path.

    Raises:
        Exception: If loading the texture, fonts, barcode generation, or image
        saving fails.
    """
    logger.info("🚀 Creando recibo con sombra y código de barras...")
    logger.debug(f"📊 DataFrame con {len(df)} filas")
    logger.debug(f"📂 Parámetros: texture='{texture_path}', barcode_text='{barcode_text}', output='{output_path}'")

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
    logger.debug(f"📏 Calculando altura total del recibo: {height}px")

    # Load your texture
    try:
        background = Image.open(texture_path).convert("RGBA")
        background = background.resize((width, height))
        img = background.copy()
        logger.info("🎨 Textura cargada correctamente")
    except Exception:
        logger.exception("❌ Error al cargar la textura de fondo")
        raise

    # Draw on the texture
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font = ImageFont.truetype("IBMPlexMono-Regular.ttf", 16)
        bold_font = ImageFont.truetype("IBMPlexMono-Bold.ttf", 16)
        logger.info("✅ Fuentes personalizadas cargadas")
    except:
        font = ImageFont.load_default()
        bold_font = font  # fallback if bold font not found
        logger.exception("⚠️ No se encontraron fuentes personalizadas. Se usará la fuente por defecto")
    
    # Example placeholder (replace this with your actual value from df or a separate variable)
    title_line1 = "Acta Milagrosa"
    title_line2 = "MA1002 - Introducción al Álgebra"

    # Draw titles
    logger.info("🖊️ Dibujando títulos del recibo...")
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

    logger.info("📦 Dibujando cursos y notas...")
    # Draw courses (left course, right grade + year)
    y = header_height
    padding = 20
    for _, row in df.iterrows():
        course = row['Evaluación']
        grade = row['Promedio']
        left_text = course[:30]
        right_text = f"{grade}"

        draw.text((padding, y), left_text, font=font, fill='black')

        # Set grade color based on value
        grade_color = 'red' if grade < 4.0 else 'black'
        bbox = draw.textbbox((0, 0), right_text, font=font)
        right_w = bbox[2] - bbox[0]
        draw.text((width - right_w - padding, y), right_text, font=font, fill=grade_color)

        y += row_height
    
    # Draw thin line
    line_y = y + 10
    draw.line([(padding, y), (width - padding, y)], fill=(100, 100, 100), width=1)

    # Nota examen
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

    # Nota final
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
    logger.info(f"💾 Recibo guardado en: {output_path}")