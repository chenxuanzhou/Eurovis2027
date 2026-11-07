# Raw data (not in the repository)

The committed products were extracted from `AURSAD.h5` of the Zenodo record
https://zenodo.org/records/4559556 (version 1.1, CC BY 4.0; 6,417,816,949 bytes,
MD5 `08e4706cf15144761a12cb86bd071d72`, the same file as in version 1.0). The record also has
`AURSAD.pkl` with the same content; it is not needed. To re-extract, put `AURSAD.h5` here (or point
`AURSAD_H5` at it) and run

```bash
python pipeline/aursad/run.py
```

`extract.py` reads the pandas "fixed" HDF5 store (key `complete_data`) in row chunks with h5py, needs
numpy, pandas, pyarrow and h5py, about 1 minute and less than 1.5 GB of memory.
