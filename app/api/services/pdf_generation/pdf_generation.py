import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from loguru import logger
from app.api.services.object_storage.r2_storage import R2Storage

class doc_generator:
    @staticmethod
    async def pdf_generator(session_id: str) -> str:
        SUPPORTED_FORMATS = {'.jpeg', '.jpg', '.png'}
        logger.info(f"Starting PDF generation for session: {session_id}")
        
        try:
            # Use R2Storage method
            all_files =await R2Storage.list_files(f"signature-images/session_id_{session_id}/")
            
            image_files = [
                key for key in all_files
                if any(key.lower().endswith(fmt) for fmt in SUPPORTED_FORMATS)
            ]
            
            if not image_files:
                logger.error(f"No image files found for session: {session_id}")
                raise Exception(f"No image files found for session {session_id}")
            
            image_files.sort()
            logger.info(f"Found {len(image_files)} image(s): {image_files}")
            
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
            
            page_image_count = 0
            positions = [
                (0, 2), (1, 2),  # Top row
                (0, 1), (1, 1),  # Middle row
                (0, 0), (1, 0),  # Bottom row
            ]
            
            for idx, r2_image_key in enumerate(image_files):
                try:
                    logger.info(f"Processing [{idx+1}/{len(image_files)}]: {r2_image_key}")
                    
                    # Use R2Storage method
                    image_bytes =await R2Storage.get_file(r2_image_key)
                    image_file = io.BytesIO(image_bytes)
                    
                    position_idx = page_image_count % 6
                    col, row = positions[position_idx]
                    x_start = MARGIN + col * CELL_WIDTH
                    y_start = MARGIN + row * CELL_HEIGHT
                    
                    img_reader = ImageReader(image_file)
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
                    display_filename = r2_image_key.split('/')[-1]
                    
                    if len(display_filename) > 25:
                        display_filename = display_filename[:22] + "..."
                    
                    c.drawCentredString(x_start + CELL_WIDTH / 2, filename_y, display_filename)
                    
                    page_image_count += 1
                    
                    if page_image_count == 6:
                        c.showPage()
                        page_image_count = 0
                        
                except Exception as e:
                    logger.warning(f"Could not process image '{r2_image_key}': {e}")
                    continue
            
            if page_image_count > 0:
                c.showPage()
            
            c.save()
            buffer.seek(0)
            
            pdf_filename = f"session_id_{session_id}.pdf"
            pdf_r2_key = f"Result_PDF/{session_id}/{pdf_filename}"
            
            # Use R2Storage method
            await R2Storage.put_file(pdf_r2_key, buffer.getvalue(), content_type='application/pdf')
            
            logger.info(f"PDF uploaded to R2: {pdf_r2_key}")
            return pdf_r2_key
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise Exception('Server error while generating PDF')
