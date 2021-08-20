from numpy.core.fromnumeric import transpose
from data_auxiliary import *
import qpcr 
import qpcr.Analysis as qA 
import pandas as pd 
import plotly.express as px
import matplotlib.pyplot as plt

def single_dCt(data_file, replicates, mode = 'replicate', transpose=True, export=True, group_names=None, stats = ['avg', 'stdv'], anchor = None, dCt_exp = True, exportname_addon=None):
    contents = data_file

    grouped_dict = qpcr.group_samples(sample_dict=contents, replicates=replicates)
    deltaCt_dict = qpcr.Delta_Ct(grouped_dict=grouped_dict, anchor=anchor, exp=dCt_exp)
    if group_names is not None:
        if group_names == "auto":
            deltaCt_dict = qpcr.rename_groups(sample_dict=deltaCt_dict, new_names=contents['Sample'])
        else:
            deltaCt_dict = qpcr.rename_groups(sample_dict=deltaCt_dict, new_names=group_names) 
    if mode == 'replicate':
        export_dict = deltaCt_dict
    elif mode == 'stats':
        export_dict = qpcr.get_stats(deltaCt_dict, export=stats)
    
    if export == True:
        #new_file = '{}_SingleCT.csv'.format(data_file.replace('.csv', ''))
        if exportname_addon is None: 
            addon = ""
        else: 
            addon = "{}_".format(exportname_addon)
        new_file = "{}_{}SingleDelta_Ct.csv".format(data_file.replace('.csv', ''), addon)
            
        qpcr.export_to_csv(data=export_dict, filename=new_file, transpose=transpose)
        print('Exported SingleDelta_Ct analysis to:\n{}'.format(new_file))
    else:
        return export_dict





def delta_dCt(data_files:list, replicates, normaliser, run_names, mode = 'replicate',  group_names=None, transpose=True, stats = ['avg', 'stdv'], anchor = None, dCt_exp = True, export=True, exportname_addon=None, export_location=None, use_combined_normalisers=False):
    samples_dict = {}
    i = 0
    for f in data_files:
        key = 'Group {}'.format(i)
        delta_Cts = single_dCt(f, replicates=replicates, mode='replicate',
                                    transpose=transpose, export=False,
                                    group_names=group_names, stats=stats, anchor=anchor, dCt_exp=dCt_exp)
        tmp = { key : delta_Cts }
        samples_dict.update(tmp)
        i+=1


    #rename dict to the gene names specified
    samples_dict = qpcr.rename_groups(samples_dict, new_names=run_names)
    
    
    keys = list(samples_dict.keys())
    
    if isinstance(normaliser, dict):
        normaliser_dict = normaliser
    else: 
        if normaliser not in keys:
            print('No match for the normaliser could be found! Make sure to have the normaliser name also specified identically in the gene_names.')
            return None
        normaliser_dict = samples_dict[normaliser]
        keys.remove(normaliser) #remove normaliser from list of samples
            
    if use_combined_normalisers == False:
        normaliser_dict = single_dCt(normaliser_dict, replicates=replicates, mode='replicate',
                                        transpose=transpose, export=False,
                                        group_names=group_names, stats=stats, anchor=anchor, dCt_exp=dCt_exp)

    #now normalise relative to normaliser
    normalised_dict = {}
    for k in keys:
        temp = qpcr.normalise(normaliser=normaliser_dict, sample=samples_dict[k])
        temp = {k : temp}
        normalised_dict.update(temp)
    
    if mode == "stats":
        stats_dict = {}
        for k in normalised_dict.keys():
            normdict = normalised_dict[k]
            tmp = qpcr.get_stats(normdict, export=stats)
            stats_dict.update({k : tmp})
        normalised_dict = stats_dict

    if export==True:
        #now save all normalised Delta_Delta Ct Values to new files
        file_index = 0
        for k in normalised_dict.keys():
            
            if export_location is None:
                file_location = data_files[file_index].split("/")
                file_location = "/".join(file_location[0:len(file_location)-1])
            else: 
                file_location = export_location
            
            if exportname_addon is None: 
                addon = ""
            else: 
                addon = "{}_".format(exportname_addon)
            new_file = "{}/{}_{}DeltaDelta_Ct.csv".format(file_location, k, addon)
            
            qpcr.export_to_csv(data=normalised_dict[k],filename=new_file, transpose=transpose)
            print('Exported DeltaDelta_Ct analysis to:\n{}'.format(new_file))
        
    return normalised_dict



def barchart(data_dict, mode, analysis, filename):
    labels, heights, yerrs = preprocess_plot_data(data_dict)

    fig = px.bar(x=labels, y=heights, error_y=yerrs)

    fig.update_layout(
    title="{} - {}".format(analysis[0], filename),
    xaxis_title="Condition",
    yaxis_title=analysis[1],)

    return fig

def preprocess_plot_data(data_dict):
    data = qpcr.get_stats(data_dict)

    labels = [i for i in data.keys() if i != "Legend"]
    heights = [data[i][0] for i in data.keys()]
    heights = heights[1:]
    yerrs = [data[i][1] for i in data.keys()]
    yerrs = yerrs[1:]
    return labels,heights,yerrs

def print_chart(data_dict, mode, analysis, filename):
    labels,heights,yerrs = preprocess_plot_data(data_dict)
    fig,ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels,heights, color="cornflowerblue", edgecolor="royalblue", width=0.7)
    ax.errorbar(labels, heights, yerrs, fmt=".",markersize=0, capsize=5, color="black")
    plt.ylabel(analysis[1], fontsize = 15)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.title(filename)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    return fig

if __name__ == '__main__':
    test1 = {
        "Legend" : ["Avg", "StDev"],
        "Group 1" : [1, 0.5],
        "Group 2" : [3, 0.32],
        "Group 3" : [5, 0.67],
        "Group 4" : [2, 0.34]
    }

    test2 = {

       "Group 1" : [1, 0.5, 2, 3.4],
        "Group 2" : [3, 0.32, 2, 3.4],
        "Group 3" : [5, 0.67, 2, 3.4],
        "Group 4" : [2, 0.34, 2, 3.4]
    }
        
    fig = barchart(test2, "replicate", "something")
    fig.show()