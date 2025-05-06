"""
Patient Data Management Module

This module handles the storage, retrieval, and management of patient information
and treatment data for the TOSCA laser device.
"""

import os
import json
import csv
import logging
import datetime
import pandas as pd
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

class PatientDataManager:
    """
    Manages patient data for the TOSCA device.
    
    This class provides methods to create, read, update, and delete patient records
    and treatment session data.
    """
    
    def __init__(self, data_dir="./data"):
        """
        Initialize the patient data manager.
        
        Args:
            data_dir (str): Directory for storing patient data
        """
        self.data_dir = Path(data_dir)
        self.patients_dir = self.data_dir / "patients"
        self.db_path = self.data_dir / "tosca.db"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.patients_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create patients table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                date_of_birth TEXT,
                gender TEXT,
                contact_info TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            ''')
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS treatment_sessions (
                session_id TEXT PRIMARY KEY,
                patient_id TEXT,
                date TEXT,
                operator TEXT,
                device_settings TEXT,
                treatment_area TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
            ''')
            
            # Create image records table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_records (
                image_id TEXT PRIMARY KEY,
                session_id TEXT,
                patient_id TEXT,
                image_path TEXT,
                image_type TEXT,
                timestamp TEXT,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES treatment_sessions (session_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def add_patient(self, patient_id, first_name, last_name, date_of_birth, 
                    gender=None, contact_info=None, notes=None):
        """
        Add a new patient record.
        
        Args:
            patient_id (str): Unique patient identifier
            first_name (str): Patient's first name
            last_name (str): Patient's last name
            date_of_birth (str): Date of birth in YYYY-MM-DD format
            gender (str, optional): Patient's gender
            contact_info (str, optional): Contact information
            notes (str, optional): Additional notes
            
        Returns:
            bool: True if patient was added successfully, False otherwise
        """
        try:
            # Check if patient already exists
            if self.get_patient(patient_id) is not None:
                logger.warning(f"Patient with ID {patient_id} already exists")
                return False
                
            # Current timestamp
            now = datetime.datetime.now().isoformat()
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add patient to database
            cursor.execute('''
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, 
                gender, contact_info, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, first_name, last_name, date_of_birth, 
                  gender, contact_info, notes, now, now))
                  
            conn.commit()
            conn.close()
            
            # Create patient directory
            patient_dir = self.patients_dir / patient_id
            patient_dir.mkdir(exist_ok=True)
            
            logger.info(f"Added patient: {patient_id} - {first_name} {last_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding patient {patient_id}: {str(e)}")
            return False
    
    def update_patient(self, patient_id, **kwargs):
        """
        Update an existing patient record.
        
        Args:
            patient_id (str): Unique patient identifier
            **kwargs: Fields to update (first_name, last_name, etc.)
            
        Returns:
            bool: True if patient was updated successfully, False otherwise
        """
        try:
            # Check if patient exists
            if self.get_patient(patient_id) is None:
                logger.warning(f"Patient with ID {patient_id} does not exist")
                return False
                
            # Current timestamp
            now = datetime.datetime.now().isoformat()
            kwargs['updated_at'] = now
            
            # Build update query
            fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['first_name', 'last_name', 'date_of_birth', 
                          'gender', 'contact_info', 'notes', 'updated_at']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                logger.warning("No valid fields to update")
                return False
                
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update patient in database
            query = f"UPDATE patients SET {', '.join(fields)} WHERE patient_id = ?"
            values.append(patient_id)
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            logger.info(f"Updated patient: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {str(e)}")
            return False
    
    def get_patient(self, patient_id):
        """
        Retrieve a patient record.
        
        Args:
            patient_id (str): Unique patient identifier
            
        Returns:
            dict or None: Patient information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                # Convert row to dict
                patient = dict(row)
                logger.debug(f"Retrieved patient: {patient_id}")
                return patient
            else:
                logger.debug(f"Patient not found: {patient_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving patient {patient_id}: {str(e)}")
            return None
    
    def delete_patient(self, patient_id):
        """
        Delete a patient record.
        
        Args:
            patient_id (str): Unique patient identifier
            
        Returns:
            bool: True if patient was deleted successfully, False otherwise
        """
        try:
            # Check if patient exists
            if self.get_patient(patient_id) is None:
                logger.warning(f"Patient with ID {patient_id} does not exist")
                return False
                
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Delete associated image records
            cursor.execute("DELETE FROM image_records WHERE patient_id = ?", (patient_id,))
            
            # Delete associated treatment sessions
            cursor.execute("DELETE FROM treatment_sessions WHERE patient_id = ?", (patient_id,))
            
            # Delete patient
            cursor.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted patient: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting patient {patient_id}: {str(e)}")
            return False
    
    def get_all_patients(self):
        """
        Retrieve all patient records.
        
        Returns:
            list: List of dictionaries containing patient information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM patients ORDER BY last_name, first_name")
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert rows to list of dicts
            patients = [dict(row) for row in rows]
            logger.debug(f"Retrieved {len(patients)} patients")
            return patients
            
        except Exception as e:
            logger.error(f"Error retrieving all patients: {str(e)}")
            return []
    
    def search_patients(self, criteria):
        """
        Search for patients based on search criteria.
        
        Args:
            criteria (dict): Search criteria (e.g., {'first_name': 'John'})
            
        Returns:
            list: List of dictionaries containing matching patient information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build search query
            query = "SELECT * FROM patients WHERE "
            conditions = []
            values = []
            
            for key, value in criteria.items():
                if key in ['patient_id', 'first_name', 'last_name', 'date_of_birth', 
                          'gender', 'contact_info', 'notes']:
                    conditions.append(f"{key} LIKE ?")
                    values.append(f"%{value}%")
            
            if not conditions:
                logger.warning("No valid search criteria provided")
                return []
                
            query += " AND ".join(conditions)
            query += " ORDER BY last_name, first_name"
            
            cursor.execute(query, values)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert rows to list of dicts
            patients = [dict(row) for row in rows]
            logger.debug(f"Found {len(patients)} patients matching criteria")
            return patients
            
        except Exception as e:
            logger.error(f"Error searching patients: {str(e)}")
            return []
    
    def add_treatment_session(self, session_id, patient_id, operator, 
                             device_settings=None, treatment_area=None, notes=None):
        """
        Add a new treatment session record.
        
        Args:
            session_id (str): Unique session identifier
            patient_id (str): Patient identifier
            operator (str): Name of the operator
            device_settings (dict, optional): Laser device settings used
            treatment_area (str, optional): Description of treatment area
            notes (str, optional): Additional notes
            
        Returns:
            bool: True if session was added successfully, False otherwise
        """
        try:
            # Check if patient exists
            if self.get_patient(patient_id) is None:
                logger.warning(f"Patient with ID {patient_id} does not exist")
                return False
                
            # Current timestamp
            now = datetime.datetime.now().isoformat()
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Convert device settings to JSON string
            if device_settings is not None:
                device_settings = json.dumps(device_settings)
                
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add session to database
            cursor.execute('''
            INSERT INTO treatment_sessions (
                session_id, patient_id, date, operator, 
                device_settings, treatment_area, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, patient_id, date, operator, 
                  device_settings, treatment_area, notes, now))
                  
            conn.commit()
            conn.close()
            
            # Create session directory
            patient_dir = self.patients_dir / patient_id
            session_dir = patient_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            logger.info(f"Added treatment session: {session_id} for patient {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding treatment session {session_id}: {str(e)}")
            return False
    
    def get_treatment_sessions(self, patient_id):
        """
        Retrieve all treatment sessions for a patient.
        
        Args:
            patient_id (str): Patient identifier
            
        Returns:
            list: List of dictionaries containing session information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM treatment_sessions 
            WHERE patient_id = ? 
            ORDER BY date DESC
            ''', (patient_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert rows to list of dicts and parse JSON fields
            sessions = []
            for row in rows:
                session = dict(row)
                if session['device_settings']:
                    try:
                        session['device_settings'] = json.loads(session['device_settings'])
                    except json.JSONDecodeError:
                        pass  # Keep as string if not valid JSON
                sessions.append(session)
                
            logger.debug(f"Retrieved {len(sessions)} treatment sessions for patient {patient_id}")
            return sessions
            
        except Exception as e:
            logger.error(f"Error retrieving sessions for patient {patient_id}: {str(e)}")
            return []
    
    def add_image_record(self, image_id, session_id, patient_id, image_path, 
                        image_type, notes=None):
        """
        Add a new image record.
        
        Args:
            image_id (str): Unique image identifier
            session_id (str): Session identifier
            patient_id (str): Patient identifier
            image_path (str): Path to the image file
            image_type (str): Type of image (e.g., 'before', 'after', 'treatment')
            notes (str, optional): Additional notes
            
        Returns:
            bool: True if image record was added successfully, False otherwise
        """
        try:
            # Current timestamp
            timestamp = datetime.datetime.now().isoformat()
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add image record to database
            cursor.execute('''
            INSERT INTO image_records (
                image_id, session_id, patient_id, image_path, 
                image_type, timestamp, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (image_id, session_id, patient_id, str(image_path), 
                  image_type, timestamp, notes))
                  
            conn.commit()
            conn.close()
            
            logger.info(f"Added image record: {image_id} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image record {image_id}: {str(e)}")
            return False
    
    def get_session_images(self, session_id):
        """
        Retrieve all images for a treatment session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            list: List of dictionaries containing image information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM image_records 
            WHERE session_id = ? 
            ORDER BY timestamp
            ''', (session_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert rows to list of dicts
            images = [dict(row) for row in rows]
            logger.debug(f"Retrieved {len(images)} images for session {session_id}")
            return images
            
        except Exception as e:
            logger.error(f"Error retrieving images for session {session_id}: {str(e)}")
            return []
    
    def export_patient_data(self, patient_id, export_dir, include_images=False):
        """
        Export patient data to CSV and JSON files.
        
        Args:
            patient_id (str): Patient identifier
            export_dir (str): Directory to export data to
            include_images (bool): Whether to copy images to export directory
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            export_path = Path(export_dir)
            export_path.mkdir(exist_ok=True)
            
            # Get patient data
            patient = self.get_patient(patient_id)
            if patient is None:
                logger.warning(f"Patient with ID {patient_id} does not exist")
                return False
                
            # Get sessions and images
            sessions = self.get_treatment_sessions(patient_id)
            
            # Export patient info as JSON
            patient_file = export_path / f"patient_{patient_id}.json"
            with open(patient_file, 'w') as f:
                json.dump(patient, f, indent=2)
                
            # Export sessions as CSV
            sessions_file = export_path / f"sessions_{patient_id}.csv"
            if sessions:
                df = pd.DataFrame(sessions)
                df.to_csv(sessions_file, index=False)
                
            # Export image records for each session
            if sessions:
                all_images = []
                for session in sessions:
                    session_id = session['session_id']
                    images = self.get_session_images(session_id)
                    all_images.extend(images)
                    
                if all_images:
                    images_file = export_path / f"images_{patient_id}.csv"
                    df = pd.DataFrame(all_images)
                    df.to_csv(images_file, index=False)
                    
                    # Copy images if requested
                    if include_images:
                        images_dir = export_path / "images"
                        images_dir.mkdir(exist_ok=True)
                        
                        import shutil
                        for img in all_images:
                            src_path = Path(img['image_path'])
                            if src_path.exists():
                                dest_path = images_dir / src_path.name
                                shutil.copy2(src_path, dest_path)
            
            logger.info(f"Exported data for patient {patient_id} to {export_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data for patient {patient_id}: {str(e)}")
            return False
    
    def import_patient_data(self, import_dir):
        """
        Import patient data from CSV and JSON files.
        
        Args:
            import_dir (str): Directory containing exported data
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            import_path = Path(import_dir)
            
            # Find patient JSON file
            patient_files = list(import_path.glob("patient_*.json"))
            if not patient_files:
                logger.warning(f"No patient data found in {import_dir}")
                return False
                
            # Process each patient file
            for patient_file in patient_files:
                # Extract patient_id from filename
                patient_id = patient_file.stem.replace("patient_", "")
                
                # Import patient data
                with open(patient_file, 'r') as f:
                    patient_data = json.load(f)
                    
                # Add or update patient
                if self.get_patient(patient_id) is None:
                    # Add new patient
                    self.add_patient(
                        patient_id=patient_data['patient_id'],
                        first_name=patient_data['first_name'],
                        last_name=patient_data['last_name'],
                        date_of_birth=patient_data['date_of_birth'],
                        gender=patient_data['gender'],
                        contact_info=patient_data['contact_info'],
                        notes=patient_data['notes']
                    )
                else:
                    # Update existing patient
                    self.update_patient(
                        patient_id=patient_data['patient_id'],
                        first_name=patient_data['first_name'],
                        last_name=patient_data['last_name'],
                        date_of_birth=patient_data['date_of_birth'],
                        gender=patient_data['gender'],
                        contact_info=patient_data['contact_info'],
                        notes=patient_data['notes']
                    )
                
                # Import sessions if available
                sessions_file = import_path / f"sessions_{patient_id}.csv"
                if sessions_file.exists():
                    sessions_df = pd.read_csv(sessions_file)
                    
                    for _, row in sessions_df.iterrows():
                        session_data = row.to_dict()
                        
                        # Convert device_settings from string to dict if needed
                        if isinstance(session_data.get('device_settings'), str):
                            try:
                                session_data['device_settings'] = json.loads(session_data['device_settings'])
                            except json.JSONDecodeError:
                                session_data['device_settings'] = None
                                
                        # Add session if it doesn't exist
                        self.add_treatment_session(
                            session_id=session_data['session_id'],
                            patient_id=session_data['patient_id'],
                            operator=session_data['operator'],
                            device_settings=session_data['device_settings'],
                            treatment_area=session_data['treatment_area'],
                            notes=session_data['notes']
                        )
                
                # Import image records if available
                images_file = import_path / f"images_{patient_id}.csv"
                if images_file.exists():
                    images_df = pd.read_csv(images_file)
                    
                    for _, row in images_df.iterrows():
                        image_data = row.to_dict()
                        
                        # Add image record
                        self.add_image_record(
                            image_id=image_data['image_id'],
                            session_id=image_data['session_id'],
                            patient_id=image_data['patient_id'],
                            image_path=image_data['image_path'],
                            image_type=image_data['image_type'],
                            notes=image_data['notes']
                        )
            
            logger.info(f"Imported patient data from {import_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing patient data: {str(e)}")
            return False
    
    def generate_session_report(self, session_id, output_path=None):
        """
        Generate a report for a treatment session.
        
        Args:
            session_id (str): Session identifier
            output_path (str, optional): Path to save the report to
            
        Returns:
            str or None: Path to the generated report or None if failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get session data
            cursor.execute('''
            SELECT s.*, p.first_name, p.last_name, p.date_of_birth 
            FROM treatment_sessions s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE s.session_id = ?
            ''', (session_id,))
            
            session = dict(cursor.fetchone())
            
            # Get image records
            cursor.execute('''
            SELECT * FROM image_records
            WHERE session_id = ?
            ORDER BY timestamp
            ''', (session_id,))
            
            images = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            # Parse device settings
            if session['device_settings'] and isinstance(session['device_settings'], str):
                try:
                    session['device_settings'] = json.loads(session['device_settings'])
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON
            
            # Generate report as HTML
            report_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Treatment Session Report - {session_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .section {{ margin-bottom: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .image-gallery {{ display: flex; flex-wrap: wrap; }}
                    .image-container {{ margin: 10px; text-align: center; }}
                    .image-container img {{ max-width: 300px; max-height: 300px; }}
                </style>
            </head>
            <body>
                <h1>TOSCA Treatment Session Report</h1>
                
                <div class="section">
                    <h2>Session Information</h2>
                    <table>
                        <tr><th>Session ID</th><td>{session_id}</td></tr>
                        <tr><th>Date</th><td>{session['date']}</td></tr>
                        <tr><th>Operator</th><td>{session['operator']}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>Patient Information</h2>
                    <table>
                        <tr><th>Patient ID</th><td>{session['patient_id']}</td></tr>
                        <tr><th>Name</th><td>{session['first_name']} {session['last_name']}</td></tr>
                        <tr><th>Date of Birth</th><td>{session['date_of_birth']}</td></tr>
                    </table>
                </div>
            """
            
            # Add device settings section if available
            if session['device_settings']:
                report_content += f"""
                <div class="section">
                    <h2>Device Settings</h2>
                    <table>
                """
                
                if isinstance(session['device_settings'], dict):
                    for key, value in session['device_settings'].items():
                        report_content += f"<tr><th>{key}</th><td>{value}</td></tr>"
                else:
                    report_content += f"<tr><td colspan='2'>{session['device_settings']}</td></tr>"
                    
                report_content += """
                    </table>
                </div>
                """
            
            # Add treatment area section if available
            if session['treatment_area']:
                report_content += f"""
                <div class="section">
                    <h2>Treatment Area</h2>
                    <p>{session['treatment_area']}</p>
                </div>
                """
            
            # Add notes section if available
            if session['notes']:
                report_content += f"""
                <div class="section">
                    <h2>Notes</h2>
                    <p>{session['notes']}</p>
                </div>
                """
            
            # Add images section if available
            if images:
                report_content += f"""
                <div class="section">
                    <h2>Images ({len(images)})</h2>
                    <div class="image-gallery">
                """
                
                for img in images:
                    img_path = img['image_path']
                    img_type = img['image_type']
                    img_notes = img['notes'] or ""
                    
                    report_content += f"""
                    <div class="image-container">
                        <img src="{img_path}" alt="{img_type}">
                        <p><strong>{img_type}</strong>: {img_notes}</p>
                    </div>
                    """
                
                report_content += """
                    </div>
                </div>
                """
            
            # Close HTML document
            report_content += """
            </body>
            </html>
            """
            
            # Save report if output path specified
            if output_path:
                output_file = Path(output_path)
                with open(output_file, 'w') as f:
                    f.write(report_content)
                logger.info(f"Generated report for session {session_id} at {output_path}")
                return str(output_file)
            else:
                return report_content
            
        except Exception as e:
            logger.error(f"Error generating report for session {session_id}: {str(e)}")
            return None 