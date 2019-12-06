import json
import os
import re

whole_dict = {}
raw_text_path = "/home/jianheng/silent-suffering/Crawling/patient/PostProcessing/data_processed_entry"
for files in os.listdir(raw_text_path):
    if '.' not in files:
        for filename in os.listdir(raw_text_path + '/' + files):
            if filename[-3:] == ".jl":
                text_f = open(raw_text_path + '/' + files + '/' + filename, 'r')
                endIndex = re.search('-',filename).span()[0]
                group = filename[:endIndex]
                if not group in whole_dict:
                    whole_dict[group] = set()
                whole_dict[group].add(json.loads(text_f.readline())['poster']) 
stas_dict = {}
for key, value in whole_dict.items():
    stas_dict[key] = len(value)
with open('unique_poster.txt', 'w') as f:
    json.dump(stas_dict, f)
