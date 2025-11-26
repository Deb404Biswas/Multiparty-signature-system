import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm

class doc_generator:
    def pdf_generator(session_id):
        IMAGE_DIRECTORY = r"C:\InfinityBit\Multiparty-signature-system\signature-images"
        OUTPUT_PDF_FILENAME = f"session_id_{session_id}.pdf"
        SUPPORTED_FORMATS = {'.jpeg', '.jpg', '.png'}
        def create_pdf_with_6_images_per_page(image_directory: str, output_filepath: str):
            if not os.path.isdir(image_directory):
                print(f"Error: Directory not found at '{image_directory}'")
                return
            image_files = [
                f for f in os.listdir(image_directory)
                if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS
            ]
            if not image_files:
                print(f"Error: No image files found in '{image_directory}'")
                return

            image_files.sort()
            print(f"Found {len(image_files)} image(s): {image_files}")
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            A4_WIDTH, A4_HEIGHT = A4
            MARGIN = 0.8 * cm
            PAGE_MARGIN_BOTTOM = 1 * cm

            USABLE_WIDTH = A4_WIDTH - 2 * MARGIN
            USABLE_HEIGHT = A4_HEIGHT - 2 * MARGIN - PAGE_MARGIN_BOTTOM

            CELL_WIDTH = USABLE_WIDTH / 2
            CELL_HEIGHT = USABLE_HEIGHT / 3
            
            IMAGE_MAX_WIDTH = CELL_WIDTH - 0.4 * cm
            IMAGE_MAX_HEIGHT = CELL_HEIGHT - 0.8 * cm 
            
            try:
                page_image_count = 0
                positions = [
                    (0, 2),  # Top-left
                    (1, 2),  # Top-right
                    (0, 1),  # Middle-left
                    (1, 1),  # Middle-right
                    (0, 0),  # Bottom-left
                    (1, 0),  # Bottom-right
                ]
                
                for idx, image_file in enumerate(image_files):
                    image_filepath = os.path.join(image_directory, image_file)
                    
                    try:
                        print(f"Processing [{idx+1}/{len(image_files)}]: {image_file}")
                        position_idx = page_image_count % 6
                        col, row = positions[position_idx]

                        x_start = MARGIN + col * CELL_WIDTH
                        y_start = MARGIN + row * CELL_HEIGHT

                        img_reader = ImageReader(image_filepath)
                        img_width, img_height = img_reader.getSize()
                        
                        width_ratio = IMAGE_MAX_WIDTH / img_width
                        height_ratio = IMAGE_MAX_HEIGHT / img_height
                        scale_factor = min(width_ratio, height_ratio)
                        
                        final_width = img_width * scale_factor
                        final_height = img_height * scale_factor

                        x_pos = x_start + (CELL_WIDTH - final_width) / 2
                        y_pos = y_start + (CELL_HEIGHT - final_height) / 2

                        c.drawImage(img_reader, x_pos, y_pos, width=final_width, height=final_height)

                        filename_y = y_start + 0.25 * cm
                        c.setFont("Helvetica", 8)

                        if len(image_file) > 25:
                            display_name = image_file[:22] + "..."
                        else:
                            display_name = image_file
                        
                        c.drawCentredString(x_start + CELL_WIDTH / 2, filename_y, display_name)
                        page_image_count += 1
                        
                        if page_image_count == 6:
                            c.showPage()
                            page_image_count = 0
                        
                    except Exception as e:
                        print(f"Warning: Could not process '{image_file}': {e}")
                        continue

                if page_image_count > 0:
                    c.showPage()

                c.save()
                buffer.seek(0)
                
                with open(output_filepath, "wb") as f:
                    f.write(buffer.read())
                
                print(f"\n✓ PDF generated successfully: {output_filepath}")
                
            except Exception as e:
                print(f"Error: {e}")

        if __name__ == "__main__":
            create_pdf_with_6_images_per_page(IMAGE_DIRECTORY, OUTPUT_PDF_FILENAME)