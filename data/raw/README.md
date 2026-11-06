# Raw data (not in the repository)

Put `voraus-ad-dataset-100hz.parquet` in this folder, or point `VORAUS_PARQUET` at it.

- Source: https://github.com/vorausrobotik/voraus-ad-dataset (download link in its README:
  `https://media.vorausrobotik.com/voraus-ad-dataset-100hz.parquet`, about 1.1 GB on disk,
  about 2.5 GB in memory).
- Licence: CC BY-NC-SA 4.0 (rights holder voraus robotik GmbH). The file is not redistributed here;
  `.gitignore` excludes `*.parquet` in this folder.
- Columns: 7 meta columns (`time`, `sample`, `anomaly`, `category`, `setting`, `action`, `active`)
  and 130 machine signals, listed in `../catalog/signals.csv`.
