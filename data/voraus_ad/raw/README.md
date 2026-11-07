# Raw data (not in the repository)

Put `voraus-ad-dataset-100hz.parquet` in this folder, or point `VORAUS_PARQUET` at it.

- Source: https://github.com/vorausrobotik/voraus-ad-dataset (download link in its README:
  `https://media.vorausrobotik.com/voraus-ad-dataset-100hz.parquet`, about 1.1 GB on disk,
  about 2.5 GB in memory).
- Licence: CC BY-NC-SA 4.0 (rights holder voraus robotik GmbH). The file is not redistributed here;
  `.gitignore` excludes `*.parquet` in this folder.
- Columns: 7 meta columns (`time`, `sample`, `anomaly`, `category`, `setting`, `action`, `active`)
  and 130 machine signals, listed in `../catalog/signals.csv`.
- The copy the committed products were built from: 1,115,942,833 bytes, SHA-256
  `c90ab1c78af52651b954d41787f7e89d750f0a128b57600b0e5ceec22621f704`; 2,321,690 rows in one row
  group (Snappy, written by parquet-cpp-arrow 6.0.0), already ordered by `sample` and `time`.
  Check yours with `sha256sum` (Linux), `shasum -a 256` (macOS) or `certutil -hashfile <file> SHA256`
  (Windows).
