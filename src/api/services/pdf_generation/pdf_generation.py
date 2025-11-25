import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm

IMAGE_FILEPATH = "C:\InfinityBit\Multiparty-signature-system\signature-images\HOD.jpeg"
OUTPUT_PDF_FILENAME = "123456.pdf"

def create_pdf_from_image(image_filepath: str, output_filepath: str):
    if not os.path.exists(image_filepath):
        print(f"Error: Image file not found at '{image_filepath}'")
        return
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    A4_WIDTH, A4_HEIGHT = A4

    MARGIN = 1.5 * cm
    DRAWABLE_WIDTH = A4_WIDTH - 2 * MARGIN
    DRAWABLE_HEIGHT = A4_HEIGHT - 2 * MARGIN

    try:
        img_reader = ImageReader(image_filepath)
        img_width, img_height = img_reader.getSize()
    
        width_ratio = DRAWABLE_WIDTH / img_width
        height_ratio = DRAWABLE_HEIGHT / img_height
        scale_factor = min(width_ratio, height_ratio)
        
        final_width = img_width * scale_factor
        final_height = img_height * scale_factor

        x_pos = MARGIN + (DRAWABLE_WIDTH - final_width) / 2
        y_pos = MARGIN + (DRAWABLE_HEIGHT - final_height) / 2

        c.drawImage(img_reader, x_pos, y_pos, width=final_width, height=final_height)
    
        c.showPage()
        c.save()

        buffer.seek(0)
        with open(output_filepath, "wb") as f:
            f.write(buffer.read())
            
        print("pdf generated")
        
        
    except Exception as e:
        print(f'Error: {e}')


if __name__ == "__main__":
    create_pdf_from_image(IMAGE_FILEPATH, OUTPUT_PDF_FILENAME)