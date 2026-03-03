# Prescription OCR Module

## Overview
Scans doctor prescriptions using OCR to auto-populate billing items.

## Dependencies
```
pytesseract==0.3.10
Pillow==10.3.0
```

## System Requirements
Install Tesseract OCR engine:
- Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-tam` (Tamil support)
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

## API
`POST /api/ai_camera/prescription/scan`
- Upload prescription image
- Returns extracted text + identified medicine names
