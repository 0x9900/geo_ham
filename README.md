# GEO_HAM

The library geo_ham a small library to transform gps coordinates in maidehead grid squares and vice versa.

## Example

```
In [1]: import geo_ham

In [2]: geo_ham.grid2latlon('CM87un', center=True)
Out[2]: (37.5625, -122.29166666666666)

In [3]: geo_ham.latlon2grid(37.5525, -122.291)
Out[3]: 'CM87un'

In [4]:
```
