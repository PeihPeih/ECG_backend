from fastapi import FastAPI, File, UploadFile, HTTPException,Form
import wfdb
import os
import numpy as np
import pywt
from tensorflow.keras.models import load_model
from model import Model
from detectRWave import split_segment
import json
from fastapi.staticfiles import StaticFiles

labels = {0:'A',1:'N'}
app = FastAPI()
model = Model('model/best.keras')
# Mount thư mục chứa các tệp tĩnh
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "./data"

@app.post("/upload_ecg_segments")
async def process_ecg_segments(data: str = Form(...)):
    try:
        signal = np.array(json.loads(data))
        
        segments, times = split_segment(data=signal)
        results = model.predict(segments)
        
        return {
            "results": results.tolist(),
            "times": times,
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# async def upload_ecg_files(dat_file: UploadFile = File(...), hea_file: UploadFile = File(...)):
#     dat_path = os.path.join(UPLOAD_DIR, dat_file.filename)
#     hea_path = os.path.join(UPLOAD_DIR, hea_file.filename)

#     try:
#         with open(dat_path, "wb") as f:
#             f.write(await dat_file.read())
        
#         with open(hea_path, "wb") as f:
#             f.write(await hea_file.read())

#         record = wfdb.rdrecord(dat_path[:-4])  

#         lead0 = record.p_signal[:, 0]
#         lead1 = record.p_signal[:, 1]        
#         fs = record.fs
#         channels = record.sig_name

#         segments,times = split_segment(data=lead0)
        
#         results = model.predict(segments)

#         return {
#             "lead0": lead0.tolist(),
#             "results": results.tolist(),
#             "times": times,
#         }

#     except Exception as e:
#         if os.path.exists(dat_path):
#             os.remove(dat_path)
#         if os.path.exists(hea_path):
#             os.remove(hea_path)
#         raise HTTPException(status_code=400, detail=str(e))
