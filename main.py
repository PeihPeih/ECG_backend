from fastapi import FastAPI, File, UploadFile, HTTPException,Form
import wfdb
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
from joblib import load
from tensorflow.keras.models import load_model
from model import Model
from detectRWave import split_segment
import json
from fastapi.staticfiles import StaticFiles
import shutil
from fastapi.middleware.cors import CORSMiddleware

latest_result_file = None
mapping = {0:'A',1:'N'}
app = FastAPI()
scaler = load('./scaler.pkl')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = Model('./model/best.keras')
# Mount thư mục chứa các tệp tĩnh
#app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "./data"


@app.post("/upload_file")
async def upload_dat_file(dat_file: UploadFile = File(...), hea_file: UploadFile = File(...)):
    global latest_result_file  
    latest_result_file = None
    if not dat_file.filename.endswith('.dat'):
        raise HTTPException(status_code=400, detail="Only .dat files are allowed")
    if not hea_file.filename.endswith('.hea'):
        raise HTTPException(status_code=400, detail="Only .hea files are allowed")
    dat_file_path = os.path.join(UPLOAD_DIR,dat_file.filename)
    hea_file_path = os.path.join(UPLOAD_DIR,hea_file.filename)
    with open(dat_file_path,"wb") as buffer:
        shutil.copyfileobj(dat_file.file,buffer)
    with open(hea_file_path,"wb") as buffer:
        shutil.copyfileobj(hea_file.file,buffer)
        
    try:
        record = wfdb.rdrecord(str(dat_file_path).replace('.dat',''))
        signal = record.p_signal[:,0]

        segments,times = split_segment(data=signal)
        segments = np.array(segments)
        segments = scaler.transform(segments)
        results = model.predict(segments)
        results = list(map(mapping.get,results))
        result_filename = os.path.join(UPLOAD_DIR, dat_file.filename.replace('.dat', '.json'))
         
        latest_result_file = result_filename
        with open(result_filename, 'w') as result_file:
            json.dump({"signal": signal.tolist(), "times": times, "results": results}, result_file) 
        return {
            "message": "File processed successfully",
            "result_file": result_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
            
            
@app.get("/get_segments")
async def get_segments(index:int=0):
    try:
        global latest_result_file
        with open(latest_result_file,'r') as file:
            data = json.load(file)
            signal = np.array(data['signal'])
            times = data['times']
            results = data['results']
            
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
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host='127.0.0.1', port=8000)
