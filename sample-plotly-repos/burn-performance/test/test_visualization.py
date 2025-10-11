import pytest
from unittest.mock import patch, MagicMock, Mock, call

import pandas as pd
from dash import no_update
import plotly.graph_objects as go


from utils.visualization import (
    update_fetch_and_exposure_graph_combined,
    process_callout_metrics,
)
from utils.viz_functions import add_year_legend_traces, add_snapshot_date_lines, add_color_bar, get_color_for_date, rgb_to_string

from utils.exception_handlers import TM1PlotError, CalloutError

# Test update_fetch_no_target_value
def test_update_fetch_no_target_value(mocker, mock_redis):
    """Test update_fetch_and_exposure_graph_combined with no target value"""
    
    # Mock fetch_and_store_data to avoid database calls
    mocker.patch('utils.data_processors.fetch_and_store_data', return_value=None)
    
    # Mock create_exposure_bar_plot to avoid database calls
    mocker.patch('utils.viz_functions.create_exposure_bar_plot', return_value=None)
    
    # Call the function with no target value
    _, _, _, style_main, style_alert, alert_note, _ = update_fetch_and_exposure_graph_combined(
        selected_clusters=[], target_value=None, mask="Unmasked", monitoring_date="2023-01-01", 
        consolidated_name="test_co", selected_dates=None
    )
    
    # Check that the function behaves correctly with no target value
    assert style_main == {"height": "100%", "display": "none"}
    assert style_alert == {"height": "100%", "display": "block"}
    assert "Oops! It looks like you have not selected any target values" in alert_note

# Test update_fetch_no_properties
def test_update_fetch_no_properties(mocker, mock_redis):
    """Test update_fetch_and_exposure_graph_combined with no schema properties"""
    
    # Mock parse_schema_properties to return None
    mocker.patch('utils.visualization.parse_schema_properties', return_value=({}, "test_co"))
    
    # Mock fetch_and_store_data to avoid database calls
    mocker.patch('utils.data_processors.fetch_and_store_data', return_value=None)
    
    # Mock create_exposure_bar_plot to avoid database calls
    mocker.patch('utils.viz_functions.create_exposure_bar_plot', return_value=None)
    
    # Call the function with target value but no properties
    fig, dev_since, dev, style_main, style_alert, alert_note, _ = update_fetch_and_exposure_graph_combined(
        selected_clusters=[], target_value=["tgt"], mask="Unmasked", 
        monitoring_date="2023-01-01", consolidated_name="test_co", selected_dates=None
    )
    
    # Check that the function returns expected values when no properties are found
    assert fig == no_update
    assert style_main == {"height": "100%", "display": "none"}
    assert style_alert == {"height": "100%", "display": "block"}

# Test process_callouts_exception
def test_process_callouts_exception(mocker, mock_dash_logger, mock_redis):
    """Test exception handling in process_callout_metrics"""
    
    # Mock the logger (its methods) on the imported instance
    import utils.visualization as viz
    viz.dash_logger.error = mock_dash_logger.error
    
    # Force an exception by directly mocking parse_schema_properties
    with patch('utils.visualization.parse_schema_properties') as mock_parse:
        mock_parse.side_effect = Exception("Bad Error")
        
        with pytest.raises(CalloutError) as exc_info:
            process_callout_metrics((0.1,0.1), 1, [], ["tgt"], "date", "name", 90)
            
        # Check that the error message contains the expected text
        assert "Error while fetching/calculating the callout metrics" in str(exc_info.value)
        mock_dash_logger.error.assert_called_once()

# Test process_callouts_none_values
def test_process_callouts_none_values(mocker):
    """Test process_callout_metrics handles None values correctly"""
    
    # Skip using the redis_mock fixture as we're directly overriding everything
    
    # Create a comprehensive mock properties dict with the required structure
    mock_properties = ({
        "current_snapshotDate": "2023-01-01",
        "monitoring_snapshotDate": {
            "name": "monitoring_date", 
            "values": ["2023-01-01"]
        },
        "targets": {
            "tgt": {
                "numerator_weight": "num_weight",
                "cpp": "cpp_val",
                "restated": "restated_val",
                "baseline": "baseline_val"
            }
        },
        "cluster": "cluster_col"
    }, "test_path")
    
    # Mock ALL functions used in the function under test
    # This is a simpler strategy than trying to patch import paths
    
    # Mock visualization.parse_schema_properties
    mocker.patch('utils.visualization.parse_schema_properties', return_value=mock_properties)
    
    # Mock format_display_values
    format_mock = mocker.patch('utils.ui_helpers.format_display_values')
    format_mock.side_effect = lambda x, *args, **kwargs: str(x) if x is not None else " - "
    
    # Mock the financial impact calls
    mocker.patch('utils.dbx_utils.get_total_financial_impact', return_value=[{'financial_impact': None}])
    mocker.patch('utils.dbx_utils.get_agg_pval', return_value=None)
    
    # Mock helper functions
    mocker.patch('utils.helper_functions.generate_significant_text', return_value=" ")
    mocker.patch('utils.helper_functions.extract_clusters', return_value=[])
    
    # Mock dash_logger to avoid actual logging
    mocker.patch('utils.visualization.dash_logger', MagicMock())
    
    # Call the function with None values
    with patch('utils.visualization.get_total_financial_impact', return_value=[{'financial_impact': None}]):
        with patch('utils.visualization.get_agg_pval', return_value=None):
            _, fin_impact, act, exp, res, sig_text = process_callout_metrics(
                (None, None), None, [], ["tgt"], "2023-01-01", "test_co", 95
            )
    
    # Verify handling of None values
    assert act == " - "
    assert exp == " - "
    assert res == " - "
    assert fin_impact == " - "
    assert sig_text == " " 




# Color points as provided
color_points = [
    (0.0, (112, 99, 137)),  # Matte purple
    (0.125, (70, 100, 170)),  # Indigo blue
    (0.25, (131, 178, 208)),  # Original light blue
    (0.375, (149, 218, 182)),  # Original mint green
    (0.5, (200, 209, 150)),  # Olive
    (0.625, (242, 230, 177)),  # Original pale yellow
    (0.75, (233, 185, 155)),  # Peach
    (0.875, (220, 133, 128)),  # Original soft coral
    (1.0, (187, 97, 109)),  # Raspberry
]

class TestAddYearLegendTraces:
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.mock_fig = Mock()
        self.min_date = pd.Timestamp('2020-01-01')
        self.max_date = pd.Timestamp('2023-12-31')
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_empty_dataframe(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with empty DataFrame"""
        df_empty = pd.DataFrame(columns=['snapshotDate'])
        
        result = add_year_legend_traces(
            self.mock_fig, df_empty, self.min_date, self.max_date, color_points
        )
        
        # Should return figure without adding any traces
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
        mock_get_color_for_date.assert_not_called()
        mock_rgb_to_string.assert_not_called()
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_single_year(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with single year of data"""
        # Create DataFrame with single year
        dates = pd.date_range('2022-01-01', periods=3, freq='M')
        df_single_year = pd.DataFrame({'snapshotDate': dates})
        
        # Mock return values
        mock_get_color_for_date.return_value = (255, 0, 0)
        mock_rgb_to_string.return_value = 'rgb(255,0,0)'
        
        result = add_year_legend_traces(
            self.mock_fig, df_single_year, self.min_date, self.max_date, color_points
        )
        
        # Should add exactly one trace for year 2022
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        # Verify the trace properties
        call_args = self.mock_fig.add_trace.call_args[0][0]
        assert isinstance(call_args, go.Scatter)
        assert call_args.name == "2022"
        assert call_args.legendgroup == "year_2022"
        assert call_args.showlegend == True
        assert call_args.line['color'] == 'rgb(255,0,0)'
        assert call_args.line['width'] == 2
        
        # Verify color calculation was called with first date
        mock_get_color_for_date.assert_called_once_with(
            dates[0], self.min_date, self.max_date, color_points
        )
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_multiple_years(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with multiple years of data"""
        # Create DataFrame with multiple years
        dates_2021 = pd.date_range('2021-01-01', periods=2, freq='M')
        dates_2022 = pd.date_range('2022-06-01', periods=3, freq='M')
        dates_2023 = pd.date_range('2023-01-01', periods=1, freq='M')
        
        all_dates = dates_2021.tolist() + dates_2022.tolist() + dates_2023.tolist()
        df_multi_year = pd.DataFrame({'snapshotDate': all_dates})
        
        # Mock return values
        mock_get_color_for_date.side_effect = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        mock_rgb_to_string.side_effect = ['rgb(255,0,0)', 'rgb(0,255,0)', 'rgb(0,0,255)']
        
        result = add_year_legend_traces(
            self.mock_fig, df_multi_year, self.min_date, self.max_date, color_points
        )
        
        # Should add three traces (one for each year)
        assert result == self.mock_fig
        assert self.mock_fig.add_trace.call_count == 3
        
        # Verify each trace was added with correct year
        call_args_list = [call[0][0] for call in self.mock_fig.add_trace.call_args_list]
        years = [trace.name for trace in call_args_list]
        assert sorted(years) == ["2021", "2022", "2023"]
        
        # Verify colors were calculated for first date of each year
        expected_calls = [
            call(dates_2021[0], self.min_date, self.max_date, color_points),
            call(dates_2022[0], self.min_date, self.max_date, color_points),
            call(dates_2023[0], self.min_date, self.max_date, color_points),
        ]
        mock_get_color_for_date.assert_has_calls(expected_calls)
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_trace_properties(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test that trace properties are set correctly"""
        dates = pd.date_range('2022-01-01', periods=1, freq='M')
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_get_color_for_date.return_value = (100, 150, 200)
        mock_rgb_to_string.return_value = 'rgb(100,150,200)'
        
        add_year_legend_traces(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Verify trace properties in detail
        trace = self.mock_fig.add_trace.call_args[0][0]
        
        # Check all required properties
        assert trace.x == (None,)  # Plotly converts [None] to tuple
        assert trace.y == (None,)  # Plotly converts [None] to tuple
        assert trace.mode == "lines"
        assert trace.name == "2022"
        assert trace.line['color'] == 'rgb(100,150,200)'
        assert trace.line['width'] == 2
        assert trace.legend == "legend"  # Plotly sets this to "legend" by default
        assert trace.legendgroup == "year_2022"
        assert trace.showlegend == True
        assert trace.hoverinfo == "skip"
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_years_sorted_correctly(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test that years are processed in sorted order"""
        # Create DataFrame with years in random order
        dates_2023 = pd.date_range('2023-01-01', periods=1, freq='M')
        dates_2021 = pd.date_range('2021-01-01', periods=1, freq='M')
        dates_2022 = pd.date_range('2022-01-01', periods=1, freq='M')
        
        # Mix the order
        all_dates = dates_2023.tolist() + dates_2021.tolist() + dates_2022.tolist()
        df_unsorted = pd.DataFrame({'snapshotDate': all_dates})
        
        mock_get_color_for_date.return_value = (255, 255, 255)
        mock_rgb_to_string.return_value = 'rgb(255,255,255)'
        
        add_year_legend_traces(
            self.mock_fig, df_unsorted, self.min_date, self.max_date, color_points
        )
        
        # Verify traces were added in sorted year order
        call_args_list = [call[0][0] for call in self.mock_fig.add_trace.call_args_list]
        years = [trace.name for trace in call_args_list]
        assert years == ["2021", "2022", "2023"]
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_year_with_no_data_after_filtering(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test edge case where year_data becomes empty after filtering"""
        # Create a DataFrame where all dates are NaT (which will be filtered out)
        df = pd.DataFrame({'snapshotDate': [pd.NaT, pd.NaT, pd.NaT]})
        
        result = add_year_legend_traces(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should return figure without adding traces since all dates are NaT
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
        mock_get_color_for_date.assert_not_called()
        mock_rgb_to_string.assert_not_called()
    
    def test_dataframe_without_snapshotdate_column(self):
        """Test behavior when DataFrame doesn't have snapshotDate column"""
        df_no_date = pd.DataFrame({'other_column': [1, 2, 3]})
        
        with pytest.raises(KeyError):
            add_year_legend_traces(
                self.mock_fig, df_no_date, self.min_date, self.max_date, color_points
            )
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_invalid_dates(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with invalid/NaN dates"""
        dates = [pd.Timestamp('2022-01-01'), pd.NaT, pd.Timestamp('2022-03-01')]
        df_with_nan = pd.DataFrame({'snapshotDate': dates})
        
        mock_get_color_for_date.return_value = (255, 0, 0)
        mock_rgb_to_string.return_value = 'rgb(255,0,0)'
        
        # This should handle NaT values gracefully
        result = add_year_legend_traces(
            self.mock_fig, df_with_nan, self.min_date, self.max_date, color_points
        )
        
        # Should still process the valid year
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        assert trace.name == "2022"
    
    @patch('utils.viz_functions.get_color_for_date', side_effect=Exception("Color calculation failed"))
    @patch('utils.viz_functions.rgb_to_string')
    def test_color_calculation_error(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior when color calculation fails"""
        dates = pd.date_range('2022-01-01', periods=1, freq='M')
        df = pd.DataFrame({'snapshotDate': dates})
        
        with pytest.raises(Exception, match="Color calculation failed"):
            add_year_legend_traces(
                self.mock_fig, df, self.min_date, self.max_date, color_points
            )


class TestAddSnapshotDateLines:
    """Test cases for add_snapshot_date_lines function"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.mock_fig = Mock()
        self.min_date = pd.Timestamp('2020-01-01')
        self.max_date = pd.Timestamp('2023-12-31')
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_empty_dataframe(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with empty DataFrame"""
        df_empty = pd.DataFrame(columns=['snapshotDate', 'obsAge', 'cum_actual', 'obsDate'])
        
        result = add_snapshot_date_lines(
            self.mock_fig, df_empty, self.min_date, self.max_date, color_points
        )
        
        # Should return figure without adding any traces
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
        mock_get_color_for_date.assert_not_called()
        mock_rgb_to_string.assert_not_called()
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_single_snapshot_date(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with single snapshot date"""
        dates = [pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1],
            'cum_actual': [100.5],
            'obsDate': [pd.Timestamp('2022-02-01')]
        })
        
        # Mock return values
        mock_get_color_for_date.return_value = (255, 0, 0)
        mock_rgb_to_string.return_value = 'rgb(255,0,0)'
        
        result = add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should add exactly one trace
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        # Verify the trace properties
        trace = self.mock_fig.add_trace.call_args[0][0]
        assert isinstance(trace, go.Scatter)
        assert trace.mode == "lines"
        assert trace.name == "2022"
        assert trace.legendgroup == "year_2022"
        assert trace.showlegend == False
        assert trace.opacity == 0.35
        assert trace.line['width'] == 1.35
        assert trace.line['color'] == 'rgb(255,0,0)'
        
        # Verify color calculation was called
        mock_get_color_for_date.assert_called_once_with(
            dates[0], self.min_date, self.max_date, color_points
        )
        mock_rgb_to_string.assert_called_once_with((255, 0, 0))
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_multiple_snapshot_dates_single_year(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with multiple snapshot dates in single year"""
        dates = [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-06-01'), pd.Timestamp('2022-12-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1, 2, 3],
            'cum_actual': [100.5, 200.5, 300.5],
            'obsDate': [pd.Timestamp('2022-02-01'), pd.Timestamp('2022-07-01'), pd.Timestamp('2023-01-01')]
        })
        
        # Mock return values
        mock_get_color_for_date.side_effect = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        mock_rgb_to_string.side_effect = ['rgb(255,0,0)', 'rgb(0,255,0)', 'rgb(0,0,255)']
        
        result = add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should add three traces (one for each snapshot date)
        assert result == self.mock_fig
        assert self.mock_fig.add_trace.call_count == 3
        
        # Verify all traces have the same year name and legendgroup
        call_args_list = [call[0][0] for call in self.mock_fig.add_trace.call_args_list]
        for trace in call_args_list:
            assert trace.name == "2022"
            assert trace.legendgroup == "year_2022"
            assert trace.showlegend == False
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_multiple_years(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with multiple years of data"""
        dates_2021 = [pd.Timestamp('2021-01-01'), pd.Timestamp('2021-06-01')]
        dates_2022 = [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-06-01')]
        all_dates = dates_2021 + dates_2022
        
        df = pd.DataFrame({
            'snapshotDate': all_dates,
            'obsAge': [1, 2, 1, 2],
            'cum_actual': [100.5, 200.5, 150.5, 250.5],
            'obsDate': [pd.Timestamp('2021-02-01'), pd.Timestamp('2021-07-01'), 
                       pd.Timestamp('2022-02-01'), pd.Timestamp('2022-07-01')]
        })
        
        # Mock return values
        mock_get_color_for_date.side_effect = [(255, 0, 0), (128, 0, 0), (0, 255, 0), (0, 128, 0)]
        mock_rgb_to_string.side_effect = ['rgb(255,0,0)', 'rgb(128,0,0)', 'rgb(0,255,0)', 'rgb(0,128,0)']
        
        result = add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should add four traces (two per year)
        assert result == self.mock_fig
        assert self.mock_fig.add_trace.call_count == 4
        
        # Verify traces are grouped by year
        call_args_list = [call[0][0] for call in self.mock_fig.add_trace.call_args_list]
        year_2021_traces = [trace for trace in call_args_list if trace.name == "2021"]
        year_2022_traces = [trace for trace in call_args_list if trace.name == "2022"]
        
        assert len(year_2021_traces) == 2
        assert len(year_2022_traces) == 2
        
        # Verify legendgroups
        for trace in year_2021_traces:
            assert trace.legendgroup == "year_2021"
        for trace in year_2022_traces:
            assert trace.legendgroup == "year_2022"
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_trace_data_properties(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test that trace data properties are set correctly"""
        dates = [pd.Timestamp('2022-01-01')]
        obs_age = [5]
        cum_actual = [123.456]
        obs_date = [pd.Timestamp('2022-06-01')]
        
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': obs_age,
            'cum_actual': cum_actual,
            'obsDate': obs_date
        })
        
        mock_get_color_for_date.return_value = (100, 150, 200)
        mock_rgb_to_string.return_value = 'rgb(100,150,200)'
        
        add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Verify trace data
        trace = self.mock_fig.add_trace.call_args[0][0]
        
        # Check x and y data
        assert list(trace.x) == obs_age
        assert list(trace.y) == cum_actual
        
        # Check customdata (obsDate column) - verify shape and content type
        expected_customdata = df[["obsDate"]]
        assert trace.customdata.shape == expected_customdata.values.shape
        # Convert both to comparable format for assertion
        trace_dates = pd.to_datetime(trace.customdata[:, 0]).tolist()
        expected_dates = expected_customdata['obsDate'].tolist()
        assert trace_dates == expected_dates
        
        # Check text (formatted snapshot date) - Plotly converts lists to tuples
        expected_text = (dates[0].strftime("%b %Y"),)
        assert trace.text == expected_text
        
        # Check hovertemplate
        expected_template = "Date: %{text}<br>obsAge: %{x:.1f}<br>obsDate: %{customdata[0]|%Y-%m-%d}<br>Value: %{y:.6f}<extra></extra>"
        assert trace.hovertemplate == expected_template
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_invalid_dates_handling(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with invalid/NaN dates"""
        dates = [pd.Timestamp('2022-01-01'), pd.NaT, pd.Timestamp('2022-03-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1, 2, 3],
            'cum_actual': [100.5, 200.5, 300.5],
            'obsDate': [pd.Timestamp('2022-02-01'), pd.Timestamp('2022-03-01'), pd.Timestamp('2022-04-01')]
        })
        
        mock_get_color_for_date.return_value = (255, 0, 0)
        mock_rgb_to_string.return_value = 'rgb(255,0,0)'
        
        # This should handle NaT values gracefully by skipping them
        result = add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should still process the valid dates
        assert result == self.mock_fig
        # Should have 2 traces (for the 2 valid dates)
        assert self.mock_fig.add_trace.call_count == 2
    
    def test_missing_required_columns(self):
        """Test behavior when DataFrame is missing required columns"""
        # Missing 'obsAge' column
        df_missing_obsage = pd.DataFrame({
            'snapshotDate': [pd.Timestamp('2022-01-01')],
            'cum_actual': [100.5],
            'obsDate': [pd.Timestamp('2022-02-01')]
        })
        
        with pytest.raises(KeyError):
            add_snapshot_date_lines(
                self.mock_fig, df_missing_obsage, self.min_date, self.max_date, color_points
            )
        
        # Missing 'cum_actual' column
        df_missing_cumactual = pd.DataFrame({
            'snapshotDate': [pd.Timestamp('2022-01-01')],
            'obsAge': [1],
            'obsDate': [pd.Timestamp('2022-02-01')]
        })
        
        with pytest.raises(KeyError):
            add_snapshot_date_lines(
                self.mock_fig, df_missing_cumactual, self.min_date, self.max_date, color_points
            )
        
        # Missing 'obsDate' column
        df_missing_obsdate = pd.DataFrame({
            'snapshotDate': [pd.Timestamp('2022-01-01')],
            'obsAge': [1],
            'cum_actual': [100.5]
        })
        
        with pytest.raises(KeyError):
            add_snapshot_date_lines(
                self.mock_fig, df_missing_obsdate, self.min_date, self.max_date, color_points
            )
    
    def test_missing_snapshotdate_column(self):
        """Test behavior when DataFrame doesn't have snapshotDate column"""
        df_no_date = pd.DataFrame({
            'other_column': [1, 2, 3],
            'obsAge': [1, 2, 3],
            'cum_actual': [100.5, 200.5, 300.5],
            'obsDate': [pd.Timestamp('2022-02-01'), pd.Timestamp('2022-03-01'), pd.Timestamp('2022-04-01')]
        })
        
        with pytest.raises(KeyError):
            add_snapshot_date_lines(
                self.mock_fig, df_no_date, self.min_date, self.max_date, color_points
            )
    
    @patch('utils.viz_functions.get_color_for_date', side_effect=Exception("Color calculation failed"))
    @patch('utils.viz_functions.rgb_to_string')
    def test_color_calculation_error(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior when color calculation fails"""
        dates = [pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1],
            'cum_actual': [100.5],
            'obsDate': [pd.Timestamp('2022-02-01')]
        })
        
        with pytest.raises(Exception, match="Color calculation failed"):
            add_snapshot_date_lines(
                self.mock_fig, df, self.min_date, self.max_date, color_points
            )
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_years_processed_in_sorted_order(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test that years are processed in sorted order regardless of data order"""
        # Create data with years in reverse order
        dates = [pd.Timestamp('2023-01-01'), pd.Timestamp('2021-01-01'), pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1, 2, 3],
            'cum_actual': [100.5, 200.5, 300.5],
            'obsDate': [pd.Timestamp('2023-02-01'), pd.Timestamp('2021-03-01'), pd.Timestamp('2022-04-01')]
        })
        
        mock_get_color_for_date.return_value = (255, 255, 255)
        mock_rgb_to_string.return_value = 'rgb(255,255,255)'
        
        add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Verify traces were processed in year order (2021, 2022, 2023)
        call_args_list = [call[0][0] for call in self.mock_fig.add_trace.call_args_list]
        years_in_order = [trace.name for trace in call_args_list]
        assert years_in_order == ["2021", "2022", "2023"]
    
    @patch('utils.viz_functions.get_color_for_date')
    @patch('utils.viz_functions.rgb_to_string')
    def test_duplicate_snapshot_dates(self, mock_rgb_to_string, mock_get_color_for_date):
        """Test behavior with duplicate snapshot dates (should create separate traces)"""
        # Same snapshot date appears twice with different data
        dates = [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({
            'snapshotDate': dates,
            'obsAge': [1, 2],
            'cum_actual': [100.5, 200.5],
            'obsDate': [pd.Timestamp('2022-02-01'), pd.Timestamp('2022-03-01')]
        })
        
        mock_get_color_for_date.return_value = (255, 0, 0)
        mock_rgb_to_string.return_value = 'rgb(255,0,0)'
        
        result = add_snapshot_date_lines(
            self.mock_fig, df, self.min_date, self.max_date, color_points
        )
        
        # Should create one trace that includes both data points
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        # Verify the trace contains both data points
        trace = self.mock_fig.add_trace.call_args[0][0]
        assert len(trace.x) == 2
        assert len(trace.y) == 2
        assert list(trace.x) == [1, 2]
        assert list(trace.y) == [100.5, 200.5]


class TestAddColorBar:
    """Test cases for add_color_bar function"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.mock_fig = Mock()
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_multiple_years(self, mock_rgb_to_string):
        """Test behavior with multiple years of data"""
        dates = [
            pd.Timestamp('2020-01-01'), pd.Timestamp('2020-06-01'),
            pd.Timestamp('2021-01-01'), pd.Timestamp('2021-06-01'),
            pd.Timestamp('2022-01-01'), pd.Timestamp('2022-06-01')
        ]
        df = pd.DataFrame({'snapshotDate': dates})
        
        # Mock return values
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should add exactly one trace (the colorbar)
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        # Verify the trace properties
        trace = self.mock_fig.add_trace.call_args[0][0]
        assert isinstance(trace, go.Scatter)
        assert trace.mode == "markers"
        assert trace.x == (None,)  # Plotly converts [None] to tuple
        assert trace.y == (None,)
        assert trace.showlegend == False
        
        # Verify marker properties
        assert trace.marker['showscale'] == True
        assert trace.marker['cmin'] == 0
        assert trace.marker['cmax'] == 1
        
        # Verify colorbar properties
        colorbar = trace.marker['colorbar']
        assert colorbar['thickness'] == 12
        assert colorbar['len'] == 0.30
        assert colorbar['orientation'] == "h"
        assert colorbar['x'] == 0.01
        assert colorbar['y'] == 1
        assert colorbar['xanchor'] == "left"
        assert colorbar['yanchor'] == "top"
        assert colorbar['outlinewidth'] == 0
        assert colorbar['tickangle'] == 0
        
        # Verify tick values for multiple years (2020, 2021, 2022)
        # Expected tickvals: (0.0, 0.5, 1.0) for years (2020, 2021, 2022) - Plotly converts to tuples
        expected_tickvals = (0.0, 0.5, 1.0)
        expected_ticktext = ("2020", "2021", "2022")
        assert colorbar['tickvals'] == expected_tickvals
        assert colorbar['ticktext'] == expected_ticktext
        
        # Verify colorscale was created from color_points
        assert len(trace.marker['colorscale']) == len(color_points)
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_single_year(self, mock_rgb_to_string):
        """Test behavior with single year of data (year_range = 0)"""
        dates = [pd.Timestamp('2022-01-01'), pd.Timestamp('2022-06-01'), pd.Timestamp('2022-12-01')]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should add exactly one trace
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        # Verify the trace was created
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # For single year, should use special handling - Plotly converts to tuples
        expected_tickvals = (0.5,)
        expected_ticktext = ("2022",)
        assert colorbar['tickvals'] == expected_tickvals
        assert colorbar['ticktext'] == expected_ticktext
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_empty_dataframe(self, mock_rgb_to_string):
        """Test behavior with empty DataFrame (no unique years)"""
        df_empty = pd.DataFrame(columns=['snapshotDate'])
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        # This should trigger an exception which gets caught and logged
        result = add_color_bar(self.mock_fig, df_empty, color_points)
        
        # Should return figure without adding traces due to exception handling
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
        mock_rgb_to_string.assert_not_called()
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_invalid_dates_only(self, mock_rgb_to_string):
        """Test behavior when DataFrame contains only NaT values (creates trace with NaN)"""
        dates = [pd.NaT, pd.NaT, pd.NaT]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        # The function still creates a trace but with NaN values
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should still create a trace, but with NaN tick values
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # Verify that tickvals/ticktext contain NaN (since no valid years)
        import math
        assert len(colorbar['tickvals']) == 1
        assert math.isnan(colorbar['tickvals'][0])
        assert len(colorbar['ticktext']) == 1
        assert pd.isna(colorbar['ticktext'][0]) or str(colorbar['ticktext'][0]) == 'nan'
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_mixed_valid_invalid_dates(self, mock_rgb_to_string):
        """Test behavior with mix of valid dates and NaT values"""
        dates = [pd.Timestamp('2021-01-01'), pd.NaT, pd.Timestamp('2022-01-01'), pd.NaT]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should add one trace, processing only valid dates
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_called_once()
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # The function includes NaT values as NaN in the calculations
        # This creates tickvals with NaN values interspersed
        import math
        tickvals = colorbar['tickvals']
        ticktext = colorbar['ticktext']
        
        # Should have valid years at positions 0 and 2, with NaN at position 1
        assert len(tickvals) == 3
        assert tickvals[0] == 0.0  # 2021
        assert math.isnan(tickvals[1])  # NaT -> NaN
        assert tickvals[2] == 1.0  # 2022
        
        assert len(ticktext) == 3
        assert ticktext[0] == "2021.0"  # Years with NaT get formatted as floats
        assert pd.isna(ticktext[1]) or str(ticktext[1]) == 'nan'  # NaT -> NaN
        assert ticktext[2] == "2022.0"  # Years with NaT get formatted as floats
    
    def test_missing_snapshotdate_column(self):
        """Test behavior when DataFrame doesn't have snapshotDate column"""
        df_no_date = pd.DataFrame({'other_column': [1, 2, 3]})
        
        # This should trigger an exception which gets caught and logged
        result = add_color_bar(self.mock_fig, df_no_date, color_points)
        
        # Should return figure without adding traces due to exception handling
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_colorscale_creation(self, mock_rgb_to_string):
        """Test that colorscale is correctly created from color_points"""
        dates = [pd.Timestamp('2020-01-01'), pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({'snapshotDate': dates})
        
        # Test with specific color returns
        mock_rgb_to_string.side_effect = [
            'rgb(112,99,137)',   # First color
            'rgb(70,100,170)',   # Second color
            'rgb(131,178,208)',  # etc.
            'rgb(149,218,182)',
            'rgb(200,209,150)',
            'rgb(242,230,177)',
            'rgb(233,185,155)',
            'rgb(220,133,128)',
            'rgb(187,97,109)'
        ]
        
        result = add_color_bar(self.mock_fig, df, color_points)
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorscale = trace.marker['colorscale']
        
        # Verify colorscale structure
        assert len(colorscale) == len(color_points)
        
        # Each colorscale entry should be a tuple (position, color_string)
        for i, (position, color_string) in enumerate(colorscale):
            expected_position = color_points[i][0]
            assert position == expected_position
            # Verify rgb_to_string was called for each color point
            assert 'rgb(' in color_string
        
        # Verify rgb_to_string was called for each color point
        assert mock_rgb_to_string.call_count == len(color_points)
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_year_range_calculations(self, mock_rgb_to_string):
        """Test year range calculations with various year spans"""
        # Test with 3-year span
        dates = [pd.Timestamp('2020-01-01'), pd.Timestamp('2022-12-31')]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        add_color_bar(self.mock_fig, df, color_points)
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # Years: 2020, 2022 (range = 2)
        # Expected tickvals: (0.0, 1.0) - Plotly converts to tuples
        expected_tickvals = (0.0, 1.0)
        expected_ticktext = ("2020", "2022")
        assert colorbar['tickvals'] == expected_tickvals
        assert colorbar['ticktext'] == expected_ticktext
    
    @patch('utils.viz_functions.dash_logger')
    @patch('utils.viz_functions.rgb_to_string', side_effect=Exception("RGB conversion failed"))
    def test_exception_handling(self, mock_rgb_to_string, mock_logger):
        """Test that exceptions are caught and logged properly"""
        dates = [pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({'snapshotDate': dates})
        
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should return figure without adding traces
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
        
        # Should have logged a warning
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        assert 'Unable to construct the colorbar' in warning_message
        assert 'RGB conversion failed' in warning_message
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_colorbar_font_properties(self, mock_rgb_to_string):
        """Test that colorbar font properties are set correctly"""
        dates = [pd.Timestamp('2021-01-01'), pd.Timestamp('2022-01-01')]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        add_color_bar(self.mock_fig, df, color_points)
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # Verify font properties
        assert colorbar['title']['font']['size'] == 10
        assert colorbar['tickfont']['size'] == 8
        assert colorbar['tickfont']['color'] == 'black'
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_no_unique_years_edge_case(self, mock_rgb_to_string):
        """Test edge case where df is not empty but has no processable dates"""
        # DataFrame with non-datetime data in snapshotDate column
        df = pd.DataFrame({'snapshotDate': ['not_a_date', 'also_not_a_date']})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        # This should trigger an exception which gets caught and logged
        result = add_color_bar(self.mock_fig, df, color_points)
        
        # Should return figure without adding traces due to exception handling
        assert result == self.mock_fig
        self.mock_fig.add_trace.assert_not_called()
    
    @patch('utils.viz_functions.rgb_to_string')
    def test_consecutive_years(self, mock_rgb_to_string):
        """Test with consecutive years to verify tick calculations"""
        dates = [
            pd.Timestamp('2019-01-01'), pd.Timestamp('2020-01-01'), 
            pd.Timestamp('2021-01-01'), pd.Timestamp('2022-01-01'), 
            pd.Timestamp('2023-01-01')
        ]
        df = pd.DataFrame({'snapshotDate': dates})
        
        mock_rgb_to_string.side_effect = lambda x: f'rgb({x[0]},{x[1]},{x[2]})'
        
        add_color_bar(self.mock_fig, df, color_points)
        
        trace = self.mock_fig.add_trace.call_args[0][0]
        colorbar = trace.marker['colorbar']
        
        # Years: 2019, 2020, 2021, 2022, 2023 (range = 4)
        # Expected tickvals: (0.0, 0.25, 0.5, 0.75, 1.0) - Plotly converts to tuples
        expected_tickvals = (0.0, 0.25, 0.5, 0.75, 1.0)
        expected_ticktext = ("2019", "2020", "2021", "2022", "2023")
        assert colorbar['tickvals'] == expected_tickvals
        assert colorbar['ticktext'] == expected_ticktext


