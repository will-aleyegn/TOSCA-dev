# TOSCA Reporting Tools

This directory contains tools and reports for documenting the TOSCA Laser Control System's features, with special focus on recent improvements to camera integration, patient data management, and UI.

## Quick Start

1. Run the setup script to ensure all dependencies are installed:
   ```
   python setup_reporting.py
   ```

2. Read the summary of new features:
   ```
   new_features_summary.md
   ```

3. Generate a comprehensive feature report with screenshots:
   ```
   python feature_reporter.py
   ```

## Contents

### Documentation Tools

- **feature_reporter.py** - Creates a comprehensive feature report with screenshots and detailed descriptions
- **setup_reporting.py** - Installs necessary dependencies and sets up directories
- **screenshot_tool.py** - Utility for capturing specific application screens
- **capture_directory_screenshots.py** - Utility for capturing file system organization

### Summary Documents

- **new_features_summary.md** - Concise overview of the new features grouped by category
- **features_screenshots.md** - Documentation guide showing what screenshots to capture

### Generated Reports

After running the reporting tools, the following will be generated:

- **TOSCA_Feature_Report_[timestamp].md** - Markdown report with feature descriptions and screenshots
- **TOSCA_Feature_Report_[timestamp].html** - HTML version of the report with styling
- **screenshots/** - Directory containing all captured screenshots

## Using the Feature Reporter

The feature reporter tool creates a comprehensive report documenting all TOSCA features with screenshots and detailed descriptions. It highlights new features with special formatting.

**Basic usage:**
```
python feature_reporter.py
```

This will guide you through:
1. Navigating to each screen of the application
2. Capturing screenshots
3. Generating a detailed report in both Markdown and HTML formats

**Non-interactive mode:**
```
python feature_reporter.py --non-interactive
```

## Feature Categories

The reports focus on these key areas:

1. **Camera Integration** - Live feed, image capture, patient linking
2. **Patient Management** - Patient records, search, data organization
3. **Treatment Sessions** - Session creation, image association, history tracking
4. **User Interface** - Streamlined controls, status indicators, workflow improvements
5. **Data Organization** - File naming, directory structure, data linkage

## Report Distribution

The generated reports are perfect for:

- Sharing with team members
- Including in user documentation
- Demonstrating system capabilities
- Tracking feature development

## Important Note

Always run the TOSCA application first before executing any of the screenshot or reporting tools. The tools expect to be able to capture the running application. 