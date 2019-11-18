
import sys
import os

# Insert path for root project folder in sys.path to make that point of origin for navigation
sys.path.insert(0, os.path.abspath('.'))

# import pytest

from sofset import sofset



if __name__ == '__main__':
    # Set path to Excel file for the input settlement field
    file_name = 'tests\\testdata\\known_settlement_values.xlsm'

    # Sheet name and number of rows to skip when reading into pandas dataframe
    sheet_name = 'known_settlement_values'
    skiprows = 10

    load_case_dict = sofset.load_cases(file_name, sheet_name, skiprows=skiprows)

    # Create master dictionary with load cases
    d = sofset.read_known_settlements(file_name, skiprows, load_case_dict,
                            points_per_section=5, sheet_name='known_settlement_values')

    # Interpolate settlements and create dat-files
    testdir = 'tests\\testdata'
    sofset.run_analysis(d, dir_lookup=testdir, dir_target=testdir, plot_results=True)

