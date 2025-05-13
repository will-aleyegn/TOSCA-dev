#!/usr/bin/env python3
"""
Test Patient Report Generator

Generates a patient report using existing data without creating new patients.
"""

import os
import sys
from pathlib import Path
from src.data_io.patient_data import PatientDataManager

def main():
    """Generate patient report using existing data."""
    print("TOSCA Patient Report Generator (Using Existing Data)")
    print("===================================================")
    
    # Initialize data manager
    pdm = PatientDataManager()
    
    # Get existing patients
    patients = pdm.get_all_patients()
    if not patients:
        print("No patients found in database. Creating a test patient...")
        # Code from test_report.py for creating a test patient and session
        import uuid
        
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
        screenshots_dir = Path('./reports/reports/screenshots')
        if screenshots_dir.exists() and screenshots_dir.is_dir():
            print(f"Found {len(list(screenshots_dir.glob('*.png')))} screenshots")
            for i, img_file in enumerate(screenshots_dir.glob('*.png')):
                # Add image record
                image_id = str(uuid.uuid4())
                pdm.add_image_record(
                    image_id=image_id,
                    session_id=session_id,
                    patient_id=patient_id,
                    image_path=str(img_file),
                    image_type=f'Test Image {i+1}'
                )
        
        patients = [{'patient_id': patient_id}]
    
    # For each patient, get their sessions and generate a report for the most recent session
    for patient in patients:
        patient_id = patient['patient_id']
        sessions = pdm.get_treatment_sessions(patient_id)
        
        if not sessions:
            print(f"No sessions found for patient {patient_id}")
            continue
        
        # Get the most recent session
        session = sessions[0]  # Already sorted by date DESC
        session_id = session['session_id']
        
        # Generate the report
        print(f"Generating report for patient {patient_id}, session {session_id}...")
        report_path = pdm.generate_session_report(session_id)
        
        if report_path:
            print(f"Generated report at: {report_path}")
            
            # Offer to open the report
            open_report = input(f"Open the report for patient {patient_id}? (y/n): ")
            if open_report.lower() == 'y':
                if os.name == 'nt':  # Windows
                    os.startfile(report_path)
                elif os.name == 'posix':  # macOS or Linux
                    import subprocess
                    subprocess.run(['xdg-open', report_path], check=False)
        else:
            print(f"Failed to generate report for session {session_id}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 