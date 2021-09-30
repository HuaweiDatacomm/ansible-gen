#!/usr/bin/env python
# -*- coding: utf-8 -*-



import re
import copy
from collections import OrderedDict


class Util(object):
    def __init__(self):
        self.age = -1

    @staticmethod
    def translate_restrict(rests):
        rest_nums = []
        rest_part_pattern = re.compile(r"(\d+\s*\.\.\s*\d+)|(\d+)")
        for src_rest in rests:
            matches = [res_t[0] if res_t[0] else res_t[1] for res_t in rest_part_pattern.findall(src_rest)]
            for res in matches:
                if ".." in res:
                    rng = [int(endpoint.strip()) for endpoint in res.split("..")]
                    rest_nums.append((rng[0], rng[1]))
                else:
                    num = int(res.strip())
                    rest_nums.append((num, num))
        rest_nums.sort(key=lambda item: item[0])

        return rest_nums

    @staticmethod
    def restrict_set_intersec(restricts):
        if not restricts:
            return []

        def get_intersec(t1, t2):
            t1_min = t1[0]
            t1_max = t1[1]
            if(t1_max is None):
                t1_max = t1_min
            t2_min = t2[0]
            t2_max = t2[1]
            if t2_max is None:
                t2_max = t2_min

            if t1_max < t2_min:
                return [[t1_min,t1_max], [t2_min,t2_max]]
            return [(max(t1_min, t2_min), min(t1_max, t2_max))]
        restricts.sort(key=lambda item: item[0])
        result = []
        result.append(restricts[0])
        idx = 1
        while idx < len(restricts):
            _ = get_intersec(result[-1], restricts[idx])
            result = result[:-1] + _
            idx += 1

        return result


def split_to_xpath_and_orderdict(xml_dict):
    tmp_dict = copy.deepcopy(list(xml_dict.values())[0])
    xpath = ""

    return xpath, tmp_dict
