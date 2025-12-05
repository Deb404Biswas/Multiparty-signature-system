import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from loguru import logger
from src.api.services.object_storage.r2_storage import s3_client, R2_Config

class doc_generator:
    @staticmethod
    async def pdf_generator(session_id: str) -> str:
        SUPPORTED_FORMATS = {'.jpeg', '.jpg', '.png'}
        logger.info(f"Starting PDF generation for session: {session_id}")
        try:

            response = s3_client.list_objects_v2(
                Bucket=R2_Config.BUCKET_NAME,
                Prefix=f"signature-images/session_id_{session_id}/"
            )

            image_files = []
            if 'Contents' in response:
                image_files = [
                    obj['Key'] for obj in response['Contents']
                    if any(obj['Key'].lower().endswith(fmt) for fmt in SUPPORTED_FORMATS)
                ]
            
            if not image_files:
                logger.error(f"No image files found in R2 for session: {session_id}")
                raise Exception(f"No image files found for session {session_id}")
            
            image_files.sort()
            logger.info(f"Found {len(image_files)} image(s) in R2: {image_files}")
            
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
                (0, 2),  # Top-left
                (1, 2),  # Top-right
                (0, 1),  # Middle-left
                (1, 1),  # Middle-right
                (0, 0),  # Bottom-left
                (1, 0),  # Bottom-right
            ]

            for idx, r2_image_key in enumerate(image_files):
                try:
                    logger.info(f"Processing [{idx+1}/{len(image_files)}]: {r2_image_key}")
                    
                    # Download image from R2
                    image_response = s3_client.get_object(
                        Bucket=R2_Config.BUCKET_NAME,
                        Key=r2_image_key
                    )
                    image_bytes = image_response['Body'].read()
                    
                    # Create BytesIO from downloaded image
                    image_file = io.BytesIO(image_bytes)
                    
                    # Get position on PDF
                    position_idx = page_image_count % 6
                    col, row = positions[position_idx]
                    x_start = MARGIN + col * CELL_WIDTH
                    y_start = MARGIN + row * CELL_HEIGHT
                    
                    # Draw image on canvas
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
                    
                    # Add filename label
                    filename_y = y_start + 0.25 * cm
                    c.setFont("Helvetica", 8)
                    
                    # Extract filename from R2 key (session_id/filename.jpeg)
                    display_filename = r2_image_key.split('/')[-1]
                    if len(display_filename) > 25:
                        display_filename = display_filename[:22] + "..."
                    
                    c.drawCentredString(x_start + CELL_WIDTH / 2, filename_y, display_filename)
                    
                    page_image_count += 1
                    
                    # Create new page after 6 images
                    if page_image_count == 6:
                        c.showPage()
                        page_image_count = 0
                        
                except Exception as e:
                    logger.warning(f"Could not process image '{r2_image_key}': {e}")
                    continue
            
            # Save final page if it has content
            if page_image_count > 0:
                c.showPage()
            
            c.save()
            buffer.seek(0)

            pdf_filename = f"session_id_{session_id}.pdf"
            pdf_r2_key = f"Result_PDF/{session_id}/{pdf_filename}"
            
            s3_client.put_object(
                Bucket=R2_Config.BUCKET_NAME,
                Key=pdf_r2_key,
                Body=buffer.getvalue(),
                ContentType='application/pdf'
            )
            
            logger.info(f"PDF uploaded to R2: {pdf_r2_key}")
            return pdf_r2_key
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise {
                'status':500,
                'message':'Server error while generating pdf'
            }