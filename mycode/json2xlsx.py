# -*- coding:utf-8 -*-
# Author:   liyanpeng
# Email:    yanpeng.li@cumt.edu.cn
# Datetime: 2023/6/12 12:16
# Filename: json2xlsx.py
import os
import json
import glob
from openpyxl import workbook


def write_xlsx(context_list, savename='output.xlsx'):
    wb = workbook.Workbook()
    ws = wb.active
    ws.append(["ItemId", "ItemName", "Question", "Answer", "Reference", "Context"])
    for context in context_list:
        ws.append(context)

    wb.save(savename)


if __name__ == '__main__':
    json_path = '/chatGLM/mycode/mydata/docx_v8'
    xlsx_path = '/chatGLM/mycode/mydata/docx_v9'

    if not os.path.exists(xlsx_path):
        os.mkdir(xlsx_path)

    json_files = glob.glob(os.path.join(json_path, '*.json'))
    json_files = sorted(json_files)
    for file in json_files[100:]:
        file_name = os.path.basename(file)
        file_id = file_name[:-5]
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)[file_id]
        context_list = []
        for d in data:
            context_list.append(list(d.values()))
        xlsx_name = file_name.replace('.json', '.xlsx')
        write_xlsx(context_list, os.path.join(xlsx_path, xlsx_name))
