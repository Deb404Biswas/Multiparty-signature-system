from fastapi import APIRouter,HTTPException,UploadFile,Form
from src.api.dependencies.database import DatabaseConnect
from src.api.routers.admin import isUpdateLocked, submit_conformation_list
from src.api.services.image_analysis.sign_image_analysis import Sign_Detect_Extract
from starlette import status
from pathlib import Path
import shutil
from fastapi.responses import FileResponse
import os

router=APIRouter(
    prefix='/parties/v1',
    tags=['Parties']
)

UPLOAD_DIR=Path('signature-images')

@router.post('/upload-image',status_code=status.HTTP_201_CREATED)
async def upload_image_signature(sign_image:UploadFile,party_role:str=Form(...),\
    party_id:str=Form(...),party_session_id:int=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_role,party_id,party_session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{party_session_id}')
    msg=''
    image_file_name=f'{party_role}_{party_id}.jpeg'
    global image_file_path
    image_file_path=UPLOAD_DIR/image_file_name
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        doc={
            'filepath':str(image_file_path),
            'image_name':str(sign_image.filename),
            'party_id':party_id
        }
        await Sign_Detect_Extract.signature_detect_extract(image_file_path)
        await DatabaseConnect.sign_collection_insert_one(doc)
        msg=f'Signature extracted from {sign_image.filename}'
    sign_image.file.close()
    return msg

@router.put('/update-image',status_code=status.HTTP_202_ACCEPTED)
async def update_image_signature(sign_image:UploadFile,party_role:str=Form(...),\
    party_id:str=Form(...),party_session_id:int=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_role,party_id,party_session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{party_session_id}')
    msg=''
    if isUpdateLocked==True:
        raise HTTPException(status_code=400,detail='File update is locked ny admin')
    image_file_path=Path(f'{party_role}_{party_id}.jpeg')
    image_file_path=UPLOAD_DIR/image_file_path
    with image_file_path.open('wb') as buffer:
        shutil.copyfileobj(sign_image.file, buffer)
        doc={
            'filepath':str(image_file_path),
            'image_name':str(sign_image.filename),
            'party_id':party_id
        }
        await Sign_Detect_Extract.signature_detect_extract(image_file_path)
        await DatabaseConnect.sign_collection_update_one(str(image_file_path),sign_image.filename)
        msg=f'Signature extracted from {sign_image.filename} has been updated'
    sign_image.file.close()
    return msg

@router.put('/submit-confirmation',status_code=status.HTTP_200_OK)
async def parties_update_confirmation(party_role:str=Form(...),\
    party_id:str=Form(...),party_session_id:int=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_role,party_id,party_session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{party_session_id}')
    global submit_conformation_list
    submit_conformation_list[party_role]=True
    print(submit_conformation_list)
    return f"{party_role} has submitted signature."

@router.get("/download-pdf")
async def download_pdf(party_role:str=Form(...),\
    party_id:str=Form(...),party_session_id:int=Form(...)):
    if not await DatabaseConnect.party_collection_find_one(party_role,party_id,party_session_id):
        raise HTTPException(status_code=404,detail=f'{party_role} does not exists in session{party_session_id}')
    filename='session_id_34567.pdf'
    pdf_directory=r"C:\InfinityBit\Multiparty-signature-system\src\api\services\pdf_generation"
    file_path = os.path.join(pdf_directory,filename)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename 
    )