#!/usr/bin/env python3
"""
Test Patient Report Generation

This script creates a test patient, session, and images, then generates a report.
"""

import uuid
from pathlib import Path
from src.data_io.patient_data import PatientDataManager

def main():
    # Initialize data manager
    pdm = PatientDataManager()

    # Create test patient
    patient_id = str(uuid.uuid4())
    pdm.add_patient(
        patient_id=patient_id,
        first_name='Test',
        last_name='Patient',
        date_of_birth='1990-01-01'
    )

    # Create test session
    session_id = str(uuid.uuid4())
    pdm.add_treatment_session(
        session_id=session_id,
        patient_id=patient_id,
        operator='Test Operator',
        device_settings={'power': '10W', 'duration': '5min'},
        treatment_area='Test Area',
        notes='Test treatment notes'
    )

    # Create sample image files
    patient_dir = Path('./data/patients') / patient_id
    screenshots_dir = Path('./reports/reports/screenshots')
    print(f"Looking for screenshots in: {screenshots_dir}")
    
    if screenshots_dir.exists() and screenshots_dir.is_dir():
        print(f"Found {len(list(screenshots_dir.glob('*.png')))} screenshots")
        for i, img_file in enumerate(screenshots_dir.glob('*.png')):
            print(f"Adding image: {img_file}")
            # Add image record
            image_id = str(uuid.uuid4())
            pdm.add_image_record(
                image_id=image_id,
                session_id=session_id,
                patient_id=patient_id,
                image_path=str(img_file),
                image_type=f'Test Image {i+1}'
            )
    else:
        print(f"Screenshots directory not found: {screenshots_dir}")

    # Generate report
    report_path = pdm.generate_session_report(session_id)
    print(f'Generated patient session report at: {report_path}')
    print(f'Patient ID: {patient_id}')
    print(f'Session ID: {session_id}')

if __name__ == "__main__":
    main() 