import wfdb
import numpy as np
import pywt


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

def split_segment(data, time_record=30, sfreq=360):
    # Denoise signal
    denoise_data = wt(data,"db4", 4, 2, 4)
    
    y = np.square(np.diff(denoise_data))
    # High, Low signal
    mwa_qrs, mwa_beat_qrs = two_average_detector(y, time_record,sfreq)
    block_qrs = generateBOI_QRS(y, mwa_qrs, mwa_beat_qrs)
    # filter position
    temp = []
    for i in range(len(block_qrs)-1):
        if block_qrs[i] == 0 and block_qrs[i+1]==1:
            temp.append(i)
        if block_qrs[i] == 1 and block_qrs[i+1]==0:
            temp.append(i)
    # take position
    pos_qrs = []
    for i in range(len(temp)//2):
        pos_qrs.append(temp[i*2:(i+1)*2])
    pos_qrs = [i for i in pos_qrs if i[1]-i[0]>=30]
    
    # Take R Wave
    R_Peaks = []
    for i in pos_qrs:
        max_signal, index = -1e4, 0
        for j in range(i[0], i[1] + 1):
            if max_signal < denoise_data[j]:
                index = j
                max_signal = denoise_data[j]
        R_Peaks.append(index)
    
    segments = []
    
    for R_peak in R_Peaks:
        if R_peak < 180 or R_peak > len(data) - 180:
            continue
        segment = data[R_peak-180:R_peak+180]
        segment = np.array(segment)
        segments.append(segment)
    
    return np.array(segments)

    