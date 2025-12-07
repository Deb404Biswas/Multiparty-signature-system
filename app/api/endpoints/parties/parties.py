from fastapi import APIRouter,HTTPException,UploadFile,Form,Depends
from app.api.dependencies.database import DatabaseConnect
from app.api.services.image_analysis.sign_image_analysis import Sign_Detect_Extract
from app.api.services.object_storage.r2_storage import R2Storage
from app.api.dependencies.parties_dependency import isPartyInSession
from app.api.endpoints.auth.auth import get_current_user
from starlette import status
from fastapi.responses import StreamingResponse
import os
from loguru import logger
from typing import Annotated
import io

router=APIRouter(
    prefix='/v1/parties',
    tags=['Parties']
)
    
current_user=Annotated[dict, Depends(get_current_user)]
try:
    @router.post('/upload-image',status_code=status.HTTP_201_CREATED)
    async def upload_image_signature(user:current_user,sign_image:UploadFile,session_id:str=Form(...)):
        session_doc=await isPartyInSession(user,session_id)
        party_role=user['user_role']
        party_id=user['user_id']
        logger.info(f"{party_role} with {party_id} from session {session_id} uploading image through post parties/v1/upload-image endpoint")
        file_content= await sign_image.read()
        file_content= await Sign_Detect_Extract.signature_detect_extract(file_content)
        image_file_path=f'signature-images/session_id_{session_id}/{party_role}_{party_id}.jpeg'
        await R2Storage.upload_file(file_content, image_file_path)
        logger.info(f"Signature image is extracted from {sign_image.filename} and stored in {image_file_path}")
        parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
        parties_sign_filepath[f'{party_role}_{party_id}'] = f'{image_file_path}'
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
            'status':201,
            'party_role':party_role,
            'party_id':party_id,
            'session_id':session_id,
            'message':'Signature extracted successfully.'
        }
except Exception as e:
    logger.error(f"Error:{e}. Occurred while executing '/upload-image' endpoint")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='Undocumented error at server-side')

try:
    @router.put('/update-image',status_code=status.HTTP_202_ACCEPTED)
    async def update_image_signature(user:current_user,sign_image:UploadFile,session_id:str=Form(...)):
        session_doc=await isPartyInSession(user,session_id)
        party_role=user['user_role']
        party_id=user['user_id']
        logger.info(f"{party_role} with {party_id} from session {session_id} updating image through put parties/v1/update-image endpoint")
        parties_submit_status=session_doc.get('parties_submit_status',{})
        parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
        if parties_submit_status[f'{party_role}_{party_id}']==True:
            raise HTTPException(status_code=403,detail=f'{party_role} with id:{party_id} has already confirmed signature')
        if parties_sign_filepath[f'{party_role}_{party_id}'] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Party needs to upload a signature')
        file_content= await sign_image.read()
        file_content= await Sign_Detect_Extract.signature_detect_extract(file_content)
        image_file_path=f'signature-images/session_id_{session_id}/{party_role}_{party_id}.jpeg'
        await R2Storage.upload_file(file_content, image_file_path)
        logger.info(f"New image : {sign_image.filename} Filepath:{image_file_path}")
        sign_image.file.close()
        logger.info(f"{party_role} with id:{party_id} in session {session_id} completed the update image process.")
        return {
            'status':202,
            'party_role':party_role,
            'party_id':party_id,
            'session_id':session_id,
            'message':'Signature updated successfully.'
        }
except Exception as e:
    logger.error(f"Error:{e}. Occurred while executing '/update-image' endpoint")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='Undocumented error at server side.')

try:
    @router.put('/submit-confirmation',status_code=status.HTTP_200_OK)
    async def parties_update_confirmation(user:current_user,session_id:str=Form(...)):
            session_doc=await isPartyInSession(user,session_id)
            party_role=user['user_role']
            party_id=user['user_id']
            logger.info(f"{party_role} with {party_id} from session {session_id} trying to submit conformation through put parties/v1/submit-conformation endpoint")
            parties_submit_status=session_doc.get('parties_submit_status',{})
            parties_sign_filepath=session_doc.get('parties_sign_filepath',{})
            if parties_submit_status[f'{party_role}_{party_id}']==True:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'{party_role} with id:{party_id} has already confirmed signature')
            if parties_sign_filepath[f'{party_role}_{party_id}'] is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'{party_role} with id:{party_id} need to upload a signature first.')
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
except Exception as e:
    logger.error(f"Error:{e}. Occurred while executing '/submit-confirmation' endpoint")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='Undocumented server side error.')

try:
    @router.get("/download-pdf/{session_id}",status_code=status.HTTP_200_OK)
    async def download_pdf(user:current_user,session_id):
            session_doc=await isPartyInSession(user,session_id)
            if not session_doc:
                raise HTTPException(status_code=403,detail=f'error:{user['user_role']} not in session id:{session_id}')
            lock_status=session_doc.get('isUpdateLocked')
            logger.debug(f'Lock_status:{lock_status}')
            if lock_status==False:
                return {
                    'status':400,
                    'message':'Admin needs to confirm the signatures and lock the process for pdf generation.'
                }
            try:
                file_content =await R2Storage.get_file(f'Result_PDF/{session_id}/session_id_{session_id}.pdf')
                logger.info(f"PDF downloaded from R2 bucket for session id:{session_id}")
            except Exception as e:
                logger.error(f"Error:{e}, Occurred while downloading pdf from r2 bucket for session id: {session_id}")
                raise HTTPException(status_code=404,detail='PDF not found')
            logger.info(f"session_id_{session_id}.pdf is being downloaded")
            return StreamingResponse(
                iter([file_content]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=session_id_{session_id}.pdf"}
            )
except Exception as e:
    logger.error(f"Error:{e}. Occurred while executing '/download-pdf/session_id' endpoint")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='Undocumented error at server side.')