import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv # Imports the 'csv' module to enable reading and writing CSV files.

def sanitize_filename(filename):
    """Sanitizes a string to be used as a valid filename."""
    # Removes characters that are invalid in most file systems from the filename string.
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)
    # Replaces space characters with underscores to ensure filename consistency.
    filename = filename.replace(' ', '_')
    # Truncates the filename to 100 characters to prevent overly long names.
    return filename[:100]

def get_field_value(section_element, label_text, default_value="N/A"):
    """
    Extracts the text of a <strong> tag associated with a given <label> text
    within the provided section_element.
    """
    try:
        # Defines an XPath to locate the desired <strong> value element relative to its <label>.
        xpath = f".//label[normalize-space()='{label_text}']/following-sibling::strong[1]"
        # Finds the specific web element using the XPath query within the given section.
        value_element = section_element.find_element(By.XPATH, xpath)
        # Extracts the text content from the found element and removes leading/trailing whitespace.
        text = value_element.text.strip()
        # Returns the cleaned text; if empty, it returns the specified default value.
        return text if text else default_value
    except Exception: # Handles exceptions, typically NoSuchElementException, if the desired element isn't found.
        # Provides a fallback default value when data extraction fails.
        return default_value

def process_multiple_projects(num_projects_to_process=6):
    options = webdriver.FirefoxOptions()
    # Configures Firefox to run in headless mode (no GUI) if this line is uncommented by the user.
    # options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    # Sets the browser window size to ensure consistent layout and element visibility.
    driver.set_window_size(1920, 1200)

    # Defines the directory name for storing screenshots captured during errors.
    screenshots_dir = "screenshots_errors"
    # Creates the error screenshots directory if it does not already exist on the filesystem.
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"Created directory for error screenshots: {screenshots_dir}")
    else:
        print(f"Directory for error screenshots '{screenshots_dir}' already exists.")

    # Specifies the URL of the main page listing all the projects to be processed.
    main_project_list_url = "https://rera.odisha.gov.in/projects/project-list"

    # Initializes an empty list to store dictionaries, each holding data for one scraped project.
    all_projects_scraped_data = []
    # Defines the column headers for the output CSV file; names are descriptive of their content and source.
    csv_headers = [
        "Sanitized_Project_Identifier_From_Card",
        "Raw_Project_Name_From_Card",
        "Project_Name_Scraped_From_Details_Page",
        "Project_Type_Scraped_From_Details_Page",
        "RERA_Reg_No_Scraped_From_Details_Page",
        "Promoter_Company_Name_Scraped",
        "Promoter_Registration_No_Scraped"
    ]

    try:
        # Navigates the web driver to the main project listing URL.
        print("STEP 1: Loading main project list page")
        driver.get(main_project_list_url)
        # Waits for the project cards to be present, ensuring the page is substantially loaded.
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card"))
        )
        print("Main project list page loaded.")
        # Allows a brief pause for any dynamic content on the page to settle.
        time.sleep(3)

        # Attempts to hide any fixed navigation bar that might obscure clickable elements.
        print("STEP 2: Hiding navbar (if it obscures elements)")
        try:
            # Defines a list of common CSS selectors used for fixed navigation bars.
            navbar_selectors = ["nav.navbar.fixed-top", "nav.fixed-top", ".navbar-main.fixed-top"]
            navbar_hidden = False
            # Iterates through the selectors to find and hide a visible navigation bar.
            for selector in navbar_selectors:
                try:
                    # Finds the navigation bar element using the current CSS selector.
                    navbar = driver.find_element(By.CSS_SELECTOR, selector)
                    # Checks if the found navigation bar is currently displayed.
                    if navbar.is_displayed():
                        # Hides the navigation bar using JavaScript if it is visible.
                        driver.execute_script("arguments[0].style.display = 'none';", navbar)
                        print(f"Navbar hidden using selector: '{selector}'.")
                        navbar_hidden = True
                        # Pauses briefly after hiding the navbar to allow the page to adjust.
                        time.sleep(1)
                        # Exits the loop once a navigation bar has been successfully hidden.
                        break
                except: # Catches exceptions if a selector doesn't find an element, allowing iteration to continue.
                    continue # Proceeds to the next selector if the current one fails.
            # Checks if a navigation bar was successfully hidden during the attempts.
            if not navbar_hidden:
                print("Navbar not found with common selectors or not displayed. Proceeding.")
        except Exception as nav_e: # Catches any other exceptions during the navbar hiding process.
            print(f"Could not hide navbar, proceeding. Error: {nav_e}")

        # Iterates through the specified number of projects to process them one by one.
        for i in range(num_projects_to_process):
            # Sets a default identifier for logging, used if project name extraction fails.
            project_identifier_for_log = f"Project_Loop_{i + 1}"
            # Initializes the variable for the raw project name extracted from the card.
            raw_project_name_from_card = "N/A"

            # Initializes a dictionary to store all scraped data for the current project, with default "N/A" values.
            current_project_data_dict = {header: "N/A" for header in csv_headers}

            print(f"\n--- Processing Project Loop Index {i} ---")

            try:
                # Ensures the driver is on the main project list page before processing each new project.
                if driver.current_url != main_project_list_url:
                    print(f"Not on main project list page. Navigating back to {main_project_list_url}")
                    # Navigates back to the main project list page if the driver is on a different URL.
                    driver.get(main_project_list_url)

                # Waits for project card elements to be present, confirming the list page is ready.
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card"))
                )
                # Pauses briefly for elements to settle after potential page reload.
                time.sleep(2)

                # Retrieves all project card elements visible on the current page.
                project_cards = driver.find_elements(By.CSS_SELECTOR, "div.project-card")

                # Checks if enough project cards are available on the page for the current iteration.
                if i >= len(project_cards):
                    print(f"Not enough project cards found on the page to process project index {i}. Found {len(project_cards)}.")
                    # Stops processing if the requested project index is out of bounds.
                    break

                # Selects the specific project card for the current iteration.
                current_project_card = project_cards[i]

                # Attempts to extract the project's name from its card for logging and data.
                try:
                    # Locates the h5 element containing the project title within the current card.
                    project_name_element = current_project_card.find_element(By.CSS_SELECTOR, "h5.card-title")
                    # Extracts and strips the text of the project name from the element.
                    temp_raw_name = project_name_element.text.strip()
                    # Updates identifiers if a valid project name is successfully extracted.
                    if temp_raw_name:
                        raw_project_name_from_card = temp_raw_name
                        project_identifier_for_log = sanitize_filename(temp_raw_name)
                    print(f"Identified Project Name (Card): '{raw_project_name_from_card}' (Identifier: '{project_identifier_for_log}')")
                except Exception as name_ex: # Handles cases where the project name cannot be extracted from the card.
                    print(f"Could not extract project name from card, using default identifier: '{project_identifier_for_log}'. Error: {name_ex}")

                # Stores the determined project identifier and raw name in the data dictionary using descriptive headers.
                current_project_data_dict["Sanitized_Project_Identifier_From_Card"] = project_identifier_for_log
                current_project_data_dict["Raw_Project_Name_From_Card"] = raw_project_name_from_card

                # Scrolls the current project card into view to ensure it's clickable.
                print(f"STEP {i+1}.A: Scrolling to project: '{project_identifier_for_log}'")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", current_project_card)
                # Waits for the scroll animation and any lazy loading to complete.
                time.sleep(2)

                # Clicks the 'View Details' button on the project card to navigate to its details page.
                print(f"STEP {i+1}.B: Clicking 'View Details' for '{project_identifier_for_log}'")
                # Waits for the 'View Details' button to become clickable before interacting.
                view_details_button = WebDriverWait(current_project_card, 20).until(
                    EC.element_to_be_clickable((By.XPATH, ".//a[contains(@class, 'btn-primary') and normalize-space()='View Details']"))
                )
                view_details_button.click()
                print("'View Details' button clicked.")

                # Verifies that the project details page has loaded by checking for a specific header.
                print(f"STEP {i+1}.C: Verifying details page and waiting for content for '{project_identifier_for_log}'")
                # Defines the XPath for the header element on the project details page.
                project_details_header_xpath = "//h5[normalize-space()='Details of the Project']"
                # Waits until the project details header is visible on the page.
                WebDriverWait(driver, 40).until(
                    EC.visibility_of_element_located((By.XPATH, project_details_header_xpath))
                )
                print("Details page (initial tab) header loaded successfully.")
                # Allows extra time for JavaScript or Angular content to fully render on the details page.
                time.sleep(4)

                # Attempts to scrape data from the "Details of the Project" section.
                print(f"STEP {i+1}.D: Scraping Project Details section for '{project_identifier_for_log}'")
                try:
                    # Defines XPath for the container of the project details section.
                    project_details_container_xpath = "//div[contains(@class, 'project-details') and .//h5[normalize-space()='Details of the Project']]"
                    # Waits for the project details section container to become visible.
                    project_details_section_element = WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, project_details_container_xpath))
                    )
                    # Scrapes specific fields from the project details section using the helper function.
                    current_project_data_dict["Project_Name_Scraped_From_Details_Page"] = get_field_value(project_details_section_element, "Project Name")
                    current_project_data_dict["Project_Type_Scraped_From_Details_Page"] = get_field_value(project_details_section_element, "Project Type")
                    current_project_data_dict["RERA_Reg_No_Scraped_From_Details_Page"] = get_field_value(project_details_section_element, "RERA Regd. No.")
                    print(f"  Scraped - Project Name: {current_project_data_dict['Project_Name_Scraped_From_Details_Page']},"
                          f" Type: {current_project_data_dict['Project_Type_Scraped_From_Details_Page']},"
                          f" RERA No: {current_project_data_dict['RERA_Reg_No_Scraped_From_Details_Page']}")
                except Exception as scrape_details_e: # Handles errors encountered during scraping of project details.
                    print(f"ERROR scraping project details for '{project_identifier_for_log}': {type(scrape_details_e).__name__} - {str(scrape_details_e)}")
                    # Saves a screenshot if an error occurs while scraping this section.
                    driver.save_screenshot(os.path.join(screenshots_dir, f"{project_identifier_for_log}_error_scraping_project_details.png"))
                # Pauses briefly after attempting to scrape.
                time.sleep(1)

                # Navigates to the "Promoter Details" tab on the project details page.
                print(f"STEP {i+1}.E: Switching to Promoter Details for '{project_identifier_for_log}'")
                # Defines an XPath targeting the 'Promoter Details' tab link or button.
                promoter_tab_link_xpath = "//a[@role='tab' and normalize-space()='Promoter Details'] | //button[@role='tab' and normalize-space()='Promoter Details']"
                # Waits for the 'Promoter Details' tab to be clickable.
                promoter_tab_element = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, promoter_tab_link_xpath))
                )
                # Scrolls the 'Promoter Details' tab into view before clicking.
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", promoter_tab_element)
                time.sleep(1) # Allows time for scrolling to complete.
                promoter_tab_element.click() # Clicks the tab to switch views.
                print("'Promoter Details' tab clicked.")

                # Waits for the content of the "Promoter Details" section to load after tab switch.
                print(f"STEP {i+1}.F: Waiting for Promoter Details content load for '{project_identifier_for_log}'")
                # Defines XPath for the container of the promoter details section.
                promoter_details_container_xpath_for_wait = "//div[contains(@class, 'promoter') and .//h5[normalize-space()='Promoter Details']]"
                # Waits for the promoter details section container to become visible.
                WebDriverWait(driver, 40).until(
                    EC.visibility_of_element_located((By.XPATH, promoter_details_container_xpath_for_wait))
                )
                # Further waits for specific content (a row with child divs) within the promoter details body to ensure it's rendered.
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, f"{promoter_details_container_xpath_for_wait}//div[contains(@class,'card-body')]//div[contains(@class,'row') and count(.//div) > 1]"))
                )
                print("Promoter details content seems loaded.")
                # Allows extra time for JavaScript or Angular content to fully render in this section.
                time.sleep(4)

                # Attempts to scrape data from the "Promoter Details" section.
                print(f"STEP {i+1}.G: Scraping Promoter Details section for '{project_identifier_for_log}'")
                try:
                    # Waits for the promoter details section element to be visible again (or confirms visibility).
                    promoter_details_section_element = WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, promoter_details_container_xpath_for_wait))
                    )
                    # Scrapes specific fields from the promoter details section.
                    current_project_data_dict["Promoter_Company_Name_Scraped"] = get_field_value(promoter_details_section_element, "Company Name")
                    current_project_data_dict["Promoter_Registration_No_Scraped"] = get_field_value(promoter_details_section_element, "Registration No.")
                    print(f"  Scraped - Promoter Co. Name: {current_project_data_dict['Promoter_Company_Name_Scraped']},"
                          f" Promoter Reg. No: {current_project_data_dict['Promoter_Registration_No_Scraped']}")
                except Exception as scrape_promoter_e: # Handles errors encountered during scraping of promoter details.
                    print(f"ERROR scraping promoter details for '{project_identifier_for_log}': {type(scrape_promoter_e).__name__} - {str(scrape_promoter_e)}")
                    # Saves a screenshot if an error occurs while scraping this section.
                    driver.save_screenshot(os.path.join(screenshots_dir, f"{project_identifier_for_log}_error_scraping_promoter_details.png"))
                # Pauses briefly after attempting to scrape.
                time.sleep(1)

                # Appends the scraped data (or defaults) for the current project to the main list.
                all_projects_scraped_data.append(current_project_data_dict)

                # Navigates back to the main project listing page to process the next project.
                print(f"STEP {i+1}.H: Returning to main project list page from '{project_identifier_for_log}'s details.")
                driver.back()
                # Waits for the project cards to reload on the main list page after navigating back.
                WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card"))
                )
                print("Successfully returned to main project list page.")
                # Pauses to allow the main list page to settle before starting the next iteration.
                time.sleep(3)

            except Exception as project_loop_e: # Handles any unexpected errors during the processing of a single project.
                print(f"!!! ERROR processing project loop for '{project_identifier_for_log}' (Project index {i}): {type(project_loop_e).__name__} - {str(project_loop_e)}")
                # Defines a filename for the error screenshot related to this project loop failure.
                error_ss_filename = f"{project_identifier_for_log}_MAIN_LOOP_ERROR.png"
                try:
                    # Attempts to save a screenshot of the page state at the time of the error.
                    driver.save_screenshot(os.path.join(screenshots_dir, error_ss_filename))
                    print(f"Saved error screenshot: {error_ss_filename}")
                except Exception as save_err: # Handles failure to save the error screenshot.
                    print(f"Could not save error screenshot: {save_err}")

                # Appends partially collected data or default values for this project if an error occurred mid-process.
                all_projects_scraped_data.append(current_project_data_dict)

                # Attempts to recover by navigating back to the main project list page to continue.
                print("Attempting to navigate back to project list to continue with the next project...")
                try:
                    driver.get(main_project_list_url)
                    # Waits for project cards to ensure the main list page is loaded after recovery attempt.
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-card"))
                    )
                    print("Successfully navigated back to project list after error.")
                    # Pauses to let the page settle after recovery.
                    time.sleep(3)
                except Exception as nav_back_err: # Handles failure to navigate back to the project list after an error.
                    print(f"Failed to navigate back to project list after error: {nav_back_err}. Aborting further projects.")
                    # Terminates the project processing loop if recovery fails.
                    break
        # Indicates that all specified projects have been attempted.
        print("\nAll specified projects processed (or attempted).")

        # Defines the name for the output CSV file.
        csv_file_path = "rera_odisha_scraped_data.csv"
        # Gets the absolute path of the CSV file for a more informative log message.
        abs_csv_path = os.path.abspath(csv_file_path)
        print(f"\nAttempting to write scraped data to: {abs_csv_path}")
        # Writes all collected project data to the specified CSV file.
        try:
            # Opens the CSV file in write mode with UTF-8 encoding.
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Creates a DictWriter object to write dictionaries to CSV, using defined headers.
                writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
                # Writes the header row to the CSV file.
                writer.writeheader()
                # Writes all rows of project data to the CSV file.
                writer.writerows(all_projects_scraped_data)
            print(f"Data successfully written to {abs_csv_path}")
        except IOError as io_e: # Specifically catches I/O errors during file writing.
            print(f"ERROR: Could not write data to CSV file '{abs_csv_path}'. Reason: {io_e}")
        except Exception as csv_e: # Catches any other unexpected errors during CSV writing.
            print(f"An unexpected error occurred during CSV writing: {type(csv_e).__name__} - {str(csv_e)}")

    except Exception as e: # Catches any critical unexpected error in the main script execution.
        print(f"An critical unexpected error occurred in the main script: {type(e).__name__} - {str(e)}")
        # Checks if the driver is still active and has a session ID.
        if 'driver' in locals() and driver.session_id:
            try:
                # Attempts to save a screenshot for critical errors.
                driver.save_screenshot(os.path.join(screenshots_dir, "critical_error_page_main_script_failure.png"))
                print("Saved a screenshot for the critical error.")
            except Exception as final_save_err: # Handles failure to save this final error screenshot.
                print(f"Could not save final error screenshot: {final_save_err}")
    finally:
        # Ensures the WebDriver quits properly, closing the browser, regardless of errors.
        if 'driver' in locals() and driver.session_id:
            driver.quit()
        print("Scraping process completed.")

if __name__ == "__main__":
    # Calls the main processing function, specifying the number of projects to scrape.
    process_multiple_projects(num_projects_to_process=6)