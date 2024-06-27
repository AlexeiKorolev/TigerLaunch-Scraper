##TigerLaunch Webscraper and Analyzer

This project uses the Selenium chrome driver and pandas to quickly gather and organize the contact details of Princeton alumni to 
significantly reduce the workload needed for our partnership outreach officers. It integrates pyside for a simple desktop
user interface. 

The scraped data is sent to a Firebase database to ensure a centralized
collection location and automatically detects and prevents the scraping of duplicate names. The second component of the
program is intended to run on one system to analyze the gathered Firebase data through LLMs and a trained
neural network, before ranking the alumni most to least likely to be interested, making the outreach process 
much more efficient and streamlined.

## Usage

Run `python main.py`. Click `Connect to Firebase` and then `Start WebDriver`. Login to TigerNet
with a Princeton account and navigate to a results page in the alumni directory. Click `Scrape` and the program
will automatically scrape all the data on the webpage. Click `Save to CSV` in order to export the data into a 
CSV file that you choose. 

## Webscraping

The web-scraping is done within main.py alongside the UI code. Once the user reaches a page on TigerNet with
alumni contacts, the scraper automatically opens each link and then uses BeautifulSoup to find and store the name, email, phone number, employer, 
and graduation year to a pandas dataframe. The prefix/title (Ms. Mr. Dr. etc) is extracted from the full name through python's split function.

The scraper saves this data automatically to *autosave.csv* in case the user exits the program prematurely without formally exporting a csv. 
The CSV is saved through pandas' dataframe.to_csv() function. The scraper also automatically uploads the CSV data to Firebase in the structure of
a json dictionary document. 

## Analyzing

First, I verify that the "employer" field contains the correct value, as it is the most fluid out of all the others.
Using a basic linked-in webscraper, I can find the most recent company that the person works for. I made the decision not 
to include the history of employment as a factor in the analysis as it seems to add more complexity and has limited benefit.

Once I have the verified fields, I run their employers through a LLM that has three preferences set:
1. Prefer alum-founded startups that are seeking VC fundraising.
2. Prefer companies with strong student-fundraising programs.
3. Prefer VCs.

As of right now, these are the only criteria being applied to rank the alumni as, from past experience, they are the most
influential at determining the interest of alumni. 
