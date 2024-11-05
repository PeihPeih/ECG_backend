from fastapi import FastAPI, File, UploadFile, HTTPException
import wfdb
import os
import numpy as np
import pywt
from tensorflow.keras.models import load_model
from model import Model
from detectRWave import split_segment
app = FastAPI()
model = Model('ECG_backend/model/best.keras')

UPLOAD_DIR = "./data"


@app.post("/upload_ecg_files")
async def upload_ecg_files(dat_file: UploadFile = File(...), hea_file: UploadFile = File(...)):
    dat_path = os.path.join(UPLOAD_DIR, dat_file.filename)
    hea_path = os.path.join(UPLOAD_DIR, hea_file.filename)

    try:
        with open(dat_path, "wb") as f:
            f.write(await dat_file.read())
        
        with open(hea_path, "wb") as f:
            f.write(await hea_file.read())

        record = wfdb.rdrecord(dat_path[:-4])  

        lead0 = record.p_signal[:, 0]
        lead1 = record.p_signal[:, 1]        
        fs = record.fs
        channels = record.sig_name

        segments = split_segment(data=lead0,time_record= len(lead0)/fs,sfreq=fs)
        
        results = model.predict(segments)
        # # Load model keras
        # model = load_model("./best.keras")
        # R_labels = []
        # for R_peak in R_Peaks[:10]:
        #     if R_peak < 180 or R_peak > len(lead0) - 180:
        #         continue
        #     input = lead0[R_peak - 180 : R_peak + 180]
        #     input = np.array(input).reshape(-1, 360, 1)
        #     predict = model.predict(input)
        #     predict = np.argmax(predict, axis=1)
        #     R_labels.append(predict[0])
            

        return {
            "lead0": lead0[:2000].tolist(),
            "R_Peaks": R_Peaks[:10],
            "R_labels": R_labels
        }

    except Exception as e:
        if os.path.exists(dat_path):
            os.remove(dat_path)
        if os.path.exists(hea_path):
            os.remove(hea_path)
        raise HTTPException(status_code=400, detail=str(e))
