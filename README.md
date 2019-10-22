# sofset
This program automatically generaties load cases of interpolated imposed displacement in the Finite Element software SOFiSTiK. It does so by receiving a set of known imposed displacements to interpolate from and a set of nodes to interpolate to. 

The primary use case is for applying interpolated settlement fields to a structure based on an array of points known beforehand, e.g. from a detailed geotechnical analysis. 

## How It Works

**Note:** You need to have Python installed with the necessary dependencies to run this program. See section on Dependencies furhter down.

1. **Download the [Python script](https://github.com/timskovjacobsen/sofset/blob/master/sofset/sofset.py).**

2. **Fill out the input Excel file called `known_settlement_values.xlsm`** with known points from a settlement curve and desired load case number, title and interpolation method.  
Download the input file here: [known_settlement_values.xlsx](https://github.com/timskovjacobsen/sofset/raw/master/input/known_settlement_values.xlsx)
3. **Create an output Excel file from Sofistik called `nodes_to_be_interpolated.xlsx`** containing node numbers and X- and Y-coordinates of the nodes where imposed displacements are to be applied. SOFiSTiK (2018 version at least) has a built-in feature for `.xlsx`-exports via ResultViewver, see e.g. [SOFiSTiK Excel Export](https://www.sofistik.de/documentation/2018/en/tutorials/listoftutorials/general-workflows/export_results_to_excel.htm). 
4. **Execute the script** from inside a Teddy task in SOFiSTiK by the command `+sys python settlement_interpolation/sofset.py`. See further explanation below. This creates a `.dat`-file with `SOFILOAD` code for each interpolated settlement load case.
5. **Apply the `SOFILOAD` code for each load case to the FE-model** by running `+apply name_of_dat_file` from Teddy. The syntax for the generated `.dat`-files is `teddy_code_settlement_field_LC{load_case_number}.dat`

After that, the load case should be visible in WinGraf.

The SOFiSTiK model folder structure should look like this:
```
model_folder
├── settlement_interpolation        # Subfolder
|   ├── known_settlements.xlsm      # Input Excel file to script
|   ├── sofset.py                   # Python script 
|
├── model_name.sofistik             # Sofistik model
├── model_name.dwg                  # Sofiplus (autocad) model

├── ...                             # Any other files

├── nodes_to_be_interpolated.xlsx   # Excel output from Sofistik, input to script
```
**Note:** The two Excel files that the script reads must have the exact names specified above!

### Visualization of interpolation
The screenshot below shows the green control points (i.e. the known points) and the interpolated values in the FE-nodes that were input to the program
![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Interpolation_3D_plot.PNG)

### Application of load case in SOFiSTiK
The resul of applying the load cases in SOFiSTiK by executing the generated `.dat`-files is shown below
![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Settlements_interpolated_by_Python.PNG)

![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Settlements_interpolated_by_Python_XZ_plane.PNG)

## Run Script Directly from SOFiSTiK
Running the Python script from inside a Teddy task in Sofistik is as easy as:

```
+sys python settlement_interpolation/sofset.py
```
This is the same way you would run the code from the command line (accept for the `+sys`, which is SOFiSTiK's way of invoking the command line from within a Teddy task).

**Note:** Since the script is being frun from the directory where the `.sofistik` files resides, it is necessary to prepend the `settlement_interpolation` folder to the path when calling the script.

<!-- ## Dependencies
TODO: The dependencies for the script are listed in the file called `requirements.txt`. -->

## Interpolation Method

The interpolation is performed by [scipy.interpolate.griddata](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) and thus follows the interpolation methods supported by that function. 

The methods of interpolation are ***linear***, ***cubic*** or ***nearest***, the latter of which is probably rarely useful for structural analysis purposes. Based on a few test cases for modelling of settlements on a tunnel project, the cubic interpolation performed best and generally does a better job of estimating structural displacements. 

## Assumptions

### Excel Input File
   * The name of the input Excel file must be ***known_settlement_values.xlsx***. The sheet with the values must have the same name. These are hardcoded into the script.    

### SOFiSTiK      
   * Nodes that are to receive an imposed displacement must be filtered inside SOFiSTiK and output to an Excel file called ***settlement_nodes.xlsx***. Every node accounted for in this Excel file gets an imposed displacement applied to it.
   
   * All imposed displacements are applied at nodes in the z-direction according to the local coordinate system of the element that the node is tied to.  

## Current Limitations

* Only four load combinations are supported (Although the code could easily be adjusted to support more). 

* The program is limited to five control points (known points) per section. Although it is questionable whether having more points would be practicle. See description below.

## Locaition of Control Points (known points)

Having too many or badly located control points can distort the interpolated field. The distortion is to be understood from a structural standpoint where abrupt geometry changes can lead to very large sectional forces from linear elastic FE-calculations. E.g. if two points are very close to eachother, even a very small difference in their imposed displacement value can have this effect. 

Through testing on projects it has been discovered that using 2D-interpolation (i.e. in both X- and Y-direction) can lead to distortions when imposed displacement values are large, e.g. for long-term settlement cases. Even using constant Y-values in the same section can cause a non-uniform settlement in the section.  
This distortion can be inspected visually by plotting isolines for the solved displacements.
<!-- TODO: Show screenshots explaining this -->

If this problem arises, consider whether variation in the Y-direction is really necessary or the model can live with having the settlements vary only in the longitudinal direction. When interpolating only in the X-direction, the isolines for solved displacements should be exactly uniform within each section.
<!-- TODO: Show screenshots explaining this -->

## Excel Input Sheet Protection
The input Excel sheet is by default protected in all cells that are not input cells to avoid changing the layout by mistake. The script assumes a certian layout in order to detect the input values correctly. If necessary, use the passwork `sofset` to clear the cell protection if you want to take notes in the sheet etc. Otherwise create new sheets to do so.

## Bugs and Improvements 
If you have discovered a bug or wish for a new feature to be implemented, please create an Issue via GitHub with a good description.

<!-- ## Contributions TODO: Add markdown file describing how to contribute-->


