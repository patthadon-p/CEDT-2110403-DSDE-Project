# External dependencies
import streamlit as st

# Project modules
from components.data_loader import TraffyDataLoader
from components.filter_logic import TraffyFilter
from matplotlib import rcParams
from pages.analysis_page import render_analysis_page
from pages.line_page import render_line_chart_page
from pages.map_page import render_map_visualizer
from pages.predictor_page import render_prediction_page

# Configuration
rcParams["font.family"] = "Tahoma"

# Streamlit page configuration
st.set_page_config(layout="wide", page_title="Bangkok Traffy Unified Dashboard")

# --- REVISED CSS TO HIDE ALL DEFAULT NAVIGATION/UI ---
st.markdown(
    """
    <style>
    /* Hides the Streamlit Header/Toolbar above the main content area */
    header {
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* Hides the "Deploy/Settings" (three-dot) menu button in the top right */
    #MainMenu {
        visibility: hidden !important;
    }
    
    /* Hides the main "Page Selector" dropdown/navigation area in the sidebar */
    /* This targets the specific div that contains the native multi-page selector */
    div[data-testid="stSidebarNav"] {
        display: none;
    }

    /* Hides the "Made with Streamlit" footer */
    footer {
        visibility: hidden !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# MAIN APP CONTROLLER
# -----------------------------------------------------------------------------
class TraffyApp:
    def __init__(self):
        # Data Loading
        self.df_cleansed = TraffyDataLoader.load_cleansed()
        self.df_score = TraffyDataLoader.load_scores()
        self.pop_data = TraffyDataLoader.load_pop_data()
        self.filter_manager = TraffyFilter(self.df_cleansed)

    def run(self):
        # Navigation and Filter Setup
        selected_page, type_filter, start_date, end_date = (
            self.filter_manager.render_sidebar()
        )

        # Data Filtering
        # Filtered by date AND selected type (used for maps, daily counts, score analysis)
        df_filtered = self.filter_manager.apply_filters(
            filter_type=True, filter_date=True
        )

        # Filtered by date only (used for correlation/scatter matrix where all types are needed)
        df_time_only = self.filter_manager.apply_filters(
            filter_type=False, filter_date=True
        )

        # Content Rendering based on Navigation
        if selected_page == "Map":
            render_map_visualizer(
                self.df_cleansed, self.pop_data, type_filter, start_date, end_date
            )
        elif selected_page == "Scatter":
            # Pass df_filtered and df_time_only
            render_analysis_page(df_filtered, self.df_score, type_filter, df_time_only)
        elif selected_page == "Line":
            # Pass df_filtered (for the new daily counts chart) and type_filter
            render_line_chart_page(self.df_cleansed, df_filtered, type_filter)
        elif selected_page == "Predictor":
            render_prediction_page()


if __name__ == "__main__":
    app = TraffyApp()
    app.run()
