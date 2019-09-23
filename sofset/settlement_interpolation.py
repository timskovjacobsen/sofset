import numpy as np
import pandas as pd
import os
import sys
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

'''

IDEA:
    This script shoud be a refined version that can be run by a machine with Python and necessary
    dependencies installed.
    For a user interface for people without Python installed, create another script.

    Limit to a single output Excel file from Sofistik


'''

### READ EXCEL FILE WITH SECTIONS AND KNOWN SETTLEMENT DATA ###
file_name = 'Settlement_interpolation\\known_settlement_values.xlsx'   # NOTE: Excel file must be in the same folder as the script
file_name = 'known_settlement_values.xlsx'   # NOTE: Excel file must be in the same folder as the script
sheet_name = 'known_settlement_values'
df_numbers = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, nrows=1)
print(df_numbers.dropna().values)
print(df_numbers.to_string())
df_x = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[1])
df_y = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[2,3,4,5])
df_z25 = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[6,7,8,9])
df_z26 = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[10,11,12,13])
df_z27 = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[14,15,16,17])
df_z28 = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[18,19,20,21])
df_z29 = pd.read_excel(file_name, sheet_name=sheet_name, skiprows=9, usecols=[22,23,24,25])

# Insert as many X-colunms as there are columns in the other dataframes
for i in range(2, len(df_y.columns)+1):
    df_x[f'X{i}'] = df_x['X']

# Flatten dataframe of y-values into array
y_temp = df_y.values.flatten()

# Get indecies where values are not NaN
idx = np.where(~np.isnan(y_temp))

# Extract all non-NaN values to create array of all known points
y_known = y_temp[idx]
x_known = df_x.values.flatten()[idx]
z25_vals = df_z25.values.flatten()[idx]
z26_vals = df_z26.values.flatten()[idx]
z27_vals = df_z27.values.flatten()[idx]
z28_vals = df_z28.values.flatten()[idx]
z29_vals = df_z29.values.flatten()[idx]

# Mirror all data, since everything is assumed symmetric about CL (only vals defined on one side)
x_known = np.append(x_known, x_known)
y_known = np.append(y_known, -y_known)



settlements_known = {'125': np.append(z25_vals, z25_vals),
                     # '26': np.append(z26_vals, z26_vals),
                     '126': np.append(z27_vals, z27_vals),
                     '127': np.append(z28_vals, z28_vals),
                     '124': np.append(z29_vals, z29_vals),
                     }

load_case_titles = {'125': 'Settlements before Jernhusen',
                    # '26': 'Settlements after Jernhusen',
                    '126': 'LT settlements - Range 1',
                    '127': 'LT settlements - Range 2',
                    '124': 'LT settlements - Range 0',
                   }

# Go one directory up to get the path for the directory where the model is located
# model_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))   # NOTE Not necessary





def interpolate_settlements(x_known, y_known, settlement_known, x, y, method='cubic'):
    '''
    Return the interpolated settlement field based on known settlements in given points.

    Args:
        x_known (list/numpy array)              : x-coordinate in points with known settlements
        y_known (list/numpy array)              : y-coordinate in points with known settlements
        settlements_known (list/numpy array)    : Settlement value in known points
        x (list/numpy array)                    : x-coordinate at points where interpolation is desired
        y (list/numpy array)                    : y-coordinate at points where interpolation is desired
        method (str) (optional)                 : Method for interpolation, defaults to 'cubic' as that
                                                  normally represents structural displacements better. Other
                                                  valid arguments are 'linear' or 'nearest'.

    Returns
        settlement_interpolated (numpy array)   : Interpolated settlement values in all points (x, y).
    '''

    # x-y coordinates of points with known displacements
    xy_known = np.array(list(zip(x_known, y_known)))

    # Calculate the interpolated z-values
    settlement_interpolated = griddata(xy_known, settlement_known, (x_nodes, y_nodes), method='cubic')

    return settlement_interpolated


def write_datfile(node_no, settlements):
    '''
    Write a .dat file with Teddy (SOFiSTiK input) code for applying input settlement field as load case.
    '''

    ### WRITE INTERPOLATED FIELD TO .DAT FILE AS TEDDY CODE ###
    # Write Teddy code for applying interpolated settlements to file
    with open(f'{model_dir}\\teddy_code_settlement_field_LC{lc}.dat', 'w') as file:       # TODO Directories!!!
        file.write(f'''+PROG SOFILOAD  $ Plaxis settlement LC{lc}
HEAD Settlement interpolation for LC{lc} - {load_case_titles[lc]}
UNIT TYPE 5

LC {lc} type 'SL' fact 1.0 facd 0.0 titl '{load_case_titles[lc]}'  \n''')
        for node, settlement in zip(node_no, settlements):
            file.write(f'  POIN NODE {node} WIDE 0 TYPE WZZ {settlement} \n')
        file.write('END')


def print_status_report(x_nodes, y_nodes, settlement_interpolated):
    '''
    Print a status report summarizing the interpolation for each load case.
    '''
    # Check if interpolated settlements have any nan values
    print('-------------------------------------------')
    print(f'    LC{lc}:')
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



print('-------------------------------------------')
print('RESULTS FROM SETTLEMENT INTERPOLATION SCRIPT')
for lc, settlement_known in settlements_known.items():

    ### D-WALL NODES ###
    # Read data file for structural points and their coordinates (To get D-wall bottom points)
    df_dwalls = pd.read_excel(f'{model_dir}\\dwall_nodes.xlsx', sheet_name='XLSX-Export')

    # Remove leading or trailing white space from column names
    df_dwalls.columns = df_dwalls.columns.str.strip()

    # Gather corner points of D-walls (x, y, z) where settlement values will be interpolated
    x_dwalls, y_dwalls, z_dwalls = df_dwalls['X [m]'], df_dwalls['Y [m]'], -df_dwalls['Z [m]']
    node_no_dwalls = df_dwalls['NR']

    ### BASE SLAB NODES ###
    # Read file with base slab node numbers and their coordinates into a dataframe
    df_slabs = pd.read_excel(f'{model_dir}\\base_slab_nodes.xlsx', sheet_name='XLSX-Export')

    # Remove leading or trailing white space from column names
    df_slabs.columns = df_slabs.columns.str.strip()

    '''
    Remove any potential nodes having Z > the base slab node with the largest Z-coordindate
    Sofistik sometimes fails to filter correctly. E.g. some nodes at beam dowels appear as being in the
    base slab. Note: Z-axis is modelled as positive downwards in Sofistik.
    '''
    Z_value_just_above_base_slab = -9.591
    df_slabs = df_slabs[df_slabs['Z [m]'] < Z_value_just_above_base_slab]
    # df_slabs.to_csv('df_slabs.txt', sep='\t')

    x_slabs, y_slabs, z_slabs = df_slabs['X [m]'], df_slabs['Y [m]'], df_slabs['Z [m]']
    node_no_slabs = df_slabs['NR']

    ### COMBINE BASE SLAB AND D-WALL DATA ###
    x_nodes = np.append(x_dwalls, x_slabs)
    y_nodes = np.append(y_dwalls, y_slabs)
    z_nodes = np.append(z_dwalls, z_slabs)
    node_no = np.append(node_no_dwalls, node_no_slabs)

    # ### COMBINE BASE SLAB AND D-WALL DATA ###
    # x_nodes = x_slabs
    # y_nodes = y_slabs
    # z_nodes = z_slabs
    # node_no = node_no_slabs

    ### PERFORM INTERPOLATION ###
    settlement_interpolated = interpolate_settlements(x_known, y_known, settlement_known,
                                                      x_nodes, y_nodes, method='cubic')

    ### PRINT STATUS REPORT FROM INTERPOLATION ###
    print_status_report(x_nodes, y_nodes, settlement_interpolated)

    ### WRITE INTERPOLATED FIELD TO .DAT FILE AS TEDDY CODE ###
    write_datfile(node_no, settlement_interpolated)




    def plot_3D_results(x_known, y_known, settlement_known, x, y, settlement_interpolated):
        '''
        Plot the result of the interpolation as a 3D scatter plot showing the known points that the
        interpolation is based on in green and the interpolated points in blue.
        '''

        # Create figure and axis object
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot known settlement points
        ax.scatter(x_known, y_known, settlement_known, '-.', color='limegreen')

        # Plot interpolated field
        ax.scatter(x, y, settlement_interpolated, '.', color='cornflowerblue', s=0.1)

        # Set limits
        # ax.set_xlim(6800, 7350)
        # ax.set_zlim(-22, -15)
        # ax.set_ylim(-100, 100)
        plt.show()
