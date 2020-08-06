
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 14:45:41 2019

@author: julia.gray
"""
import nltk
import re
import requests
import datetime
from flashtext import KeywordProcessor
import logging
from unidecode import unidecode

###############################################################################
"""Be sure to add log file path or remove log + try statements prior to running"""
logging.basicConfig(filename = 'added_tagged_entities_error_log.log')
###############################################################################

def line_break_cleaning(s):
    try:
        s=s.replace('\r\n',' ')
    #    s=re.sub('\n+',' ',s)
        s=s.replace('\n',' ')
        s=s.replace('\t',' ')
        s=re.sub(' +',' ',s) #remove consecutive spaces
        s=s.replace('’', "'")
        s = s.encode('ascii','ignore').decode('utf-8')
        #s = s.encode('utf-8','ignore').encode('utf-8')
        
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.line_break_cleaning %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        #print(unidecode(unicode(s, encoding = "utf-8")))
    return s

def text_to_sentences(text_content):
    try:
        sentence_ls_raw = nltk.sent_tokenize(text_content)
        sentence_ls = []
        for sentence in sentence_ls_raw:
            sentence_ls.append(line_break_cleaning(sentence))
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.text_to_sentenceslog %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
    
    return sentence_ls

def solr_clean_special_char(string_to_mask, solr_specialchars='\+-&|!(){}[]^"~*?:/'):
    masked = string_to_mask
    # mask every special char with leading \
    for char in solr_specialchars:
        if char == ':':  # need an exception when the next char is a letter and not a digit
            colon_start = masked.find(':', 0, len(masked))
            if colon_start < len(masked)-1: #"skin lump:" ending with ":" fails otherwise
                try:
                    int(masked[colon_start+1])  # if it doesn't fail, it's a number
                    masked = masked.replace(char, " ")
                except Exception:  # if it fails, it's not a number so keep the ':'
                    if masked[colon_start+1] == ' ':
                        masked = masked.replace(char, " ")
        else:
            masked = masked.replace(char, " ")
    masked = masked.strip()  # remove trailing spaces
    masked = re.sub(' +', ' ', masked)  # remove consecutive spaces
    return masked

def solr_clean_special_char_subscriptions(string_to_mask, solr_specialchars='\+-&|!(){}[]^"~*?/'):
    masked = string_to_mask
    # mask every special char with leading \
    for char in solr_specialchars:
        if char == ':':  # need an exception when the next char is a letter and not a digit
            colon_start = masked.find(':', 0, len(masked))
            if colon_start < len(masked)-1: #"skin lump:" ending with ":" fails otherwise
                try:
                    int(masked[colon_start+1])  # if it doesn't fail, it's a number
                    masked = masked.replace(char, " ")
                except Exception:  # if it fails, it's not a number so keep the ':'
                    if masked[colon_start+1] == ' ':
                        masked = masked.replace(char, " ")
        else:
            masked = masked.replace(char, " ")
    masked = masked.strip()  # remove trailing spaces
    masked = re.sub(' +', ' ', masked)  # remove consecutive spaces
    return masked

def get_keyword_sentences(document_text, keyword):
    try:
        """Return only sentences with keyword"""
        
        
        keyword_processor = KeywordProcessor()
        #keyword_fr_process = re.sub('[-/]', ' ', keyword) ## remove keyword special characters using regex
        keyword_fr_process = solr_clean_special_char(keyword)
        keyword_processor.add_keyword(keyword_fr_process.lower())
        #document_text_copy = re.sub('[-/]', ' ', document_text) ## remove keyword special characters using regex
        document_text_copy = solr_clean_special_char(document_text)
        #print(document_text_copy,'--- cleaned documents')
        keywords_found = keyword_processor.extract_keywords(document_text_copy.lower(), span_info=True) # for counting keywords w/o special characters
        
        #print(keyword, '--- this is the keyword')
        
        # if keyword == 'Gonadotropin-releasing hormone':# or keyword == 'size exclusion':
        #     #print(keyword,'---- the keywords found')
        #     print(keyword_processor,'---- full processor')

        #     print(keywords_found, '---- the keywords found')
        #     #print(document_text_copy,'--- cleaned documents')
        #     #print(keyword_processor,'---- full processor')

        shorter_sentence = ""
    
        sentence_ls = text_to_sentences(document_text_copy)
        last_sentence_index = 0    
        
        for i in range(0, len(sentence_ls)):
            #keyword = re.sub('[^a-zA-Z0-9 \n\.]', '', keyword)
            #print('this is the keyword --->' + str(keyword))
            #sentence_ls[i] = re.sub('[-/]', ' ', sentence_ls[i])
            #print('this is the sentence --->' + str(sentence_ls[i]))
            if keyword_fr_process.lower() in sentence_ls[i].lower(): #<----- replace/remove all special characters
                if i == 0:
                    shorter_sentence += sentence_ls[i]
                elif (i == last_sentence_index + 1) and (len(shorter_sentence) < 500):
                    shorter_sentence += ' ' + sentence_ls[i]
                elif len(shorter_sentence) < 500:
                    shorter_sentence += ' ... ' + sentence_ls[i]
                else:
                    #shorter_sentence += ' ... ' + sentence_ls[i]
                    pass
                last_sentence_index = i  
                
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.log %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return keywords_found, shorter_sentence

def subscription_scrape_section_designation(sentence):
    scraped_section_headers = ['link:','text:','content:','type:','compnay:'
                                'date:','headline:','source:', 'Link:',
                                'Text:','Content:','Type:','Date:','Headline:','Source:','Company:']
    for section in scraped_section_headers:
        #print(section, '--- this is the section being replaced')
        #print(sentence, '--- this is the sentence being replaced')
        sentence = sentence.replace(section, ' || ' + str(section))
        #print(sentence, '---this is the cleaned sentence')
    return sentence

def get_keyword_sentences_subscriptions(document_text, keyword):

    try:
        """Return only sentences with keyword"""
        
        
        keyword_processor = KeywordProcessor()
        #keyword_fr_process = re.sub('[-/]', ' ', keyword) ## remove keyword special characters using regex
        keyword_fr_process = solr_clean_special_char_subscriptions(keyword)
        keyword_processor.add_keyword(keyword_fr_process.lower())
        #document_text_copy = re.sub('[-/]', ' ', document_text) ## remove keyword special characters using regex
        document_text_copy = solr_clean_special_char_subscriptions(document_text)
        #print(document_text_copy,'--- cleaned documents')
        keywords_found = keyword_processor.extract_keywords(document_text_copy.lower(), span_info=True) # for counting keywords w/o special characters
        
        #print(keyword, '--- this is the keyword')
        
        # if keyword == 'Gonadotropin-releasing hormone':# or keyword == 'size exclusion':
        #     #print(keyword,'---- the keywords found')
        #     print(keyword_processor,'---- full processor')

        #     print(keywords_found, '---- the keywords found')
        #     #print(document_text_copy,'--- cleaned documents')
        #     #print(keyword_processor,'---- full processor')

        shorter_sentence = ""
    
        sentence_ls = text_to_sentences(document_text_copy)
        last_sentence_index = 0    
        
        for i in range(0, len(sentence_ls)):
            #keyword = re.sub('[^a-zA-Z0-9 \n\.]', '', keyword)
            #print('this is the keyword --->' + str(keyword))
            #sentence_ls[i] = re.sub('[-/]', ' ', sentence_ls[i])
            #print('this is the sentence --->' + str(sentence_ls[i]))
            if keyword_fr_process.lower() in sentence_ls[i].lower(): #<----- replace/remove all special characters
                if i == 0:
                    shorter_sentence += subscription_scrape_section_designation(sentence_ls[i])
                elif (i == last_sentence_index + 1) and (len(shorter_sentence) < 500):
                    shorter_sentence += ' ' + subscription_scrape_section_designation(sentence_ls[i])
                elif len(shorter_sentence) < 500:
                    shorter_sentence += ' ... ' + subscription_scrape_section_designation(sentence_ls[i])
                else:
                    #shorter_sentence += ' ... ' + sentence_ls[i]
                    pass
                last_sentence_index = i  
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.log %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return keywords_found, shorter_sentence

def dictionary_matcher(text, limit=10000, tagger='all_labels_ss_tag', solr='http://10.115.1.195:8983/solr/', core='opensemanticsearch', core_entities='opensemanticsearch-entities'):
    
    """SOLR tagger = pass any string of text and returns tags from all dictionaries"""
    #print('dictionary_matcher on %s characters'%(str(len(text))))
    
    url = solr + core_entities + '/' + tagger
    
    relevant_dictionaries = ['company_OME_txt_ss', 'drug_OME_txt_ss', 'target_ChemBL_txt_ss', 'target_OME_txt_ss', 'target_MeSH_txt_ss', 'indication_OME2_txt_ss', 'indication_MeSH_orpha_txt_ss', 'indication_MeSH_suppl_txt_ss']

    fields = [  'id',
                'type_ss',
                'preferred_label_s',
                'skos_prefLabel_ss',
                'label_ss',
                'skos_altLabel_ss',
                'all_labels_ss',
    ]


    params = {    'wt': 'json',
                'matchText': 'true',
                'overlaps': 'NO_SUB',
                # 'overlaps': 'ALL',
                'fl': ','.join(fields),
    }

    if limit:
        params['tagsLimit'] = str(limit)

    r = requests.post(url, data=text.encode('utf-8'), params=params)

#    print ("Entity linking / Solr Text Tagger result for tagger {}: {}".format(tagger, r.text))
    
    matches = r.json()
    

    normalized_entities = {}
    for entity in matches['response']['docs']:
        #for debugging
#        if entity['id'] == 'Amlodipine valsartan (MeSH)':
#            break

        label = None

        if 'preferred_label_s' in entity:
            label = entity['preferred_label_s']


        if not label:
            if 'skos_prefLabel_ss' in entity:
                label = entity['skos_prefLabel_ss'][0]

        if not label:
            if 'label_ss' in entity:
                label = entity['label_ss'][0]

        if not label:
            if 'skos_altLabel_ss' in entity:
                label = entity['skos_altLabel_ss'][0]

        if not label:
            label = entity['id']

        types = []
        if 'type_ss' in entity:
            types = entity['type_ss']
                        
        result = {
            'id': entity['id'],
#            'name': label,
            'all_labels_ss': entity['all_labels_ss'],
#            'match': True,
            'type': types,
            'matchtext': [],
            'matchtext_count':{},
            'valid_match': [],
            'charOffset': [],
            'tag_count': 0,
            'tag_count_cleaned': 0,
        }

        if types[0] in relevant_dictionaries:
            normalized_entities[entity['id']] = {}
            #        normalized_entities[entity['id']]['result'] = [result]
            normalized_entities[entity['id']]['result'] = result       
        
    relevant_tags = []
    
    # add label matches in text
    for tag in matches['tags']:
        
        matchtext = ''
        entity_ids = []

        is_variablename = True
        variablename = ""
        tag_type = ""
        
        add_to_relevant_tags = False
        
        for entry in tag:
            if is_variablename:
                variablename = entry
            elif variablename == 'matchText':
                matchtext = entry
            elif variablename == 'ids':
                entity_ids = entry
                tag_type = []
                for i in range(0, len(entry)):
                    if entry[i] in normalized_entities:
                        i_tag_type = normalized_entities[entry[i]]['result']['type']
                        add_to_relevant_tags = True
                        tag_type.append(i_tag_type)
                #tag_type = normalized_entities[entry[0]]['result']['type']
            elif variablename == 'startOffset':
                startOffset = entry    
            elif variablename == 'endOffset':
                endOffset = entry 
            
                    
            if is_variablename == True:
                is_variablename = False
            else:
                is_variablename = True
        tag.append(tag_type)
        #for debugging
#        if "Amlodipine valsartan (MeSH)" in entity_ids:
#            break
        
        if add_to_relevant_tags:
            relevant_tags.append(tag)

        for entity_id in entity_ids: 
#            if matchtext and not matchtext in normalized_entities[entity_id]['result'][0]['matchtext']:
            if matchtext and (entity_id in normalized_entities):
#                normalized_entities[entity_id]['result'][0]['matchtext'].append(matchtext)
#                normalized_entities[entity_id]['result'][0]['charOffset'].append([startOffset, endOffset])
#                normalized_entities[entity_id]['result'][0]['tag_count'] += 1
                match_not_all_cap = check_tag_match(matchtext, normalized_entities[entity_id]['result']['type'][0])
                #match_not_all_cap = match_check_all_cap(normalized_entities, entity_id, matchtext)
                if match_not_all_cap:
                    normalized_entities[entity_id]['result']['tag_count_cleaned'] += 1
                normalized_entities[entity_id]['result']['valid_match'].append(match_not_all_cap)
                normalized_entities[entity_id]['result']['matchtext'].append(matchtext)
                normalized_entities[entity_id]['result']['charOffset'].append([startOffset, endOffset])
                normalized_entities[entity_id]['result']['tag_count'] += 1
                if matchtext not in normalized_entities[entity_id]['result']['matchtext_count']:
                    normalized_entities[entity_id]['result']['matchtext_count'][matchtext] = 1
                else:
                    normalized_entities[entity_id]['result']['matchtext_count'][matchtext] += 1
                    

    return normalized_entities, relevant_tags


def parse_tag_lists(drug_tags, target_tags, company_tags, indication_tags):
    
    try:
        normalized_tags = {}
        
        for d in drug_tags:
            tag = d.split("\t")[0].encode('ascii','ignore').decode('utf-8')
            matchtext = d.split("\t")[1]
            if tag not in normalized_tags:
                normalized_tags[tag] = {'type':['drug_OME_txt_ss'], 'matchtext':[matchtext]}
            else:
                normalized_tags[tag]['matchtext'].append(matchtext)
        for t in target_tags:
            tag = t.split("\t")[0].encode('ascii','ignore').decode('utf-8')
            matchtext = t.split("\t")[1]
            if tag not in normalized_tags:
                normalized_tags[tag] = {'type':['target_OME_txt_ss'], 'matchtext':[matchtext]}
            else:
                normalized_tags[tag]['matchtext'].append(matchtext)
        for c in company_tags:
            tag = c.split("\t")[0].encode('ascii','ignore').decode('utf-8')
            matchtext = c.split("\t")[1]
            if tag not in normalized_tags:
                normalized_tags[tag] = {'type':['company_OME_txt_ss'], 'matchtext':[matchtext]}
            else:
                normalized_tags[tag]['matchtext'].append(matchtext)
        for i in indication_tags:
            tag = i.split("\t")[0].encode('ascii','ignore').decode('utf-8')
            matchtext = i.split("\t")[1]
            if tag not in normalized_tags:
                normalized_tags[tag] = {'type':['indication_OME2_txt_ss'], 'matchtext':[matchtext]}
            else:
                normalized_tags[tag]['matchtext'].append(matchtext)
                
        normalized_tags_ordered = sorted(normalized_tags, key=lambda k: len(normalized_tags[k]['matchtext']), reverse=True)
        
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.parse_tag_lists.log %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
    
    return normalized_tags, normalized_tags_ordered

def get_overall_tag_type(tag_type_list):
    try:
        for tag_type in tag_type_list:
            if 'indication' in tag_type:
                overall_type = 'indication'
            elif 'target' in tag_type:
                overall_type = 'target'
            elif 'company' in tag_type:
                overall_type = 'company'
            elif 'drug' in tag_type:
                overall_type = 'drug'
            else:
                overall_type = 'unknown'
                
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.get_overall_tag_type.log %s', (e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return overall_type



def highlight_keyword(text, keyword, color="#FFFF00", check_all_cases='yes'):
    try:
        #remove special characters from keyword and text in order to compare and highlight
        #keyword = re.sub('[-/]', ' ', keyword)
        keyword = solr_clean_special_char(keyword)
        #text = re.sub('[-/]', ' ', text)
        text = solr_clean_special_char(text)
    
        if check_all_cases == 'no':
            (keyword in text) and (text[text.index(keyword) - 1] != '>')
            #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
            text = text.replace(keyword, '<span style="background-color: %s">{}</span>'.format(keyword)%(color))
            #(print(text + '<---- this is the text in highlight_keyword_func'))
    
        if check_all_cases == 'yes':
            if (keyword.lower() in text.lower()) and (text.lower()[text.lower().index(keyword.lower()) - 1] != '>'):
                #print(keyword + '<---- this is the keyword in highlight_keyword_func')
                text = text.lower().replace(keyword.lower(), '<span style="background-color: %s">{}</span>'.format(keyword.lower())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
            if (keyword.upper() in text.upper()) and (text.upper()[text.upper().index(keyword.upper()) - 1] != '>'):
                #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
                text = text.upper().replace(keyword.upper(), '<span style="background-color: %s">{}</span>'.format(keyword.upper())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
            if (keyword.title() in text) and (text[text.index(keyword.title()) - 1] != '>'):
                #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
                text = text.replace(keyword.title(), '<span style="background-color: %s">{}</span>'.format(keyword.title())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_keyword.log %s'%(e, str(datetime.datetime.now())) 
        logging.error(error_string)

    return text

def highlight_keyword_subscriptions(text, keyword, color="#FFFF00", check_all_cases='yes'):
    try:
        #remove special characters from keyword and text in order to compare and highlight
        #keyword = re.sub('[-/]', ' ', keyword)
        keyword = solr_clean_special_char_subscriptions(keyword)
        #text = re.sub('[-/]', ' ', text)
        text = solr_clean_special_char_subscriptions(text)
    
        if check_all_cases == 'no':
            (keyword in text) and (text[text.index(keyword) - 1] != '>')
            #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
            text = text.replace(keyword, '<span style="background-color: %s">{}</span>'.format(keyword)%(color))
            #(print(text + '<---- this is the text in highlight_keyword_func'))
    
        if check_all_cases == 'yes':
            if (keyword.lower() in text.lower()) and (text.lower()[text.lower().index(keyword.lower()) - 1] != '>'):
                #print(keyword + '<---- this is the keyword in highlight_keyword_func')
                text = text.lower().replace(keyword.lower(), '<span style="background-color: %s">{}</span>'.format(keyword.lower())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
            if (keyword.upper() in text.upper()) and (text.upper()[text.upper().index(keyword.upper()) - 1] != '>'):
                #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
                text = text.upper().replace(keyword.upper(), '<span style="background-color: %s">{}</span>'.format(keyword.upper())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
            if (keyword.title() in text) and (text[text.index(keyword.title()) - 1] != '>'):
                #(print(keyword + '<---- this is the keyword in highlight_keyword_func'))
                text = text.replace(keyword.title(), '<span style="background-color: %s">{}</span>'.format(keyword.title())%(color))
                #(print(text + '<---- this is the text in highlight_keyword_func'))
        text = subscription_scrape_section_designation(text)

        #For those shorter sentences returned, split and only take list entries with desired headers:
        desired_headers = ['text:','content:','type:',
                            'date:','headline:','source:','Company:','company:'
                            'Text:','Content:','Type:','Date:','Headline:','Source:']
        
        #Split and check if relevant section header is in split lsit item,
        #  if it is append to new string and  use that as text
        text_ls = text.split(' || ')
        #print(text_ls, '--- splitting text_ls')
        curated_text = []
        for pos, t in enumerate(text_ls):
            #print(t,'--- this is the t to add')
            if any(dx in t for dx in desired_headers):
                #print(t,'--- this is the t to add')
                curated_text.append(t) #.replace(' || ',' ')

        #print(curated_text, '--- this is the curated text')
        text = ' '.join(curated_text) 

    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_keyword.log %s'%(e, str(datetime.datetime.now())) 
        logging.error(error_string)

    return text

def highlight_keyword_tag(text, keyword, color="255, 255, 0", border_color="255, 255, 0", check_all_cases='yes'):
    try:
        style_string = '"background-color: rgb(' + color + '); padding: 0px 0.35em; margin: 0px 0.25em; line-height: 1; border-radius: 0.25em; border: 1px solid; border-color: rgb(' + border_color + ');"'
        
        if (keyword in text) and (text[text.index(keyword) - 1] != '>'):
            text = text.replace(keyword, '<span style=%s>{}</span>'.format(keyword)%(style_string))
        
        if check_all_cases == 'yes':
            if (keyword.lower() in text.lower()) and (text[text.index(keyword.lower()) - 1] != '>'):
                text = text.replace(keyword.lower(), "<span style='%s'>{}</span>".format(keyword.lower())%(style_string))
            if (keyword.upper() in text) and (text[text.index(keyword.upper()) - 1] != '>'):
                text = text.replace(keyword.upper(), "<span style='%s'>{}</span>".format(keyword.upper())%(style_string))
            if (keyword.title() in text) and (text[text.index(keyword.title()) - 1] != '>'):
                text = text.replace(keyword.title(), "<span style='%s'>{}</span>".format(keyword.title())%(style_string))
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_keyword_log.log %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return text

def highlight_keyword_for_web(text, keyword, tag_class, check_all_cases='yes'):
    try:
    
        if (keyword in text) and (text[text.index(keyword) - 1] != '>'):
            text = text.replace(keyword, "<span class='tag_span %s'>{}</span>".format(keyword)%(tag_class))
        
        if check_all_cases == 'yes':
            if (keyword.lower() in text) and (text[text.index(keyword.lower()) - 1] != '>'):
                text = text.replace(keyword.lower(), "<span class='tag_span %s'>{}</span>".format(keyword.lower())%(tag_class))
            if (keyword.upper() in text) and (text[text.index(keyword.upper()) - 1] != '>'):
                text = text.replace(keyword.upper(), "<span class='tag_span %s'>{}</span>".format(keyword.upper())%(tag_class))
            if (keyword.title() in text) and (text[text.index(keyword.title()) - 1] != '>'):
                text = text.replace(keyword.title(), "<span class='tag_span %s'>{}</span>".format(keyword.title())%(tag_class))
        
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_keyword_for_web.log %s', (e, str(datetime.datetime.now()))
        logging.error(error_string)
    return text  

def highlight_keyword_list(text, keyword_list):
    try:
    
    #keyword_set = list(set(keyword_list))
    
        for i in keyword_list:
            text = highlight_keyword(text, i)
    except Exception as e:
        logging.error('%s | error in add_tagged_entities_error_log.highlight_keyword_list.log %s', (datetime.datetime.now(), e))
        
    return text    

def highlight_tags(text, tags, for_web=True):
    try:
        t0 = datetime.datetime.now()
        #color_dictionary = {'drug':'#00FF00', 'indication':'#00FFFF', 'target':'#FF4500', 'company':'#FF69B4'}
        color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                                 'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
        
        border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                                 'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
        
        
        print('tagging %s entities'%(str(len(tags))))
        
        already_tagged = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        
        for i in tags:
            #print(i)
            if i[5] in already_tagged:
                pass
            elif check_tag_match(i[5], i[8]) == False:
                pass
            else:
                #print(i[5])
                if for_web == True:
                    try:
                        text = highlight_keyword_for_web(text, i[5], i[8][0][0], check_all_cases='no')
                    except:
                        print('HIGHLIGHTING EXCEPTION')
                        print(i)
                else:
                    try:
                        text = highlight_keyword_tag(text, i[5], color_dictionary[i[8][0][0]], border_color_dictionary[i[8][0][0]], check_all_cases='no')
                    except:
                        print('HIGHLIGHTING EXCEPTION')
                        print(i)
    
                already_tagged.append(i[5])
                
        tf = datetime.datetime.now()
        print('tagging execution time: %s\n'%(str(tf-t0)))
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_tags.log %s' %(e, str(datetime.datetime.now()))
        logging.error(error_string)
    
    return text

def highlight_tags_from_list(text, tags, for_web=True):
    try:
        t0 = datetime.datetime.now()
        #color_dictionary = {'drug':'#00FF00', 'indication':'#00FFFF', 'target':'#FF4500', 'company':'#FF69B4'}
        color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                                 'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
        
        border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                                 'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
        
        
        print('tagging %s entities'%(str(len(tags))))
        #print(tags)
        already_tagged = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        
        for i in tags:
            #print(i)
            for j in tags[i]['matchtext']:
                if j in already_tagged:
                    pass
                else:
                #print(i[5])
                #try:
            
                    text = highlight_keyword_for_web(text, j, tags[i]['type'][0], check_all_cases='no')
                #except:
                    #    print('HIGHLIGHTING EXCEPTION')
                    #    print(i)
                
    
                already_tagged.append(j)
                
        tf = datetime.datetime.now()
        print('tagging execution time: %s\n'%(str(tf-t0)))
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.highlight_tags_from_list.log %s', (e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return text
    
def check_tag_match(tag, tag_type):
    try:
        tag_match = False
        
        trash_aliases = ['3% -4 .1', '14 .1', '2 .1', '2% 1', 'T', 'R', 'BL', 'multi', 'plan', 'ED', 'full', 'mark', 'DM', 'impact', 'Impact', 'name', 'large', 'sync', 'apps', 'rest', 'DC', 'BD', 'was', 'an', 'An']
        if tag in trash_aliases:
            tag_match = False
        elif len(tag) > 3:
            tag_match = True
        else:
            if ('target' in tag_type) or ('indication' in tag_type):
                if tag.isupper() == True:
                    tag_match = True
    
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.check_tag_match.log %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
    
    return tag_match


def get_new_indication_moa_pairs(document_text, normalized_tags, dict_MoA_indications_DB):
    try:
        moa_indication_pairs = []
        new_moa_indication_pairs = []
        new_moas = []
        
        sentence_ls = text_to_sentences(document_text)
        
        keyword_processor = KeywordProcessor()
        already_processed = []
        
        #print('SETTING UP KEYWORD PROCESSOR')
        for tag in normalized_tags:
            if ((normalized_tags[tag]['result']['type'] == ['target_OME_txt_ss']) or (normalized_tags[tag]['result']['type'] == ['indication_OME_txt_ss'])) and (True in normalized_tags[tag]['result']['valid_match']):
                for i in range(0, len(normalized_tags[tag]['result']['matchtext'])):
                    if (normalized_tags[tag]['result']['valid_match'][i] == True) and (normalized_tags[tag]['result']['matchtext'][i] not in already_processed):
                        #print(normalized_tags[tag]['result']['matchtext'][i])
                        #print(tag)
                        keyword_processor.add_keyword(normalized_tags[tag]['result']['matchtext'][i], tag)
                        already_processed.append(normalized_tags[tag]['result']['matchtext'][i])
        
        #print('PARSING SENTENCES')    
        for s in sentence_ls:
            keywords_found = keyword_processor.extract_keywords(s)
            #print(keywords_found)
            moas = []
            indications = []
            
            for k in keywords_found:
                if 'target' in normalized_tags[k]['result']['type'][0]:
                    if k not in moas:
                        moas.append(k)
                elif 'indication' in normalized_tags[k]['result']['type'][0]:
                    if k not in indications:
                        indications.append(k)
            if (len(moas) > 0) and (len(indications)> 0):
                moa_indication_pairs.append([moas, indications])
        
        #print(moa_indication_pairs)
        for pair_index in range(0, len(moa_indication_pairs)):
            for m in moa_indication_pairs[pair_index][0]:
                if m not in dict_MoA_indications_DB:
                    #print('NEW MECHANISM OF ACTION')
                    if [m, moa_indication_pairs[pair_index][1]] not in new_moas:
                        new_moas.append([m, moa_indication_pairs[pair_index][1]])
                    #new_moa_indication_pairs.append([m, moa_indication_pairs[pair_index][1]])
                    #if m not in new_moas:
                    #    new_moas.append([m,)
                else:
                    for i in moa_indication_pairs[pair_index][1]:
                        if i not in dict_MoA_indications_DB[m]:
                            if [m, i] not in new_moa_indication_pairs:
                                new_moa_indication_pairs.append([m, i])
    except Exception as e:
        error_string = '%s | error in add_tagged_entities_error_log.get_new_indication_moa_pairs.log %s' %(str(e), datetime.datetime.now())
        logging.error(error_string)
                    
            
            
    return new_moa_indication_pairs, new_moas



#test_text = "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nReviewing Kodiak Sciences Inc. (KOD)'s and Neurocrine Biosciences Inc. (NASDAQ:NBIX)'s results | YomiBlog\n\n\n\n\t\n\n \t\t\n\n\t\t\t\n\n \t\t\t\t\n \n\t\n\n\n\n\n\n \t\t\t\t\n\n\t\t\t\t\t\n\t\t\t\t\n \n  \t\t\t\t\n\n\n\t\t\t\t\n\t\t\t\t\t\n\t\t\t\t\t\n\t\t\t\t\t\tYomiBlog\t\t\t\t\t\n\n\n\n\t\t\t\t\t\n\t\t\t\t\t\t\t\t\t\n\n\n\n\t\t\t\t\n\n\t\t\t\t\n\n\t\t\t\t\t\tHeadlines\n\tBusiness\n\tEconomy\n\tFinance\n\tAbout US\n\tOur Team\n\tContact\n\n\n\t\t\t\t\n \n\n\t\t\t\n \n\t\t\t\n\n\n \t\t\t\n\n\n\t\t\t\t\n \t\t\n\n\t\t\t\t\t\t\n\t\t\tReviewing Kodiak Sciences Inc. (KOD)’s and Neurocrine Biosciences Inc. (NASDAQ:NBIX)’s results\n\n\n\t\t\t\n\n\t\t\t\tPosted by Joseph Shaffer\n\t\t\t\ton March 2, 2019 at 1:18 pm\n\t\t\t\t\t\t\t\n\t\t\t\n\t\t\t\n\t\t\t\n\n\t\t\t\n\n\n\n\n\n\n\nKodiak Sciences Inc. (NASDAQ:KOD) and Neurocrine Biosciences Inc. (NASDAQ:NBIX) compete against each other in the Biotechnology sector.  We will contrast them and contrast their risk, analyst recommendations, profitability, dividends, institutional ownership, earnings and valuation. \n\nEarnings & Valuation\n\n\t\tGross Revenue\tPrice/Sales Ratio\tNet Income\tEarnings Per Share\tPrice/Earnings Ratio\n\tKodiak Sciences Inc.\tN/A\t0.00\t38.35M\t-1.07\t0.00\n\tNeurocrine Biosciences Inc.\t451.24M\t15.93\t21.11M\t0.07\t1243.62\n\n\n We can see in table 1 the earnings per share, gross revenue and valuation of Kodiak Sciences Inc. and Neurocrine Biosciences Inc.    \n\nProfitability\n\n Table 2 demonstrates the return on assets, net margins and return on equity of Kodiak Sciences Inc. and Neurocrine Biosciences Inc. \n\n\t\tNet Margins\tReturn on Equity\tReturn on Assets\n\tKodiak Sciences Inc.\t0.00%\t0%\t0%\n\tNeurocrine Biosciences Inc.\t4.68%\t2.5%\t1.2%\n\n\nLiquidity\n\n 2.3 and 2.3 are the respective Current Ratio and a Quick Ratio of Kodiak Sciences Inc. Its rival Neurocrine Biosciences Inc.’s Current and Quick Ratios are 1.6 and 1.6 respectively. Kodiak Sciences Inc. has a better chance of clearing its pay short and long-term debts than Neurocrine Biosciences Inc.     \n\nAnalyst Ratings\n\n The Recommendations and Ratings for Kodiak Sciences Inc. and Neurocrine Biosciences Inc. are featured in the next table. \n\n\t\tSell Ratings\tHold Ratings\tBuy Ratings\tRating Score\n\tKodiak Sciences Inc.\t0\t0\t1\t3.00\n\tNeurocrine Biosciences Inc.\t0\t3\t4\t2.57\n\n\n Kodiak Sciences Inc.’s average target price is $22.5, while its potential upside is 218.25%. Competitively the average target price of Neurocrine Biosciences Inc. is $116.83, which is potential 47.64% upside. Based on the data delivered earlier, Kodiak Sciences Inc. is looking more favorable than Neurocrine Biosciences Inc., analysts belief. \n\nInsider and Institutional Ownership\n\n The shares of both Kodiak Sciences Inc. and Neurocrine Biosciences Inc. are owned by institutional investors at 13.6% and 0% respectively. About 11.6% of Kodiak Sciences Inc.’s share are held by insiders. Competitively, Neurocrine Biosciences Inc. has 1.2% of it’s share held by insiders. \n\nPerformance\n\n Here are the Weekly, Monthly, Quarterly, Half Yearly, Yearly and YTD Performance of both pretenders. \n\n\t\tPerformance (W)\tPerformance (M)\tPerformance (Q)\tPerformance (HY)\tPerformance (Y)\tPerformance (YTD)\n\tKodiak Sciences Inc.\t-8.65%\t-4.2%\t0%\t0%\t0%\t-16.83%\n\tNeurocrine Biosciences Inc.\t-2.79%\t-20.91%\t-27.61%\t-13.46%\t18.36%\t10.59%\n\n\n  For the past year Kodiak Sciences Inc. has -16.83% weaker performance while Neurocrine Biosciences Inc. has 10.59% stronger performance. \n\nSummary\n\n Neurocrine Biosciences Inc. beats on 9 of the 12 factors Kodiak Sciences Inc. \n\nKodiak Sciences Inc., a clinical stage biopharmaceutical company, provides novel therapeutics to treat ophthalmic diseases. The company's lead product candidate is KSI-301, a vascular endothelial growth factor (VEGF)-biologic that is in Phase I clinical study to treat wet age-related macular degeneration (AMD) and diabetic retinopathy. Its preclinical stage product candidates include KSI-501, a bispecific anti-interleukin 6/VEGF bioconjugate to target inflammation and abnormal angiogenesis in the pathogenesis of retinal vascular diseases; KSI-201, a recombinant mammalian cell expressed dual inhibitor antibody biopolymer bioconjugate for the treatment of wet AMD; and KSI-401, a recombinant mammalian cell expressed antibody biopolymer conjugate for the treatment of dry AMD. The company was formerly known as Oligasis, LLC and changed its name to Kodiak Sciences Inc. in September 2015. Kodiak Sciences Inc. was founded in 2009 and is headquartered in Palo Alto, California.\n\nNeurocrine Biosciences, Inc. discovers and develops pharmaceuticals for the treatment of neurological and endocrine-related diseases and disorders in the United States and internationally. The companyÂ’s lead products include INGREZZA (valbenazine), a vesicular monoamine transporter 2 inhibitor (VMAT2) used for the treatment of movement disorders; elagolix, a gonadotropin-releasing hormone (GnRH) antagonist that is in Phase III clinical trials used for womenÂ’s health; and opicapone, a catechol-O-methyltransferase inhibitor, which is in Phase III clinical trials used for in adjunct therapy and preparations of levodopa/DOPA decarboxylase inhibitors for adult patients with ParkinsonÂ’s disease. It is also developing NBI-640756 that is in Phase I clinical trials used for the treatment of essential tremor; and NBI-74788, which is in Phase I clinical trials used for the treatment of classic congenital adrenal hyperplasia. In addition, the companyÂ’s research programs comprise VMAT2 Inhibitors for movement disorders, bipolar disorders, and schizophrenia; and G Protein-Coupled Receptors and Ion Channels for epilepsy, essential tremor, pain, and other Indications. It has collaborations with AbbVie Inc. to develop and commercialize elagolix and GnRH antagonists for womenÂ’s and menÂ’s health; Mitsubishi Tanabe Pharma Corporation to develop and commercialize INGREZZA for movement disorders; and BIAL Â– Portela & Ca, S.A. to develop and commercialize opicapone for the treatment of human diseases and conditions, including ParkinsonÂ’s disease. Neurocrine Biosciences, Inc. was founded in 1992 and is headquartered in San Diego, California.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\t\t\t\t\t\t\n\n\n\n\n\n\n\t\t\t\t\n\t\n\t\t\t\t\n\t\t\t\t\n\t\t\t\t\n\n\n \t\t\t\t\n\t\t\t\t\n\n\t\t\t\n\t\t\t\n\n\t\t\t\n\n\n\t\t\t\n\t\t\t\n\n\n\t\t\t\n\t\t\t\n\t\t\n\n\n\n\t\t\t\t\n\t\t\n\n\n\n\n\n\t\t\t\t\n\n\n\n\n\n\n\n\t\t\n\t\t\t\n\n\n\n\t\t\n\n\n\n\n \n\t\t\n\n\t\t\n \n\n\t\n\n\t\n \n\n\t\n\n\t\t\n\n\t\t\t\n\t\t\t\t\t\t\t\n\n\n\t\t\t\n\t\t\t\t\t\t\t\n\n\n\t\t\t\n\t\t\t\t\t\t\t\n\n\n\t\t\t\n\n\t\t\n\n\t\t\n\n\n\n\t\t\n\t\t\t\tAbout US\n\tOur Team\n\tContact US\n\tPrivacy Policy\n\tComment Policy\n\n\n\t\t\tDesigned by WPZOOM\n\n\t\t\tCopyright © 2019 — YomiBlog. All Rights Reserved.\t\t\n\n\n\t\n \n\n\t\n\n\n\n \n\n\n\n\n\n\n\n\n\n\n"
#sentence_ls = text_to_sentences(test_text)


#test_sentence = sentence_ls[18]

#clean_sentence = test_sentence.replace('’', "'").encode('ascii', 'ignore').decode('utf-8')
#print(clean_sentence)  

#test_text = 'Migraine is a disorder that affects millions of Americans and can be execerbated by use of humira made by pfizer which is a tnf-alpha inhibitor'      
#normalized_tags, document_tags = dictionary_matcher(test_text)