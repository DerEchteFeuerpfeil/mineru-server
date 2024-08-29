BEFORE optimization:

root@aafccbce0b47:/app# du -sh /opt/*
2.8G    /opt/mineru_venv
12G     /opt/models

root@aafccbce0b47:/app# du -sh /opt/models/* | sort -h
4.0K    /opt/models/README.md
334M    /opt/models/MFD
538M    /opt/models/Layout
1.5G    /opt/models/TabRec
3.5G    /opt/models/MFR
5.9G    /opt/models/PDF-Extract-Kit


root@aafccbce0b47:/app# du -sh /opt/mineru_venv/lib/python3.10/site-packages/* | sort -h
...
31M     /opt/mineru_venv/lib/python3.10/site-packages/babel
36M     /opt/mineru_venv/lib/python3.10/site-packages/numpy
37M     /opt/mineru_venv/lib/python3.10/site-packages/numpy.libs
37M     /opt/mineru_venv/lib/python3.10/site-packages/skimage
39M     /opt/mineru_venv/lib/python3.10/site-packages/onnxruntime
41M     /opt/mineru_venv/lib/python3.10/site-packages/scipy.libs
48M     /opt/mineru_venv/lib/python3.10/site-packages/pymupdf
52M     /opt/mineru_venv/lib/python3.10/site-packages/sklearn
56M     /opt/mineru_venv/lib/python3.10/site-packages/sympy
63M     /opt/mineru_venv/lib/python3.10/site-packages/opencv_python_headless.libs
66M     /opt/mineru_venv/lib/python3.10/site-packages/pandas
75M     /opt/mineru_venv/lib/python3.10/site-packages/transformers
88M     /opt/mineru_venv/lib/python3.10/site-packages/cv2
92M     /opt/mineru_venv/lib/python3.10/site-packages/opencv_contrib_python.libs
92M     /opt/mineru_venv/lib/python3.10/site-packages/opencv_python.libs
105M    /opt/mineru_venv/lib/python3.10/site-packages/scipy
127M    /opt/mineru_venv/lib/python3.10/site-packages/pyarrow
450M    /opt/mineru_venv/lib/python3.10/site-packages/paddle
712M    /opt/mineru_venv/lib/python3.10/site-packages/torch
root@aafccbce0b47:/app#

--------------------------------------------------------------------------------
AFTER optimization:

root@8d2483c00b85:/app# du -sh /opt/*
2.8G    /opt/mineru_venv
5.9G    /opt/models

root@8d2483c00b85:/app# du -sh /opt/models/* | sort -h
4.0K    /opt/models/README.md
8.0K    /opt/models/PDF-Extract-Kit
334M    /opt/models/MFD
538M    /opt/models/Layout
1.5G    /opt/models/TabRec
3.5G    /opt/models/MFR
