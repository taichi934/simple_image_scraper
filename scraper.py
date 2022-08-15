from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import subprocess, os, json, time, random, re, sys, atexit, shutil

# ++++ Change  SAVE_DIR and BRAVE_PATH for your environment +++++++
SAVE_DIR: str = r"C:\Users\<user name>\Downloads"
# used for option of webdriver; windows example below
BRAVE_PATH: str = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
# path to chromedriver which you have to download
DRIVER_PATH: str = r"path\to\chromedriver"
# find media server url with web developper tools of your browser
MEDIA_URL: str = "https://abcde.com/galleries/" # example



def get_failed_urls_from_file() -> list[str]:
    path: str = r".\failed_urls.txt"
    # if txt file does not exist, create one
    if not os.path.exists(path):
        with open(path, "w") as f: f.write("")
        return []
    else:
        try:
            with open(path,'r') as f:
                failed_urls: list[str] =  f.readlines()
                print("failed_urls:")
                print(failed_urls)
                return failed_urls
        except Exception as e:
            print(e)
            sys.exit()


def add_failed_urls_to_file(urls: list[str]) -> None:
    path: str = r".\urls.txt"
    try:
        with open(path, "a") as f:
            f.write("\n")
            f.writelines(urls)
    except Exception as e:
        print(e)
        print("Cannot add failed urls to file...")
        sys.exit()


# move urls from failed_urls.txt to urls.txt
def failed_urls_to_urls() -> None:
    path_failed_urls: str = r".\failed_urls.txt"
    # if txt file does not exist, create one
    if not os.path.exists(path_failed_urls):
        with open(path_failed_urls, "w") as f: f.write("")
    path_urls: str = r".\urls.txt"
    try:
        with open(path_failed_urls,'r') as f:
            failed_urls: list[str] =  f.readlines()
            print("failed_urls:")
            print(failed_urls)

        with open(path_urls, "a") as f:
            f.write("\n")
            f.writelines(failed_urls)
    except Exception as e:
        print(e)
        print("Cannot open file...")
        sys.exit()



def get_urls_from_file() -> list[str]:
    try:
        with open(r".\urls.txt",'r') as f:
            url_list: list[str] =  f.readlines()
        # url_list = [url.rstrip("\n") for url in url_list if url != "\n"] # remove elements; "\n"
        url_list = [url for url in url_list if url != "\n"] # remove elements; "\n"
        print("urls:")
        print(url_list, end="\n\n")
        return url_list
    except Exception as e:
        print(e)
        print("Cannot read file from urls.txt...")
        sys.exit()


def get_html(i: int, driver, urls: list[str]):
    try:
        driver.get(urls[i])
        if i == 0:
            time.sleep(15)
        else:
            time.sleep(3)
        html = driver.page_source
        return html
    except Exception as e:
        driver.quit()
        print(e)
        print(f"Could not get html at driver.get({urls[i]})")


def extract_json_from_script_tag(script) -> dict:
    json_str: str = script.string
    json_str = json_str[json_str.find("\"{"):] # cut until json
    json_str = json_str.replace(");", "") # cut after json
    # print("json_str: ") # log json
    return json.loads(json_str)


def extract_title(data: dict) -> str:
    title: str = data["japanese"]
    if title == "":
        # use english title instead
        title = data["english"]

    return title


def rename(title: str) -> str:
    # validate folder name
    # valid:  ￥　／　：　＊　？　”　＜　＞　｜
    title = title.replace("　", " ")
    title = title.replace("?", "？")
    title = title.replace(":", "：")
    title = title.replace("/", "／")
    title = title.replace("\\", "￥")
    title = title.replace("|", "｜")

    # remove unnecessary words
    title = title.replace("[DL版]", "")
    title = title.replace("[Digital]", "")
    title = title[title.index("["):] # "["があるところからがtitle
    title = re.sub("\s$", "", title) # 末尾の空白除去
    title = re.sub("\.$", "", title) # 末尾のピリオド除去
    # pattern = re.compile(r"\(C[0-9].\)\s")
    # return pattern.sub("", title)
    return title

def get_tag_list_from_file() -> list[str]:
    try:
        with open(r".\tags.txt",'r') as f:
            tag_list: list[str] = f.readlines()

        # remove "\n" at the end of each tag and element "\n"
        tag_list = [tag.rstrip("\n") for tag in tag_list if tag != "\n"]
        return tag_list
    except Exception as e:
        print(e)
        print("Cannot read tags from tags.txt...")
        sys.exit()


def extract_tags(json: dict) -> str:
    # chose only popular tags
    tags_list: list[str] = get_tag_list_from_file()
    tags: list[dict] = json["tags"]
    tags = sorted(tags, key=lambda t: t["count"], reverse=True)

    t: str = "__{"
    parody: str = ""
    artist: str = ""
    for tag in tags:
        # tagがtags.txtに含まれてるものは追加
        if tag["type"] == "tag" and tag["name"] in tags_list:
            t+= tag["name"].replace(" ", "-") + "_"

        # "original"以外のparodyも追加
        elif ("type", "parody") in tag.items() and tag["name"] != "original":
            parody += tag["name"].replace(" ", "-") + "_"

        elif ("type", "artist") in tag.items():
            artist += "artist(" + tag["name"].replace(" ", "-") + ")_"

    t += parody + artist

    if t == "__{":
        t = ""
    else:
        t = t.rstrip("_") + "}"

    return t


def download_images(title: str, tags: str, media_id: str, num_pages:int) -> int:
    partial_url: str = f"{MEDIA_URL}{media_id}/"

    save_dir: str = f"{SAVE_DIR}\\{title}{tags}"
    num_pages += 1 # 表紙を最後から2番目に挿入するから

    # mkdir if it does not exist
    # check [00_temp] and comics folder
    if not os.path.exists(save_dir):
        try:
            os.mkdir(save_dir)
            print("\tNew Folder: ", end="")
            print(save_dir)
            print(f"\t{num_pages} pages")
            download_start_index: int = 1
        except Exception as e:
            print(e)
            print("\tFoldername is invalid... ")
            print(save_dir)
            return 1
    else:
        # check if all the images are downloaded
        if os.path.exists(f"{save_dir}\\{num_pages}.jpg") or os.path.exists(f"{save_dir}\\{num_pages}.png"):
            # check failed png images
            download_failed_png_image(num_pages, partial_url, save_dir)
            print(f"\tThis one is already downloaded; {title}{tags}")
            return -1
        else:
            print("\tThis folder still has images left to download.")
            download_start_index = skip_already_downloaded(save_dir, num_pages)

    # subprocess to run command curl
    download_start: float = time.perf_counter()

    print(f"\trun command: curl -s -O {partial_url}[{download_start_index}-{num_pages-1}].jpg\n\tdownloading . . .")
    try:
        subprocess.run(["curl", "-s", "-O", f"{partial_url}[{download_start_index}-{num_pages-1}].jpg"], cwd=save_dir)

        # フォルダーには最後から2番目、1番目の準で2枚表示される
        # 表紙を最後から2番目になるようにもう一回ダウンロード
        subprocess.run(["curl", "-s", "-o", f"{num_pages-1}.jpg", f"{partial_url}1.jpg"], cwd=save_dir)
        subprocess.run(["curl", "-s", "-o", f"{num_pages}.jpg", f"{partial_url}{num_pages-1}.jpg"], cwd=save_dir)

        download_failed_png_image(num_pages, partial_url, save_dir)
    except Exception as e: # for ctrl+c pushed
        remove_last_image(title, tags)
        print(e)
        sys.exit() # move_remaining_list will be executed followingly


    download_end: float = time.perf_counter()
    print_time_spent("\tCompleted downloading !\tTook", download_start, download_end, "\n")

    return 0


# find where to start download
def skip_already_downloaded(save_dir: str, num_pages: int) -> int:
    for i in range(1,num_pages+1):
        # if both .jpg and .png not found
        if ( not os.path.exists(f"{save_dir}\\{i}.jpg") ) and ( not os.path.exists(f"{save_dir}\\{i}.png") ):
                return i
    return 1 # supposed not to reach here


# search not-downloaded image and download it as .png
def download_failed_png_image(num_pages: int, partial_url: str, save_dir: str) -> None:
    print("\t  checking if there's a failed png image and replace it...")
    for i in range(1,num_pages+1):
        jpg_file: str = f"{save_dir}\\{i}.jpg"
        try:
            if os.path.getsize(jpg_file) < 500:  # failed image size is 146 byte
                if i == num_pages-1: # 後ろから2番目の表紙
                    subprocess.run(["curl", "-s", "-o", f"{partial_url}{i}.png", f"{partial_url}1.png"], cwd=save_dir)
                elif i == num_pages: # 最後のページ
                    subprocess.run(["curl", "-s", "-o", f"{partial_url}{i}.png", f"{partial_url}{num_pages - 1}.png"], cwd=save_dir)
                else:
                    subprocess.run(["curl", "-s", "-O", f"{partial_url}{i}.png"], cwd=save_dir)
                os.remove(jpg_file)
        except OSError as e:
            if os.path.exists(f"{save_dir}\{i}.png"):
                continue


# remove last downloaded image which should be a broken file
def remove_last_image(title: str, tags: str) -> None:
    dir: str = f"{SAVE_DIR}\\{title}{tags}"

    last: str = max(os.listdir(dir))
    last = last[:-4] # file name without extension
    try:
        os.remove(f"{dir}\\{last}.jpg")
        print(f"removed {last}.jpg")
    except FileNotFoundError as e:
        os.remove(f"{dir}\\{last}.png")
        print(f"removed {last}.png")


def move_remaining_list(invalid_urls: list[str], urls: list[str], current_i: int) -> None:
    remained_urls: list[str] = urls[current_i:]
    print("\nRemained urls will be moved to 'failed_urls.txt' because something occured...")
    print("\nInvalid urls:")
    print(invalid_urls)
    print("\nRemained urls:")
    print(remained_urls, end="\n\n")
    output_failed_urls(invalid_urls + remained_urls)


def print_time_spent(str: str, s: float, e: float, end: str) -> None:
        time_spent: float = round(e - s)
        minuite: int = round(time_spent / 60)
        second: int = time_spent % 60
        print(f"{str} {minuite}min {second}sec\n", end=end)


def output_failed_urls(urls: list[str]) -> None:
    try:
        with open(r".\failed_urls.txt", "w") as f:
            f.writelines(urls)
    except Exception as e:
        print(e)
        print("Failed to output urls to 'failed_urls.txt'")





if __name__ == "__main__":

    program_start: float = time.perf_counter() # measure time

    f_urls: list[str] = get_failed_urls_from_file()
    add_failed_urls_to_file(f_urls)
    # failed_urls_to_urls() # bring the urls that failed last time

    urls: list[str] = get_urls_from_file()


    # use Brave instead of Chrome
    service = Service(excutable_path=DRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.binary_location = BRAVE_PATH
    driver = webdriver.Chrome(service=service, options=options)

    page_all: int = 0
    stop_download: int = 0
    invalid_urls: list[str] = ['\n\n']
    download_error_list: dict = {}

    for i in range(0, len(urls)):
        atexit.register(move_remaining_list, invalid_urls=invalid_urls, urls=urls, current_i=i)

        print(f"[ {i+1} / {len(urls)} ]  {urls[i]}")
        # get HTML
        response_html = get_html(i, driver, urls)
        soup = BeautifulSoup(response_html, "html.parser") # analyze html by selected parser

        # get json from <script> tag
        scripts: list = soup.find_all("script")
        script = scripts[4]
        extracted_json = extract_json_from_script_tag(script)

        # get title, media_id, num_pages
        extracted_json: dict = json.loads(extracted_json)
        media_id: str = extracted_json["media_id"]
        title: str = rename(extract_title(extracted_json["title"])) # remove invalid words
        num_pages: int = extracted_json["num_pages"]
        tags: str = extract_tags(extracted_json)
        page_all += num_pages # for logging

        download_error: int = download_images(title, tags, media_id, num_pages)

        if download_error == 1: # folder name includes a invalid word
            download_error_list[urls[i]] = title + tags
            invalid_urls.append(urls[i])
            stop_download += 1
        elif download_error == -1: #quit to download bc already there
            page_all -= num_pages # does not count already downloaded one
            stop_download += 1

        atexit.unregister(move_remaining_list) # to update the argument for next loop

    if download_error_list:
        print("Failed to download:")
        print(download_error_list)
        output_failed_urls(invalid_urls)

    driver.quit()

    program_end: float = time.perf_counter()
    print_time_spent("\nProgram:\n\tTook ", program_start, program_end, f"\tDownloaded {page_all} images from {len(urls)-stop_download} urls\n")

