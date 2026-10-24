# SpikeAnalysisServer

Spike-analysis server for the client/server workflow.


## Requirements

Create a virtual environment and install the Python dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Local configuration

Copy GUI_support/settings/user_info_data.example.json to GUI_support/settings/user_info_data.json and replace the placeholder password before use. Use opaque account and folder aliases. The real account file is excluded from Git.

Set SPIKE_DATA_ROOT to the recording-data directory (default: ./data). Set KILOSORT_PATH, KILOSORT2_PATH and/or KILOSORT3_PATH to locally installed sorter directories.

Local processing uses ~/Documents/SpikeAnalysisCache/ as disposable scratch space. Keep permanent data outside that directory.

Install the external Kilosort tools required by your workflow before launching SpikeAnalysisServer.py. Run only on a trusted network; this publication cleanup does not add transport encryption or redesign authentication.

Version 1 contributor: Jinyu Zang
