# sofset

This program automatically generates load cases of interpolated imposed displacement in the Finite Element software SOFiSTiK. It does so by receiving a set of known imposed displacements to interpolate from and a set of nodes to interpolate to.

The primary use case is for applying interpolated settlement fields to a structure based on an array of points known beforehand, e.g. from a detailed geotechnical analysis.

## How It Works

**Note:** You need to have Python installed with the necessary dependencies to run this program. See section on Dependencies further down.

1. **Download the latest release here: [sofset_v0.1.1.zip](https://github.com/timskovjacobsen/sofset/releases/download/v0.1.1/sofset.zip).** This zip-folder contains the input `.xlsm` file and the script `sofset.py`.

2. **Fill out the input Excel file called `known_settlement_values.xlsm`** with known points from a settlement curve and desired load case number, title and interpolation method.  

3. **Create an output Excel file from Sofistik called `nodes_to_be_interpolated.xlsx`** containing node numbers and X- and Y-coordinates of the nodes where imposed displacements are to be applied. SOFiSTiK (2018 version at least) has a built-in feature for `.xlsx`-exports via ResultViewver, see e.g. [SOFiSTiK Excel Export](https://www.sofistik.de/documentation/2018/en/tutorials/listoftutorials/general-workflows/export_results_to_excel.htm).

4. **Execute the script** from inside a Teddy task in SOFiSTiK by the command `+sys python insert_path_to_script`. See further explanation below. This creates a `.dat`-file with `SOFILOAD` code for each interpolated settlement load case.
5. **Apply the `SOFILOAD` code for each load case to the FE-model** by running `+apply insert_name_of_dat_file` from Teddy. The syntax for the generated `.dat`-files is `settlement_LC{load_case_number}.dat`

After that, the load case should be visible in WinGraf.

The SOFiSTiK model folder structure should look like this:

```markdown
model_folder
├── Settlement_interpolation        # Subfolder
|   ├── known_settlements.xlsm      # Input Excel file to script
|
├── model_name.sofistik             # Sofistik model
├── model_name.dwg                  # Sofiplus (autocad) model

├── ...                             # Any other files

├── nodes_to_be_interpolated.xlsx   # Excel output from Sofistik, input to script
```

**Note:** The two Excel files that the script reads must have the exact names specified above!

## Run Script Directly from SOFiSTiK

Running the Python script from inside a Teddy task in Sofistik is as easy as:

```markdown
+sys python insert_path_to_script
```

This is the same way you would run the code from the command line (accept for the `+sys`, which is SOFiSTiK's way of invoking the command line from within a Teddy task).

E.g. if the script was located in the subfolder `Settlement_interpolation`, the call to it would look like:

```markdown
+sys python Settlement_interpolation\sofset.py
```

### Where to put the script

The script (`sofset.py` file) can be placed wherever in the file system. Just make sure that you insert the correct path to it when calling it from Teddy. The code auto-detects the path from which it was invoked, i.e. the folder containing the `.sofistik` file. From there it navigates to the input files, so they have to comply with the folder structure shown above.

**It is recommended to keep the script in a central location and call it from there.** This way, every version of the Sofistik model refers to the same script and it eliminates the need for creating new copies with each version.

<!-- ## Dependencies
TODO: The dependencies for the script are listed in the file called `requirements.txt`. -->

### Visualization of interpolation

The screenshot below shows the green control points (i.e. the known points) and the interpolated values in the FE-nodes that were input to the program
![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Interpolation_3D_plot.PNG)

### Application of load case in SOFiSTiK

An example of applying the load cases in SOFiSTiK by executing a generated `.dat`-file is shown below:
![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Settlements_interpolated_by_Python.PNG)

![3D_plot from script](https://github.com/timskovjacobsen/sofset/blob/assets/Settlements_interpolated_by_Python_XZ_plane.PNG)

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

* The program is limited to five control points (known points) per section. Although it is questionable whether having more points would be practical. See description below.

## Location of Control Points (known points)

Having too many or badly located control points can distort the interpolated field. The distortion is to be understood from a structural standpoint where abrupt geometry changes can lead to very large sectional forces from linear elastic FE-calculations. E.g. if two points are very close to each other, even a very small difference in their imposed displacement value can have this effect.

Through testing on projects it has been discovered that using 2D-interpolation (i.e. in both X- and Y-direction) can lead to distortions when imposed displacement values are large, e.g. for long-term settlement cases. Even using constant Y-values in the same section can cause a non-uniform settlement in the section.  
This distortion can be inspected visually by plotting isolines for the solved displacements.
<!-- TODO: Show screenshots explaining this -->

If this problem arises, consider whether variation in the Y-direction is really necessary or the model can live with having the settlements vary only in the longitudinal direction. When interpolating only in the X-direction, the isolines for solved displacements should be exactly uniform within each section.
<!-- TODO: Show screenshots explaining this -->

## Excel Input Sheet Protection

The input Excel sheet is by default protected in all cells that are not input cells to avoid changing the layout by mistake. The script assumes a certain layout in order to detect the input values correctly. If necessary, the cells can be unprotected from the "Review" tab.
There is not password.

## Bugs and Improvements

If you have discovered a bug or wish for a new feature to be implemented, please create an Issue via GitHub with a good description.

<!-- ## Contributions TODO: Add markdown file describing how to contribute-->
