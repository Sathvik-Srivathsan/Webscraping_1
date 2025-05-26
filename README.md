# Webscraping_1

Purpose: Automates scraping of project and promoter details from the Odisha RERA project listing website.
Core Technology: Uses Python with the Selenium library for web browser automation.
Process:

    Launches a Firefox browser instance.
    Navigates to the main project list URL: https://rera.odisha.gov.in/projects/project-list.
    Iterates through a specified number of projects (default: 6) from the list.
    For each project:
        Clicks "View Details" to open the individual project page.
        Scrapes "Project Name", "Project Type", and "RERA Regd. No." from the "Details of the Project" section.
        Switches to the "Promoter Details" tab.
        Scrapes "Company Name" and "Registration No." for the promoter.
        Navigates back to the main project list to process the next project.
    Includes robust error handling, attempts to hide obscuring navbars, and saves error screenshots.

Output:

    Generates a single CSV file named rera_odisha_scraped_data.csv containing all scraped information.
    Creates a screenshots_errors/ directory to store screenshots captured during errors.

Setup: Requires Python, pip install selenium, and the geckodriver executable for Firefox.
