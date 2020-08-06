# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 12:21:06 2019

@author: julia.gray
"""

import mysql.connector as MySQLdb
import json
import datetime
from urllib.parse import urlencode
import add_tagged_entities 
import pickle
import logging
import time
from fuzzywuzzy import fuzz
import os
import codecs


from google.modules.utils import get_html

###############################################################################
"""Be sure to add log file path or remove log + try statements prior to running"""
logging.basicConfig(filename = 'get_documents_error_log.log')
###############################################################################


def start_db():
    try:
        db = MySQLdb.connect(host="10.115.1.196",    
                            user="julia",         
                             passwd="Roivant1",  
                             db="ome_star_schema")
        
    except Exception as e:
        logging.error('%s | error in get_documents.start_db %s'%(e, str(datetime.datetime.now())))
    return db


def get_solr_search_url(keyword_list, from_date=datetime.date.today(), to_date=datetime.date.today(), search_params='standard'):
    """Format SOLR search URL depending on the search parameters - 
    standard search = [keyword]
    concurrent search = [keyword0, keyword1, ...]
    """
    try:    
        keyword_fail_list = []
        
        yy = str(from_date).split("-")[0]
        mm = str(from_date).split("-")[1]
        dd = str(from_date).split("-")[2]
    
        eyy = str(to_date).split("-")[0]
        emm = str(to_date).split("-")[1]
        edd = str(to_date).split("-")[2]
        
        if search_params == 'standard':
            if '"' not in keyword_list[0]:
                keyword = '"' + keyword_list[0] + '"'
            else:
                keyword = keyword_list[0]
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +keyword.encode('utf8')}
            params_solr = urlencode(params_solr)
            #url_query = "http://10.115.1.31:8983/solr/core1/select?" + params_solr +'&wt=json&rows=100&fq=file_modified_dt:['+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+eyy+'-'+emm+'-'+edd+'T23:59:59Z]' # CS - adjust second day time stamp to from eyy, emm, edd to to yy,mm,dd
            #print(url_query)
            url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        
    except Exception as e:
        logging.error('%s | error in get_documents.get_solr_search_url %s'%(e, str(datetime.datetime.now())))
        
    return url_query



def construct_solr_search_url(search_terms, from_date=datetime.date.today(), to_date=datetime.date.today()):
    """Possible search terms: keyphrase1, keyphrase2, keyphrase_distance, source_select"""
    try:
        yy = str(from_date).split("-")[0]
        mm = str(from_date).split("-")[1]
        dd = str(from_date).split("-")[2]
    
        eyy = str(to_date).split("-")[0] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        emm = str(to_date).split("-")[1] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        edd = str(to_date).split("-")[2] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        
        if ('keyphrase2' in search_terms) and ('keyphrase_distance' in search_terms):
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"(\\\"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '\\\") (\\\"'.encode('utf8') + search_terms['keyphrase2'].encode('utf8') + '\\\")"~'.encode('utf8') + search_terms['keyphrase_distance'].encode('utf8')}
        elif ('keyphrase2' in search_terms):        
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ':"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '" AND cleaned_html_content_txt:"'.encode('utf8') + search_terms['keyphrase2'].encode('utf8') + '"'.encode('utf8')}
        elif ('keyphrase_distance' in search_terms):
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"(\\\"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '\\\")"~'.encode('utf8') + search_terms['keyphrase_distance'].encode('utf8')}
        else:
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '"'.encode('utf8')}

        
        params_solr = urlencode(params_solr)
        
        if ('source_select' in search_terms):
            if search_terms['source_select'] != 'all':
                source_select = search_terms['source_select'].split(', ')# CS- split on source_select consistent with splitting for aliases get_search_params_list
                if len(source_select) > 1:
                    #print('source select is longer than 1')
                    source_string_list = []
                    for i in range(0, len(source_select)):
                        if source_select[i] == "Ct.gov":
                            source_string_list.append("path_basename_s:CT.gov-added_or_modified_studies*")    
                        else:
                            source_string_list.append("path0_s:%22" + source_select[i]+"%22")    
                    source_string = ' OR '.join(source_string_list)
                    params_solr = params_solr + ' AND (' + source_string + ')'
                    params_solr = params_solr.replace(' ','%20')
                    #print(params_solr, '-----this is params solr')
                    #print('before url query')
                    url_query = 'http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:['+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+eyy+'-'+emm+'-'+edd+'T23:59:59Z]&' + params_solr + '&rows=500'# CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
                    #print('after url_query')
                else:
                    if source_select[0] == "Ct.gov":
                        url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path_basename_s:" + "CT.gov-added_or_modified_studies*" + "&fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
                    else:
                        url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path0_s:%22" + source_select[0].replace(' ', '%20') + "%22&fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
            else:
                url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        else:
            url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500'# CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd


    except Exception as e:
        logging.error('%s | error in get_documents.construct_solr_search_url %s', (e, str(datetime.datetime.now())))        
    
    #print(url_query , '---- this is the url query')
    return url_query


##CS get_solr_results function adjusted to accommodate new filters for journal_select, author_select, institutional_select, and the fuzzy match leeway
def get_solr_results(keyword, search_url, journal_select='', author_select='', institution_select='', filter_leeway=70, tags='tagged_entities_for_web', from_date=None, to_date=None):
    """Parse JSON result of search URL using re HTML. Add tags depending on parametes
    tagged_entities_for_web = tags are CSS classes 
    tagged_entities_for_web_new_moas_indications = tags are CSS classes + get MOA/Indication pairs not in DB
    tagged_entities = inline CSS for HTML email string
    """
    try:
        keyword_fail_list = []
        #print('KEYWORD: %s'%(keyword))
        #print(search_url)
        
        
        t0 = datetime.datetime.now()
        solr_results = {'keyword':[], 'path':[], 'file_modified_date':[], 'title':[], 'tagged_document_text':[], 'document_text':[], 'document_type':[], 'detailed_type':[], 'document_tags':[], 'normalized_tags':[], 'normalized_tags_ordered':[], 'normalized_tags2':[], 'normalized_tags_ordered2':[], 'document_id':[], 'new_moa_indication_pairs':[], 'new_moas':[], 'shorter_sentences':[], 'keyword_count':[],'LDA_class':[]}
        
        if tags in ['tagged_entities_indication_moa_pairs', 'tagged_entities_for_web_new_moas_indications']:
            path = '//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/OME alerts/input data/' #YMR addition to load data - path redefined in get_documents.py ...
            with open (path+'dict_MoA_indications_DB', 'rb') as fp:
                dict_MoA_indications_DB = pickle.load(fp)
        try:
            html = get_html(search_url)
        except Exception as e:
            print(e)
        
        if html:
            #print('--- entering html document extraction---')
            d = json.loads(html.decode('utf-8'))
            #print(str(d['response']['numFound']) + ' documents found')
            journal_docid_list = []
            author_docid_list = []
            institution_docid_list = []
            for doc_idx, doc in enumerate(d['response']['docs']):
                #print(doc['id'],'---- this is the document id')
                #if doc_idx % 100 == 0:
                #    print('DOC ' + str(doc_idx) + '/' + str(d['response']['numFound']))
                #if (doc['id'] in solr_results['document_id']) or (doc['title'][0] in solr_results['title']):
                if (doc['id'] in solr_results['document_id']) or (doc['title_txt'][0] in solr_results['title']):
                    pass
                elif doc['id'] == "":
                    pass
                elif 'cleaned_html_content_txt' not in doc:
                    pass
                elif 'flag_OME_alert_exclusion_ss' in doc:
                    pass
                else:
                    #print(doc)
                    #if any(s in doc['id'] for s in ct_paths):
                    #if doc['title'][0] not in clinical_trials['title']:
                    document_type, detailed_type = get_document_type(doc['id'])
                    #print(document_type, '--- this is the document type')
                                    
                    # document_text extraction should be contingent on tocument type for 
                    #if (document_type == 'Cortellis') and ('Drug_Status_Changes_alert' in doc['id']):
                    #    print(doc['id'] , '---- this is the doc id')
                    #    file_to_read = doc['id']
                    #    = codecs.open(file_to_read, "r", "utf-8")
                    
                    
                    #document_text = text_to_sentences(doc['content'][0])
                    document_text = ' '.join(add_tagged_entities.text_to_sentences(doc['cleaned_html_content_txt'][0]))
                    #hs = highlight_sentences(t, keyword)
                    
                    # hss = insert_highlight("\n".join(hs), keyword)
                    file_modified_date = doc['file_modified_dt'].split("T")[0]
                    #file_path = 'http://ome.vant.com/test-app_ome/ome_alert_document/'+doc['id'].replace('/', '!!!').strip('!!!')
                    file_path = 'http://52.23.161.54/redirect/<user_name>/' + doc['id'].replace('/', '!!!').strip('!!!')				
    
                    
                    ##CS Implementing journal, author, and institution checks. These are a work in progress
                    
                    ##CS pubmed list pulled from get_document_type function
                    pubmed_list= ['pubmed_abstract', 'pubmed_article']
                    
                    ## CS Journal filter
                    if (journal_select != '') and (document_type in pubmed_list):
                        journal_list = journal_select.split(', ')
                        
                        if 'Article_Journal_Title_ss' in doc:
                            #print('----- we entered the first field check for journal check')
                            for i in journal_list:
                                #print(i, '----this is user submitted journal')
                                fuzzy_journal_score = fuzz.ratio(i,doc['Article_Journal_Title_ss'][0])
                                #print(fuzzy_journal_score)
                                #print(doc['Article_Journal_Title_ss'])
                                if fuzzy_journal_score > filter_leeway:
                                    journal_docid_list.append(doc['id'])
                                # CS append journals to filter list to only append these later
                        
                        elif 'journal_name_ss' in doc:
                            #print('----- we have entered the second field check for journals')
                            for i in journal_list:
                                fuzzy_journal_score = fuzz.ratio(i,doc['journal_name_ss'][0])
                                if fuzzy_journal_score > filter_leeway:
                                    journal_docid_list.append(doc['id'])
                                # CS append journals to filter list to only append these later
                    
                    ##CS Author Filter
                    if (author_select != '') and (document_type in pubmed_list):
                        author_list = author_select.split(', ')
                        if 'Article_AuthorList_Author_Name_ss' in doc:
                            for doc_author in doc['Article_AuthorList_Author_Name_ss']:
                                for user_author in author_list:
                                    #print(doc_author,'---- this is the doc_author')
                                    #print(user_author, ' ---- this is the user_author')
                                    fuzzy_author_score = fuzz.ratio(user_author,doc_author)
                                    #print(fuzzy_author_score, '----- this is the fuzzy match score')
                                    if fuzzy_author_score > filter_leeway:
                                        #print(doc['id'],'----- append success!')
                                        author_docid_list.append(doc['id'])
                                # CS append authors to filter list to only append these later
                                
                                
                    ##CS Institution filter
                    if (institution_select != '') and (document_type in pubmed_list):
                        institution_list = institution_select.split(', ')
                        if 'company_OME_txt_ss' in doc:
                            for doc_ins in doc['company_OME_txt_ss']:
                                for user_ins in institution_list:
                                    fuzzy_ins_score = fuzz.ratio(doc_ins, user_ins)
                                    if fuzzy_ins_score > filter_leeway:
                                        institution_docid_list.append(doc['id'])
                            # CS append insititutions to filter list to only append these later
                                
                            
                    if document_type in pubmed_list:
                        if ('Article_Journal_Title_ss' in doc) and ('Article_ArticleTitle_ss' in doc):
                            document_title = doc['Article_Journal_Title_ss'][0] + " | " + doc["Article_ArticleTitle_ss"][0]
                        elif "Article_ArticleTitle_ss" in doc:
                            document_title = doc["Article_ArticleTitle_ss"][0]
                        elif ('Article_Journal_Title_ss' in doc) and ('article_title_ss' in doc):
                            document_title = doc['Article_Journal_Title_ss'][0] + " | " + doc["article_title_ss"][0]
                        elif "journal_name_ss" in doc:
                            document_title = doc["journal_name_ss"][0] + " | " + doc["article_title_ss"][0]
                        elif "article_title_ss" in doc:
                            document_title = doc["article_title_ss"][0]
                        else:
                            document_title = doc["title_txt"][0]
                        #document_title = doc['cleaned_html_content_txt'][0].split('\t')[3]
                        
                        try:
                            if "DateCompleted_Year_ss" in doc:                            
                                original_pub_date = datetime.date(int(doc["DateCompleted_Year_ss"][0]), int(doc["DateCompleted_Month_ss"][0]), int(doc["DateCompleted_Day_ss"][0]))                    
                            elif "Article_Journal_JournalIssue_PubDate_dt" in doc:
                                original_pub_date = datetime.date(int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[0]), int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[1]), int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[2]))
                            elif "Article_ArticleDate_Year_ss" in doc:
                                original_pub_date = datetime.date(int(doc["Article_ArticleDate_Year_ss"][0]), int(doc["Article_ArticleDate_Month_ss"][0]), int(doc["Article_ArticleDate_Day_ss"][0]))
                            elif "pub_date_dt" in doc:
                                original_pub_date = datetime.date(int(doc["pub_date_dt"].split('T')[0].split('-')[0]), int(doc["pub_date_dt"].split('T')[0].split('-')[1]), int(doc["pub_date_dt"].split('T')[0].split('-')[2]))
                            elif "History_PubMedPubDate_pubmed_ss" in doc:    
                                original_pub_date = datetime.date(int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[0]), int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[1]), int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[2]))
                            elif "History_PubMedPubDate_pubmed_dt" in doc:
                                original_pub_date = datetime.date(int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[0]), int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[1]), int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[2]))
                            else:
                                original_pub_date = datetime.date.today()
                                #print(original_pub_date)
                            if original_pub_date < from_date:
                                #print('REVISED PUBMED ARTICLE')
                                continue
                        except:
                            print('no pub date')
                    
                    else:
                        document_title = doc['title_txt'][0]
               
                    #if doc['id'] == 'pmc_6516158.xml':
                    #    print(document_text)
                    
                    if keyword != '':
                        if document_type not in ['Adis Insight','Cortellis','GBD_email','Evaluate News']:
                            keywords_found, shorter_sentences = add_tagged_entities.get_keyword_sentences(document_text, keyword)
                            tagged_document_text = add_tagged_entities.highlight_keyword(document_text, keyword)
                            tagged_shorter_sentences = add_tagged_entities.highlight_keyword(shorter_sentences, keyword)
                        else:
                            keywords_found, shorter_sentences = add_tagged_entities.get_keyword_sentences_subscriptions(document_text, keyword)
                            tagged_document_text = add_tagged_entities.highlight_keyword_subscriptions(document_text, keyword)
                            tagged_shorter_sentences = add_tagged_entities.highlight_keyword_subscriptions(shorter_sentences, keyword)

                    else:
                        tagged_document_text = document_text
                        shorter_sentences = ''
                        keywords_found = []
                        tagged_shorter_sentences = document_text
                    
                    if tags =='tagged_entities_for_web':
                        #print(doc['id'])
                        #normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                        #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                        #document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                        #tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags)
                        new_indication_moa_pairs = []
                        new_moas = []
                        if 'drug_OME_txt_ss_matchtext_ss' in doc:
                            drug_tag_list = doc['drug_OME_txt_ss_matchtext_ss']
                        else:
                            drug_tag_list = []
					
                        if 'target_OME_txt_ss_matchtext_ss' in doc:
                            target_tag_list = doc['target_OME_txt_ss_matchtext_ss']
                        else:
                            target_tag_list = []
						
                        if 'company_OME_txt_ss_matchtext_ss' in doc:
                            company_tag_list = doc['company_OME_txt_ss_matchtext_ss']
                        else:
                            company_tag_list = []
					
                        if 'indication_OME_txt_ss_matchtext_ss' in doc:
                            indication_tag_list = doc['indication_OME_txt_ss_matchtext_ss']
                        else:
                            indication_tag_list = []
						
                        document_tags = drug_tag_list + target_tag_list + company_tag_list + indication_tag_list
                        normalized_tags, document_tags_list = add_tagged_entities.parse_tag_lists(drug_tag_list, target_tag_list, company_tag_list, indication_tag_list)
                        tagged_document_text = add_tagged_entities.highlight_tags_from_list(tagged_document_text, normalized_tags)
                    elif tags =='tagged_entities_for_web_new_moas_indications':
                        #print(doc['id'])
                        normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                        tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                        document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                        tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags)
                        new_indication_moa_pairs, new_moas = add_tagged_entities.get_new_indication_moa_pairs(document_text, normalized_tags, dict_MoA_indications_DB)
                    elif tags =='tagged_entities':
                        #print(doc['id'])
                        normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                        tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags, for_web=False)
                        document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                        tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags, for_web=False)
                        new_indication_moa_pairs = []
                        new_moas = []
                    elif tags =='tagged_entities_for_email':
                        #print(doc['id'])
                        #normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                        #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags, for_web=False)
                        #document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                        #tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags, for_web=False)
                        new_indication_moa_pairs = []
                        new_moas = []
                        
                        if 'drug_OME_txt_ss_matchtext_ss' in doc:
                            drug_tag_list = doc['drug_OME_txt_ss_matchtext_ss']
                        else:
                            drug_tag_list = []
                        
                        if 'target_OME_txt_ss_matchtext_ss' in doc:
                            target_tag_list = doc['target_OME_txt_ss_matchtext_ss']
                        else:
                            target_tag_list = []
                            
                        if 'company_OME_txt_ss_matchtext_ss' in doc:
                            company_tag_list = doc['company_OME_txt_ss_matchtext_ss']
                        else:
                            company_tag_list = []
                        
                        if 'indication_OME_txt_ss_matchtext_ss' in doc:
                            indication_tag_list = doc['indication_OME_txt_ss_matchtext_ss']
                        else:
                            indication_tag_list = []
                            
                        document_tags = drug_tag_list + target_tag_list + company_tag_list + indication_tag_list
                        normalized_tags, document_tags_list = add_tagged_entities.parse_tag_lists(drug_tag_list, target_tag_list, company_tag_list, indication_tag_list)
                    
                    elif tags == 'tagged_entities_indication_moa_pairs':
                        normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                        #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                        document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                        new_indication_moa_pairs, new_moas = add_tagged_entities.get_new_indication_moa_pairs(document_text, normalized_tags, dict_MoA_indications_DB)
                        
                        
                    
                    else:
                        document_tags = {}
                        normalized_tags = {}
                        document_tags_list = []
                        new_indication_moa_pairs = []
                        new_moas = []
                        
                    
                    solr_results['document_id'].append(doc['id'])
                    if 'lda_class_ss' in doc.keys():
                        #print('this is -----', doc['lda_class_ss'][0])
                        solr_results['LDA_class'].append(str(doc['lda_class_ss'][0]))
                        #print('solr results here-----',solr_results['LDA_class'])
                    else:
                        solr_results['LDA_class'].append('Not Evaluated')
                    solr_results['keyword'].append(keyword.strip())
                    #print(keyword, '--- this is the keyword')
                    #print(keyword.strip(),'--- this is the stripped keyword')
                    solr_results['path'].append(file_path)
                    solr_results['file_modified_date'].append(file_modified_date)
                    solr_results['title'].append(document_title)
                    solr_results['tagged_document_text'].append(tagged_document_text)
                    if document_type in ['Adis Insight','Evaluate News','Cortellis','GBD_email']:
                        #print(tagged_document_text,'--- this is the tagged_document_text')
                        pass
                    solr_results['document_type'].append(document_type)
                    solr_results['detailed_type'].append(detailed_type)
                    solr_results['document_text'].append(document_text)
                    solr_results['normalized_tags'].append(normalized_tags)
                    solr_results['document_tags'].append(document_tags)
                    solr_results['normalized_tags_ordered'].append(document_tags_list)
                    solr_results['new_moa_indication_pairs'].append(new_indication_moa_pairs)
                    solr_results['new_moas'].append(new_moas)
                    solr_results['shorter_sentences'].append(tagged_shorter_sentences)
                    if document_type in ['Adis Insight','Evaluate News','Cortellis','GBD_email']:
                        #print(tagged_shorter_sentences,'--- this is the tagged_document_text')
                        pass
                    solr_results['keyword_count'].append(keywords_found)
                
                    
                    #solr_results['normalized_tags2'].append(normalized_tags2)
                    #solr_results['normalized_tags_ordered2'].append(document_tags2)
                
    
    
        tf = datetime.datetime.now()
        #print('SOLR execution time: %s'%(str(tf-t0)))    
        

    except Exception as e:
        logging.error('%s | error in get_documents.get_solr_results %s'%(e, str(datetime.datetime.now())))
        
    ## CS edit returned function from get_solr_results function      
    return solr_results, journal_docid_list, author_docid_list, institution_docid_list


def get_solr_results_from_path(keyword, document_path, tags='tagged_entities_for_web'):
    """For display of single document"""
    try:   
        keyword_path = 'id:"' + '/' + document_path + '"' 
        
        params_solr = {'q':keyword_path.encode('utf8')}
        params_solr = urlencode(params_solr)
        search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?" + params_solr +'&wt=json&rows=100'
        
        
        solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results(keyword, search_url, tags=tags)
    except Exception as e:
        logging.error('%s | error in get_documents.get_solr_results_from_path %s'%(e, str(datetime.datetime.now())))            
    return solr_results
        
                            
def get_document_type(doc_id):
    try:    
        document_type = 'newswire'
        detailed_type = 'newswire'
        
        #ct_paths = ['CT.gov', 'EMEA', 'EU_CT', 'PMDA', 'FDA']
        
        #if any(s in doc_id for s in ct_paths):
        if 'CT.gov' in doc_id:    
            document_type = 'clinical_trials'
            detailed_type = 'CT.gov'
        elif 'EMEA' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'EMEA'
        elif 'EU_CT' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'EU_CT'
        elif 'Adis' in doc_id:
            document_type = 'Adis Insight'
            detailed_type = 'Adis Insight'
        elif 'evaluate' in doc_id: 
            document_type = 'Evaluate News'
            detailed_type = 'Evaluate News'
        elif 'PMDA' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'PMDA'
        elif 'FDA_Medical_reviews' in doc_id:
            document_type = 'FDA_Medical_reviews'
            detailed_type = 'FDA_Medical_reviews'
        elif 'fda_guidance' in doc_id:
            document_type = 'fda_guidance'
            detailed_type = 'fda_guidance'
        elif 'fiercepharma' in doc_id:
            document_type = 'newswire'
            detailed_type = 'fiercepharma'
        elif 'fiercebiotech' in doc_id:
            document_type = 'newswire'
            detailed_type = 'fiercebiotech'
        elif 'politico' in doc_id:
            document_type = 'newswire'
            detailed_type = 'politico_morning_eHealth'
        elif 'alpha' in doc_id:
            document_type = 'newswire'
            detailed_type = 'seeking_alpha_healthcare'
        elif any(x in doc_id for x in ['cortellis','Cortellis']):
            document_type = 'Cortellis'
            detailed_type = 'Cortellis'
        elif any(x in doc_id for x in ['IPD','ipd']):
            document_type = 'IPD'
            detailed_type = 'IPD'
        elif 'GBD' in doc_id:
            document_type = 'GBD_email'
            detailed_type = 'GBD_email'
        elif 'PMC' in doc_id:
            document_type = 'pubmed_article'
            detailed_type = 'pubmed_article'
        elif 'Google_Search' in doc_id:
            document_type = 'google_news'
            detailed_type = 'google_news'
        elif 'google_news' in doc_id:
            document_type = 'google_news'
            detailed_type = 'google_news'
        elif 'PRNW' in doc_id:
            document_type = 'pr_newswire'
            detailed_type = 'pr_newswire'
        elif 'streetaccount' in doc_id:
            document_type = 'streetaccount'
            detailed_type = 'streetaccount'
        elif 'PubMed_abstracts' in doc_id:
            document_type = 'pubmed_abstract'
            detailed_type = 'pubmed_abstract'
        elif 'evercore' in doc_id:
            document_type = 'evercore'
            detailed_type = 'evercore'
        elif 'Twitter' in doc_id:
            document_type = 'twitter'
            detailed_type = 'twitter'
        elif 'SEC_Filings' in doc_id:
            document_type = 'SEC_filing'
            detailed_type = 'SEC_filing'
        elif 'Press releases' in doc_id:
            document_type = 'press_release'
            source_name = doc_id.split('/')[-1].split('_')[0]
            
            if source_name not in ['FirstWordPharma', 'PinkPharmaintelligenceInforma', 'EndPoints', 'MassDevice']:
                detailed_type = 'CompanyPR_' + source_name
            else:
                detailed_type = source_name
    except Exception as e:
        logging.error('%s | error in get_documents.get_document_type %t', (e, str(datetime.datetime.now())))        
    return document_type, detailed_type



def get_ome_alert_results(search_params_list,from_date=datetime.date.today(), to_date=datetime.date.today(), tags='tagged_entities_for_web'):
    """Execute multiple SOLR searches and return result as dictionary"""
    try:
        ome_alert_results = {'keyword':[],'full_keyword_list':[] ,'path':[], 'file_modified_date':[], 'title':[], 'tagged_document_text':[], 'document_text':[], 'document_type':[], 'document_tags':[], 'normalized_tags':[], 'normalized_tags_ordered':[], 'document_id':[], 'shorter_sentences':[], 'keyword_count':[],'LDA_class':[]}
        url_query = ''
        

        path_full_dict = {} #necessary for keyword for keyword_full_list parameter
        for params in search_params_list:
            
            ##CS filter_leeway parameter must always be set to be an integer, 
            ##CS hide on front end until filters selected and edited. Then allow filter leeway editing
            filter_type = params['filter_type']
            filter_leeway = int(params['filter_leeway'])


            ##CS Create and execute solr_query, print statements to help with debugging
            ##CS note new returns from get_solr_results function
            url_query = construct_solr_search_url(params, from_date, to_date)
            #print(url_query, '---- this is the url query')
            #print('complete with url_query')
            solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results(params['keyword'], url_query, params['journal_select'], params['author_select'], params['institution_select'], filter_leeway, tags=tags, from_date=from_date, to_date=to_date) #CS included params['journal select]
            #print('complete with getting solr_results')            
            #print(journal_docid_list,'---- this is the journal docid list')
            #print(author_docid_list, '---- this is the author docid list')
            #print(institution_docid_list, '----- this is the institution_docid_list')
            
            
            ##CS union or intersection parameters for filter type. Determined by user input
            if filter_type == 'and':
                journal_set = journal_set = set(journal_docid_list)
                author_set = set(author_docid_list)
                institution_set = set(institution_docid_list)
                jr_au_ins_filter_set = journal_set & author_set & institution_set
                jr_au_ins_filter_list = list(jr_au_ins_filter_set)
            
            else:
                journal_set = set(journal_docid_list)
                author_set = set(author_docid_list)
                institution_set = set(institution_docid_list)
                jr_au_ins_filter_set = journal_set | author_set | institution_set
                jr_au_ins_filter_list = list(jr_au_ins_filter_set)
                
            
            #print(jr_au_ins_filter_list, '------this is the final filtered list')
            #print(solr_results.keys())
            
            
            ##Create if statement to handle granular filter parameters
            if (params['journal_select'] != '') or (params['author_select'] != '') or (params['institution_select'] != ''):

                #First loop for is keyword list collection
                for j in range(0, len(solr_results['path'])):
                    kw = solr_results['keyword'][j]
                    path = solr_results['path'][j]
                    
                    #Kw_cnt comes out as a list of tuples. The tuple describes keyword mentions in the text
                    #Take the length to find the number of mentions for that keyword
                    kw_cnt = len(solr_results['keyword_count'][j])
                    
                    #print(kw, '---- this is the kw')
                    #print(path, '--- this is the path')
                    
                    if path not in path_full_dict.keys():
                        path_full_dict[path] = [(kw, kw_cnt)]
                    elif path in path_full_dict.keys():
                        path_full_dict[path].append((kw, kw_cnt))
                    else:
                        print('problem investigate line 644')
                        pass

                #print('we entered the filtering stage')
                for j in range(0, len(solr_results['path'])):
                    if (solr_results['path'][j] not in ome_alert_results['path']) & (solr_results['document_id'][j] in jr_au_ins_filter_list):
                        print('success for filters!!!!!!!')
                        ome_alert_results['keyword'].append(solr_results['keyword'][j])
                        ome_alert_results['path'].append(solr_results['path'][j])
                        ome_alert_results['file_modified_date'].append(solr_results['file_modified_date'][j])
                        ome_alert_results['title'].append(solr_results['title'][j])
                        ome_alert_results['tagged_document_text'].append(solr_results['tagged_document_text'][j])
                        ome_alert_results['document_text'].append(solr_results['document_text'][j])
                        ome_alert_results['document_type'].append(solr_results['document_type'][j])
                        ome_alert_results['document_tags'].append(solr_results['document_tags'][j])
                        ome_alert_results['normalized_tags'].append(solr_results['normalized_tags'][j])
                        ome_alert_results['normalized_tags_ordered'].append(solr_results['normalized_tags_ordered'][j])
                        ome_alert_results['LDA_class'].append(solr_results['LDA_class'][j])
                        #REMOVE AFTER CLEAWNED NORMALIZED TAGS
                        #ome_alert_results['normalized_tags2'].append(solr_results['normalized_tags2'][j])
                        #ome_alert_results['normalized_tags_ordered2'].append(solr_results['normalized_tags_ordered2'][j])
                        ome_alert_results['document_id'].append(solr_results['document_id'][j])
                        ome_alert_results['shorter_sentences'].append(solr_results['shorter_sentences'][j])
                        ome_alert_results['keyword_count'].append(solr_results['keyword_count'][j])
            
            ##CS alternative to filter statement where no granular filters in place (source select still functional though)
            else:

                for j in range(0, len(solr_results['path'])):
                    kw = solr_results['keyword'][j]
                    path = solr_results['path'][j]
                    
                    #Kw_cnt comes out as a list of tuples. The tuple describes keyword mentions in the text
                    #Take the length to find the number of mentions for that keyword
                    kw_cnt = len(solr_results['keyword_count'][j])
                    
                    #print(kw, '---- this is the kw')
                    #print(path, '--- this is the path')
                    
                    if path not in path_full_dict.keys():
                        path_full_dict[path] = [(kw, kw_cnt)]
                    elif path in path_full_dict.keys():
                        path_full_dict[path].append((kw, kw_cnt))
                    else:
                        print('problem investigate line 644')
                        pass

                for j in range(0, len(solr_results['path'])):
                    if (solr_results['path'][j] not in ome_alert_results['path']):
                        ome_alert_results['keyword'].append(solr_results['keyword'][j])
                        ome_alert_results['path'].append(solr_results['path'][j])
                        ome_alert_results['file_modified_date'].append(solr_results['file_modified_date'][j])
                        ome_alert_results['title'].append(solr_results['title'][j])
                        ome_alert_results['tagged_document_text'].append(solr_results['tagged_document_text'][j])
                        ome_alert_results['document_text'].append(solr_results['document_text'][j])
                        ome_alert_results['document_type'].append(solr_results['document_type'][j])
                        ome_alert_results['document_tags'].append(solr_results['document_tags'][j])
                        ome_alert_results['normalized_tags'].append(solr_results['normalized_tags'][j])
                        ome_alert_results['normalized_tags_ordered'].append(solr_results['normalized_tags_ordered'][j])
                        #REMOVE AFTER CLEAWNED NORMALIZED TAGS
                        #ome_alert_results['normalized_tags2'].append(solr_results['normalized_tags2'][j])
                        #ome_alert_results['normalized_tags_ordered2'].append(solr_results['normalized_tags_ordered2'][j])
                        ome_alert_results['document_id'].append(solr_results['document_id'][j])
                        ome_alert_results['shorter_sentences'].append(solr_results['shorter_sentences'][j])
                        ome_alert_results['keyword_count'].append(solr_results['keyword_count'][j])
                        ome_alert_results['LDA_class'].append(solr_results['LDA_class'][j])
                            
        #print(path_full_dict, '--- this is the dictionary')
        #Create new for loop to include the full keyword list per path. 
        #print(path_full_dict,'--- this is the path to full dict')
        for p in range(0, len(ome_alert_results['path'])):
            path_to_inv = ome_alert_results['path'][p]
            #print(path_to_inv, '-- this is the path to investigate')
            ome_alert_results['full_keyword_list'].append(path_full_dict[path_to_inv])

        #Order list of tuples in ome_alert_results['full_keyword_list']
        
        for pos, kw_full_list in enumerate(ome_alert_results['full_keyword_list']):
            if len(ome_alert_results['full_keyword_list'][pos]) > 0:
                ome_alert_results['full_keyword_list'][pos] = sorted(ome_alert_results['full_keyword_list'][pos], key= lambda x:x[1], reverse = True)
            else:
                ome_alert_results['full_keyword_list'] = ome_alert_results['full_keyword_list']
                pass

    
    except Exception as e:                
        print(e, '---- this is the exception in get ome alert results')
        logging.error('%s | error in get_documents.get_ome_alert_results %s'%(e, str(datetime.datetime.now())))      
                
    return ome_alert_results, url_query
        

def get_ome_alerts_of_user(user):
    try:
        ome_alerts = {'keyword':[], 'aliases':[], 'id':[], 'alert_type':[], 'email':[], 'source_select':[], 'alert_title':[]}
        ome_alert_ids = []
    
        # query = """SELECT * FROM ome_star_schema.ome_alerts
        #         WHERE `user` LIKE "%s" AND alert_title LIKE '%NWSLTR_cooccurence%'""" %("%" + user + "%")

        query = """SELECT * FROM ome_star_schema.ome_alerts
                WHERE `user` LIKE "%yoann.randriamihaja%" AND alert_title LIKE '%NWSLTR_cooccurence%'"""

        db = start_db()
        cur = db.cursor()
        cur.execute(query)
    
        for row in cur.fetchall():
            #if row[5] in ['standard', 'standard_title']:
            ome_alerts['id'].append(row[0])
            ome_alerts['keyword'].append(row[1])
            ome_alerts['aliases'].append(row[2])
            ome_alerts['alert_type'].append(row[5])
            ome_alerts['email'].append(row[4])
            ome_alerts['source_select'].append(row[6])
            ome_alerts['alert_title'].append(row[7])
            ome_alert_ids.append(row[0])
    except Exception as e:                
        logging.error('%s | error in get_documents.get_ome_alert_results %s'%(e, str(datetime.datetime.now())))

    return ome_alerts, ome_alert_ids

def get_keyword_list_from_ome_alert_id(keyword_id):
    try:
        keyword_list = []
        clean_keyword_title = []
        clean_keyword_list = []
    
        query = """SELECT * FROM ome_star_schema.ome_alerts
                WHERE idome_alerts = %s"""%(keyword_id.strip('"').strip("'"))
    
        #print(keyword_id)
        #print(query)
    
        db = start_db()
        cur = db.cursor()
        cur.execute(query)
    
        for row in cur.fetchall():
            if row[5] == 'standard_title':
                clean_keyword_title.append(row[1])
            else:
                keyword_list.append(row[1])
                clean_keyword_title.append(row[1])
                
            if row[2] not in ['', None]:
                keyword_list += row[2].split(',')
    
        for k in keyword_list:
            clean_keyword_list.append([k.strip()])
    except Exception as e:
        logging.error('%s | error in get_documents.get_keyword_list_from_ome_alert_id %s'%(e, str(datetime.datetime.now())))        
    return clean_keyword_list, clean_keyword_title

def get_search_params_list(ome_alert_id):
    #keyword gets highlighted - keyphrase gets searched
    try:    
        search_params_list = []
        alert_title = ''
        
        query = """SELECT * FROM ome_star_schema.ome_alerts
                    WHERE idome_alerts = %s"""%(str(ome_alert_id))
            
        db = start_db()
        cur = db.cursor()
        cur.execute(query)
        for row in cur.fetchall():
            alert_title = row[7]
            if row[5] == 'standard':
                if len(row[2]) >= 2:# CS - prevents second, irrelevant + empty search params_list generation
                    search_list = [row[1]] + row[2].split(', ')# CS - prevents second, irrelevant + empty search params_list generation
                elif len(row[2]) < 2:# CS - prevents second, irrelevant + empty search params_list generation
                    search_list = [row[1]]# CS - prevents second, irrelevant + empty search params_list generation
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    search_params_list.append({'search_type':'standard', 'keyphrase1':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                    #^^^CS adjusted search_params_list to include new filter columns 
                    
            elif row[5] == 'standard_title':
                search_list = row[2].split(', ')
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    search_params_list.append({'search_type':'standard', 'keyphrase1':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                    #^^^CS adjusted search_params_list to include new filter columns 
                    
            elif 'cooccurence' in row[5]:
                search_list = row[2].split(', ')
                #print(search_list, '--- this is the search list')
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    if len(row[5].split('_')) > 1:
                        search_params_list.append({'search_type':'coocurence', 'keyphrase1':row[1], 'keyphrase2':i, 'keyword':i, 'keyphrase_distance':row[5].split('_')[1], 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                        #^^^CS adjusted search_params_list to include new filter columns 
                    else:
                        search_params_list.append({'search_type':'coocurence', 'keyphrase1':row[1], 'keyphrase2':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                        #^^^CS adjusted search_params_list to include new filter columns 
    except Exception as e:        
        logging.error('%s | error in get_documents.get_search_params_list %s'%(e, str(datetime.datetime.now())))       
    return search_params_list, alert_title
        
                
                

def get_daily_stats(from_date):
    try:    
        daily_stats = {'date':str(from_date), 'indexed_article_count':0, 'by_source':{}, 'by_source_detail':{}, 'tagged_entity_count_repeat':{}, 'tagged_entity_count':{}, 'new_moa_indication_pairs':[], 'new_moas':[]}
        
        yy = str(from_date).split('-')[0]
        mm = str(from_date).split('-')[1]
        dd = str(from_date).split('-')[2]
        
        url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:[" + yy + "-" + mm + "-" + dd + "T00:00:00Z%20TO%20" + yy + "-" + mm + "-" + dd + "T23:59:59Z]&q=*&rows=10000"
        
        
        #url_query = "http://10.115.1.195:8983/solr/core1/select?indent=on&q=%22NLRP3_google_news_search_PR5_03-02-2019_20_45.html%22&wt=json"
        
        solr_results = get_solr_results('', url_query, tags='tagged_entities_indication_moa_pairs', from_date=from_date, to_date=datetime.date.today())
        
        daily_stats['indexed_article_count'] = len(solr_results['path'])
        
        
        for i in range(0, len(solr_results['path'])):
            if solr_results['document_type'][i] not in daily_stats['by_source']:
                daily_stats['by_source'][solr_results['document_type'][i]] = 1
            else:
                daily_stats['by_source'][solr_results['document_type'][i]] += 1
                
            if solr_results['detailed_type'][i] not in daily_stats['by_source_detail']:
                daily_stats['by_source_detail'][solr_results['detailed_type'][i]] = 1
            else:
                daily_stats['by_source_detail'][solr_results['detailed_type'][i]] += 1
            
            if len(solr_results['new_moa_indication_pairs'][i]) > 0:
                for m in solr_results['new_moa_indication_pairs'][i]:
                    daily_stats['new_moa_indication_pairs'].append([m[0], m[1], solr_results['path'][i].replace('ome_alert_document', 'curate_ome_alert_document')])
            if len(solr_results['new_moas'][i]) > 0:
                for m in solr_results['new_moas'][i]:
                    daily_stats['new_moas'].append([m[0], m[1], solr_results['path'][i].replace('ome_alert_document', 'curate_ome_alert_document')])
            
            for tag in solr_results['normalized_tags'][i]:
                if True in solr_results['normalized_tags'][i][tag]['result']['valid_match']:
                    if tag not in daily_stats['tagged_entity_count']:
                        daily_stats['tagged_entity_count'][tag] = 1
                        daily_stats['tagged_entity_count_repeat'][tag] = 0
                    else:
                        daily_stats['tagged_entity_count'][tag] += 1
                    
                    for j in range(0, len(solr_results['normalized_tags'][i][tag]['result']['valid_match'])):
                        if solr_results['normalized_tags'][i][tag]['result']['valid_match'][j] == True:
                            daily_stats['tagged_entity_count_repeat'][tag] += 1
    except Exception as e:
        logging.error('%s | error in get_documents.get_daily_stats %s', (e, str(datetime.datetime.now())))        
    return solr_results, daily_stats, url_query


def save_daily_stats(daily_stats):
    try:
        path = '//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/OME alerts/output data/daily_stats_' + daily_stats['date'] + '.json'
        
        with open(path, 'w') as fp:
            json.dump(daily_stats, fp)
    except Exception as e:    
        logging.error('%s | error in get_documents.save_daily_stats %s', (e, str(datetime.datetime.now())))        


def get_company_pr_solr_url(company_string, from_date=None, to_date=None):
	company_path = 'path_basename_s:*' + '\ '.join(company_string.split(' ')) + '*'
	params_solr = {'q':company_path.encode('utf8')}
	params_solr = urlencode(params_solr)
	
	if from_date:
		yy = str(from_date).split("-")[0]
		mm = str(from_date).split("-")[1]
		dd = str(from_date).split("-")[2]
    
		eyy = str(to_date).split("-")[0]
		emm = str(to_date).split("-")[1]
		edd = str(to_date).split("-")[2]
		
		search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+eyy+'-'+emm+'-'+edd+"T23:59:59Z]&fq=-id:*google_news_search*&fq=path0_s:%22Press%20releases%22&" + params_solr +'&wt=json&rows=100'
	else:
		search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=-id:*google_news_search*&fq=path0_s:%22Press%20releases%22&" + params_solr +'&wt=json&rows=100'
	#search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?" + params_solr +'&wt=json&rows=100'
	
	return search_url



#url_query =  'http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path0_s:%22PubMed_abstracts%22&fq=file_modified_dt:[2019-04-02T00:00:00Z%20TO%202019-04-10T23:59:59Z]&q=cleaned_html_content_txt%3A%22blood%22&rows=500'
#solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results('blood',url_query,'Diabetes','','', tags='tagged_entities_for_web', from_date=None, to_date=None)

#url_query = get_company_pr_solr_url('GlaxoSmithKline plc')
#solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results('', url_query, tags="tagged_entities_for_web")

#solr_results = get_solr_results_from_path('', "PubMed_abstracts/Archive/28/18/87/28188715.xml.gz")
#solr_results = get_solr_results_from_path('sickle cell disease', "PubMed_abstracts/Archive/30/04/43/30044354.xml.gz")
#solr_results = get_solr_results('multiple sclerosis', url_query, tags='tagged_entities_for_web')


#solr_results, daily_stats = get_daily_stats(datetime.date(2019, 2, 14))
#save_daily_stats(daily_stats)
        
        
#print(solr_results)

#url_query = get_solr_search_url(['multiple sclerosis'])
#solr_results = get_solr_results('multiple sclerosis', url_query, tags='tagged_entities_for_web')

#len(solr_results['shorter_sentences'][0])

#from_date = datetime.date.today() - datetime.timedelta(days=1)
#to_date = datetime.date.today()

#julias_alerts, julias_alert_ids = get_ome_alerts_of_user('julia.gray')
#clean_keyword_list, clean_keyword_title = get_keyword_list_from_ome_alert_id('124')
#clean_keyword_list, clean_keyword_title = get_search_params_list('124')
#ome_alert_results, url_query = get_ome_alert_results(clean_keyword_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

#print('')
#print('------------------------------------')
#print('')

#test_search_term_list, test_alert_title = get_search_params_list('39')
#test_ome_alert_results, test_url_query = new_get_ome_alert_results(test_search_term_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

#test_search_terms = {'keyphrase1':'multiple sclerosis', 'keyphrase2':'efficacy', 'source_select':'Press releases'}
#test_url = construct_solr_search_url('psoriasis', from_date=from_date)


#doc_text = ome_alert_results['tagged_document_text'][0]
#doc_tags = ome_alert_results['normalized_tags'][0]

#tagged_doc_text = add_tagged_entities.highlight_tags_from_list(doc_text, doc_tags)
