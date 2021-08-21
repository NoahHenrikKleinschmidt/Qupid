from os import remove
import pandas as pd
import  qpcr
import qpcr.Analysis as qA 
from copy import deepcopy
import base64
import streamlit as st
import zipfile
import io
import matplotlib.pyplot as plt
import statistics as stat
from datetime import datetime 

# all of the import data, read data and open file work together, let's not question why...
def import_data(data_obj):
    data = read_data(data_obj)
    if isinstance(data, list):
        overall = []
        for i in data:
            overall.append(open_file(i))
        return overall
    else:
        data = open_file(data)
        return data

def read_data(data_obj):
    if isinstance(data_obj, list):
        overall = []
        for d in data_obj:
            obj1 = deepcopy(d)
            tmp1 = pd.read_csv(d, delimiter=";")
            tmp2 = pd.read_csv(obj1)
            cols1 = [i for i in tmp1.columns]
            cols2 = [i for i in tmp2.columns]
            if len(cols1) > len(cols2):
                overall.append(tmp1)
            else: 
                overall.append(tmp2)
        return overall
    else: 
        obj1 = deepcopy(data_obj) #this deepcopy nonsense is actually recuired as the data_obj appears to get "used up" once read_csv has been performed...
        tmp1 = pd.read_csv(data_obj, delimiter=";")
        tmp2 = pd.read_csv(obj1)
        cols1 = [i for i in tmp1.columns]
        cols2 = [i for i in tmp2.columns]
        if len(cols1) > len(cols2):
            return tmp1
        else:
            return tmp2



def open_file(dataframe, export='dict'):
    contents = convert_to_lines(dataframe)

    if ";" in contents[0]:
        contents = [i.replace(';', ',') for i in contents]
    contents = [i.replace('\n', '') for i in contents]

    #now split the raw lines into lists each
    contents = [i.split(',') for i in contents]
    
    #now remove the unnecessary lines
    temp = []
    for i in contents:
        if i[1] != '':
            temp.append(i)
    contents = temp
    if export == 'list':
        return contents
    elif export == 'dict':
        new_dict = {
            'Sample' : [i[0] for i in contents[0:]],
            'Mean Ct' : [i[1] for i in contents[0:]],
            #'Stdev' : [i[2] for i in contents[1:]],

        }
        return new_dict

def convert_to_lines(dataframe):
    idx = 0
    lines = []
    while True:
        try: 
            string = ""
            for i in dataframe.keys():
                string = "{},{}".format(string, dataframe[i][idx])
            lines.append(string[1:])    
            idx += 1
        except: 
            break
    return lines

# process the group names, if provided...

def get_group_names(group_name_field):
    if group_name_field == "":
        group_names = None
    else: 
        group_names = group_name_field.split(",")
        group_names = [i.strip() for i in group_names]
    return group_names

# re-convert data-dict from results into displayable dataframe

def dict_to_frame(data_dict):
    frame = pd.DataFrame(data_dict)
    return frame

# generate download link for the results csv file
def generate_download_link(results_dict, filename, analysis):
    result_frame = pd.DataFrame(results_dict)
    csv_file = result_frame.to_csv(index=False)
    b64 = base64.b64encode(csv_file.encode()).decode()
    filename = "{}_{}.csv".format(filename, analysis[0])
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download Results as CSV</a>'
    return href

# generate a zip download link

def generate_zip_download_link(zip):
    z = zip.read()
    filename = "results_{}.zip".format(datetime.now().strftime(("%d%m%Y_%H%M%S")))
    b64 = base64.b64encode(z.encode()).decode()
    href = f'<a href="data:file/zip;base64,{b64}" download="{filename}">Download Results as ZIP</a>'
    return href

# generate run_names
def generate_run_names(target_files, normaliser):
    norm_name = remove_suffix(normaliser)
    target_names = [remove_suffix(i) for i in target_files]
    run_names = ["{}_rel_{}_ddct".format(i, norm_name) for i in target_names]
    return run_names

def remove_suffix(file):
    norm_name = file.name
    norm_name = norm_name.split(".")
    norm_name = norm_name[0]
    return norm_name


    
# combine normalisers functions (these will take the place of the qpcr functions)

# not yet edited! 


#if several normalisers should be used they first have to be pre-processed to get their Delta_Ct values before they can be combined using combine_normalisers
def preprocess_normalisers(normalisers:list, replicates, run_names, group_names=None, anchor=None, return_type='list'):
    normalisers_dict = {}
    ndx = 0
    for norm in normalisers:
        try: 
            name = run_names[ndx]
        
            tmp = norm
            tmp = qpcr.group_samples(tmp, replicates=replicates)
            if group_names is not None:
                tmp = qpcr.rename_groups(tmp, new_names=group_names)
            tmp = qpcr.Delta_Ct(tmp, anchor=anchor)
            tmp = {name : tmp}
            normalisers_dict.update(tmp)
            ndx +=1
            if return_type == 'list':
                temp = []
                for i in run_names:
                    temp.append(normalisers_dict[i])
                normalisers_dict = list(temp)
        except: pass    
    return normalisers_dict

#if several normalisers should be averaged, use combine_normalisers
def combine_normalisers(normalisers:list):
    combined_normaliser = {}
    keys = list(normalisers[0].keys()) #get all groupings
    for k in keys:
        temp = []
        for norm in normalisers:
            length = len(norm[k])
            assert isinstance(norm[k][0], float), "norm[k][0] is not a simple number but: {} ... \nAre you sure you already performed qpcr.Delta_Ct on your normaliser?".format(norm[k][0])
            for i in norm[k]:
                temp.append(i)
        temp = {k : [stat.mean(temp) for i in range(length)]} #we must conserve dimensionality...
        combined_normaliser.update(temp)
    return combined_normaliser

# generate run_names
def generate_normaliser_combined_names(normaliser_file, target_file):
    names = [remove_suffix(normaliser_file)]
    for t in target_file:
        names.append(remove_suffix(t))
    return names

if __name__ == '__main__':
    n1 = "/Users/NoahHK/OneDrive - Universitaet Bern/Bachelor Project/qPCR/Week 5/16.03.21/Pre-Processed/28S.csv"
    n2 = "/Users/NoahHK/OneDrive - Universitaet Bern/Bachelor Project/qPCR/Week 5/16.03.21/Pre-Processed/HNRNPL_nmd.csv"
    n3 = "/Users/NoahHK/OneDrive - Universitaet Bern/Bachelor Project/qPCR/Week 5/16.03.21/Pre-Processed/HNRNPL_prot.csv"

    prepped = qpcr.preprocess_normalisers([n1, n2, n3], 6, ["28S", "TRA_NMD", "HNprot"], anchor="first")
    normed = qpcr.combine_normalisers(prepped)
    print(normed)