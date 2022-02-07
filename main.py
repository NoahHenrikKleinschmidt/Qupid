import streamlit as st
import pandas as pd
import qpcr
from qpcr.Pipes import BasicPlus
import qpcr.Filters as Filters
import qpcr.Plotters as Plotters

st.set_page_config(
                        page_title="Qupid",
                        page_icon="📈",
                        layout="wide",
                        initial_sidebar_state = "collapsed",
                    )

st.title("Qupid")
st.markdown("### A web-application to facilitate Delta-Delta-Ct analysis")

# setup layout

# =================================================================
# upload input files for normalisers and assays
# =================================================================

files_expander = st.expander("Input Data Files", expanded = True)
assay_files_col, norm_files_col = files_expander.columns(2)

assay_files = assay_files_col.file_uploader(
                                            "Upload Input Assays", 
                                            type = "csv",
                                            accept_multiple_files = True,
                                            help = "Upload csv files here for all assays that shall be treated as samples-of-interest.\nPlease, upload a separate file for each assay."
                                        )

norm_files = norm_files_col.file_uploader(
                                            "Upload Normaliser Assays", 
                                            type = "csv",
                                            accept_multiple_files = True,
                                            help = "Upload csv files here for all assays that shall be treated as normalisers.\nPlease, upload a separate file for each assay."
                                        )

# check if data is supplied
got_data = assay_files is not None and norm_files is not None

# =================================================================
# Control settings for experiment
# =================================================================

controls_panel = st.container()
controls, chart = controls_panel.columns((10,20))

# setting up controls
replicates = controls.number_input(
                                    "Number of Replicates per group",
                                    min_value = 1,
                                    value = 3,
                                    step = 1,
                                    help = "The number of replicates in each group of replicates. Note, this assumes there are always the same number of replicates. If there are outliers in your data, please, keep these, to preserve dimensionality. Outliers will be filtered out by the app itself."
                                )

group_names = controls.text_input(
                                    "Names of Replicate groups",
                                    placeholder = "control, conditionA, conditionB",
                                    help = "The names for your groups of replicates (optional). Please, specify names comma-separated."
                                )
# pre-process group_names into list or set to None
group_names = None if group_names == "" else [i.strip() for i in group_names.split(",")]

filter_type = controls.radio(
                                "Select Filter", 
                                ["Range", "IQR", "None"], 
                                help = "Select which filter to apply before Delta-Delta-Ct computation. By default a Range Filter of +/- 1 around the group median is applied. Alternatively, an IQR filter of 1.5 x IQR around the median can be selected. If None is selected, no filtering will be done."
                            )

chart_mode = controls.radio(
                                "Select Plotting Mode", 
                                ["interactive", "static"], 
                                help = "Select which type of plot to display. Either an interactive plot, or a static figure."

                            )

run_button = controls.button(
                                "Run Analysis",
                            )


# =================================================================
# Run our analysis
# =================================================================


if run_button and got_data:
    
    # setup pipeline
    pipeline = BasicPlus()
    pipeline.replicates(replicates)
    pipeline.names(group_names)

    # setup filter
    if filter_type != "None":
        if filter_type == "Range":
            _filter = Filters.RangeFilter()
        elif filter_type == "IQR":
            _filter = Filters.IQRFilter()
        pipeline.add_filters(_filter)
    
    # setup plotter
    _plotter = Plotters.PreviewResults(chart_mode)
    pipeline.add_plotters(_plotter)

    # link the data
    pipeline.add_assays(assay_files)
    pipeline.add_normalisers(norm_files)

    # run pipeline
    pipeline.run()

    # get results
    results = pipeline.get()
    chart.write(results)