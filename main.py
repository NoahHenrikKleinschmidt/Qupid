import streamlit as st
import pandas as pd
import qpcr
from qpcr.Pipes import _Qupid_Blueprint
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
                                    placeholder = "control, conditionA, conditionB, ...",
                                    help = "The names for your groups of replicates (optional). Please, specify names comma-separated."
                                )
# pre-process group_names into list or set to None
group_names = None if group_names == "" else [i.strip() for i in group_names.split(",")]


# ----------------------------------------------------------------
# Generic settings like Filter type and Plotter...
# ----------------------------------------------------------------


filter_type = controls.radio(
                                "Select Filter", 
                                ["Range", "IQR", "None"], 
                                help = "Select which filter to apply before Delta-Delta-Ct computation. By default a Range Filter of +/- 1 around the group median is applied. Alternatively, an IQR filter of 1.5 x IQR around the median can be selected. If None is selected, no filtering will be done."
                            )
# pre-process filter_type
filter_type = None if filter_type == "None" else filter_type

chart_mode = controls.radio(
                                "Select Plotting Mode", 
                                ["interactive", "static"], 
                                help = "Select which type of plot to display. Either an interactive plot, or a static figure."

                            )


# ----------------------------------------------------------------
# Advances settings like Anchor...
# ----------------------------------------------------------------

more_controls_expander = controls.expander("Advanced Settings")

# anchor settings
anchor = more_controls_expander.selectbox(
                                            "Select anchor", 
                                            ["first", "grouped", "specified"],
                                            help = "The anchor is the intra-dataset reference for the first Delta-Ct. Using 'first' will choose the very first data entry, 'grouped' will use the first entry of each replicate group. Using 'specified' you may pass an externally computed numeric value."
                                            
                                        )

# preprocess anchor input (and allow specific entry)
if anchor == "specified":
    new_anchor = more_controls_expander.number_input("Specify an anchor value")
    anchor = new_anchor

# filtering inclusion range
preset_range = (-1.0, 1.0) if filter_type == "Range" else (-1.5, 1.5)
inclusion_range = more_controls_expander.slider(
                                                "Filter Inclusion Range",
                                                min_value = -10.0, 
                                                max_value = 10.0, 
                                                value = preset_range,
                                                step = 0.1,
                                                help = "Set the upper and lower boundries for the filter inclusion range. In case of RangeFilter this will be absolute numbers around the group median. In case of IQRFilter this will be factors n x IQR around the group median."
                                            )
# ...     'Select a range of values',
# ...     0.0, 100.0, (25.0, 75.0))



# =================================================================
# Run our analysis
# =================================================================

run_button = controls.button(
                                "Run Analysis",
                            )

def add_figure(fig, container, mode):
    """
    Adds a figure to a container...
    """
    if mode == "interactive":
        container.plotly_chart(fig, use_container_width = True)
    elif mode == "static":
        container.pyplot(fig, use_container_width = True)
        

if run_button and got_data:
    
    # setup pipeline
    pipeline = _Qupid_Blueprint()
    pipeline.replicates(replicates)
    pipeline.names(group_names)

    # setup custom Analyser and Normaliser...
    # actually, the Normaliser is a default one, 
    # but it would not work unless specifically added as well... 
    # (very curious)
    analyser = qpcr.Analyser()
    analyser.anchor(anchor)
    pipeline.Analyser(analyser)
    pipeline.Normaliser(qpcr.Normaliser())


    # setup filter
    if filter_type is not None:
        if filter_type == "Range":
            _filter = Filters.RangeFilter()
        elif filter_type == "IQR":
            _filter = Filters.IQRFilter()
        _filter.plotmode(chart_mode)
        pipeline.add_filters(_filter)
    
    # setup plotter
    _plotter = Plotters.PreviewResults(chart_mode)
    _plotter.params(show = False)
    pipeline.add_plotters(_plotter)

    # link the data
    pipeline.add_assays(assay_files)
    pipeline.add_normalisers(norm_files)

    # run pipeline
    pipeline.run()

    figures = pipeline.Figures()

    # ----------------------------------------------------------------
    # Get the Results to be nicely displayed...
    # ----------------------------------------------------------------
    
    # make new expanders for the figures

    if filter_type is not None: 
        filter_fig_expander = chart.expander("Filter Overview")
        pre_filter, post_filter = figures[:2]
        add_figure(pre_filter, filter_fig_expander, chart_mode)
        add_figure(post_filter, filter_fig_expander, chart_mode)

    preview_expander = chart.expander("Preview Results", expanded = True)
    preview = figures[-1]
    add_figure(preview, preview_expander, chart_mode)

    
    