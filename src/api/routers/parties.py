from fastapi import APIRouter,HTTPException,UploadFile,Form
from src.api.dependencies.database import DatabaseConnect
from src.api.services.image_analysis.sign_image_analysis import Sign_Detect_Extract
from starlette import status
from pathlib import Path
import shutil
from fastapi.responses import FileResponse
import os
from loguru import logger

logger.remove()
logger.add(
    "app.log",
    format="{time:MMMM D, YYYY - HH:mm:ss} {level} ----- {message}"
)
router=APIRouter(
    prefix='/parties/v1',
    tags=['Parties']
)

UPLOAD_DIR=Path('signature-images')

@router.post('/upload-image',status_code=status.HTTP_201_CREATED)
async def upload_image_signature(sign_image:UploadFile,party_role:str=Form(...),\
    party_id:str=Form(...),session_id:str=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_id,session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{session_id}')
    logger.info(f"{party_role} with {party_id} from session {session_id} uploading image through post parties/v1/upload-image endpoint")
    msg=''
    session_folder = UPLOAD_DIR / session_id
    session_folder.mkdir(parents=True, exist_ok=True)
    image_file_name=f'{party_role}_{party_id}.jpeg'
    image_file_path=session_folder/image_file_name
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        await Sign_Detect_Extract.signature_detect_extract(image_file_path)
        logger.info(f"Signature image is extracted from {sign_image.filename} and stored in {image_file_path}")
        session_doc=await DatabaseConnect.session_collection_find_one(session_id)
        parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
        parties_sign_filepath[f'{party_role}_{party_id}'] = str(image_file_path)
        update_data = {
            "$set": {
                "parties_sign_filepath":parties_sign_filepath
            }}
        await DatabaseConnect.session_collection_update_one(update_data,session_id)
        logger.info(f"{party_role} with {party_id} able to upload image.")
        logger.info(f"The image filepath in database is : {image_file_path}")
        msg=f'Signature extracted from {sign_image.filename} provided by {party_role} with id:{party_id} in session:{session_id}'
    sign_image.file.close()
    logger.info(f"{party_role} with id:{party_id} in session {session_id} completed the upload image process.")
    return msg

@router.put('/update-image',status_code=status.HTTP_202_ACCEPTED)
async def update_image_signature(sign_image:UploadFile,party_role:str=Form(...),\
    party_id:str=Form(...),session_id:str=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_id,session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{session_id}')
    logger.info(f"{party_role} with {party_id} from session {session_id} updating image through put parties/v1/update-image endpoint")
    msg=''
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    parties_submit_status=session_doc.get('parties_submit_status',{})
    if parties_submit_status[f'{party_role}_{party_id}']==True:
        raise HTTPException(status_code=403,detail=f'{party_role} with id:{party_id} has already confirmed signature')
    image_file_path=Path(f'{party_role}_{party_id}.jpeg')
    image_file_path=UPLOAD_DIR/session_id/image_file_path
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        await Sign_Detect_Extract.signature_detect_extract(image_file_path)
        logger.info(f"New image : {sign_image.filename} Filepath:{image_file_path}")
        parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
        parties_sign_filepath[f'{party_role}_{party_id}'] = str(image_file_path)
        update_data = {
            "$set": {
                "parties_sign_filepath":parties_sign_filepath
            }}
        await DatabaseConnect.session_collection_update_one(update_data,session_id)
        logger.info(f"The update image filepath is stored in database")
        msg=f'Signature extracted from {sign_image.filename} used to update existing signature by {party_role} with id:{party_id} in session{session_id}'
    sign_image.file.close()
    logger.info(f"{party_role} with id:{party_id} in session {session_id} completed the update image process.")
    return msg

@router.put('/submit-confirmation',status_code=status.HTTP_200_OK)
async def parties_update_confirmation(party_role:str=Form(...),\
    party_id:str=Form(...),session_id:str=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_id,session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{session_id}/{party_id} is incorrect for {party_role}')
    logger.info(f"{party_role} with {party_id} from session {session_id} trying to submit conformation through put parties/v1/submit-conformation endpoint")
    session_doc=await DatabaseConnect.session_collection_find_one(session_id)
    parties_submit_status=session_doc.get('parties_submit_status',{})
    parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
    if parties_submit_status[f'{party_role}_{party_id}']==True:
        raise HTTPException(status_code=403,detail=f'{party_role} with id:{party_id} has already confirmed signature')
    if parties_sign_filepath[f'{party_role}_{party_id}'] is None:
        raise HTTPException(status_code=403,detail=f'{party_role} with id:{party_id} need to uplaod a signature first.')
    parties_submit_status[f'{party_role}_{party_id}']=True
    update_data = {
            "$set": {
                "parties_submit_status":parties_submit_status
            }}
    await DatabaseConnect.session_collection_update_one(update_data,session_id)
    logger.info(f"{party_role} with {party_id} from session {session_id} completed submit conformation through put parties/v1/submit-conformation endpoint")
    return f"{party_role} with id:{party_id} of session:{session_id} has submitted signature."

@router.get("/download-pdf/{session_id}")
async def download_pdf(session_id):
    if not await DatabaseConnect.session_collection_find_one(session_id):
        raise HTTPException(status_code=404,detail=f'Session is:{session_id} does not exists in record')
    logger.info(f"session_id_{session_id}.pdf is being downloaded")
    filename=f"session_id_{session_id}.pdf"
    pdf_directory=Path(r'src\api\services\pdf_generation')
    file_path = os.path.join(pdf_directory,filename)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename 
    )