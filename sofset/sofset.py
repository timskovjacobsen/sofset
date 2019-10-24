import numpy as np
import pandas as pd
import os
import sys
from scipy.interpolate import griddata
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

'''
* Consider better names for the output .dat files

NOTE Some parameters in this script are hardcoded as they are dictated from the layout of the Excel file
     that serves as the settlement field input. It is the purpose that the Excel file has as rigid a
     layout as possible to make the data treatment easier.
        E.g. it is assumed that the X-coordinates are always in the column "B" in the Excel file, and
        that there is exactly five data points available for each cross section.
        These restrictions are to be controlled via the Excel sheet.

TODO Create possibility for choosing load type for each load case ['SL', 'G', ...]. Should default to 'SL' (short term load, taken away instantly after calculation) 

'''
# TODO The main dictionary could be renamed to master_dict or something else


def read_known_settlements(file_name, skiprows, load_case_dict, points_per_section=5, sheet_name='known_settlement_values'):
    '''
    Return load_case_dict updated to include (X, Y, Z)-coordinate arrays, where Z represents the known settlements.

    '''
    if points_per_section != 5:
        raise Exception('Arg points_per_section is currently only allowed to be 5')

    # Extract X-and Y-coordinates of sections
    x = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows,
                      usecols=[1]).values.flatten()
    y = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows,
                      usecols=[2,3,4,5,6]).values.flatten()  # FIXME Assumes points_per_section=5

    # Get indices where values are not NaN in the array of y-coordinates
    idx_no_nan = np.where(~np.isnan(y))

    n = points_per_section

    for i, lc in enumerate(load_case_dict.keys()):

        # Insert Y-array for load case
        load_case_dict[lc]['Y'] = y[idx_no_nan]

        # Extract string describing interpolation method for given load case
        int_method = load_case_dict[lc]['int_method']

        # Create the list specifying which columns to take from the Excel sheet for creating dataframe
        #   If load case is 1D, take only the first row, otherwise take the next four rows.
        # FIXME List size does not currently scale with points_per_section (assumes points_per_section=5) 
        cols = [7 + n*i] if '1D' in int_method else [7+n*i, 7+n*i+1, 7+n*i+2, 7+n*i+3, 7+n+i*4]
 
        # Read the columns from Excel file into dataframe
        df_temp = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows, usecols=cols)

        # Extract settlements (here denoted Z suffixed by the load case number)
        if '1D' in int_method:
            # NOTE: No Y-values in this scenario

            # In 1D case, take all values as flattened array
            load_case_dict[lc]['Z'] = df_temp.values.flatten()

            # Store X-coordinates of sections in main dict
            load_case_dict[lc]['X'] = x

        elif '2D' in int_method:
            # In 2D case take only values that have valid Y-values associated as flattened array
            #   Valid values has corresponding value in the Y-array that are not nan
            load_case_dict[lc]['Z'] = df_temp.values.flatten()[idx_no_nan]

            # Repeat all X-values 'points_per_section' times
            x_temp = np.tile(x, points_per_section)
            load_case_dict[lc]['X'] = x_temp[idx_no_nan]

    return load_case_dict


def interpolate_settlements2D(x_known, y_known, settlement_known, x, y, method='cubic'):
    '''
    Return the interpolated settlement field based on known settlements in given points.

    Args:
        x_known (list/numpy array)        : x-coordinate in points with known settlements
        y_known (list/numpy array)        : y-coordinate in points with known settlements
        settlements_known (list/np array) : Settlement value in known points
        x (list/numpy array)              : x-coordinate at points where interpolation is desired
        y (list/numpy array)              : y-coordinate at points where interpolation is desired
        method (str) (optional)           : Method for interpolation, defaults to 'cubic' as that
                                            normally represents structural displacements better.
                                            Other valid arguments are 'linear' or 'nearest'.

    Returns
        settlement_interpolated (np array) : Interpolated settlement values in all points (x, y).
    '''

    # Check validity of interpolation method input
    if method not in ['cubic', 'linear', 'nearest']:
        raise Exception('''Interpolation method must be either "cubic", "linear" or "nearest", 
                           not {method}.''') 

    # x-y coordinates of points with known displacements
    xy_known = np.array(list(zip(x_known, y_known)))

    # Calculate the interpolated z-values
    settlement_interpolated = griddata(xy_known, settlement_known, (x, y), method='cubic')

    return settlement_interpolated


def write_datfile(load_case_number, load_case_title, node_numbers, settlements, 
                  target_dir='current'):
    '''
    Write a .dat file with Teddy (SOFiSTiK input) code for applying input settlement field as a 
    load case.
    '''

    if target_dir == 'current':
        # Get directory where this module resides
        target_dir = os.getcwd()

    ### WRITE INTERPOLATED FIELD TO .DAT FILE AS TEDDY CODE ###
    # Write Teddy code for applying interpolated settlements to file
    with open(f'{target_dir}\\teddy_code_settlement_field_LC{load_case_number}.dat', 'w') as file:
        file.write(f'''+PROG SOFILOAD  $ Plaxis settlement LC{load_case_number}
HEAD Settlement interpolation for LC{load_case_number} - {load_case_title}
UNIT TYPE 5

LC {load_case_number} type 'SL' fact 1.0 facd 0.0 titl '{load_case_title}'  \n''')
        for node, settlement in zip(node_numbers, settlements):
            file.write(f'  POIN NODE {node} WIDE 0 TYPE WZZ {settlement} \n')
        file.write('END')


def print_status_report(x_nodes, y_nodes, settlement_interpolated, load_case):
    '''
    Print a status report summarizing the interpolation for each load case.

    TODO Is this function totally adapted to handle both 1D and 2D interpolation?
    '''
    print('--------------------------------------------')
    print('RESULTS FROM SETTLEMENT INTERPOLATION SCRIPT')
    print('--------------------------------------------')

    # Check if interpolated settlements have any nan values
    print(f'    LC{load_case}:')
    if np.isnan(settlement_interpolated).any():
        print('         INFO:')
        print("         Some interpolated settlement values are 'nan'.")
        print('''         This is probably beacause they fall out of the region defined by known points
        (extrapolation not suported).''')
        nans = np.argwhere(np.isnan(settlement_interpolated))
        print(f'         Number of nan values are {len(nans)} out of {len(settlement_interpolated)} total values.')

        # Extract X- and Y-coordinates and round to 1 digit
        x_nans = np.round(x_nodes[nans.flatten()], 1)
        y_nans = np.round(y_nodes[nans.flatten()], 1)
        nan_coords = list(zip(x_nans, y_nans))

        print(f'         (X, Y)-coordinates of points that failed to interpolate are:\n{nan_coords} ')
        # TODO: Replace those nan-values with 0 and make sure they are colored red in the plot

    else:
        print('         All values interpolated succesfully!')
    print('-------------------------------------------')


def read_excel_nodes(directory_lookup='current', filename='nodes_to_be_interpolated.xlsx', sheet_name='XLSX-Export'):
    '''
    Return the x-, y- and z-coordinates as well as node numbers for nodes present in 'filename'.
    '''

    if directory_lookup == 'current':
        # Get directory where this module resides
        directory_lookup = os.getcwd()

    # Read Excel file with node numbers and their coordinates into a dataframe
    df_nodes = pd.read_excel(f'{directory_lookup}\\{filename}', sheet_name=sheet_name)

    # Remove leading or trailing white space from column names
    df_nodes.columns = df_nodes.columns.str.strip()

    x_nodes, y_nodes, z_nodes = df_nodes['X [m]'], df_nodes['Y [m]'], df_nodes['Z [m]']
    node_no = df_nodes['NR']

    return x_nodes, y_nodes, z_nodes, node_no


def plot_3D_results(lc, master_dict, settlements_interpolated):
    '''
    Plot the result of the interpolation as a 3D scatter plot showing the known points that the
    interpolation is based on in green and the interpolated points in blue.
    '''

    # Read (x, y)-coordinates and numbers of nodes to be interpolated (read from Excel)
    x_nodes, y_nodes, _, node_no = read_excel_nodes()   # TODO Excel file name should be input

    # Extract known coordinates and interpo method from master dict
    x_known = master_dict[lc]['X']
    y_known = master_dict[lc]['Y']
    settlements_known = master_dict[lc]['Z']
    int_method = master_dict[lc]['int_method'].lower()

    # Create figure object
    fig = plt.figure()

    if '2d' in int_method:
        # Create axis object for 3D plot (Visualizing 2D interpolations)
        ax = fig.add_subplot(111, projection='3d')

        # Plot known settlement points
        ax.scatter(x_known, y_known, settlements_known, '-.', color='limegreen')

        # Plot interpolated field
        ax.scatter(x_nodes, y_nodes, settlements_interpolated, '.', color='cornflowerblue', s=0.1)

    elif '1d' in int_method:
        # Create axis object for 2D plot (Visualizing 1D interpolations)
        ax = plt.subplots()

        # Plot known points
        ax.plot(x_known, settlements_known, '.', color='limegreen')

        # Plot interpolated points
        ax.plot(x_known, settlements_known, '.', color='cornflowerblue', s=0.1)

    else:
        raise Exception("The interpolation method ('int_method') needs to specify 1D or 2D and linear or cubic.")

    # Set limits
    # ax.set_xlim(6800, 7350)
    # ax.set_zlim(-22, -15)
    # ax.set_ylim(-100, 100)
    plt.show()


def filter_nodes_for_Zmin(df, Zmin_allowable):
    '''
    Return df filtered by filter_condition.

    The parameters 'Zmax_allowable' and 'Zmin_allowable' are mutually exclusive and at 
    least one of them must be specified.

    Args: 
        df (dataframe)          : Pandas dataframe with a column named 'Z [m]' present
        Zmin_allowable (number) : Min allowable Z-value for resulting df
    '''

    try:
        return df[df['Z [m]'] < Zmin_allowable]
    
    except KeyError:
        print('KeyError: Make sure the input dataframe contains a column named "Z [m]".')


def run_analysis(master_dict, directory_lookup='current', target_dir='current', plot_results=False):

    for lc in master_dict:

        # Set variables from dict for load case
        title = master_dict[lc]['title']
        x_known = master_dict[lc]['X']
        y_known = master_dict[lc]['Y']
        settlements_known = master_dict[lc]['Z']
        int_method = master_dict[lc]['int_method'].lower()
        lc_title = master_dict[lc]['title']

        if directory_lookup == 'current':
            # Get directory where script is run from
            directory_lookup = os.getcwd()

        # Read (x, y)-coordinates and numbers of nodes to be interpolated (read from Excel)
        x_nodes, y_nodes, _, node_no = read_excel_nodes(directory_lookup=directory_lookup)

        # Extract chosen method for interpolation
        if 'linear' in int_method:
            # Set method to linear interpolation
            method = 'linear'
        elif 'cubic' in int_method:
            # Set method to cubic interpolation
            method = 'cubic'

        # Check for interpolation dimention and run analysis
        if '1d' in int_method:
            
            try:
                # Perform 1D interpolation and store results (only X-coordinate varying)
                f_int = interp1d(x_known, settlements_known, kind=method)

                # Sort X-coordinates of nodes and node numbers
                sorted_indices = x_nodes.argsort()
                x_nodes = x_nodes[sorted_indices]
                node_no = node_no[sorted_indices]

                # Extract interpolated settlemnt values at desired X-coordinates
                settlements_interpolated = f_int(x_nodes)

        except ValueError:
            print(f'''1D interpolation couldn't be performed for LC{lc}. Check if the input X-values 
                     are encompassing all the points where interpolated is desired.
                     E.g. if the desired points to be interpolated have X-coordinates 
                     x = (0, 100, 200), the input X-values must contain a point where X < 0 and one 
                     where X > 200 (extrapolation is not allowed).''')

        elif '2d' in int_method:
            # Perform linear 2D interpolation (X,Y-coordinates varying)
            settlements_interpolated = interpolate_settlements2D(x_known, y_known, settlements_known,
                                                                x_nodes, y_nodes, method=method)

        else:
            raise Exception("The interpolation method ('int_method') needs to specify 1D or 2D and linear or cubic.")

        # Print status report from interpolation
        print_status_report(x_nodes, y_nodes, settlements_interpolated, lc)

        # Determine directory for saving the dat-file
        if target_dir == 'current_dir':
            # Get current working directory (where module is run from, i.e. Sofistik dir)
            target_dir = os.getcwd()

        # Write interpolated field to .dat file as Teddy code
        write_datfile(lc, lc_title, node_no, settlements_interpolated, target_dir)

        if plot_results:
            plot_3D_results(lc, master_dict, settlements_interpolated)


if __name__ == "__main__":

    # Set path to Excel file for the input settlement field
    file_name = 'Settlement_interpolation\\known_settlement_values.xlsm'  

    # Sheet name and number of rows to skip when reading into pandas dataframe 
    sheet_name = 'known_settlement_values'
    skiprows = 10

    # Read load cases, their titles and the desired interpolation method
    df_load_cases = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=skiprows-2, usecols=range(6, 26))

    # Retain only columns starting with integers of any length (must be the load case numbers)
    df_load_cases = df_load_cases.filter(regex='^\d+',axis=1).loc[:1]

    # Convert dataframe of load cases, titles and int_method to a dict of dicts, one for each load case
    #   format: { lc_number: {0: 'title_will_be_here', 1: 'method_will_be_here'} }
    load_case_dict = df_load_cases.to_dict(orient='dict')

    # Rename keys in inner dictionaries
    #   format: { lc_number: {title: 'title_will_be_here', 'int_method': 'method_will_be_here'} }
    for dic in load_case_dict.values():
        dic['title'] = dic.pop(0)
        dic['int_method'] = dic.pop(1)

    # Create master dictionary with load cases
    d = read_known_settlements(file_name, skiprows, load_case_dict, points_per_section=5, sheet_name='known_settlement_values')

    # Interpolate settlements and create dat-files
    run_analysis(d, plot_results=False)     # FIXME Results can't be plotted as of now
