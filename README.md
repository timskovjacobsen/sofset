# sofset
This program enables automatic generation of imposed displacement fields as load cases in the Finite Element software SOFiSTiK. 

The primary use case is for applying interpolated settlement fields to a structure based on an array of points known beforehand, e.g. from a detailed geotechnical analysis. 

## How It Works

1. Fill out Excel file with known points from a settlement curve
2. Output Excel file from Sofistik containing node numbers and X- and Y-coordinates of the nodes where a imposed displacement is desired
3. 
4. 
...

## Run Script Directly from SOFiSTiK
Running a Python script from inside a Teddy task in Sofistik is as easy as:

`+sys python script_name.py`

This is the same way you would run the code from the command line (accept for the `+sys`, which is SOFiSTiK's way of invoking the command line from within a Teddy task). 

**Note:** This assumes that you ahve the script in the same directory as the .sofistik file that the Teddy task resides in.  

### Example


```
+sys python settlement_interpolation/sofset.py
```
This is the same way you would run the code from the command line (accept for the `+sys`, which is SOFiSTiK's way of invoking the command line from within a Teddy task).

**Note:** The code assumes that in the same directory as the .sofistik file that the Teddy task resides in.

## Interpolation Method

The interpolation is performed by [scipy.interpolate.griddata](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) and thus follows the interpolation methods supported by that function. 

The methods of interpolation are ***linear***, ***cubic*** or ***nearest***, the latter of which is probably rarely useful for structural analysis purposes. Based on a few test cases for modelling of settlements on a tunnel project, the cubic interpolation performed best and generally does a better job of estimating structural displacements. 

## Assumptions

### Excel Input File
   * The name of the input Excel file must be ***known_settlement_values.xlsx***. The sheet with the values must have the same name. These are hardcoded into the script.

   * *Only* yellow cells may be changed.
   
   * Yellow cells must retain their exact cell numbers as these are hardcoded inside the script. Thus, the user must refrain from creating new rows or columns.     
   
   * All cells that are not yellow are not used or read by the script. Thus, these can hold any information, notes etc. that the user desires. 

### SOFiSTiK      
   * Nodes that are to receive an imposed displacement must be filtered inside SOFiSTiK and output to an Excel file called ***settlement_nodes.xlsx***. Every node accounted for in this Excel file gets an imposed displacement applied to it.
   
   * All imposed displacements are applied at nodes in the z-direction according to the local coordinate system of the element that the node is tied to.  


## Current Limitations

* Only four load combinations are supported (Although the code could easily be adjusted to support more). 

* The program is limited to five control points (known points) per section. Although it is questionable whether more points would be practicle. See description in the section on Control Points

## Control Points (known points)

Having too many control points can distort the interpolated field. Badly placed control point can show in the FE-results as very large sectional forces caused by the structure being "forced" down 
