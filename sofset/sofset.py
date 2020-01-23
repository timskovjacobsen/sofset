

'''Module for generation of sofistik input files for settlement load cases

Notes
-----
Some parameters in this script are hardcoded as they are dictated from
the layout of the Excel file that serves as the settlement field input.
It is the purpose that the Excel file has as rigid a layout as possible
to make the data treatment easier.
E.g. it is assumed that the X-coordinates are always in the column "B"
in the Excel file, and that there is exactly five data points available
for each cross section.
These restrictions are to be controlled via the Excel sheet.

Todo
-----
* Create possibility for choosing load type for each load case
  ['SL', 'G', ...]. Should default to 'SL' (short term load, taken away
  instantly after calculation)

'''

import numpy as np
import pandas as pd
import os
# import sys
from scipy.interpolate import griddata
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D     # noqa


def read_known_settlements(file_name, skiprows, load_case_dict,
                           points_per_section=5,
                           sheet_name='known_settlement_values'):
    '''
    Return dictionary with known settlement points included.

    Updates `load_case_dict` to include (X, Y, Z)-coordinate arrays,
    where Z represents the known settlements.

    Parameters
    ----------
    filename : str
        Name of Excel file where known settlement points are stored.
    skiprows : int
        Number of rows to skip when reading the Excel file.
    load_case_dict : dict
        Dictionary containing data about settlement load cases. This is
        the dictionary that gets updated and returned.
    points_per_section : int, optional
        Number of maximum values that can be input per section. Defaults
        to 5.
    sheet_name : str
        Name of sheet to read in the Excel file.

    Returns
    -------
    dict
        Dictionary including point coordinates with known (or prescribed)
        settlement values along with the actual settlement values.

    Notes
    -----
    The number of points per section is currently set to 5, which is
    controlled in the input spreadsheet. Thus, this is currently the only
    valid value.
    '''
    if points_per_section != 5:
        raise Exception('''Arg points_per_section is currently only allowed to
     be 5''')

    # Extract X-and Y-coordinates of sections
    x = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows,
                      usecols=[1]).values.flatten()
    y = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows,
                      usecols=[2, 3, 4, 5, 6]).values.flatten()

    # Get indices where values are not NaN in the array of y-coordinates
    idx_no_nan = np.where(~np.isnan(y))

    n = points_per_section

    for i, lc in enumerate(load_case_dict.keys()):

        # Insert Y-array for load case
        load_case_dict[lc]['Y'] = y[idx_no_nan]

        # Extract string describing interpolation method for given load case
        int_method = load_case_dict[lc]['int_method']

        # Create the list specifying which columns to take from the Excel
        # sheet for creating dataframe. If load case is 1D, take only the
        # first row, otherwise take the next four rows.
        row1 = 7 + n*i
        cols = [row1] if '1D' in int_method else [row1, row1+1, row1+2, row1+3,
                                                  row1+4]

        # Read the columns from Excel file into dataframe
        df_temp = pd.read_excel(file_name, sheet_name=sheet_name,
                                skiprows=skiprows, usecols=cols)

        # Extract settlements (here denoted Z suffixed by the load case number)
        if '1D' in int_method:
            # In 1D case, take all values as flattened array
            load_case_dict[lc]['Z'] = df_temp.values.flatten()

            # Store X-coordinates of sections in main dict
            load_case_dict[lc]['X'] = x

        elif '2D' in int_method:
            # In 2D case take only values that have valid Y-values associated
            # as flattened array. Valid values has corresponding value in the
            # Y-array that are not nan
            load_case_dict[lc]['Z'] = df_temp.values.flatten()[idx_no_nan]

            # Repeat all X-values 'points_per_section' times
            x_temp = np.repeat(x, points_per_section)

            # Save x-coordinates in dict
            load_case_dict[lc]['X'] = x_temp[idx_no_nan]

    return load_case_dict


def interpolate_settlements2D(x_known, y_known, settlement_known, x, y,
                              method='cubic'):
    '''
    Return the interpolated settlement field based on known settlements in
    given points.

    Parameters
    ----------
    x_known : list/numpy array
        x-coordinate in points with known settlements
    y_known : list/numpy array
        y-coordinate in points with known settlements
    settlements_known : list/np array
        Settlement value in known points
    x : list/numpy array
        x-coordinate at points where interpolation is desired
    y : list/numpy array
        y-coordinate at points where interpolation is desired
    method : str, optional
        Method for interpolation, defaults to 'cubic' as that
        normally represents structural displacements better.
        Other valid arguments are 'linear' or 'nearest'.

    Returns
    -------
    settlement_interpolated : np array
        Interpolated settlement values in all points (x, y).
    '''
    # Check validity of interpolation method input
    if method not in ['cubic', 'linear', 'nearest']:
        raise Exception('''Interpolation method must be either "cubic",
     "linear" or "nearest", not {method}.''')

    # x-y coordinates of points with known displacements
    xy_known = np.array(list(zip(x_known, y_known)))

    # Calculate the interpolated z-values
    settlement_interpolated = griddata(xy_known, settlement_known, (x, y),
                                       method='cubic')

    return settlement_interpolated


def write_datfile(load_case_number, load_case_title, node_numbers,
                  settlements, dir_target='current'):
    '''Write .dat file with Teddy input code to apply load cases.

    The load cases represent a settlement field with the load type 'SL', which
    defined a short term load in Sofistik.

    Parameters
    ----------
    load_case_number : int
        Desired load case number.
    load_case_title : str
        Title for load case.
    node_numbers : list or list-like
        Node numbers that should receive a settlement in the given load case.
    settlements : list or list-like
        Settlement values to be paired with `node_numbers` in the given load case.
    dir_target : str
        Path to directory to dump the output .dat file.
    '''
    if dir_target == 'current':
        # Set target directory for the saved file to current working directory
        dir_target = os.getcwd()

    # --- WRITE INTERPOLATED FIELD TO .DAT FILE AS TEDDY CODE ---
    # Write Teddy code for applying interpolated settlements to file
    file_name = f'{dir_target}\\settlement_LC{load_case_number}.dat'
    with open(file_name, 'w') as file:
        file.write(f'''+PROG SOFILOAD  $ Plaxis settlement LC{load_case_number}
HEAD Settlement interpolation for LC{load_case_number} - {load_case_title}
UNIT TYPE 5

LC {load_case_number} type 'SL' fact 1.0 facd 0.0 titl '{load_case_title}'  \n
''')
        for node, settlement in zip(node_numbers, settlements):
            file.write(f'  POIN NODE {node} WIDE 0 TYPE WZZ {settlement} \n')
        file.write('END')


def print_status_report(x_nodes, y_nodes, settlement_interpolated, load_case):
    '''
    Print a status report summarizing the interpolation for each load case.
    '''
    print('--------------------------------------------')
    print('RESULTS FROM SETTLEMENT INTERPOLATION SCRIPT')
    print('--------------------------------------------')

    # Check if interpolated settlements have any nan values
    print(f'    LC{load_case}:')
    if np.isnan(settlement_interpolated).any():
        print('''
    ### --- INFO --- ###:
    Some interpolated settlement values are 'nan'.
    This is probably because they fall out of the region
    defined by known points (extrapolation not supported).

    The input field must encompass all the points where
    interpolated is desired.
    E.g. if the desired points for a 1D interpolation are
    X-coordinates x = (0, 100, 200), the input X-values
    must contain a point where X < 0 and one where X > 200''')

        nans = np.argwhere(np.isnan(settlement_interpolated))
        no_all = len(settlement_interpolated)
        print(
            f'''
    Number of nan values are {len(nans)} out of {no_all} total values.''')

        # Extract X- and Y-coordinates and round to 1 digit
        x_nans = np.round(x_nodes[nans.flatten()], 1)
        y_nans = np.round(y_nodes[nans.flatten()], 1)
        nan_coords = list(zip(x_nans, y_nans))

        print(
            f'''
    The interpolation can be visually inspected in the generated
    PNG-file. It will reveal the locations of the nan-values.
    (X, Y)-coordinates of points that failed to interpolate are:\n{nan_coords} ''')

    else:
        print('         All values interpolated successfully!')
    print('-------------------------------------------')


def read_excel_nodes(dir_lookup='current',
                     filename='nodes_to_be_interpolated.xlsx',
                     sheet_name='XLSX-Export'):
    '''Return (x, y, z)-coordinates and node numbers for all nodes.

    Parameters
    ----------
    dir_lookup : str
        Directory where the Excel file is located.
    filename : str
        Filename of Excel file with extension (.xlsx or .xlsm).
    sheet_name : str
        Sheet name where node data is located within the Excel file
    '''
    if dir_lookup == 'current':
        # Get directory where this module resides
        dir_lookup = os.getcwd()

    # Read Excel file with node numbers and their coordinates into a dataframe
    df_nodes = pd.read_excel(
        f'{dir_lookup}\\{filename}', sheet_name=sheet_name)

    # Remove leading or trailing white space from column names
    df_nodes.columns = df_nodes.columns.str.strip()

    # Extract node coordinates and node numbers and return them
    x_nodes, y_nodes = df_nodes['X [m]'].values, df_nodes['Y [m]'].values
    z_nodes, node_no = df_nodes['Z [m]'].values, df_nodes['NR'].values

    return x_nodes, y_nodes, z_nodes, node_no


def load_cases(file_name, sheet_name, skiprows):
    '''Return a dictionary of load case data from Excel file.

    Parameters
    ----------
    file_name : str
        Name of Excel file to read, including file extention (.xlsx or .xlsm)
    sheet_name : str
        Name of sheet where the data for load cases is stored.
    skiprows : int
        Number of beginning rows to skip when reading the Excel file

    Returns
    -------
    dict
        A dictionary containing a subdictionary for each load case and its
        metadata. The subdictionaries for each load case have the format:
        {lc_number: {title: 'title_here', 'int_method': 'method_here'}}
    '''

    # Read load cases, their titles and the desired interpolation method
    df_load_cases = pd.read_excel(file_name, sheet_name=sheet_name,
                                  skiprows=skiprows-2, usecols=range(6, 26))

    # Retain only columns starting with integers of any length
    df_load_cases = df_load_cases.filter(regex='^\d+', axis=1).loc[:1]

    # Convert df of LCs, titles and int_method to dict of dicts,
    # one for each LC
    #   format: { lc_number: {0: 'title_here', 1: 'method_here'} }
    load_case_dict = df_load_cases.to_dict(orient='dict')

    # Rename keys in inner dictionaries
    #   format: {lc_number: {title: 'title_here', 'int_method': 'method_here'}}
    for dic in load_case_dict.values():
        dic['title'] = dic.pop(0)
        dic['int_method'] = dic.pop(1)

    return load_case_dict


def plot_interpolation(xycoords, node_no, lc, master_dict,
                       settlements_interpolated, png_targetdir='current'):
    '''
    Plot the result of the interpolation as a 3D scatter plot showing
    the known points that the interpolation is based on in green and
    the interpolated points in blue.
    '''
    # Extract x- and y-coordinates
    x_nodes, y_nodes = xycoords

    # Extract known coordinates and interpolation method from master dict
    x_known = master_dict[lc]['X']
    y_known = master_dict[lc]['Y']
    settlements_known = master_dict[lc]['Z']
    int_method = master_dict[lc]['int_method'].lower()

    if '2d' in int_method:
        # Create figure object
        fig = plt.figure()

        # Create axis object for 3D plot (Visualizing 2D interpolations)
        ax = fig.add_subplot(111, projection='3d')

        # Plot known settlement points
        ax.scatter(x_known, y_known, settlements_known,
                   '-.', color='limegreen', label='Known points')

        # Plot interpolated field
        ax.scatter(x_nodes, y_nodes, settlements_interpolated,
                   '.', color='cornflowerblue', s=0.1, label='Interpolated points')

        # Create separate array of nan-values, if there are any
        if np.isnan(settlements_interpolated).any():
            # Nan-values are present, extract indices where values are nan
            idx_nan = np.where(np.isnan(settlements_interpolated))

            # Create array x-values where settlement is nan
            x_nan = x_nodes[idx_nan]
            y_nan = y_nodes[idx_nan]
            z_nan_temp = settlements_interpolated[idx_nan]
            z_nan = np.nan_to_num(z_nan_temp)

            # Plot all nan-values with y=0 and make them red
            ax.scatter(x_nan, y_nan, z_nan, color='red', s=0.1,
                       label="NaN (interp. failed)")

        # Set titles and activate legend
        ax.set_title(f'Settlement interpolation for LC{lc}')
        ax.set_xlabel('Chainage [m]')
        ax.set_ylabel('y [mm]')
        ax.set_zlabel('Settlement [mm]')
        plt.legend(loc='center left', bbox_to_anchor=(-0.15, 0.5), fontsize='small')

        # Define name for png file to save
        png_name = f'LC{lc}_settl_interp_plot.png'

        if png_targetdir == 'current':
            # Save figure
            fig.savefig(png_name)
        else:
            # Save figure in the folder that was input
            fig.savefig(f'{png_targetdir}\\{png_name}')

    elif '1d' in int_method:
        # Create plot and save as png-figure
        plot_1d_interpolation(lc, x_known, settlements_known, x_nodes,
                              settlements_interpolated, png_targetdir='current')

    else:
        raise Exception(
            '''The interpolation method ("int_method") needs to specify 1D or
             2D and linear or cubic.''')


def plot_1d_interpolation(load_case, x_known, settlements_known, x_nodes,
                          settlements_interpolated, png_targetdir='current'):
    # Create axis object for 2D plot (Visualizing 1D interpolations)
    fig, ax = plt.subplots()

    # Plot known points
    ax.plot(x_known, settlements_known, '.',
            color='limegreen', markersize=15, label='Known points')

    # Plot interpolated points
    ax.plot(x_nodes, settlements_interpolated, '-',
            color='cornflowerblue', label='Interpolated points')

    # Create separate array of nan-values, if there are any
    if np.isnan(settlements_interpolated).any():
        # Nan-values are present, extract indices where values are nan
        idx_nan = np.where(np.isnan(settlements_interpolated))

        # Create array x-values where settlement is nan
        x_nan = x_nodes[idx_nan]
        y_nan_temp = settlements_interpolated[idx_nan]
        y_nan = np.nan_to_num(y_nan_temp)

        # Plot all nan-values with y=0 and make them red
        ax.plot(x_nan, y_nan, 'x', ms=2, color='red',
                label="NaN (interpolation failed)")

    # Set titles and activate legend
    ax.set_title(f'Settlement interpolation for LC{load_case}')
    ax.set_xlabel('Chainage [m]')
    ax.set_ylabel('Settlement [mm]')
    plt.legend()

    # Define name for png file to save
    png_name = f'LC{load_case}_settl_interp_plot.png'

    if png_targetdir == 'current':
        # Save figure
        fig.savefig(png_name)
    else:
        # Save figure in the folder that was input
        fig.savefig(f'{png_targetdir}\\{png_name}')


def filter_nodes_for_Z(df, Zmax_allowable):
    '''
    Return df filtered by filter_condition.

    Currently only Zmax_allowable is available.

    Args:
        df (dataframe)          : Pandas dataframe with a column named 'Z [m]'
         present
        Zmax_allowable (number) : Max allowable Z-value for resulting df
    '''

    try:
        return df[df['Z [m]'] < Zmax_allowable]

    except KeyError:
        print(
            '''KeyError: Make sure the input dataframe contains a column
             named "Z [m]".''')


def run_analysis(master_dict, dir_lookup='current', dir_target='current',
                 plot_results=True, png_targetdir='current'):
    '''Run interpolation analysis and write dat file in Teddy input language.

    Parameters
    ----------
    master_dict : dict
        Dictionary storing all information about the load cases and the
        results.
    dir_lookup : str, optional
        Directory where Excel file containing nodal geometry is located.
        Defaults to current working directory.
    dir_target : str, optional
        Directory in which to save the generated dat files.
        Defaults to current working directory.
    plot_results : bool, optional
        Whether to plot the interpolated results and save as png files
        after the analysis. Defaults to `True`.
    png_targetdir : str, optional
        Directory in which to save the plotted interpolation results
        as png files. This parameter only takes effect if `plot_results`
        is `True`.
        Defaults to current working directory.

    Notes
    -----
    Current working directory will in most cases be the the directory
    where the .sofistik (ssd) file is located.  
    '''

    for lc in master_dict:

        # Set variables from dict for load case
        title = master_dict[lc]['title']
        x_known = master_dict[lc]['X']
        y_known = master_dict[lc]['Y']
        settlements_known = master_dict[lc]['Z']
        int_method = master_dict[lc]['int_method'].lower()
        lc_title = master_dict[lc]['title']

        if dir_lookup == 'current':
            # Get directory where script is run from
            dir_lookup = os.getcwd()

        # Read (x, y)-coordinates and numbers of nodes to be interpolated
        # (read from Excel)
        x_nodes, y_nodes, _, node_no = read_excel_nodes(dir_lookup=dir_lookup)

        # Extract chosen method for interpolation
        if 'linear' in int_method:
            # Set method to linear interpolation
            method = 'linear'
        elif 'cubic' in int_method:
            # Set method to cubic interpolation
            method = 'cubic'

        # Check for interpolation dimension and run analysis
        if '1d' in int_method:

            # Perform 1D interpolation and store results (only X-coordinate varying)
            f_int = interp1d(x_known, settlements_known, kind=method,
                             bounds_error=False)

            # Sort X-coordinates of nodes and node numbers
            sorted_indices = x_nodes.argsort()
            x_nodes = x_nodes[sorted_indices]
            node_no = node_no[sorted_indices]

            # Extract interpolated settlement values at desired X-coords
            settlements_interpolated = f_int(x_nodes)

        elif '2d' in int_method:
            # Perform linear 2D interpolation (X,Y-coordinates varying)
            settlements_interpolated = interpolate_settlements2D(
                x_known, y_known, settlements_known, x_nodes, y_nodes,
                method=method)

        else:
            raise Exception(
                f'''The interpolation method ("int_method") needs to specify
                1D or 2D and linear or cubic. The input was {int_method}''')

        # Print status report from interpolation
        print_status_report(x_nodes, y_nodes, settlements_interpolated, lc)

        # Determine directory for saving the dat-file
        if dir_target == 'current_dir':
            # Get current working directory (where module is run from, i.e.
            # Sofistik dir)
            dir_target = os.getcwd()

        # Write interpolated field to .dat file as Teddy code
        write_datfile(lc, lc_title, node_no,
                      settlements_interpolated, dir_target)

        # Plot results if was chosen to do so in the function call
        if plot_results:
            plot_interpolation((x_nodes, y_nodes), node_no, lc,
                               master_dict, settlements_interpolated,
                               png_targetdir=png_targetdir)


if __name__ == "__main__":

    # Set path to Excel file for the input settlement field
    file_name = 'Settlement_interpolation\\known_settlement_values.xlsm'

    # Sheet name and number of rows to skip when reading into pandas dataframe
    sheet_name = 'known_settlement_values'
    skiprows = 10

    # Create master dictionary for storing load case information
    load_case_dict = load_cases(file_name, sheet_name, skiprows=skiprows)

    # Create master dictionary with load cases
    d = read_known_settlements(file_name, skiprows, load_case_dict,
                               points_per_section=5,
                               sheet_name='known_settlement_values')

    # Interpolate settlements and create dat-files
    run_analysis(d, plot_results=True)
