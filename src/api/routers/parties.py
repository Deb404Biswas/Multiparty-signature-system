from fastapi import APIRouter,HTTPException,UploadFile
from src.api.dependencies.database import DatabaseConnect
from src.api.routers.admin import isUpdateLocked
from starlette import status
from pathlib import Path
import shutil
import os
router=APIRouter(
    prefix='/parties/v1',
    tags=['Parties']
)

party_id='6920a74f35bcbbaf4519cd66'
party_role='HOD'

UPLOAD_DIR=Path('signature-images')

@router.post('/upload-image',status_code=status.HTTP_201_CREATED)
async def upload_image_signature(sign_image:UploadFile):
    msg=''
    image_file_name=f'{party_role}.jpeg'
    global image_file_path
    image_file_path=UPLOAD_DIR/image_file_name
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        doc={
            'filepath':str(image_file_path),
            'image_name':str(sign_image.filename),
            'party_id':party_id
        }
        await DatabaseConnect.sign_collection_insert_one(doc)
        msg=f'Signature extracted from {sign_image.filename}'
    sign_image.file.close()
    return msg

@router.put('/update-image',status_code=status.HTTP_202_ACCEPTED)
async def update_image_signature(sign_image:UploadFile):
    msg=''
    if isUpdateLocked==True:
        raise HTTPException(status_code=400,detail='File update is locked ny admin')
    image_file_path=Path(f'{party_role}.jpeg')
    image_file_path=UPLOAD_DIR/image_file_path
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        doc={
            'filepath':str(image_file_path),
            'image_name':str(sign_image.filename),
            'party_id':party_id
        }
        await DatabaseConnect.sign_collection_update_one(str(image_file_path),sign_image.filename)
        msg=f'Signature extracted from {sign_image.filename} has been updated'
    sign_image.file.close()
    return msg