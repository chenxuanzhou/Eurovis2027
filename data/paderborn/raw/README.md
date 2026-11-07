# Raw data (not in the repository)

The committed products were extracted from the original KAt-DataCenter `.mat` files of 12 bearings
(K001–K004, KA04, KA15, KA16, KA22, KI04, KI14, KI16, KI18; 80 files each, about 8.4 GB), downloaded
from https://mb.uni-paderborn.de/kat/forschung/kat-datacenter/bearing-datacenter (CC BY-NC 4.0; the
data are not redistributed here). To re-extract, unpack the bearing folders here (or point
`PADERBORN_RAW` at them) so that the layout is `<code>/N15_M07_F10_<code>_1.mat` etc., then run

```bash
python pipeline/paderborn/run.py
```

`extract.py` caches each file under `raw/_cache/`, so an interrupted run resumes. It needs numpy, scipy,
pandas and pyarrow, takes about 0.3 s per file and less than 1 GB of memory.
