from fastapi import FastAPI, File, UploadFile, HTTPException
import wfdb
import os
import numpy as np
import pywt
from tensorflow.keras.models import load_model


app = FastAPI()

UPLOAD_DIR = "./data"

def wt(index_list, wavefunc, lv, m, n):
    coeff = pywt.wavedec(index_list, wavefunc, mode="sym", level=lv) 

    sgn = lambda x: 1 if x > 0 else -1 if x < 0 else 0

    # Xét từng level sóng từ level m -> n
    for i in range(m, n + 1):
        cD = coeff[i]
        for j in range(len(cD)):
            Tr = np.sqrt(2 * np.log(len(cD)))
            if cD[j] >= Tr:
                coeff[i][j] = sgn(cD[j]) - Tr
            else:
                coeff[i][j] = 0

    denoised_index = pywt.waverec(coeff, wavefunc)
    return denoised_index

# Thuật toán terma

def MWA(input_array, window_size):
    mwa = np.zeros(len(input_array))
    for i in range(len(input_array)):
        if i < window_size // 2:
            section = input_array[0 : i * 2]
        else:
            section = input_array[i - window_size // 2 : i + window_size // 2]

        if i != 0:
            mwa[i] = np.mean(section)
        else:
            mwa[i] = input_array[i]

    return mwa


def two_average_detector(ecg_signal, window1, window2):
    mwa_1 = MWA(ecg_signal, window1)
    mwa_2 = MWA(ecg_signal, window2)
    return mwa_1, mwa_2

def generateBOI_QRS(signal,mwa_1, mwa_2):
    blocks = np.zeros(len(signal))
    for i in range(len(mwa_1)):
      if mwa_1[i] > mwa_2[i]+15e-6:
          blocks[i] = 1
      else:
          blocks[i] = 0
    return blocks


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

        lead0_wt = wt(lead0, "db4", 4, 2, 4)

        # Sinh ra các blocks chứa đỉnh R
        y = np.square(np.diff(lead0_wt))
        mwa_qrs, mwa_beat_qrs = two_average_detector(y, 30,360)
        blocks_qrs = generateBOI_QRS(y, mwa_qrs, mwa_beat_qrs)

        # Sinh ra mảng lưu các vị trí [đầu, cuối] của 1 QRS
        tmp = []
        for i in range(len(blocks_qrs) - 1):
            if blocks_qrs[i] == 0 and blocks_qrs[i + 1] == 1:
                tmp.append(i)
            if blocks_qrs[i] == 1 and blocks_qrs[i + 1] == 0:
                tmp.append(i)
        pos_qrs = []  
        for i in range(len(tmp) // 2):
            pos_qrs.append(tmp[i * 2 : (i + 1) * 2])
        pos_qrs = [i for i in pos_qrs if i[1]-i[0]>=30]

        # Xét các blocks, chỗ nào có tín hiệu cao nhất là đỉnh R
        R_Peaks = []
        for i in pos_qrs:
            max_signal, index = -1e4, 0
            for j in range(i[0], i[1] + 1):
                if max_signal < lead0_wt[j]:
                    index = j
                    max_signal = lead0_wt[j]
            R_Peaks.append(index)

        # Load model keras
        model = load_model("./best.keras")
        R_labels = []
        for R_peak in R_Peaks[:10]:
            if R_peak < 180 or R_peak > len(lead0) - 180:
                continue
            input = lead0[R_peak - 180 : R_peak + 180]
            input = np.array(input).reshape(-1, 360, 1)
            predict = model.predict(input)
            predict = np.argmax(predict, axis=1)
            R_labels.append(predict[0])
            

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
