# -*- coding:utf-8 -*-
# Author:   liyanpeng
# Email:    liyanpeng@cumt.edu.cn
# Datetime: 2023/6/6 18:41
# Filename: chinese_text_splitter_only_txt.py
from langchain.text_splitter import CharacterTextSplitter
import re
from typing import List
from configs.model_config import SENTENCE_SIZE


__all__ = ['ChineseTextSplitterOnlyTxt']


class ChineseTextSplitterOnlyTxt(CharacterTextSplitter):
    def __init__(self, sentence_size: int = SENTENCE_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.sentence_size = sentence_size

    def split_text(self, text: str) -> List[str]:
        text = text.rstrip()
        split_text = text.split('\n')

        # optional：以句子(。)为单位
        split_text_all = []
        for text in split_text:
            if len(text) > 256:
                tmp_list = [t for t in text.split('。') if t]
                split_text_all.extend(tmp_list)

        # split_text_all = []
        # for text in split_text:
        #     if len(text) > 256:
        #         tmp_list = [t for t in text.split('。') if t]
        #         for tl in tmp_list:
        #             tmp_list_ = [t for t in tl.split('；') if t]
        #             split_text_all.extend(tmp_list_)
        #     else:
        #         split_text_all.append(text)

        return split_text_all
