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
import shutil

latest_result_file = None
mapping = {0:'A',1:'N'}
app = FastAPI()
model = Model('model/best.keras')
# Mount thư mục chứa các tệp tĩnh
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "./data"

@app.post("/upload_file")
async def upload_dat_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.dat'):
        raise HTTPException(status_code=400, detail="Only .dat files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR,file.filename)
    
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
        
    try:
        record = wfdb.rdrecord(str(file_path).replace('.dat',''))
        signal = record.p_signal[:,0]
        fs = record.fs
        
        segments,times = split_segment(data=signal)
        results = model.predict(segments)
        results = list(map(mapping.get,results))
        
        result_filename = os.path.join(UPLOAD_DIR, file.filename.replace('.dat', '.json'))
        with open(result_filename, 'w') as result_file:
            json.dump({"signal": signal.tolist(),
                       "times": times.tolist(), "results": results}, result_file) 
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            "message": "File processed successfully",
            "result_file": result_filename
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
            
            
@app.get("/get_segments")
async def get_segments(result_file:str,index:int=0):
    try:
        with open(result_file,'r') as file:
            data = json.load(file)
            signal = np.array(data['signal'])
            times = data['times']
            results = data['reuslts']
            
        if index >= len(times):
            return {
                "message": "Index out of range",
                "segments": [],
                "results": []
            }
        
        start_time = max(0,int(times[index]-180))
        end_time = min(len(signal),int(times[index]+180))
        segment_signal = signal[start_time:end_time]
        
        return {
            "segment_signal": segment_signal.tolist(),
            "time_range": [start_time, end_time],
            "label": results[index]
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Result file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving segments: {str(e)}")
    
