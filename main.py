import streamlit as st
import pandas as pd
import qpcr
from copy import deepcopy
from pathlib import Path
import base64

from data_auxiliary import * 
from data_analysis import *

def main():
    st.title("qPCR-Analyser")
    st.markdown("""
        ---
        """)
    # get the input data files
    expander = st.expander("Upload your files here")
    e_col1, e_col2 = expander.columns(2)
    normaliser_file = e_col1.file_uploader("Select csv file for the normaliser", type=["csv"])
    target_file = e_col2.file_uploader("Select csv file(s) for your target runs", type=["csv"], accept_multiple_files=True)

    if target_file:
        target = import_data(target_file)
    if normaliser_file:
        norm_backup = deepcopy(normaliser_file)
        normaliser = import_data(normaliser_file)

    # setup the settings containers
    container = st.container()
    col1, col2 = container.columns(2)

    replicate_type = col1.selectbox("Select what type of replicates to use", ["equal replicates (n)", "specified (list)"])

    if replicate_type == "equal replicates (n)":
        replicates = col1.number_input("Define the number of replicates",
                            min_value = 1, step = 1)
    elif replicate_type == "specified (list)":
        replicates = col1.text_input("Provide a list of replicates (n) for each group")
        replicates = replicates.split(",")
        try: 
            replicates = [int(i) for i in replicates]
        except: pass
        
    anchor = col1.selectbox("Select what anchor to use", 
                    ["grouped", "first", "specified"])
    
    if anchor == "specified":
        new_anchor = col1.number_input("Specify the anchor value")
        if new_anchor:
            anchor = new_anchor
    elif anchor == "grouped":
        anchor = None

    groupnames = col1.text_input("Insert group names here (optional)")
    groupnames = get_group_names(groupnames)

    mode = col1.selectbox("Mode of analysis", ["replicate", "stats"])

    use_combined_normalisers = col1.checkbox("Uses combined normalisers")

    # setup the analysis controls in the second column 

    col2.markdown("## Available Analysis")
    col2.markdown("""
        ---
        """)

    # single delta ct analysis – basically normalisation within one data-file
    single_delta_ct = col2.button("Single Delta CT")
    if single_delta_ct:
        try: 
            var = target
        except: 
            st.error("At least one target file is required!")
        
        analysis = ["Single Delta CT", "$\Delta$CT"] #just as a label for the plot later on...

        if len(target) > 1:
            st.error("Single Delta CT only works on one target file!")
        else:
            result = single_dCt(target[0], replicates, mode, anchor=anchor, group_names = groupnames, export=False)
            result_filename = target_file[0].name
    
    # delta delta CT analysis 
    delta_delta_ct = col2.button("Delta Delta CT")
    if delta_delta_ct:
        try: 
            var = normaliser
            var = target
        except:
            st.error("Make sure you have both one normaliser and at least one target file selected!")

        analysis = ["Delta Delta CT", "$\Delta\Delta$CT"]

        data_files = []
        for i in target:
            data_files.append(deepcopy(i))
        
        # run names are automatically assigned from the file-names
        run_names = generate_run_names(target_file, normaliser_file)

        # when using combined normalisers we need to specially import the file so as to avoid the pre-processing 
        if use_combined_normalisers == True:
            norm = read_data(norm_backup)
            norm = norm.to_dict()
            normaliser = norm
        
        result = delta_dCt(data_files, replicates, deepcopy(normaliser), run_names, group_names=groupnames, anchor=anchor, export=False, use_combined_normalisers=use_combined_normalisers)

    # combine normalisers
    combine_normaliser = col2.button("Combine Normalisers")
    if combine_normaliser:
        try: 
            var = normaliser
            var = target
        except: 
            st.error("Please, select one normaliser and at least one target which shall be combined with the normalisers")
        
        to_combine = [normaliser]
        for i in target:
            to_combine.append(i)
        
        run_names = generate_normaliser_combined_names(normaliser_file,target_file)

        to_combine = preprocess_normalisers(to_combine, replicates, run_names, groupnames, anchor=anchor)
        result = combine_normalisers(to_combine)
        
        analysis = ["combine", ""]

    container2 = st.container()

    try: 
        
        container2.markdown("""
        ---
        """)
       
        if analysis[0] == "Single Delta CT":
            display_results_singleCT(container2, mode, analysis, result, result_filename)
        elif analysis[0] == "Delta Delta CT":
            print_figs = display_results_ddCT(container2, mode, analysis, result)            
            zip_result = convert_to_stats(mode, result)
            link = zip_compiler(zip_result, print_figs)
            st.markdown(link, unsafe_allow_html=True)

        elif analysis[0] == "combine":
            container.write(dict_to_frame(result), use_container_width=True)
            download_link = generate_download_link(result, "-".join(run_names), analysis)
            container.markdown(download_link, unsafe_allow_html=True)
        
    except Exception as e: pass #st.write(e)

    col2.markdown("""
    ---
    """)
    citation = """Kleinschmidt, N. (2021). qpcr-Analyser -- a web-based application to facilitate qPCR data analysis (Version 0.0.1) [Computer software]. https://github.com/NoahHenrikKleinschmidt/qpcr-Analyser.git"""
    col2.markdown("""
    When using this app to analyse your data, please cite: \n\n {}
    """.format(citation))
    


def convert_to_stats(mode, result):
    if mode == "stats":
        zip_result = {}
        for i in result:
            tmp = {i : qpcr.get_stats(result[i])}
            zip_result.update(tmp)
    else:
        zip_result = result
    return zip_result

def display_results_singleCT(container, mode, analysis, result, result_filename):
    if result:
        barplot = barchart(result, mode, analysis, result_filename)
        container.plotly_chart(barplot, use_container_width=True)
        container.write(dict_to_frame(result), use_container_width=True)
        download_link = generate_download_link(result, result_filename, analysis)
        container.markdown(download_link, unsafe_allow_html=True)

def display_results_ddCT(container, mode, analysis, result):
    if result:
        print_figs = []
        for d in result:
            fig = barchart(result[d], mode, analysis, d)
            container.plotly_chart(fig, use_container_width=True)
            f1 = print_chart(result[d], mode, analysis, d)
            print_figs.append(f1)
    return print_figs




def zip_compiler(result, print_figs):
    st.markdown("Your results have been compiled into a ZIP file:")
    now_string = datetime.now()
    now_string = now_string.strftime("%d%m%Y_%H%M%S")
    filename = "results_{}.zip".format(now_string)
    st.write(filename)
    with zipfile.ZipFile(filename, mode="w") as zf:
        # store figures
        for f in print_figs:
            name = "{}.jpg".format(f.axes[0].get_title())
            buf = io.BytesIO()
            f.savefig(buf, dpi=150)
            plt.close()
            zf.writestr(name, data=buf.getvalue())

        # store the dict entries as csv files
        for d in result:
            buf = io.StringIO()
            csv = result[d]
            csv = pd.DataFrame(csv)
            csv = csv.to_csv(buf)
            name = "{}.csv".format(d)
            zf.writestr(name, data=buf.getvalue())

        # now the download link
        #z = zf.read()
        b64 = base64.b64encode(zf.encode()).decode()
        st.write(b64)

        href = href = f'<a href="data:file/zip;base64,{b64}" download=\'{filename}.zip\'>\Click to download\</a>'
        st.markdown(href)

if __name__=="__main__":
    main()