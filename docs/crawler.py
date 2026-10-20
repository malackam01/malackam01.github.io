import urllib
import re
from bs4 import BeautifulSoup

# types:
# 0     PU
# 1     PO
# 2     GO
# 3     MO
# 4     Dodano
# 5     Predano
# 6     Odstaveno
# 7     Odvezeno

class Date:
    def __init__(self, month, year):
        self.month = int(month)
        self.year = int(year)
    def __repr__(self):
        return f"{self.month}.{self.year}"

class TramData:
    def __init__(self):
        self.inspections = []
    def __repr__(self):
        return self.inspections.__repr__()
    def add(self, type, date, isnew):
        self.inspections.append((type, date, isnew))

class Inspections:
    def __init__(self):
        self.data = dict()
    def __repr__(self):
        res = ""
        for tram_num in self.data:
            res += f"{tram_num}:\n"
            res += self.data[tram_num].__repr__() + "\n"
        return res
    def add(self, tram_num, type, date, isnew):
        if tram_num not in self.data:
            self.data[tram_num] = TramData()
        self.data[tram_num].add(type, date, isnew)

current_date = Date(0,0)
current_isnew = False
date_searcher = re.compile(r"(\d?\d)\.(\d\d\d\d)")
evid_searcher = re.compile(r"\D(\d\d\d\d)\D")
all_inspections = Inspections()
start_year = 2012
end_year = 2026

def set_date(line):
    global current_date
    date = date_searcher.search(line)
    if not date:
        current_date = Date(7, 2012)
    else:
        month = date[1]
        year = date[2]
        current_date = Date(month, year)

def add_inspections(line):
    global all_inspections, current_isnew, current_date, evid_searcher

    if line.startswith("PÚ"):
        current_type = 0
    elif line.startswith("PO"):
        current_type = 1
    elif line.startswith("GO"):
        current_type = 2
    elif line.startswith("MO"):
        current_type = 3
    elif line.startswith("Dodán"):
        current_type = 4
    elif line.startswith("Předán"):
        current_type = 5
    elif line.startswith("Odstaven") or line.startswith("K odstaven"):
        current_type = 6
    elif line.startswith("Odvezen"):
        current_type = 7
    else:
        return

    evids = evid_searcher.findall(line)
    for evid in evids:
        all_inspections.add(evid, current_type, current_date, current_isnew)

def process_page(url):
    global current_isnew, current_date, date_searcher
    sock = urllib.request.urlopen(url)
    htmlSource = sock.read()
    sock.close()
    soup = BeautifulSoup(htmlSource, features="lxml")
    txt = soup.get_text()
    for line in txt.splitlines():
        if line.startswith("Novinky v dílnách"):
            current_isnew = True
            set_date(line)
        elif line.startswith("Stav dílen"):
            current_isnew = False
            set_date(line)
        elif line.startswith("Související"):
            break
        else:
            add_inspections(line)

def insp_num_to_text(num):
    num = int(num)
    if num == 0:
        return "🟩"
    elif num == 1:
        return "🟨"
    elif num == 2:
        return "🟥"
    elif num == 3:
        return "💥"
    elif num == 4:
        return "🆕"
    elif num == 5:
        return "🔜"
    elif num == 6:
        return "🪴"
    elif num == 7:
        return "↩️"

def print_frontmatter(f, evid):
    f.write(f"---\nlayout: default\ntitle: {evid}\npermalink: /data/{evid}\n---\n")

def print_table_header(f):
    for m in range(0,13):
        f.write(f"|{m}")
    f.write("|\n")
    for _ in range(0,13):
        f.write("|:-:")
    f.write("|\n")

def generate_md_page(evid, inspections):
    global start_year, end_year
    insp_list = list(reversed(inspections.inspections))
    with open(f"data/{evid}.markdown", "w") as f:
        print_frontmatter(f, evid)
        print_table_header(f)
        type, date, isnew = insp_list[0]
        for y in range(start_year, end_year+1):
            f.write(f"|{y}")
            for m in range(1, 13):
                f.write("|")
                first = True
                while date.month == m and date.year == y:
                    if first:
                        f.write(f"{insp_num_to_text(type)}")
                        if isnew:
                            f.write("❗️")
                    insp_list = insp_list[1:]
                    first = False
                    if not insp_list:
                        date = Date(0,0)
                    else:
                        type, date, isnew = insp_list[0]
            f.write("|\n")

def generate_index_page(evids):
    evid_nums = []
    with open("index.markdown", "w") as f:
        f.write("---\nlayout: home\n---\n")
        for e in evids:
            evid_nums.append(int(e))
        evid_nums = sorted(evid_nums)
        for ix, e in enumerate(evid_nums):
            if int(e)//100 > int(evid_nums[ix-1])//100:
                f.write("\n")
            f.write(f"[{e}](data/{e})\n")

urls = []
with open("urls.txt", "r") as url_file:
    for url_line in url_file:
        urls.append(url_line)
for url in urls:
    process_page(url)

for evid in all_inspections.data:
    generate_md_page(evid, all_inspections.data[evid])

generate_index_page(all_inspections.data)