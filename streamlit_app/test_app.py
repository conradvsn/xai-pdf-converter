#!/usr/bin/env python3
"""
Quick test script to verify Streamlit app dependencies and structure
"""

import sys
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("🔍 Testing Dependencies...")
    print("=" * 60)

    dependencies = {
        'streamlit': 'Streamlit web framework',
        'pandas': 'Data manipulation',
        'PyPDF2': 'PDF reading',
        'docx': 'DOCX generation',
        'openpyxl': 'Excel generation',
        'PIL': 'Image processing',
        'spacy': 'NLP and NER'
    }

    results = {}

    for module, description in dependencies.items():
        try:
            __import__(module)
            results[module] = True
            print(f"✅ {module:15} - {description}")
        except ImportError:
            results[module] = False
            print(f"❌ {module:15} - {description} (NOT INSTALLED)")

    # Check spaCy model
    print("\n🔍 Testing spaCy Model...")
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✅ spaCy model 'en_core_web_sm' loaded successfully")
        results['spacy_model'] = True
    except Exception as e:
        print(f"❌ spaCy model 'en_core_web_sm' not available: {e}")
        results['spacy_model'] = False

    return results

def test_structure():
    """Test if all required files exist"""
    print("\n🔍 Testing App Structure...")
    print("=" * 60)

    base_dir = Path(__file__).parent

    required_files = {
        'Home.py': 'Main dashboard',
        'pages/1_📄_Single_PDF.py': 'Single PDF page',
        'pages/2_📦_Batch_Processing.py': 'Batch processing page',
        'pages/3_📊_Results.py': 'Results page',
        'pages/4_⚙️_Settings.py': 'Settings page',
        'components/stats_cards.py': 'Stats components',
        'components/__init__.py': 'Components package',
        'utils/session.py': 'Session management',
        'utils/__init__.py': 'Utils package',
        '.streamlit/config.toml': 'Streamlit config',
        'requirements.txt': 'Dependencies list',
        'run.sh': 'Launch script',
        'README.md': 'Documentation',
        'QUICKSTART.md': 'Quick start guide'
    }

    results = {}

    for file_path, description in required_files.items():
        full_path = base_dir / file_path
        if full_path.exists():
            results[file_path] = True
            print(f"✅ {file_path:40} - {description}")
        else:
            results[file_path] = False
            print(f"❌ {file_path:40} - {description} (MISSING)")

    return results

def test_imports():
    """Test if custom modules can be imported"""
    print("\n🔍 Testing Custom Modules...")
    print("=" * 60)

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    modules = {
        'src.config': 'Configuration module',
        'src.converter': 'PDF Converter module',
        'src.batch_processor': 'Batch processor module',
        'src.analysis.report_generator': 'Report generator module',
        'src.analysis.sensitive_info_detector': 'Sensitive info detector'
    }

    results = {}

    for module, description in modules.items():
        try:
            __import__(module)
            results[module] = True
            print(f"✅ {module:45} - {description}")
        except ImportError as e:
            results[module] = False
            print(f"❌ {module:45} - {description}")
            print(f"   Error: {e}")

    return results

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 xAI PDF Converter - Streamlit App Test")
    print("=" * 60)

    # Test dependencies
    dep_results = test_dependencies()

    # Test structure
    struct_results = test_structure()

    # Test imports
    import_results = test_imports()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    total_tests = len(dep_results) + len(struct_results) + len(import_results)
    passed_tests = sum(dep_results.values()) + sum(struct_results.values()) + sum(import_results.values())

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")

    # Critical dependencies
    critical = ['streamlit', 'PyPDF2', 'pandas']
    critical_passed = all(dep_results.get(dep, False) for dep in critical)

    print("\n" + "=" * 60)
    if critical_passed and passed_tests >= total_tests * 0.8:
        print("✅ App is ready to launch!")
        print("\nRun: ./run.sh")
        print("Or:  streamlit run Home.py")
        return 0
    elif critical_passed:
        print("⚠️  App can launch but some features may not work")
        print("\nMissing optional dependencies - install with:")
        print("pip install -r requirements.txt")
        return 1
    else:
        print("❌ Critical dependencies missing!")
        print("\nInstall with: pip install -r requirements.txt")
        return 2

if __name__ == "__main__":
    exit(main())
