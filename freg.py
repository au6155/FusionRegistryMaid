# test case'ai:
# 1. svarus grazus failiukas be jokiu balaganu
# 2. failiukas su vienu pasikartojanciu codelistu
# 3. failiukas su keliais pasikartojanciais codelistais
# 4. failiukas su vienu pasikartojanciu codelistu ir clashais jame
# 5. failiukas su keliais pasikartojanciais codelistais ir clashais visuose juose

import xml.etree.ElementTree as et
from xml.etree.ElementTree import Element, ElementTree
import time
from bs4 import BeautifulSoup as bs
from colorama import init, Back, Fore
import os

TO_CHOP_OFF = [' ', '\n', '\t', '\r', '\xa0']
TO_DELETE = ['\t', '\r']

def normalize_text(text_to_normalize):
    normalized_text = str(text_to_normalize)
    
    for symbol in TO_DELETE:
        if str(symbol) in normalized_text:
            normalized_text = normalized_text.replace(symbol, '')

    while normalized_text:
        if any(s == normalized_text[0] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[1:]
        elif any(s == normalized_text[-1] for s in TO_CHOP_OFF):
            normalized_text = normalized_text[:-1]
        else:
            break

    return str(normalized_text)

def print_xml(element):
    text = et.tostring(element, encoding = 'unicode')
    text = bs(text, 'lxml')
    text = text.prettify()
    text = text.replace('<html>', '')
    text = text.replace('</html>', '')
    text = text.replace('<body>', '')
    text = text.replace('</body>', '')
    text = normalize_text(text)
    return text

def ets_equal(et1, et2):
    tag1 = et1.tag
    tag2 = et2.tag
    if tag1 != tag2:
        return False

    attrib1 = str(et1.attrib)
    attrib2 = str(et2.attrib)
    attrib1 = remove_version_str(attrib1)
    attrib2 = remove_version_str(attrib2)
    if attrib1 != attrib2:
        return False

    text1 = normalize_text(et1.text)
    text2 = normalize_text(et2.text)
    if text1 != text2:
        return False

    if (list(et1) == []) ^ (list(et2) == []):
        return False

    if (list(et1) != []) and (list(et2) != []):
        if not children_equal(et1, et2):
            return False

    return True

def children_equal(et1, et2):

    children = list(et1) + list(et2)
    total_len = len(children)

    for i, child in enumerate(children):
        for n in range(i+1, len(children)):
            if ets_equal(child, children[n]):
                children[i] = 0

    while 0 in children:
        children.remove(0)
        if 2 * len(children) == total_len:
            return True
            
    return False

def conflict(et1, et2):
    try:
        value1 = et1.attrib['value']
        value2 = et2.attrib['value']
        if value1 == value2:
            return True
    except:
        try:
            if et1.tag == et2.tag == 'str:Name':
                lang1 = et1.attrib['xml:lang']
                lang2 = et2.attrib['xml:lang']
                if lang1 == lang2:
                    return True
        except:
            return False
        return False
    return False

def openxml(filename):

    with open(filename, 'r', encoding = 'utf-8') as f:
        file = f.read()

    register_namespaces(file)

    root = et.parse(filename).getroot()
    return root

def register_namespaces(file):
    start = file.find('Structure') + 10
    end = file[start:].find('>') + start
    structure = file[start:end]
    
    namespaces = {}
    start = structure.find('"') + 1

    while start != 0:
        end = structure[start:].find('"') + start

        namespace_start = structure[:start].rfind(':') + 1
        namespace_end = structure[namespace_start:].find('=') + namespace_start

        namespace = structure[namespace_start:namespace_end]
        uri = structure[start:end]
        namespaces[namespace] = uri
        
        structure = structure[end+1:]        
        start = structure.find('"') + 1

    del namespaces['schemaLocation']
    for ns in namespaces:
        et.register_namespace(ns, namespaces[ns])

def sortCode(et):
    try:
        urn = et.attrib['urn']
        key = urn.split('.')
        key = str((et.tag)) + key[-1]
        return key
    except:
        return '_'

def remove_version_str(urn):
    try:
        start = urn.rfind('(')
        end = urn.rfind(')') + 1

        _ = float(urn[start + 1:end - 1])

        if start == -1 or end == -1:
            return urn
        else:
            return urn[:start] + '(1.0)' + urn[end:]
    except Exception:
        return urn

def remove_version_et(obj):
    try:
        urn = remove_version_str(obj.attrib['urn'])
        new_obj = obj
        new_obj.attrib['urn'] = urn
        return new_obj
    except:
        return obj

def add_version(et):
    try:
        length = len(et.attrib['value']) + 1
        new_et = et
        urn = new_et.attrib['urn']
        urn = urn[:length] + '(1.0)' + urn[length:]
        new_et.attrib['urn'] = urn
        return new_et
    except:
        return et

def print_comparison(str1, str2):
    code1 = str1.split('\n')
    code2 = str2.split('\n')
    one_hot = [0] * (len(code1) + len(code2))
    offset = len(code1)

    for i, line in enumerate(code1):
        if len(code1) >= i:
            if remove_version_str(line) not in [remove_version_str(a) for a in code2]:
                one_hot[i] = 1

    for i, line in enumerate(code2):
        if len(code2) >= i:
            if remove_version_str(line) not in [remove_version_str(a) for a in code1]:
                one_hot[i + offset] = 1

    print('A:\n')
    for i, line in enumerate(code1):
        if one_hot[i] == 1:
            print(Back.RED + line + Back.BLACK)
        else:
            print(line)

    print('B:\n')
    for i, line in enumerate(code2):
        if one_hot[i + offset] == 1:
            print(Back.RED + line + Back.BLACK)
        else:
            print(line)


def parse_xml_codelist(codelists, id):
    descriptions = []
    urns = []
    
    for codelist in codelists:   # codelist === vienos codelist versijos kodai (įrašai) -> "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=LB:KS_APREPTIS_UVR(1.0).E"
        try:
            urns.append(codelist)
        except Exception as e:
            print('freg.py exception 1: ', e)
            pass

    urns.insert(0, descriptions) # kiekvienas description masyvas yra urns masyvo dalis (masyvų masyvas) ir yra vienos versijos codelistas

    descriptions = []

    for codelist in urns: # skirtingos versijos su tuo pačiu id
        for code in codelist: # eina per visus vienos versijos įrašus
            flag = 0
            for element in descriptions: # tikrina, ar jau nėra tokio paties įrašo
                if ets_equal(element, code):
                    flag = 1

                elif conflict(element, code):
                    # leisti pasirinkti, kurio reikia
                    text1 = print_xml(code) # code -> dar ne descriptions masyve
                    text2 = print_xml(element) # element -> jau descriptions masyve

                    print('\n')
                    print_comparison(text1, text2)
                    answer = input('\nKuris įrašas lieka: ')
                    while not any(s == answer.lower() for s in ['a', 'b']):
                        answer = input('Bandykite dar kartą: ')

                    if answer.lower() == 'a':
                        descriptions.remove(element)
                    elif answer.lower() == 'b':
                        flag = 1
            if flag == 0:
                descriptions.append(code) # tvarkingai surūšiuotas masyvas nuo didžiausios versijos iki mažiausios
    descriptions.sort(key = sortCode)
    # gal tiesiog geriau grąžinti vieną jau paruoštą codelistą ir jį appendinti prie codelists childo (ir removint visus kitus pradinius codelistus su tuo id)????
    return descriptions


def main():
    init()
    rt = openxml('small_codelist.xml')
    _, codelists = list(rt)
    
    versions = {}

    for codelist in codelists:

        id = codelist.attrib['id']
        if id in versions:
            versions[id].append(codelist)
        else:
            versions[id] = [codelist]

    parsed_codelists = []
    for id in versions:
        new_codelist = parse_xml_codelist(versions[id], id)
        for version in versions[id][1:]:
            codelists.remove(version)
        
        versions[id][0].attrib['version'] = '1.0'
        versions[id][0].attrib['urn'] = remove_version_str(versions[id][0].attrib['urn']) # nustato versiją į 1.0
        versions[id][0].attrib['isFinal'] = 'true'
        
        for code in reversed(versions[id][0]):
            versions[id][0].remove(code)

        for code in new_codelist:
            versions[id][0].append(remove_version_et(code))
        parsed_codelists.append(new_codelist)

    final_string = et.tostring(rt)
    with open('new_small_codelist.xml', 'wb') as f:
        f.write(final_string)

    print(Back.GREEN + 'Failas išsaugotas sėkmingai' + Back.BLACK)

main()
