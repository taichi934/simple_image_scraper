# simple_image_scraper
web scraping for downloading a number of images from web

This script is made for scaping a number of images from certain web site.

I made this repo so that i can refer this when i code something for web scraping next time.

If you want to use this script, you most likely have to alter some parts of this script based on a web site you use at. Using deveopper mode of browsers would be helpful.

Hope you can get something from this piece of codes too !


## what does this code do?
1. Read urls from urls.txt
1. Open each url with brave browser using selenium and get html
1. Get <script> tag which contains JSON using BeautifulSoup4
1. Extract some information from JSON
1. Create a new directory and ownload images from server by running curl command on shell, and save them on the directory

## Modules
```
python3 -m pip install -r requirements.txt
```
By doing this, you can import beautifulsoup4 and selenium.

## Notes
- You need to list target urls in the urls.txt
- If something happens and code stops, urls which is not downloaded yet will be output to the failed_urls.txt. Next time you run the code, urls in the failed_urls.txt will be added to the urls.txt automatically.
- Selenium manipulates Brave browser on this code. You can use Chrome as well.
- You have to download chromedriver.exe from web. You can put it in your working directory if you want.