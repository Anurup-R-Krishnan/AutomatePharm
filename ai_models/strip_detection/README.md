# Medicine Strip Detection Module

## Overview
Uses YOLO object detection + barcode scanning to:
- Auto-identify medicines from strip/box photos
- Detect expiry dates printed on packaging
- Validate medicine authenticity

## Dependencies
```
ultralytics==8.2.18   # YOLOv8
opencv-python==4.9.0.80
```

## API
`POST /api/ai_camera/barcode/scan`
- Upload strip/box image
- Returns detected barcode and medicine info
