# Fake product Detection System

This project aims to detect fake FMCG products using computer vision and machine learning techniques.

## Features

- Multi-view image analysis (front, back, side, barcode)
- OCR text extraction
- Brand verification
- ML-based authenticity prediction
- User-friendly web interface

## Setup Instructions

1. Clone the repository
```bash
git clone [your-repository-url]
cd Project_Major_food
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run migrations
```bash
cd webapp
python manage.py migrate
```

4. Create superuser
```bash
python manage.py createsuperuser
```

5. Run the server
```bash
python manage.py runserver
```

## Project Structure

- `webapp/`: Django project root
- `detector/`: Main application
- `models/`: ML model files
- `data/`: Training data
- `src/`: Source code for ML training

## Technologies Used

- Django
- TensorFlow
- OpenCV
- Pytesseract OCR
- TailwindCSS

## Contributors
- [Rajendra Singh]

## License
[Your chosen license]
