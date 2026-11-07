# Raw data (in the repository)

`lp1.data` … `lp5.data` are the original files of the UCI dataset "Robot Execution Failures"
(doi:10.24432/C5M89N, CC BY 4.0), unchanged.

The UCI site was not reachable from the build environment, so the files were taken from four
independent copies on GitHub (marcopeix/time-series-classification-in-python,
WWW5911/Robot-Execution-Failures, 7houce/cluster_ensemble, MaxBenChrist/robot-failure-dataset). All
four agree byte for byte except one corrupted copy of `lp2.data`, which was ignored. The instance counts
(88, 47, 47, 117, 164), the class shares and the file sizes match the UCI description, and
`pipeline/robot_failures/build.py` refuses files whose SHA-256 differs from:

| File | SHA-256 |
|---|---|
| lp1.data | e146de5aeaffd864f0e57ce2fe0b58e98582c3e808e6c0e8deb9b25a54ef0cb5 |
| lp2.data | 565096a67cc8b9e4cef299316b3ab769054215a6342636e208611eafa780f950 |
| lp3.data | 38e5cb0b22477772a03edee82599591375790cb945cf1256ed0a4b516cc30e1a |
| lp4.data | f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c |
| lp5.data | 0f327415504dccec9509a84f6fa7aea9ebc28e5fa85f2f00933c90565d51108d |
