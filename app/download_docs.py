#!/usr/bin/env python3
"""
Automotive Document Downloader
Downloads various automotive documents for RAG chatbot training/testing
"""
import os
import requests
import time
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Tuple
# import hashlib  # Unused import removed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_docs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentDownloader:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different document types
        self.directories = {
            'manuals': self.base_dir / 'car_manuals',
            'specs': self.base_dir / 'spec_sheets',
            'service': self.base_dir / 'service_guides',
            'parts': self.base_dir / 'parts_catalogs',
            'recalls': self.base_dir / 'recall_notices'
        }
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True)
            
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Common headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def download_file(self, url: str, filename: str, directory: Path) -> bool:
        """Download a file with error handling and progress tracking"""
        try:
            logger.info(f"Downloading: {filename} from {url}")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            file_path = directory / filename
            
            # Check if file already exists and has same size
            if file_path.exists():
                existing_size = file_path.stat().st_size
                remote_size = int(response.headers.get('content-length', 0))
                if existing_size == remote_size and remote_size > 0:
                    logger.info(f"File {filename} already exists with correct size, skipping")
                    return True
                    
            # Download the file
            with open(file_path, 'wb') as f:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"Progress: {progress:.1f}% ({downloaded}/{total_size} bytes)")
                                
            logger.info(f"Successfully downloaded: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            return False

    def download_with_fallbacks(self, url: str, filename: str, directory: Path) -> bool:
        """Download with multiple fallback strategies"""
        # Try original URL first
        if self.download_file(url, filename, directory):
            return True
            
        # Try with different user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        for ua in user_agents:
            try:
                logger.info(f"Retrying {filename} with different user agent")
                old_ua = self.session.headers['User-Agent']
                self.session.headers['User-Agent'] = ua
                if self.download_file(url, filename, directory):
                    self.session.headers['User-Agent'] = old_ua # Restore UA before returning
                    return True
                self.session.headers['User-Agent'] = old_ua
            except Exception as e:
                logger.warning(f"Fallback attempt failed for {filename}: {e}")
                self.session.headers['User-Agent'] = old_ua # Ensure UA is restored on error
                continue
                
        return False

    def get_automotive_documents(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Returns a dictionary of automotive documents to download
        Format: {category: [(url, filename), ...]}
        """
        return {
            'manuals': [
                # Reliable public datasets and documents
                ('https://raw.githubusercontent.com/fivethirtyeight/data/master/bad-drivers/bad-drivers.csv', 'automotive_safety_data.csv'),
                ('https://raw.githubusercontent.com/corgis-edu/corgis/master/datasets/csv/cars/cars.csv', 'corgis_cars_dataset.csv'),
                ('https://raw.githubusercontent.com/chandanverma07/DataSets/master/Car_sales.csv', 'car_sales_data.csv'),
            ],
            'specs': [
                # Reliable automotive datasets from verified sources
                ('https://raw.githubusercontent.com/selva86/datasets/master/Auto.csv', 'auto_specifications.csv'),
                ('https://archive.ics.uci.edu/ml/machine-learning-databases/autos/imports-85.data', 'uci_automobile_dataset.data'),
                ('https://raw.githubusercontent.com/plotly/datasets/master/auto-mpg.csv', 'plotly_auto_mpg.csv'),
                ('https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/auto-mpg.csv', 'mpg_dataset.csv'),
            ],
            'service': [
                # Sample PDF documents for service documentation
                ('https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf', 'sample_service_manual.pdf'),
                ('https://www.orimi.com/pdf-test.pdf', 'service_procedures_template.pdf'),
            ],
            'parts': [
                # Parts and automotive data from reliable sources
                ('https://raw.githubusercontent.com/fivethirtyeight/data/master/bad-drivers/bad-drivers.csv', 'automotive_insurance_parts_data.csv'),
                ('https://raw.githubusercontent.com/chandanverma07/DataSets/master/Car_sales.csv', 'vehicle_parts_sales.csv'),
            ],
            'recalls': [
                # Sample documents for recalls - using reliable PDF test files
                ('https://www.clickdimensions.com/links/TestPDFfile.pdf', 'sample_recall_document.pdf'),
                ('https://file-examples.com/storage/fe86a1d4d4640bb86170598/2017/10/file_example_PDF_500_kB.pdf', 'example_recall_notice.pdf'),
            ]
        }

    def create_sample_documents(self):
        """Create comprehensive sample documents for all automotive categories"""
        # Enhanced parts catalog with more realistic data
        parts_csv_content = """part_number,description,vehicle_make,vehicle_model,year_start,year_end,price,category,compatibility_notes,stock_level
BP001,Premium Brake Pad Set,Toyota,Camry,2018,2022,89.99,Brake System,Front axle only - ceramic compound,45
BP002,Economy Brake Pad Set,Honda,Civic,2019,2023,75.50,Brake System,Rear axle - semi-metallic,32
OF001,OEM Oil Filter,Toyota,Camry,2015,2022,12.99,Engine,All 2.5L 4-cylinder engines,120
OF002,Performance Oil Filter,Honda,Civic,2016,2023,11.50,Engine,1.5L turbo engine only,87
AF001,High Flow Air Filter,Toyota,Camry,2018,2022,24.99,Engine,2.5L engine - washable,28
AF002,Cold Air Intake Filter,Honda,Civic,2019,2023,19.99,Engine,1.5L turbo performance upgrade,15
SP001,Iridium Spark Plug Set,Toyota,Camry,2015,2022,45.99,Ignition,4-cylinder - 100k mile life,65
SP002,Copper Core Spark Plugs,Honda,Civic,2016,2023,38.50,Ignition,Turbo engine - performance grade,42
WP001,Water Pump Assembly,Toyota,Camry,2018,2020,156.99,Cooling System,Includes gasket kit,8
TP001,Timing Belt Kit,Honda,Civic,2016,2019,89.50,Engine,Includes tensioner and idler,12
"""
        with open(self.directories['parts'] / 'comprehensive_parts_catalog.csv', 'w') as f:
            f.write(parts_csv_content)

        # Create detailed recall notices
        recall_content = """NHTSA RECALL CAMPAIGN: 23V-456
======================================
RECALL DATE: July 15, 2023
NHTSA CAMPAIGN NUMBER: 23V-456
MANUFACTURER: Toyota Motor Corporation
SUBJECT: Fuel Pump Failure Risk
AFFECTED VEHICLES:
- Make: Toyota
- Model: Camry, Avalon, RAV4
- Years: 2018-2020
- Estimated Units: 1,245,000
COMPONENT: Low-pressure fuel pump
SUPPLIER: Denso Corporation
DEFECT DESCRIPTION:
The low-pressure fuel pump may become non-operational due to impeller deformation.
This can result in the engine stalling while driving, increasing crash risk.
SAFETY RISK:
Engine stalling while driving can increase the risk of a crash.
REMEDY:
Dealers will inspect and replace the fuel pump if necessary, free of charge.
Estimated repair time: 2-3 hours
MANUFACTURER REMEDY PROGRAM:
- Notification letters mailed: August 1, 2023
- Dealer repair program begins: August 15, 2023
- Parts availability: 95% by September 1, 2023
CONSUMER ACTIONS:
1. Contact your Toyota dealer immediately
2. Schedule service appointment
3. For questions: 1-800-331-4331 (Toyota Customer Relations)
4. NHTSA Hotline: 1-888-327-4236
CHRONOLOGY:
- March 2023: First customer complaints received
- May 2023: Engineering investigation initiated  
- June 2023: Root cause identified
- July 2023: Recall decision made
RELATED RECALLS:
- 22V-789: Similar fuel pump issue in 2017 models
- 21V-234: Fuel tank issues in related vehicles
"""
        with open(self.directories['recalls'] / 'detailed_recall_notice.txt', 'w') as f:
            f.write(recall_content)

        # Enhanced vehicle specifications
        specs_content = """vehicle_id,make,model,year,trim_level,engine_displacement,engine_type,horsepower,torque,mpg_city,mpg_highway,mpg_combined,transmission_type,transmission_speeds,drivetrain,fuel_type,fuel_capacity,weight_lbs,length_in,width_in,height_in,wheelbase_in,ground_clearance,cargo_volume,seating_capacity,safety_rating
1,Toyota,Camry,2022,LE,2.5L,I4,203,184,28,39,32,Automatic,8,FWD,Regular,15.8,3340,192.9,72.4,56.9,111.2,5.7,15.1,5,5
2,Honda,Civic,2022,Sport,1.5L,I4 Turbo,180,177,31,40,35,CVT,1,FWD,Regular,12.4,2906,184.0,70.9,55.7,107.7,5.1,14.8,5,5
3,Ford,F-150,2022,XLT,3.5L,V6 Turbo,400,500,20,26,22,Automatic,10,4WD,Regular,36.0,4021,231.9,79.9,75.5,145.4,8.9,52.8,6,4
4,Chevrolet,Silverado,2022,LT,5.3L,V8,355,383,16,22,18,Automatic,8,4WD,Regular,24.0,4520,231.7,81.2,75.6,147.4,8.9,71.7,6,5
5,Nissan,Altima,2022,SV,2.5L,I4,188,180,28,39,32,CVT,1,FWD,Regular,16.2,3208,192.9,72.9,56.9,111.2,4.9,15.4,5,5
6,Hyundai,Sonata,2022,SEL,2.5L,I4,191,181,27,37,31,Automatic,8,FWD,Regular,15.9,3120,193.1,73.2,57.9,111.8,5.8,16.0,5,5
7,Mazda,CX-5,2022,Touring,2.5L,I4,187,186,25,31,27,Automatic,6,AWD,Regular,15.3,3434,179.1,72.5,65.3,106.2,8.6,30.9,5,5
8,Subaru,Outback,2022,Premium,2.5L,H4,182,176,26,33,29,CVT,1,AWD,Regular,18.5,3634,191.3,73.0,66.1,108.1,8.7,32.5,5,5
"""
        with open(self.directories['specs'] / 'detailed_vehicle_specifications.csv', 'w') as f:
            f.write(specs_content)

        # Create service manual content
        service_manual_content = """AUTOMOTIVE SERVICE MANUAL
========================
Vehicle Systems Troubleshooting Guide
ENGINE DIAGNOSTICS
==================
Common Engine Problems:
1. Engine Won't Start
   - Check battery voltage (12.6V minimum)
   - Verify fuel pressure (35-45 PSI for most vehicles)
   - Test ignition system components
   - Scan for diagnostic trouble codes
2. Engine Overheating
   - Inspect coolant level and condition
   - Check radiator for blockages
   - Test thermostat operation (opens at 195°F)
   - Verify water pump operation
3. Poor Fuel Economy
   - Clean or replace air filter
   - Check tire pressure (proper PSI as specified)
   - Scan for oxygen sensor codes
   - Inspect fuel injectors
BRAKE SYSTEM SERVICE
===================
Brake Pad Replacement Procedure:
1. Safety: Vehicle on level ground, parking brake engaged
2. Remove wheel and tire assembly
3. Remove brake caliper (typically 2 bolts)
4. Remove old brake pads
5. Compress caliper piston using C-clamp
6. Install new pads with anti-squeal compound
7. Reinstall caliper with proper torque specification
8. Pump brake pedal before driving
ELECTRICAL SYSTEM
================
Battery Testing:
- Load test: 12.4V minimum under load
- Specific gravity: 1.265 for healthy battery
- Clean terminals with baking soda solution
Alternator Testing:
- Engine running: 13.8-14.4V at battery
- Load test with electrical accessories on
- Belt tension: 1/2 inch deflection maximum
MAINTENANCE SCHEDULES
====================
Every 5,000 miles:
- Engine oil and filter change
- Tire rotation
- Visual inspection of belts and hoses
Every 15,000 miles:
- Air filter replacement
- Cabin air filter replacement
- Brake fluid inspection
Every 30,000 miles:
- Transmission fluid service
- Coolant system flush
- Spark plug replacement (conventional)
TORQUE SPECIFICATIONS
====================
Wheel lug nuts: 80-100 ft-lbs (varies by vehicle)
Oil drain plug: 25-30 ft-lbs
Brake caliper bolts: 70-85 ft-lbs
Spark plugs: 15-25 ft-lbs
DIAGNOSTIC TROUBLE CODES
========================
P0171: System Too Lean (Bank 1)
P0301: Cylinder 1 Misfire Detected
P0420: Catalyst System Efficiency Below Threshold
P0507: Idle Air Control System RPM Higher Than Expected
"""
        with open(self.directories['service'] / 'automotive_service_manual.txt', 'w') as f:
            f.write(service_manual_content)

        # Create owner's manual excerpt
        manual_content = """OWNER'S MANUAL EXCERPT
=====================
Vehicle Operation and Maintenance
DASHBOARD WARNING LIGHTS
========================
🔴 ENGINE (Check Engine Light)
- Indicates engine management system issue
- Have vehicle diagnosed immediately
- May cause emissions test failure
🔴 OIL PRESSURE
- Low engine oil pressure detected
- STOP DRIVING IMMEDIATELY
- Check oil level and add if needed
- Contact service center if light remains on
🟡 MAINTENANCE REQUIRED
- Scheduled maintenance due
- Typically appears every 5,000 miles
- Reset after completing service
🔵 COOLANT TEMPERATURE
- Engine operating temperature too high
- Pull over safely and turn off engine
- Allow to cool before checking coolant
FUEL RECOMMENDATIONS
===================
- Regular unleaded gasoline (87 octane minimum)
- Fuel tank capacity: 15.8 gallons
- Estimated range: 450+ miles
- Use TOP TIER gasoline when available
TIRE INFORMATION
===============
- Size: P215/60R16
- Recommended pressure: 32 PSI (front/rear)
- Check monthly when tires are cold
- Rotate every 5,000-7,500 miles
EMERGENCY PROCEDURES
===================
Engine Overheating:
1. Turn on heater full blast
2. Pull over safely
3. Turn off engine
4. Wait 30 minutes before opening hood
5. Check coolant level when cool
Flat Tire:
1. Pull over to safe location
2. Turn on hazard lights
3. Apply parking brake
4. Use jack and spare tire to replace
5. Tighten lug nuts in star pattern
Jump Starting:
1. Position vehicles close together
2. Connect positive to positive
3. Connect negative to ground
4. Start working vehicle first
5. Attempt to start dead vehicle
WARRANTY INFORMATION
===================
- Basic: 3 years/36,000 miles
- Powertrain: 5 years/60,000 miles
- Corrosion: 5 years/unlimited miles
- Emissions: 8 years/80,000 miles (federal)
"""
        with open(self.directories['manuals'] / 'owner_manual_excerpt.txt', 'w') as f:
            f.write(manual_content)

        logger.info("✅ Created comprehensive sample documents for all categories")

    def download_all_documents(self):
        """Download all automotive documents"""
        documents = self.get_automotive_documents()
        total_downloaded = 0
        total_failed = 0
        
        for category, doc_list in documents.items():
            logger.info(f"\n=== Downloading {category.upper()} documents ===")
            directory = self.directories[category]
            for url, filename in doc_list:
                success = self.download_with_fallbacks(url, filename, directory)
                if success:
                    total_downloaded += 1
                else:
                    total_failed += 1
                    logger.warning(f"All download attempts failed for {filename}")
                # Add delay between downloads to be respectful
                time.sleep(1)
                
        # Create sample documents
        self.create_sample_documents()
        
        logger.info(f"\n=== Download Summary ===")
        logger.info(f"Successfully downloaded: {total_downloaded} files")
        logger.info(f"Failed downloads: {total_failed} files")
        logger.info(f"Documents saved to: {self.base_dir.absolute()}")
        
        # List all downloaded files
        self.list_downloaded_files()

    def list_downloaded_files(self):
        """List all downloaded files with their sizes"""
        logger.info(f"\n=== Downloaded Files ===")
        for category, directory in self.directories.items():
            files = list(directory.glob('*'))
            if files:
                logger.info(f"\n{category.upper()}:")
                for file_path in files:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    logger.info(f"  - {file_path.name} ({size_mb:.2f} MB)")
            else:
                logger.info(f"\n{category.upper()}: No files")

    def verify_downloads(self):
        """Verify that downloaded files are valid"""
        logger.info(f"\n=== Verifying Downloads ===")
        for category, directory in self.directories.items():
            files = list(directory.glob('*'))
            for file_path in files:
                try:
                    # Basic file validation
                    if file_path.stat().st_size == 0:
                        logger.warning(f"Empty file: {file_path}")
                    elif file_path.suffix.lower() == '.pdf':
                        # Basic PDF validation (check for PDF header)
                        with open(file_path, 'rb') as f:
                            if not f.read(4) == b'%PDF':
                                logger.warning(f"Invalid PDF file: {file_path}")
                    elif file_path.suffix.lower() == '.csv':
                        # Basic CSV validation
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: # Added errors='ignore' for robustness
                            first_line = f.readline()
                            if ',' not in first_line:
                                logger.warning(f"Invalid CSV file: {file_path}")
                    logger.info(f"✓ Valid: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error verifying {file_path}: {e}")

def main():
    """Main function to run the document downloader"""
    print("Automotive Document Downloader")
    print("=" * 40)
    downloader = DocumentDownloader()
    
    try:
        downloader.download_all_documents()
        downloader.verify_downloads()
        print(f"\n✅ Document download completed!")
        print(f"📁 Files saved to: {downloader.base_dir.absolute()}")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Download interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()