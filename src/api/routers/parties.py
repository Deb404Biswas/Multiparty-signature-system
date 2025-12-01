from fastapi import APIRouter,HTTPException,UploadFile,Form,Depends
from src.api.dependencies.database import DatabaseConnect
from src.api.services.image_analysis.sign_image_analysis import Sign_Detect_Extract
from src.api.dependencies.parties_dependency import isPartyInSession
from src.api.routers.auth import get_current_user
from starlette import status
from pathlib import Path
import shutil
from fastapi.responses import FileResponse
import os
from loguru import logger
from typing import Annotated

router=APIRouter(
    prefix='/parties/v1',
    tags=['Parties']
)

UPLOAD_DIR=Path('signature-images')
current_user=Annotated[dict, Depends(get_current_user)]

@router.post('/upload-image',status_code=status.HTTP_201_CREATED)
async def upload_image_signature(user:current_user,sign_image:UploadFile,session_id:str=Form(...)):
    session_doc=await isPartyInSession(user,session_id)
    party_role=user['user_role']
    party_id=user['user_id']
    logger.info(f"{party_role} with {party_id} from session {session_id} uploading image through post parties/v1/upload-image endpoint")
    session_folder = UPLOAD_DIR / session_id
    session_folder.mkdir(parents=True, exist_ok=True)
    image_file_name=f'{party_role}_{party_id}.jpeg'
    image_file_path=session_folder/image_file_name
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        await Sign_Detect_Extract.signature_detect_extract(image_file_path)
        logger.info(f"Signature image is extracted from {sign_image.filename} and stored in {image_file_path}")
        parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
        parties_sign_filepath[f'{party_role}_{party_id}'] = str(image_file_path)
        update_data = {
            "$set": {
                "parties_sign_filepath":parties_sign_filepath
            }}
        await DatabaseConnect.session_collection_update_one(update_data,session_id)
        logger.info(f"{party_role} with {party_id} able to upload image.")
        logger.info(f"The image filepath in database is : {image_file_path}")
    sign_image.file.close()
    logger.info(f"{party_role} with id:{party_id} in session {session_id} completed the upload image process.")
    return {
        'status':200,
        'party_role':party_role,
        'party_id':party_id,
        'session_id':session_id,
        'message':f'Signature extracted successfully.'
    }

@router.put('/update-image',status_code=status.HTTP_202_ACCEPTED)
async def update_image_signature(user:current_user,sign_image:UploadFile,session_id:str=Form(...)):
    session_doc=await isPartyInSession(user,session_id)
    party_role=user['user_role']
    party_id=user['user_id']
    logger.info(f"{party_role} with {party_id} from session {session_id} updating image through put parties/v1/update-image endpoint")
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
    sign_image.file.close()
    logger.info(f"{party_role} with id:{party_id} in session {session_id} completed the update image process.")
    return {
        'status':200,
        'party_role':party_role,
        'party_id':party_id,
        'session_id':session_id,
        'message':f'Signature updated successfully.'
    }

@router.put('/submit-confirmation',status_code=status.HTTP_200_OK)
async def parties_update_confirmation(user:current_user,session_id:str=Form(...)):
    session_doc=await isPartyInSession(user,session_id)
    party_role=user['user_role']
    party_id=user['user_id']
    logger.info(f"{party_role} with {party_id} from session {session_id} trying to submit conformation through put parties/v1/submit-conformation endpoint")
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
    return {
        'status':200,
        'party_role':party_role,
        'party_id':party_id,
        'session_id':session_id,
        'message':f'Signature submitted successfully.'
    }

@router.get("/download-pdf/{session_id}")
async def download_pdf(user:current_user,session_id):
    session_doc=await isPartyInSession(user,session_id)
    if not session_doc:
        raise HTTPException(status_code=403,detail=f'error:{user['user_role']} not in session id:{session_id}')
    lock_status=session_doc.get('isUpdateLocked')
    logger.info(f'Lock_status:{lock_status}')
    if lock_status==False:
        return {
            'status':200,
            'message':'Admin needs to confirm the signatures and lock the process for pdf generation.'
        }
    logger.info(f"session_id_{session_id}.pdf is being downloaded")
    filename=f"session_id_{session_id}.pdf"
    pdf_directory=Path(r'src\api\services\pdf_generation')
    file_path = os.path.join(pdf_directory,filename)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename 
    )