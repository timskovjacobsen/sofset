# sofset
Creating load cases of imposed displacements in SOFiSTiK models.


## How It Works

1. Fill out Excel file with known points from a settlement curve
2. Output Excel file from Sofistik containing node numbers and X- and Y-coordinates of the nodes where a imposed displacement is desired
3. 
4. 
...

## Run Script Directly from SOFiSTiK
`+sys ....`


## Interpolation Method

The interpolation is performed by [scipy.interpolate.griddata](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html) and thus follows the interpolation methods supported by that function. 

The methods of interpolation are ***linear***, ***cubic*** or ***nearest***, the latter of which is probably rarely useful for structural analysis purposes. Based on a few test cases for modelling of settlements on a tunnel project, the cubic interpolation performed best and generally does a better job of estimating structural displacements. 

## Assumptions

   * **Excel Input File:** The name of the input Excel file must be ***known_settlement_values.xlsx***. The sheet with the values must have the same name. These are hardcoded into the script.

   * **Excel Input File:** *Only* yellow cells may be changed.
   
   * **Excel Input File:** Yellow cells must retain their exact cell numbers as these are hardcoded inside the script. Thus, the user must refrain from creating new rows or columns.     
   
   * **Excel Input File:** All cells that are not yellow are not used or read by the script. Thus, these can hold any information, notes etc. that the user desires. 
      
   * **SOFiSTiK:** Nodes that are to receive an imposed displacement must be filtered inside SOFiSTiK and output to an Excel file called ***settlement_nodes.xlsx***. Every node accounted for in this Excel file gets an imposed displacement applied to it.
   
   * **SOFiSTiK:** All imposed displacements are applied at nodes in the z-direction according to the local coordinate system of the element that the node is tied to.  


## Current Limitations

* Only four load combinations are supported (Although the code could easily be adjusted to support more). 

* There is not a lot of input parameters to the script. 
