from tensorflow.keras.models import load_model
import numpy as np

class Model:
    def __init__(self,model_path:str):
        self.model = load_model(model_path)
    
    def predict(self,data:np.ndarray) -> np.ndarray:
        pre = self.model.predict(data)
        return np.argmax(pre,axis=1)
        
