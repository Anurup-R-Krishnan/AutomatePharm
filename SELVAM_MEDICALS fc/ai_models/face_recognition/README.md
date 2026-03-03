# Face Recognition Module

## Overview
Used for identifying returning customers at the billing counter via webcam.

## Flow
1. Camera captures customer face at entry
2. `ai_camera` API endpoint `/face/identify` is called
3. If matched → customer profile + loyalty points auto-loaded in billing
4. If not matched → walk-in customer or prompt to register

## Dependencies
```
face-recognition==1.3.0
deepface==0.0.93
opencv-python==4.9.0.80
```

## Setup
```bash
pip install face-recognition deepface opencv-python
```

## Training Custom Model
Place training images in `data/customers/<customer_id>/` folders.
Run `train.py` to generate encodings saved to the database.
