# -*- coding:utf-8 -*-
# Author:   liyanpeng
# Email:    yanpeng.li@cumt.edu.cn
# Datetime: 2023/6/9 10:42
# Filename: auto_query_gen.py
from configs.model_config import *
from chains.local_doc_qa import LocalDocQA
import os
import nltk
from models.loader.args import parser
import models.shared as shared
from models.loader import LoaderCheckPoint

import json
import glob
from openpyxl.workbook import Workbook


nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

# Show reply with source text from input document
REPLY_WITH_SOURCE = True


def json_format(context):
    try:
        context_json = json.loads(context)
    except:
        context_json = {}
        context_list = context.split('\n')
        count = 0
        for i, context in enumerate(context_list):
            if count == 10:
                break

            if context and context[0].isdigit():
                context_json[i] = context.split('. ')[-1]
                count += 1

    if context_json.get(' questions', ''):
        context_json_tmp = {}
        for i, questions in enumerate(context_json.get(' questions')):
            context_json_tmp[i] = questions['question']
        context_json = context_json_tmp

    return context_json


def write_excel(context_list, savename='question-set.xlsx'):
    wb = Workbook()
    ws = wb.active
    ws.append(['ItemId', 'ItemName', 'Question', 'Answer', 'Reference', 'Context'])
    for context in context_list:
        ws.append(context)

    wb.save(savename)


def main():
    args = None
    args = parser.parse_args()
    args_dict = vars(args)
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)
    llm_model_ins = shared.loaderLLM()
    llm_model_ins.history_len = LLM_HISTORY_LEN

    local_doc_qa = LocalDocQA()
    local_doc_qa.init_cfg(llm_model=llm_model_ins,
                          embedding_model=EMBEDDING_MODEL,
                          embedding_device=EMBEDDING_DEVICE,
                          top_k=VECTOR_SEARCH_TOP_K)
    vs_path = None
    filepath = '/chatGLM/mycode/mydata/docx_v6'
    if not vs_path:
        vs_path, _ = local_doc_qa.init_knowledge_vector_store(filepath)
    # history = []
    # last_print_len = 0

    # for resp, history in local_doc_qa.get_question_based_answer_start(chat_history=history,
    #                                                                   streaming=STREAMING):
    #     if STREAMING:
    #         print(resp["result"][last_print_len:], end="", flush=True)
    #         last_print_len = len(resp["result"])
    #     else:
    #         print(resp["result"])

    save_json_info = '/chatGLM/mycode/mydata/docx_v8'
    if not os.path.exists(save_json_info):
        os.mkdir(save_json_info)

    excel_list = []
    txt_files = glob.glob(os.path.join(filepath, '*.txt'))
    for txt_file in txt_files:
        print(txt_file)
        json_info = {}
        file_id = os.path.basename(txt_file)[:-4]
        json_info[file_id] = []
        """
        00001.txt: [
            {question: xxx, answer: xxx, reference: [], sim_score: [], bleu_score: []},
            ...
        ]
        """
        with open(os.path.join(filepath, txt_file), 'r', encoding='utf-8') as f:
            context_list = f.readlines()
        item_name = context_list[0].split('的')[0]
        # json_info[file_id].append('{}如何办理?'.format(item_name))
        for context in context_list:
            last_print_len = 0
            llm_output = ''
            history = []
            for resp, history in local_doc_qa.get_question_based_answer(context=context,
                                                                        vs_path=vs_path,
                                                                        chat_history=history,
                                                                        streaming=STREAMING):
                if STREAMING:
                    llm_output += resp["result"][last_print_len:]
                    last_print_len = len(resp["result"])
                else:
                    llm_output = resp["result"]

            llm_output = json_format(llm_output)
            history = [[context, context]]  # 可以考虑结合(非结构化与结构化两种)
            last_print_len = 0
            for question in llm_output.values():
                if isinstance(question, dict):  # 00015.txt
                    break
                question = item_name + question if item_name not in question else question

                llm_output_str = ''
                for resp, history in local_doc_qa.get_knowledge_based_answer(query=question,
                                                                            vs_path=vs_path,
                                                                            chat_history=history,
                                                                            streaming=STREAMING):
                    if STREAMING:
                        llm_output_str += resp["result"][last_print_len:]
                        last_print_len = len(resp["result"])
                    else:
                        llm_output_str = resp["result"]


                # sub_json_info = {
                #     'question': question,
                #     'answer': llm_output_str.replace('\n', ''),
                #     'reference': [doc.metadata['source'] for doc in resp['source_documents']],
                #     'sim_score': [doc.metadata['score'] for doc in resp['source_documents']],
                #     'bleu_score': [doc.metadata['bleu_score'] for doc in resp['source_documents']],
                #     'context': [doc.page_content for doc in resp['source_documents']]
                # }

                sub_txt_json = {
                    'ItemId': file_id,
                    'ItemName': item_name,
                    'Question': question,
                    'Answer': llm_output_str.replace('\n', ''),
                    'Reference': file_id + '.txt',
                    'Context': context
                }
                json_info[file_id].append(sub_txt_json)

                # json_info[file_id].append(question)

        llm_output_str = ''
        last_print_len = 0
        question = '{}如何办理?'.format(item_name)
        history = [[context, context]]
        for resp, history in local_doc_qa.get_knowledge_based_answer(query=question,
                                                                    vs_path=vs_path,
                                                                    chat_history=history,
                                                                    streaming=STREAMING):
            if STREAMING:
                llm_output_str += resp["result"][last_print_len:]
                last_print_len = len(resp["result"])
            else:
                llm_output_str = resp["result"]

        sub_txt_json = {
            'ItemId': file_id,
            'ItemName': item_name,
            'Question': question,
            'Answer': llm_output_str.replace('\n', ''),
            'Reference': file_id + '.txt',
            'Context': context
        }
        json_info[file_id].insert(0, sub_txt_json)

        with open(os.path.join(save_json_info, '{}.json'.format(file_id)), 'w', encoding='utf-8') as f:
            json.dump(json_info, f, indent=4, ensure_ascii=False)

        for row_dict in json_info[file_id]:
            excel_list.append(list(row_dict.values()))

    write_excel(excel_list, savename=os.path.join(save_json_info, 'all_questions.xlsx'))

    # with open('/chatGLM/mycode/mydata/question.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_info, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
