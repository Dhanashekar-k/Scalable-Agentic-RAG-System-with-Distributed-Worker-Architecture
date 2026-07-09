#!/usr/bin/env python3
"""
Quick test runner - Execute full test suite and generate report
Usage: python run_tests.py [--url http://localhost:8000]
"""

import sys
import argparse
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_framework import TestFramework

def main():
    parser = argparse.ArgumentParser(description='Run Niyanta comprehensive tests')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Backend URL (default: http://localhost:8000)')
    parser.add_argument('--output', default='tests/results/test_report.html',
                       help='Output HTML report file')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🧪 NIYANTA TESTING FRAMEWORK")
    print("="*70)
    print(f"Backend URL: {args.url}")
    print(f"Report output: {args.output}")
    print("="*70 + "\n")
    
    # Create results directory
    result_dir = Path(args.output).parent
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize framework
    framework = TestFramework(base_url=args.url)
    
    try:
        # Run all tests
        success = framework.run_all_tests()
        
        if success:
            # Generate report
            report_path = framework.generate_report(args.output)
            print(f"\n✅ All tests completed successfully!")
            print(f"\n📊 View report: file://{report_path}")
            return 0
        else:
            print(f"\n❌ Tests failed")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
